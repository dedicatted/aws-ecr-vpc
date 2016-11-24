from troposphere import (
    GetAtt,
    Tags,
    Base64,
    Join,
    Ref,
	FindInMap,
	AWS_REGION,
	Parameter
)
from troposphere.ec2 import Instance
from troposphere.policies import CreationPolicy, ResourceSignal

from stack.cluster.infrastructure import secret_key
from stack.template import template

from stack.vpc import (
    vpc,
    unsafe_security_group,
    container_a_subnet
)

mongo_user = template.add_parameter(Parameter(
    "MongoDBUser",
    Description="Enter MongoDB User",
    Type="String"
))

mongo_pass = template.add_parameter(Parameter(
    "MongoDBPassword",
    Description="Enter MongoDB Password",
    Type="String"
))

template.add_mapping("InstanceRegionMap", {
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
    SubnetId=Ref(container_a_subnet),
    ImageId=FindInMap("NATRegionMap", Ref(AWS_REGION), "AMI"),
    SecurityGroupIds=[Ref(unsafe_security_group), GetAtt(vpc, "DefaultSecurityGroup")],
    InstanceType="t2.micro",
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
		Ref(mongo_user), 
		"', pwd: '",
		Ref(mongo_pass), 
		"', roles: [ { role: 'userAdminAnyDatabase', db: 'admin' } ] });\"\n",
        "/opt/aws/bin/cfn-signal -e $? ",
        "         --stack ",
        Ref('AWS::StackName'),
        "         --resource %s " % mongo_instance_name,
        '         --region ',
        Ref('AWS::Region'),
        '\n',
    ])),
    DependsOn="Nat",
    CreationPolicy=CreationPolicy(
        ResourceSignal=ResourceSignal(
            Timeout='PT15M')),
    Tags=Tags(Name="mongo_db_instance")
)
