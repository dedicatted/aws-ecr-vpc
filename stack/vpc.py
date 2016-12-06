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

instance_type = Ref(template.add_parameter(Parameter(
    "InstanceType",
    Description="Select Instance Type",
    Type="String",
    Default="t2.large",
    AllowedValues=["t2.large", "t2.xlarge", "m4.large", "m4.xlarge"]
)))

secret_key = template.add_parameter(Parameter(
    "KeyPair",
    Description="Select Key Pair",
    Type="AWS::EC2::KeyPair::KeyName"
))

aws_access_key = template.add_parameter(Parameter(
    "AWSACCESSKEY",
    Description="Enter Your AWS Access Key ID",
    Type="String",
	NoEcho=True
))

aws_secret_key = template.add_parameter(Parameter(
    "AWSSECRETKEY",
    Description="Enter Your AWS Secret Key",
    Type="String",
	NoEcho=True
))


template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterGroups': [
            {
                'Label': {'default': 'Network Configuration'},
                'Parameters': ["VPCID", "PublicSubnet"]
            },
			{
                'Label': {'default': 'App Configuration'},
                'Parameters': ["InstanceType", "KeyPair", "AWSACCESSKEY", "AWSSECRETKEY"]
            },
        ],
        'ParameterLabels': {
            'VPCID': {"default" : "VPC ID"},
			'PublicSubnet': {"default" : "Public Subnet ID"},
			'InstanceType': {"default" : "Instance Type"},
			'KeyPair': {"default" : "Key Pair"},
			'AWSACCESSKEY': {"default" : "AWS_ACCESS_KEY"},
			'AWSSECRETKEY': {"default" : "AWS_SECRET_KEY"},
        }
    }
})