from troposphere import (
    GetAtt,
    Tags,
    Base64,
    Join,
    Ref,
	FindInMap,
	AWS_REGION,
	Parameter,
	Output
)
from troposphere.ec2 import Instance, NetworkInterfaceProperty
from troposphere.policies import CreationPolicy, ResourceSignal

from stack.cluster.infrastructure import instance_security_group
from stack.template import template

from stack.vpc import (
    vpc_id,
    default_security_group,
    public_subnet,
	instance_type,
	secret_key
)

mongo_user = "bigid"

mongo_pass = "bigid111"

template.add_mapping("InstanceRegionMap", {
    "eu-central-1": {"AMI": "ami-f9619996"},
    "eu-west-1": {"AMI": "ami-9398d3e0"},
    "us-east-1": {"AMI": "ami-b73b63a0"},
    "us-west-2": {"AMI": "ami-5ec1673e"},
    "us-west-1": {"AMI": "ami-23e8a343"},
})

mongo_instance_name = "MongoDB"
mongo_instance = Instance(
    mongo_instance_name,
    template=template,
    SourceDestCheck="false",
    KeyName=Ref(secret_key),
	NetworkInterfaces=[
		NetworkInterfaceProperty(
			AssociatePublicIpAddress=True,
			SubnetId=Ref(public_subnet),
			DeviceIndex="0",
			GroupSet=[Ref(default_security_group), Ref(instance_security_group)],
	)],
    ImageId=FindInMap("InstanceRegionMap", Ref(AWS_REGION), "AMI"),
#    SecurityGroupIds=[Ref(default_security_group)],
    InstanceType=instance_type,
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "sleep 30s\n",
        "touch /tmp/init.log\n",
        "yum update -y\n",
        "echo update-done >> /tmp/init.log\n",
        "yum install -y docker \n",
        "echo docker-install-done >> /tmp/init.log\n",
        "usermod -a -G docker ec2-user \n",
        "service docker start\n",
        "echo docker-start-done >> /tmp/init.log\n",
        "mkdir -p /data\n",
        "docker run --name mongo -v /data:/data/db -p 27017:27017 -d mongo --auth\n",
        "echo docker-mongo-started >> /tmp/init.log\n",
        "sleep 5s \n",
		"docker exec mongo mongo admin --eval \"db.createUser({ user: '",
		mongo_user, 
		"', pwd: '",
		mongo_pass, 
		"', roles: [ { role: 'userAdminAnyDatabase', db: 'admin' }, { role: 'dbAdminAnyDatabase', db: 'admin' }, { role: 'readWriteAnyDatabase', db: 'admin' } ] });\"\n",
        "/opt/aws/bin/cfn-signal -e $? ",
        "         --stack ",
        Ref('AWS::StackName'),
        "         --resource %s " % mongo_instance_name,
        '         --region ',
        Ref('AWS::Region'),
        '\n',
    ])),
    CreationPolicy=CreationPolicy(
        ResourceSignal=ResourceSignal(
            Timeout='PT15M')),
    Tags=Tags(Name="mongo_db_instance")
)

template.add_output(Output(
    "Login",
    Description="BigId Login",
    Value=mongo_user
))

template.add_output(Output(
    "Password",
    Description="BigId Password",
    Value=mongo_pass
))
