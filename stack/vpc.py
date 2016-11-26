from troposphere import (
    Parameter,
)

from stack.template import template

vpc_id = template.add_parameter(Parameter(
	"VPCID",
	Description="Enter Your VPC ID",
	Type="String",
))

public_subnet = template.add_parameter(Parameter(
	"PublicSubnet",
	Description="Enter Your Public Subnet ID",
	Type="String",
))

default_security_group = template.add_parameter(Parameter(
	"DefaultSecurityGroup",
	Description="Enter Your Default Security Group ID",
	Type="String",
))