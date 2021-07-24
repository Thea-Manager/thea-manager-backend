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

# CDK Imports - auto scale group
from aws_cdk.aws_autoscaling import (
    HealthCheck,
    AutoScalingGroup
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
from aws_cdk.aws_ecs import Cluster, ContainerImage, Ec2TaskDefinition, PortMapping, FargateTaskDefinition, FargateService
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedEc2Service, ApplicationLoadBalancedTaskImageOptions, ApplicationLoadBalancedFargateService

# CDK Imports - Certificate Manager
from aws_cdk.aws_certificatemanager import Certificate

# ---------------------------------------------------------------
#                           Globals
# ---------------------------------------------------------------

# Current directoy
current_directory = path.dirname(__file__)

# Env vars
load_dotenv(path.join(current_directory, "../.env"))
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                           Custom EC2 stack
# ---------------------------------------------------------------


class CdkEcsStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # #######################################
        # #           Configure ASG             #
        # #######################################

        # self.asg = AutoScalingGroup(
        #     scope=self,
        #     vpc=vpc_stack.vpc,
        #     id=f"{construct_id}-asg",
        #     auto_scaling_group_name=f"{construct_id}-asg",
        #     min_capacity=1,
        #     max_capacity=3,
        #     desired_capacity=3,
        #     allow_all_outbound=True,
        #     machine_image=MachineImage.generic_linux({
        #         "ca-central-1":"ami-0a2069a4a4d1a023e"
        #     }),
        #     instance_type=InstanceType(instance_type_identifier="t2.micro"),
        #     vpc_subnets=SubnetSelection(subnet_group_name="app-tier"),
        #     role=Role(
        #         scope=self,
        #         id=f"{construct_id}-iam-roles",
        #         assumed_by=ServicePrincipal("ec2.amazonaws.com"),
        #         managed_policies=[
        #             ManagedPolicy.from_aws_managed_policy_name("service-role/AWSCodeDeployRole"),
        #             ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforAWSCodeDeploy"),
        #             ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role")
        #         ]
        #     )
        # )

        # # Attach inline policies - DynamoDB | DENY
        # self.asg.role.attach_inline_policy(
        #     policy=Policy(
        #         scope=self,
        #         id=f"{construct_id}-thea-ec2-inline-policy",
        #         policy_name=f"{construct_id}-thea-ec2-inline-policy",
        #         statements=[
        #             PolicyStatement(
        #                 effect=Effect.DENY,
        #                 resources=[self.asg.auto_scaling_group_arn],
        #                 actions=[
        #                     "s3:*",
        #                     "SES:*",
        #                     "dynamodb:*"
        #                 ]
        #             ),
        #             PolicyStatement(
        #                 effect=Effect.ALLOW,
        #                 resources=[self.asg.auto_scaling_group_arn],
        #                 actions=[
        #                     "S3:PutObject",
        #                     "S3:GetObject",
        #                     "S3:HeadObject",
        #                     "S3:DeleteObject",
        #                     "S3:DeleteObjects",
        #                     "S3:ListObjectsV2",
        #                     "S3:ListObjectVersions",
        #                     "SES:ListIdentities",
        #                     "SES:ListEmailIdentities",
        #                     "SES:VerifyEmailIdentity",
        #                     "SES:SendTemplatedEmail",
        #                     "SES:DeleteEmailIdentity",
        #                     "SES:SendTemplatedEmail",
        #                     "SES:DeleteIdentity",
        #                     "dynamodb:Query",
        #                     "dynamodb:PutItem",
        #                     "dynamodb:GetItem",
        #                     "dynamodb:UpdateItem",
        #                     # "dynamodb:DeleteItem"
                            
        #                 ]
        #             )
        #         ]
        #     )
        # )

        # #######################################
        # #            Configure ECS            #
        # #######################################

        self.ecs_cluster = Cluster(
            scope=self,
            id=f"thea-backend-{ACCOUNT_NUMBER}",
            cluster_name=f"thea-backend-{ACCOUNT_NUMBER}",
            vpc=vpc_stack.vpc
        )

        self.ecs_fargate_service = ApplicationLoadBalancedFargateService(
            scope=self, 
            id=f"thea-backend-service-{ACCOUNT_NUMBER}",
            service_name=f"thea-backend-service-{ACCOUNT_NUMBER}",
            cluster=self.ecs_cluster,            
            cpu=512,
            desired_count=2,
            task_image_options=ApplicationLoadBalancedTaskImageOptions(
                container_port=5000,
                # image=ContainerImage.from_registry("digitalocean/flask-helloworld")
                image=ContainerImage.from_asset(
                    file="Dockerfile",
                    directory=path.join(current_directory,"src")
                )
                # image=ContainerImage.from_ecr_repository(
                #     repository=Repository.from_repository_name(
                #         scope=self,
                #         id="thea-backend-server-repo",
                #         repository_name="553198756977-test")
                #     )
            ),
            task_subnets=SubnetSelection(subnet_group_name="app-tier"),
            memory_limit_mib=2048,
            load_balancer=ApplicationLoadBalancer(
                scope=self,
                http2_enabled=True,
                id=f"{construct_id}-alb",
                vpc=vpc_stack.vpc,
                internet_facing=True,
                load_balancer_name=f"{construct_id}-alb",
                vpc_subnets=SubnetSelection(subnet_group_name="alb-tier")
            ),
            public_load_balancer=True
        )