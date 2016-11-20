from troposphere import (
    GetAtt,
    Tags,
    Base64,
    Join,
    Ref,
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

mongo_instance_name = "MongoDB"
mongo_instance = Instance(
    mongo_instance_name,
    template=template,
    SourceDestCheck="false",
    KeyName=Ref(secret_key),
    SubnetId=Ref(container_a_subnet),
    ImageId="ami-23e8a343",
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
        "docker run --name mongo -v /data:/data/db -d mongo --auth\n",
        "echo docker-mongo-started >> /tmp/init.log\n",
        "sleep 5s \n",
        "docker exec mongo mongo admin --eval \"db.createUser({ user: 'jsmith', pwd: 'some-initial-password', roles: [ { role: 'userAdminAnyDatabase', db: 'admin' } ] });\"\n",
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
