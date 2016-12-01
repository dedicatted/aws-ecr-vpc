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
    main_cluster,
    container_instance_profile,
    load_balancer,
	autoscaling_group_name,
	app_service_role, 
	repo_id
)

from stack.vpc import (
	instance_type,
	secret_key
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

from stack.cluster.mongo import mongo_instance, mongo_user, mongo_pass

bigid_task_definition = TaskDefinition(
    "BigIdTask",
    template=template,
    ContainerDefinitions=[
        ContainerDefinition(
            Name="bigid-web",
			Memory="200",
            Essential=True,
            Image=Join("", [
                repo_id,
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
                    Value=mongo_user,
                ),
                Environment(
                    Name="BIGID_MONGO_PWD",
                    Value=mongo_pass,
                ),
				Environment(
                    Name="WEB_URL_EXT",
                    Value=Join("", ["http://", GetAtt(load_balancer, "DNSName"), ":3000"]),
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-orch",
			Memory="200",
            Essential=True,
            Image=Join("", [
                repo_id,
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
                    Value=mongo_user,
                ),
                Environment(
                    Name="BIGID_MONGO_PWD",
                    Value=mongo_pass,
                ),
				Environment(
                    Name="ORCHESTRATOR_URL_EXT",
			        Value=Join("", ["http://", GetAtt(load_balancer, "DNSName"), ":3001"]),
                ),
                Environment(
                    Name="BIGID_MONGO_HOST_EXT",
                    Value=GetAtt(mongo_instance, "PrivateIp"),
                ),
				Environment(
                    Name="SAVE_SCANNED_IDENTITIES_AS_PII_FINDINGS",
                    Value="False",
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-corr",
			Memory="200",
            Essential=True,
            Image=Join("", [
                repo_id,
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
                    Value=mongo_user,
                ),
                Environment(
                    Name="BIGID_MONGO_PWD",
                    Value=mongo_pass,
                ),
				Environment(
                    Name="CORR_URL_EXT",
                    Value=Join("", ["http://", GetAtt(load_balancer, "DNSName"), ":3002"]),
                ),
			],
        ),
		ContainerDefinition(
            Name="bigid-scanner",
			Memory="200",
            Essential=True,
			Privileged=True,
            Image=Join("", [
                repo_id,
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
			Memory="192",
            Essential=True,
            Image=Join("", [
                repo_id,
                "/bigid-ui",
            ]),
            PortMappings=[PortMapping(
                ContainerPort="8080",
                HostPort="8080"
            )],
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
