#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native Imports
from os import getenv, path
from dotenv import load_dotenv

# CDK Imports - core
from aws_cdk import core as cdk

# CDK Imports - EC2
from aws_cdk.aws_ec2 import (
    MachineImage,
    InstanceType,
    SubnetSelection
)

# CDK Imports - IAM
from aws_cdk.aws_iam import (
    Role,
    Policy,
    Effect,
    ManagedPolicy,
    PolicyStatement,
    ServicePrincipal
)

# CDK Imports - elastic load balancer
from aws_cdk.aws_elasticloadbalancingv2 import ApplicationLoadBalancer


# CDK Imports - Log Groups
from aws_cdk.aws_logs import LogGroup

# CDK Imports - EKS & ECS Patterns
from aws_cdk.aws_ecr import Repository
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedEc2Service
from aws_cdk.aws_ecs import (
    Cluster,
    Protocol,
    LogDriver,
    NetworkMode, 
    PortMapping,
    ContainerImage,
    EnvironmentFile,
    Ec2TaskDefinition, 
    AddCapacityOptions
)


# CDK Imports - Certificate Manager
from aws_cdk.aws_certificatemanager import Certificate

# ---------------------------------------------------------------
#                           Globals
# ---------------------------------------------------------------

# Current directoy
current_directory = path.dirname(__file__)

# Env vars
load_dotenv(path.join(current_directory, "../.env"))
DEDICATED=getenv("DEDICATED")
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                           Custom EC2 stack
# ---------------------------------------------------------------


class CdkEcsStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #######################################
        #         Configure ECS Cluster       #
        #######################################

        self.ecs_cluster = Cluster(
            scope=self,
            id=f"thea-backend-{ACCOUNT_NUMBER}",
            cluster_name=f"thea-backend-{ACCOUNT_NUMBER}",
            vpc=vpc_stack.vpc,
            capacity=AddCapacityOptions(
                auto_scaling_group_name="thea-backend-server-asg",
                min_capacity=1,
                max_capacity=6,
                desired_capacity=3,
                vpc_subnets=SubnetSelection(subnet_group_name="app-tier"),
                machine_image=MachineImage.generic_linux({
                    "ca-central-1":"ami-0a2069a4a4d1a023e"
                }),
                instance_type=InstanceType(instance_type_identifier="t2.medium"),
                can_containers_access_instance_role=True
            )
        )

        #######################################
        #   Configure Task Def & containers   #
        #######################################

        # Create task definition
        self.task_definition = Ec2TaskDefinition(
            scope=self,
            id="thea-backend-server-ec2-task-definition",
            network_mode=NetworkMode.AWS_VPC
        )

        # Add docker containers
        self.task_definition.add_container(
            id="thea-backend-server-ec2-container",
            memory_limit_mib=1024,
            logging=LogDriver.aws_logs(
                stream_prefix="thea-backend-server-log-group",
                log_group=LogGroup(
                    scope=self,
                    removal_policy=cdk.RemovalPolicy.DESTROY,
                    id="thea-backend-server-log-group",
                    log_group_name="thea-backend-server-log-group"
                )
            ),
            # image=ContainerImage.from_asset(
            #     directory=path.join(current_directory, "src")
            # ),
            # image=ContainerImage.from_ecr_repository(
            #     repository=Repository.from_repository_name(
            #         scope=self,
            #         id="thea-backend-server-repo",
            #         repository_name="553198756977-test"
            #     )
            # ),
            image=ContainerImage.from_registry("ielkadi1993/sandbox"),
            port_mappings=[
                PortMapping(
                    container_port=5000,
                    protocol=Protocol.TCP
                )
            ],
            readonly_root_filesystem=True,
            # environment_files=EnvironmentFile(
            #     path=path.join(current_directory, "src/.env")
            # )
        )

        #######################################
        #           Configure ALB             #
        #######################################

        self.alb = ApplicationLoadBalancer(
            scope=self,
            http2_enabled=True,
            id=f"{construct_id}-alb",
            vpc=vpc_stack.vpc,
            internet_facing=True,
            load_balancer_name=f"{construct_id}-alb",
            vpc_subnets=SubnetSelection(subnet_group_name="alb-tier")
        )

        #######################################
        #   Configure Load balanced service   #
        #######################################

        self.ecs_ec2_service = ApplicationLoadBalancedEc2Service(
            scope=self,
            id=f"thea-backend-service-{ACCOUNT_NUMBER}",
            service_name=f"thea-backend-service-{ACCOUNT_NUMBER}",
            cluster=self.ecs_cluster,
            task_definition=self.task_definition,
            load_balancer=self.alb,
            public_load_balancer=True
        )