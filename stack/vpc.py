from troposphere import (
    Parameter,
	Ref
)

from stack.template import template

vpc_id = template.add_parameter(Parameter(
	"VPCID",
	Description="Select Your VPC ID",
	Type="AWS::EC2::VPC::Id",
))

public_subnet = template.add_parameter(Parameter(
	"PublicSubnet",
	Description="Select Your Public Subnet ID",
	Type="AWS::EC2::Subnet::Id",
))

default_security_group = template.add_parameter(Parameter(
	"DefaultSecurityGroup",
	Description="Select Your VPC Default Security Group ID",
	Type="AWS::EC2::SecurityGroup::Id",
))

instance_type = Ref(template.add_parameter(Parameter(
    "InstanceType",
    Description="Select Instance Type",
    Type="String",
    Default="t2.large",
    AllowedValues=["t2.medium", "t2.large", "t2.xlarge"]
)))

secret_key = template.add_parameter(Parameter(
    "KeyPair",
    Description="Select Key Pair",
    Type="AWS::EC2::KeyPair::KeyName"
))


template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterGroups': [
            {
                'Label': {'default': 'Network Configuration'},
                'Parameters': ["VPCID", "PublicSubnet", "DefaultSecurityGroup"]
            },
			{
                'Label': {'default': 'App Configuration'},
                'Parameters': ["InstanceType", "KeyPair"]
            },
        ],
        'ParameterLabels': {
            'VPCID': {"default" : "VPC ID"},
			'PublicSubnet': {"default" : "Public Subnet ID"},
			'DefaultSecurityGroup': {"default" : "VPC Default Security Group ID"},
			'InstanceType': {"default" : "Instance Type"},
			'KeyPair': {"default" : "Key Pair"},
        }
    }
})