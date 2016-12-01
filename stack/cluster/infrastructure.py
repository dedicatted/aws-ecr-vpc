from awacs import ecr
from troposphere import (
    AWS_REGION,
    AWS_STACK_ID,
    AWS_STACK_NAME,
    autoscaling,
    Base64,
    cloudformation,
    FindInMap,
    GetAtt,
    iam,
    Join,
    Parameter,
    Ref,
    Output
)

from troposphere.ec2 import (
    SecurityGroup,
    SecurityGroupRule,
)

from troposphere.ecs import (
    Cluster,
)

from troposphere import elasticloadbalancing as elb

from troposphere.autoscaling import (
    LaunchConfiguration,
    Metadata,
    AutoScalingGroup
)

from stack.template import template
from stack.vpc import (
    vpc_id,
	public_subnet,
    default_security_group,
	instance_type,
	secret_key
)



repo_id = "424632819416.dkr.ecr.us-west-2.amazonaws.com"

template.add_mapping("ECSRegionMap", {
    "eu-central-1": {"AMI": "ami-54f5303b"},
    "eu-west-1": {"AMI": "ami-4e6ffe3d"},
    "us-east-1": {"AMI": "ami-8f7687e2"},
    "us-west-2": {"AMI": "ami-84b44de4"},
    "us-west-1": {"AMI": "ami-9fadf8ff"},
})

instance_security_group = SecurityGroup(
    'InstanceSecurityGroup',
    template=template,
    GroupDescription="Instance security group.",
    VpcId=Ref(vpc_id),
    SecurityGroupIngress=[
        SecurityGroupRule(
            IpProtocol='-1',
            FromPort='-1',
            ToPort='-1',
            CidrIp='0.0.0.0/0',
        )
    ]
)

load_balancer = elb.LoadBalancer(
    'LoadBalancer',
    template=template,
    Subnets=[
        Ref(public_subnet),
    ],
    SecurityGroups=[Ref(default_security_group), Ref(instance_security_group)],
    Listeners=[
		elb.Listener(
        LoadBalancerPort=80,
        InstanceProtocol='HTTP',
        InstancePort=8080,
        Protocol='HTTP'
		),
		elb.Listener(
        LoadBalancerPort=3000,
        InstanceProtocol='tcp',
        InstancePort=3000,
        Protocol='tcp'
		),
		elb.Listener(
        LoadBalancerPort=3001,
        InstanceProtocol='tcp',
        InstancePort=3001,
        Protocol='tcp'
		),
		elb.Listener(
        LoadBalancerPort=3002,
        InstanceProtocol='tcp',
        InstancePort=3002,
        Protocol='tcp'
		),
	],
    HealthCheck=elb.HealthCheck(
        Target=Join("", ["HTTP:", 8080, "/"]),
        HealthyThreshold="2",
        UnhealthyThreshold="2",
        Interval="100",
        Timeout="10",
    ),
#    CrossZone=True,
)

template.add_output(Output(
    "LoadBalancerDNSName",
    Description="Loadbalancer DNS",
    Value=Join("", ["http://", GetAtt(load_balancer, "DNSName")])
))

# ECS cluster
main_cluster = Cluster(
    "MainCluster",
    ClusterName="MainCluster",
    template=template,
)

# ECS container role
container_instance_role = iam.Role(
    "ContainerInstanceRole",
    template=template,
    AssumeRolePolicyDocument=dict(Statement=[dict(
        Effect="Allow",
        Principal=dict(Service=["ec2.amazonaws.com"]),
        Action=["sts:AssumeRole"],
    )]),
    Path="/",
    Policies=[
        iam.Policy(
            PolicyName="ECSManagementPolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "ecs:*",
                        "elasticloadbalancing:*",
                    ],
                    Resource="*",
                )],
            ),
        ),
        iam.Policy(
            PolicyName='ECRManagementPolicy',
            PolicyDocument=dict(
                Statement=[dict(
                    Effect='Allow',
                    Action=[
                        ecr.GetAuthorizationToken,
                        ecr.GetDownloadUrlForLayer,
                        ecr.BatchGetImage,
                        ecr.BatchCheckLayerAvailability,
                    ],
                    Resource="*",
                )],
            ),
        ),
        iam.Policy(
            PolicyName="LoggingPolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "logs:Create*",
                        "logs:PutLogEvents",
                    ],
                    Resource="arn:aws:logs:*:*:*",
                )],
            ),
        ),
    ]
)

# ECS container instance profile
container_instance_profile = iam.InstanceProfile(
    "ContainerInstanceProfile",
    template=template,
    Path="/",
    Roles=[Ref(container_instance_role)],
)

container_instance_configuration_name = "MainContainerLaunchConfiguration"

container_instance_configuration = LaunchConfiguration(
    container_instance_configuration_name,
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
                                % container_instance_configuration_name,
                                "Metadata.AWS::CloudFormation::Init\n",
                                "action=/opt/aws/bin/cfn-init -v ",
                                "         --stack",
                                Ref(AWS_STACK_NAME),
                                "         --resource %s"
                                % container_instance_configuration_name,
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
    SecurityGroups=[Ref(default_security_group), Ref(instance_security_group)],
	AssociatePublicIpAddress=True,
    InstanceType=instance_type,
    ImageId=FindInMap("ECSRegionMap", Ref(AWS_REGION), "AMI"),
    IamInstanceProfile=Ref(container_instance_profile),
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "yum install -y aws-cfn-bootstrap\n",

        "/opt/aws/bin/cfn-init -v ",
        "         --stack ", Ref(AWS_STACK_NAME),
        "         --resource %s " % container_instance_configuration_name,
        "         --region ", Ref(AWS_REGION), "\n",
    ]))
)

autoscaling_group_name = "ECSAutoScalingGroup"
AutoScalingGroup(
    autoscaling_group_name,
    template=template,
    VPCZoneIdentifier=[Ref(public_subnet)],
    MinSize=1,
    MaxSize=1,
    DesiredCapacity=1,
    LaunchConfigurationName=Ref(container_instance_configuration),
	DependsOn=["LoadBalancer"],
    # Since one instance within the group is a reserved slot
    # for rolling ECS service upgrade, it's not possible to rely
    # on a "dockerized" `ELB` health-check, else this reserved
    # instance will be flagged as `unhealthy` and won't stop respawning'
    HealthCheckType="EC2",
    HealthCheckGracePeriod=300,
    Tags=[autoscaling.Tag("Name", "ecs-auto-scaling-group-instances", True)],
)

app_service_role = iam.Role(
    "AppServiceRole",
    template=template,
    AssumeRolePolicyDocument=dict(Statement=[dict(
        Effect="Allow",
        Principal=dict(Service=["ecs.amazonaws.com"]),
        Action=["sts:AssumeRole"],
    )]),
    Path="/",
    Policies=[
        iam.Policy(
            PolicyName="WebServicePolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "elasticloadbalancing:Describe*",
                        "elasticloadbalancing"
                        ":DeregisterInstancesFromLoadBalancer",
                        "elasticloadbalancing"
                        ":RegisterInstancesWithLoadBalancer",
                        "ec2:Describe*",
                        "ec2:AuthorizeSecurityGroupIngress",
                    ],
                    Resource="*",
                )],
            ),
        ),
    ]
)
