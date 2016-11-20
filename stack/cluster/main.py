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
    container_instance_profile,
    load_balancer
)

from troposphere.ecs import (
    ContainerDefinition,
    Environment,
    LogConfiguration,
    VolumesFrom,
    Volume,
    MountPoint,
    PortMapping,
    TaskDefinition,
    Service,
    LoadBalancer
)

from stack.template import template

from stack.cluster.infrastructure import autoscaling_group_name, app_service_role

simple_app_task_definition = TaskDefinition(
    "SimpleApp",
    template=template,
    ContainerDefinitions=[
        ContainerDefinition(
            Name="simple-app",
            Cpu="10",
            Memory="100",
            Essential=True,
            Image="httpd:2.4",
            MountPoints=[MountPoint(
                ContainerPath="/usr/local/apache2/htdocs",
                SourceVolume="my-vol"
            )]
        ),
        ContainerDefinition(
            Name="busybox",
            Cpu="10",
            Memory="100",
            Essential=False,
            Image="busybox",
            Command=[
                "/bin/sh -c \"while true; do echo '<html> <head> <title>Amazon ECS Sample App</title> <style>body {margin-top: 40px; background-color: #333;} </style> </head><body> <div style=color:white;text-align:center> <h1>Amazon ECS Sample App</h1> <h2>Congratulations!</h2> <p>Your application is now running on a container in Amazon ECS.</p>' > top; /bin/date > date ; echo '</div></body></html>' > bottom; cat top date bottom > /usr/local/apache2/htdocs/index.html ; sleep 1; done\""
            ],
            VolumesFrom=[VolumesFrom(
                SourceContainer="simple-app",
            )]
        )],
    Volumes=[Volume(
        Name="my-vol"
    )]
)

app_service = Service(
    "AppService",
    template=template,
    Cluster=Ref(main_cluster),
    DependsOn=[autoscaling_group_name],
    DesiredCount=1,
    LoadBalancers=[LoadBalancer(
        ContainerName="simple-app",
        ContainerPort=80,
        LoadBalancerName=Ref(load_balancer),
    )],
    TaskDefinition=Ref(simple_app_task_definition),
    Role=Ref(app_service_role),
)
