from troposphere import (
    AWS_REGION,
    Join,
    Parameter,
    Ref,
    GetAtt,
    Tags
)

from troposphere.ec2 import (
    SecurityGroup,
    SecurityGroupRule,
    SecurityGroupIngress
)

from troposphere.ec2 import (
    EIP,
    Instance,
    InternetGateway,
    Route,
    RouteTable,
    Subnet,
    SubnetRouteTableAssociation,
    VPC,
    VPCGatewayAttachment,
)

from .template import template

# NAT
nat_instance_type_param = template.add_parameter(Parameter(
    "NatInstanceType",
    Description="NAT InstanceType",
    Default="t2.micro",
    Type="String",
))

nat_image_id_param = template.add_parameter(Parameter(
    "NatImageId",
    Description="NAT ImageId",
    Default="ami-863b6391",
    Type="String",
))

nat_instance_keyname_param = template.add_parameter(Parameter(
    "NatKeyName",
    Description="NAT KeyName",
    Type="String",
))

vpc = VPC(
    "Vpc",
    template=template,
    CidrBlock="10.0.0.0/16",
)

unsafe_security_group = SecurityGroup(
    'UnsafeSecurityGroup',
    template=template,
    GroupDescription="Unsafe Security Group.",
    VpcId=Ref(vpc),
    SecurityGroupIngress=[
        # ssh access from any source
        SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp="0.0.0.0/0",
        )
    ],
    Tags=Tags(Name="unsafe_security_group")
)

# Allow outgoing to outside VPC
internet_gateway = InternetGateway(
    "InternetGateway",
    template=template,
)

# Attach Gateway to VPC
VPCGatewayAttachment(
    "GatewayAttachement",
    template=template,
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(internet_gateway),
)

# Public route table
public_route_table = RouteTable(
    "PublicRouteTable",
    template=template,
    VpcId=Ref(vpc),
)

public_route = Route(
    "PublicRoute",
    template=template,
    GatewayId=Ref(internet_gateway),
    DestinationCidrBlock="0.0.0.0/0",
    RouteTableId=Ref(public_route_table),
)

# Holds public instances
public_subnet_cidr = "10.0.1.0/24"

public_subnet = Subnet(
    "PublicSubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=public_subnet_cidr,
)

SubnetRouteTableAssociation(
    "PublicSubnetRouteTableAssociation",
    template=template,
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(public_subnet),
)

nat_instance = template.add_resource(Instance(
    "Nat",
    SourceDestCheck="false",
    KeyName=Ref(nat_instance_keyname_param),
    SubnetId=Ref(public_subnet),
    ImageId=Ref(nat_image_id_param),
    SecurityGroupIds=[Ref(unsafe_security_group), GetAtt(vpc, "DefaultSecurityGroup")],
    InstanceType=Ref(nat_instance_type_param),
    Tags=Tags(Name="nat_instance")
))

nat_eip = template.add_resource(EIP(
    "NatEIP",
    InstanceId=Ref("Nat"),
    Domain="vpc",
))

# Holds load balancer
loadbalancer_a_subnet_cidr = "10.0.2.0/24"
loadbalancer_a_subnet = Subnet(
    "LoadbalancerASubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=loadbalancer_a_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
)

SubnetRouteTableAssociation(
    "LoadbalancerASubnetRouteTableAssociation",
    template=template,
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(loadbalancer_a_subnet),
)

loadbalancer_b_subnet_cidr = "10.0.3.0/24"
loadbalancer_b_subnet = Subnet(
    "LoadbalancerBSubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=loadbalancer_b_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "b"]),
)

SubnetRouteTableAssociation(
    "LoadbalancerBSubnetRouteTableAssociation",
    template=template,
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(loadbalancer_b_subnet),
)

# Private route table
private_route_table = RouteTable(
    "PrivateRouteTable",
    template=template,
    VpcId=Ref(vpc),
)

private_nat_route = Route(
    "PrivateNatRoute",
    template=template,
    RouteTableId=Ref(private_route_table),
    DestinationCidrBlock="0.0.0.0/0",
    InstanceId=Ref("Nat"),
)

# Holds containers instances
container_a_subnet_cidr = "10.0.10.0/24"
container_a_subnet = Subnet(
    "ContainerASubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=container_a_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
)

SubnetRouteTableAssociation(
    "ContainerARouteTableAssociation",
    template=template,
    SubnetId=Ref(container_a_subnet),
    RouteTableId=Ref(private_route_table),
)

container_b_subnet_cidr = "10.0.11.0/24"
container_b_subnet = Subnet(
    "ContainerBSubnet",
    template=template,
    VpcId=Ref(vpc),
    CidrBlock=container_b_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "b"]),
)

SubnetRouteTableAssociation(
    "ContainerBRouteTableAssociation",
    template=template,
    SubnetId=Ref(container_b_subnet),
    RouteTableId=Ref(private_route_table),
)
