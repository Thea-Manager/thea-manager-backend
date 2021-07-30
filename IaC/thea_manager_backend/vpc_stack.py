#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# CDK Imports - core
from aws_cdk import core as cdk

# CDK Imports - EC2
from aws_cdk.aws_ec2 import (

    # VPC Imports
    Vpc,
    FlowLogOptions,
    # DefaultInstanceTenancy,

    # Subnet Imports
    SubnetType,
    SubnetSelection,
    SubnetConfiguration,

    # NACL Imports
    Action,
    AclCidr,
    NetworkAcl,
    AclTraffic,
    TrafficDirection,

    # Gateway Endpoint imports
    GatewayVpcEndpointOptions,
    GatewayVpcEndpointAwsService
)

# ---------------------------------------------------------------
#                           Custom VPC
# ---------------------------------------------------------------

class CdkVpcStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ######################################
        #     Define internal attributes     #
        ######################################

        self.subnet_group_names = {
            "public":"alb-tier",
            "shared":"shared-tier",
            "private":"app-tier",
            "isolated":"database-tier",
        }

        ######################################
        #        Configure custom VPC        #
        ######################################

        # Instantiate custom VPC
        self.vpc = Vpc(
            scope=self,
            id=construct_id,
            cidr="10.0.0.0/16",
            flow_logs={
                "thea-custom-vpc-logs": FlowLogOptions()
            },
            max_azs=3,
            subnet_configuration=[
                SubnetConfiguration(
                    subnet_type=SubnetType.PUBLIC,
                    name=self.subnet_group_names["public"],
                    cidr_mask=24,
                    reserved=False
                ),
                SubnetConfiguration(
                    subnet_type=SubnetType.PUBLIC,
                    name=self.subnet_group_names["shared"],
                    cidr_mask=24,
                    reserved=False
                ),
                SubnetConfiguration(
                    subnet_type=SubnetType.PRIVATE,
                    name=self.subnet_group_names["private"],
                    cidr_mask=24,
                    reserved=False
                ),
                SubnetConfiguration(
                    subnet_type=SubnetType.ISOLATED,
                    name=self.subnet_group_names["isolated"],
                    cidr_mask=24,
                    reserved=False
                )
            ],
            enable_dns_support=True,
            enable_dns_hostnames=True,
            nat_gateway_subnets=SubnetSelection(
                subnet_group_name=self.subnet_group_names["shared"]
            ),
            # default_instance_tenancy=DefaultInstanceTenancy("DEDICATED"),
            gateway_endpoints={
                "s3-vpc-endpoint":GatewayVpcEndpointOptions(
                    service=GatewayVpcEndpointAwsService.S3,
                    subnets=[SubnetSelection(subnet_group_name="app-tier")]
                ),
                "dynamo-vpc-endpoint":GatewayVpcEndpointOptions(
                    service=GatewayVpcEndpointAwsService.DYNAMODB,
                    subnets=[SubnetSelection(subnet_group_name="app-tier")]
                )
            }
        )

        #######################################
        #       Create & configure NACL       #
        #######################################

        # Get subnet IPv4 CIDR blocks
        app_tier_subnets = self.vpc.select_subnets(subnet_group_name="app-tier").subnets

        # Define NACL configurations rules
        self._nacl_configurations={
            "public":[
                {
                    "id":"public-nacl-config-0",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":50,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW            
                },
                {
                    "id":"public-nacl-config-1",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW            
                },
                {
                    "id":"public-nacl-config-2",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":1100,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW             
                },
                {
                    "id":"public-nacl-config-3",
                    "cidr":AclCidr.ipv4(app_tier_subnets[1].ipv4_cidr_block),
                    "rule_number":1200,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"public-nacl-config-4",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":1000,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                },
                {
                    "id":"public-nacl-config-5",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":1100,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                },
                {
                    "id":"public-nacl-config-6",
                    "cidr":AclCidr.ipv4(app_tier_subnets[1].ipv4_cidr_block),
                    "rule_number":1200,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                },
                {
                    "id":"public-nacl-config-7",
                    "cidr":AclCidr.ipv4(app_tier_subnets[2].ipv4_cidr_block),
                    "rule_number":1300,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                },
                {
                    "id":"public-nacl-config-8",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":2100,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                },
                {
                    "id":"public-nacl-config-9",
                    "cidr":AclCidr.ipv4(app_tier_subnets[1].ipv4_cidr_block),
                    "rule_number":2200,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                },
                {
                    "id":"public-nacl-config-10",
                    "cidr":AclCidr.ipv4(app_tier_subnets[2].ipv4_cidr_block),
                    "rule_number":2300,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW       
                }
            ],
            "shared":[
                {
                    "id":"shared-nacl-config-0",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":50,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-1",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port_range(1, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-2",
                    "cidr":AclCidr.ipv4(app_tier_subnets[1].ipv4_cidr_block),
                    "rule_number":150,
                    "traffic":AclTraffic.tcp_port_range(1, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-3",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":200,
                    "traffic":AclTraffic.tcp_port_range(1, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-4",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":50,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-5",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-6",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":200,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                }
            ],
            "private":[
                {
                    "id":"private-nacl-config-0",
                    "cidr":AclCidr.ipv4("10.0.0.0/16"),
                    "rule_number":50,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"private-nacl-config-1",
                    "cidr":AclCidr.ipv4("10.0.0.0/16"),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-2",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":150,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-3",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port(80),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"shared-nacl-config-4",
                    "cidr":AclCidr.ipv4("0.0.0.0/0"),
                    "rule_number":150,
                    "traffic":AclTraffic.tcp_port(443),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"private-nacl-config-13",
                    "cidr":AclCidr.ipv4("10.0.0.0/16"),
                    "rule_number":200,
                    "traffic":AclTraffic.all_traffic(),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                }
            ],
            "isolated":[
                {
                    "id":"isolated-nacl-config-0",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":50,
                    "traffic":AclTraffic.tcp_port(3306),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW             
                },
                {
                    "id":"isolated-nacl-config-1",
                    "cidr":AclCidr.ipv4(app_tier_subnets[1].ipv4_cidr_block),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port(3306),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"isolated-nacl-config-2",
                    "cidr":AclCidr.ipv4(app_tier_subnets[2].ipv4_cidr_block),
                    "rule_number":150,
                    "traffic":AclTraffic.tcp_port(3306),
                    "direction":TrafficDirection.INGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"isolated-nacl-config-3",
                    "cidr":AclCidr.ipv4(app_tier_subnets[0].ipv4_cidr_block),
                    "rule_number":50,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW             
                },
                {
                    "id":"isolated-nacl-config-4",
                    "cidr":AclCidr.ipv4(app_tier_subnets[1].ipv4_cidr_block),
                    "rule_number":100,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                },
                {
                    "id":"isolated-nacl-config-5",
                    "cidr":AclCidr.ipv4(app_tier_subnets[2].ipv4_cidr_block),
                    "rule_number":150,
                    "traffic":AclTraffic.tcp_port_range(1024, 65535),
                    "direction":TrafficDirection.EGRESS,
                    "rule_action":Action.ALLOW
                }
            ]
        }

        # Create NACLs
        self.nacls={}
        for tier in self.subnet_group_names:

            # Create NACL
            self.nacls[tier]=NetworkAcl(
                scope=self,
                id=f"{construct_id}-{tier}-nacl",
                vpc=self.vpc,
                network_acl_name=tier,
                subnet_selection=SubnetSelection(subnet_group_name=self.subnet_group_names[tier])
            )

            # Associate NACL to subnet
            self.nacls[tier].associate_with_subnet(
                id=f"{construct_id}-{tier}-nacl-subnet",
                subnet_group_name=self.subnet_group_names[tier]
            )

            # Create NACL Rules
            for configuration in self._nacl_configurations[tier]:
                self.nacls[tier].add_entry(**configuration)


        ######################################
        #              CFN Output            #
        ######################################
        
        cdk.CfnOutput(
            scope=self,
            id="vpc_id",
            value=self.vpc.vpc_id
        )