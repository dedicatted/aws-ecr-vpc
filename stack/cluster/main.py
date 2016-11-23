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
    LoadBalancer,
	HostEntry
)

from stack.template import template

from stack.cluster.infrastructure import autoscaling_group_name, app_service_role, repo_id

from stack.cluster.mongo import mongo_instance

bigid_task_definition = TaskDefinition(
    "BigIdTask",
    template=template,
    ContainerDefinitions=[
        ContainerDefinition(
            Name="bigid-web",
			Memory="100",
            Essential=False,
            Image=Join("", [
                Ref(repo_id),
                "/bigid-web",
            ]),
            PortMappings=[PortMapping(
                ContainerPort="3000",
                HostPort="3000"
            )],
			Links=["bigid-orch"],
			ExtraHosts=[HostEntry(
				Hostname="bigid-mongo",
				IpAddress=GetAtt(mongo_instance, "PrivateIp")
			)],
			Environment=[
                Environment(
                    Name="BIGID_MONGO_USER",
                    Value="Value",
                ),
                Environment(
                    Name="BIGID_MONGO_PWD",
                    Value="Value",
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-orch",
			Memory="100",
            Essential=False,
            Image=Join("", [
                Ref(repo_id),
                "/bigid-orch",
            ]),
            PortMappings=[PortMapping(
                ContainerPort="3001",
                HostPort="3001"
            )],
			Links=["bigid-scanner"],
			ExtraHosts=[HostEntry(
				Hostname="bigid-mongo",
				IpAddress=GetAtt(mongo_instance, "PrivateIp")
			)],
			Hostname="bigid-orch",
			Environment=[
                Environment(
                    Name="BIGID_MONGO_USER",
                    Value="Value",
                ),
                Environment(
                    Name="BIGID_MONGO_PWD",
                    Value="Value",
                ),
				Environment(
                    Name="ORCHESTRATOR_URL_EXT",
                    Value="Value",
                ),
                Environment(
                    Name="BIGID_MONGO_HOST_EXT",
                    Value="Value",
                ),
				Environment(
                    Name="SAVE_SCANNED_IDENTITIES_AS_PII_FINDINGS",
                    Value="Value",
                ),
                Environment(
                    Name="SCANNED_VALUES_IGNORE_LIST",
                    Value="Value",
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-corr",
			Memory="100",
            Essential=False,
            Image=Join("", [
                Ref(repo_id),
                "/bigid-corr",
            ]),
            PortMappings=[PortMapping(
                ContainerPort="3002",
                HostPort="3002"
            )],
			Links=["bigid-orch"],
			ExtraHosts=[HostEntry(
				Hostname="bigid-mongo",
				IpAddress=GetAtt(mongo_instance, "PrivateIp")
			)],
			Hostname="bigid-corr",
			Environment=[
                Environment(
                    Name="BIGID_MONGO_USER",
                    Value="Value",
                ),
                Environment(
                    Name="BIGID_MONGO_PWD",
                    Value="Value",
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-scanner",
			Memory="100",
            Essential=False,
			Privileged=True,
            Image=Join("", [
                Ref(repo_id),
                "/bigid-scanner",
            ]),
			ExtraHosts=[HostEntry(
				Hostname="bigid-mongo",
				IpAddress=GetAtt(mongo_instance, "PrivateIp")
			)],
            PortMappings=[
				PortMapping(
					ContainerPort="9999",
					HostPort="9999"
				),
				PortMapping(
					ContainerPort="2049",
					HostPort="2049"
				),
				PortMapping(
					ContainerPort="2049",
					HostPort="2049",
					Protocol="udp"
				),
				PortMapping(
					ContainerPort="111",
					HostPort="111",
				),
				PortMapping(
					ContainerPort="111",
					HostPort="111",
					Protocol="udp"
				),
			],
			Environment=[
                Environment(
                    Name="JAVA_OPTS",
                    Value="-Xmx1024m",
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-ui",
			Memory="100",
            Essential=True,
            Image=Join("", [
                Ref(repo_id),
                "/bigid-ui",
            ]),
            PortMappings=[PortMapping(
                ContainerPort="8080",
                HostPort="8080"
            )],
			Environment=[
                Environment(
                    Name="BIG_ID_API_ENDPOINT",
                    Value="Value",
                ),
			],
        ),
    ],
)

app_service = Service(
    "AppService",
    template=template,
    Cluster=Ref(main_cluster),
    DependsOn=[autoscaling_group_name],
    DesiredCount=1,
    LoadBalancers=[LoadBalancer(
        ContainerName="bigid-ui",
        ContainerPort=8080,
        LoadBalancerName=Ref(load_balancer),
    )],
    TaskDefinition=Ref(bigid_task_definition),
    Role=Ref(app_service_role),
)

