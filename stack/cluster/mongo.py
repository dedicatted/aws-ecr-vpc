from troposphere import (
    AWS_REGION,
    AWS_STACK_ID,
    AWS_STACK_NAME,
    autoscaling,
    Base64,
    cloudformation,
    FindInMap,
    GetAtt,
    Join,
    Ref,
)

from stack.cluster.infrastructure import (
    secret_key,
    main_cluster,
    container_instance_type,
    container_security_group,
    container_instance_profile
)

from stack.template import template
from stack.vpc import (
    vpc,
    unsafe_security_group,
    container_a_subnet,
    container_b_subnet
)

from troposphere.autoscaling import (
    LaunchConfiguration,
    Metadata,
    AutoScalingGroup
)

mongo_container_instance_configuration_name = "MongoMainContainerLaunchConfiguration"

mongo_container_instance_configuration = LaunchConfiguration(
    mongo_container_instance_configuration_name,
    template=template,
    KeyName=Ref(secret_key),
    Metadata=Metadata(
        cloudformation.Init(dict(
            config=cloudformation.InitConfig(
                commands=dict(
                    register_cluster=dict(command=Join("", [
                        "#!/bin/bash\n",
                        # Register the cluster
                        "echo ECS_CLUSTER=",
                        Ref(main_cluster),
                        " >> /etc/ecs/ecs.config\n",
                        # Enable CloudWatch docker logging
                        'echo \'ECS_AVAILABLE_LOGGING_DRIVERS=',
                        '["json-file","awslogs"]\'',
                        " >> /etc/ecs/ecs.config\n",
                    ]))
                ),
                files=cloudformation.InitFiles({
                    "/etc/cfn/cfn-hup.conf": cloudformation.InitFile(
                        content=Join("", [
                            "[main]\n",
                            "template=",
                            Ref(AWS_STACK_ID),
                            "\n",
                            "region=",
                            Ref(AWS_REGION),
                            "\n",
                        ]),
                        mode="000400",
                        owner="root",
                        group="root",
                    ),
                    "/etc/cfn/hooks.d/cfn-auto-reload.conf":
                        cloudformation.InitFile(
                            content=Join("", [
                                "[cfn-auto-reloader-hook]\n",
                                "triggers=post.update\n",
                                "path=Resources.%s."
                                % mongo_container_instance_configuration_name,
                                "Metadata.AWS::CloudFormation::Init\n",
                                "action=/opt/aws/bin/cfn-init -v ",
                                "         --stack",
                                Ref(AWS_STACK_NAME),
                                "         --resource %s"
                                % mongo_container_instance_configuration_name,
                                "         --region ",
                                Ref("AWS::Region"),
                                "\n",
                                "runas=root\n",
                            ])
                        )
                }),
                services=dict(
                    sysvinit=cloudformation.InitServices({
                        'cfn-hup': cloudformation.InitService(
                            enabled=True,
                            ensureRunning=True,
                            files=[
                                "/etc/cfn/cfn-hup.conf",
                                "/etc/cfn/hooks.d/cfn-auto-reloader.conf",
                            ]
                        ),
                    })
                )
            )
        ))
    ),
    SecurityGroups=[Ref(container_security_group), GetAtt(vpc, "DefaultSecurityGroup"), Ref(unsafe_security_group)],
    InstanceType=container_instance_type,
    ImageId=FindInMap("ECSRegionMap", Ref(AWS_REGION), "AMI"),
    IamInstanceProfile=Ref(container_instance_profile),
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "yum install -y aws-cfn-bootstrap\n",

        "/opt/aws/bin/cfn-init -v ",
        "         --stack ", Ref(AWS_STACK_NAME),
        "         --resource %s " % mongo_container_instance_configuration_name,
        "         --region ", Ref(AWS_REGION), "\n",
    ]))
)

AutoScalingGroup(
    "MongoECSAutoScalingGroup",
    template=template,
    VPCZoneIdentifier=[Ref(container_a_subnet), Ref(container_b_subnet)],
    MinSize=1,
    MaxSize=1,
    DesiredCapacity=1,
    LaunchConfigurationName=Ref(mongo_container_instance_configuration),
    # Since one instance within the group is a reserved slot
    # for rolling ECS service upgrade, it's not possible to rely
    # on a "dockerized" `ELB` health-check, else this reserved
    # instance will be flagged as `unhealthy` and won't stop respawning'
    HealthCheckType="EC2",
    HealthCheckGracePeriod=300,
    Tags=[autoscaling.Tag("Name", "mongo-ag-instance", True)],
)
