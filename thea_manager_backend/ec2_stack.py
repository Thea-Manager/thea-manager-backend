#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native Imports
from os import getenv

# CDK Imports - core
from aws_cdk import core as cdk

# CDK Imports - Code deploy
import aws_cdk.aws_codedeploy as codedeploy

# CDK Imports - elastic load balancer
from aws_cdk.aws_elasticloadbalancingv2 import (
    ApplicationProtocol,
    ListenerCertificate,
    ApplicationLoadBalancer
)

# CDK Imports - auto scale group
from aws_cdk.aws_autoscaling import (
    BlockDevice,
    HealthCheck,
    AutoScalingGroup,
    BlockDeviceVolume,
    EbsDeviceVolumeType
)

# CDK Imports - EC2
from aws_cdk.aws_ec2 import (
    Vpc,
    Port,
    UserData,
    InstanceType,
    MachineImage,
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
# ---------------------------------------------------------------
#                           Globals
# ---------------------------------------------------------------

STAGE=getenv("STAGE")
REGION=getenv("REGION")

# ---------------------------------------------------------------
#                           Configurations
# ---------------------------------------------------------------

user_data = f"yum -y update; yum install -y ruby aws-cli; \
            cd /home/ec2-user; aws s3 cp s3://aws-codedeploy-{REGION}/latest/install . --region {REGION}; \
            chmod +x install; ./install auto"

# ---------------------------------------------------------------
#                           Custom EC2 stack
# ---------------------------------------------------------------


class CdkEc2Stack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #######################################
        #            Configure ALB            #
        #######################################

        # Lookup VPC
        # self.vpc = Vpc.from_lookup(
        #     scope=self,
        #     id=f"{construct_id}-lookup",
        #     is_default=False,
        #     vpc_id=vpc_id,
        # )
        self.vpc = vpc_stack

        # Subnet group names
        self.subnet_group_names = {
            "public":"alb-tier",
            "shared":"shared-tier",
            "private":"app-tier",
            "isolated":"database-tier",
        }

        # Create ALB
        self.alb = ApplicationLoadBalancer(
            scope=self,
            http2_enabled=True,
            id=f"{construct_id}-alb",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name=f"{construct_id}-alb",
            vpc_subnets=SubnetSelection(subnet_group_name=self.subnet_group_names["public"])
        )

        # Add redirect - http to https
        self.alb.add_redirect(
            open=True,
            source_port=80,
            source_protocol=ApplicationProtocol.HTTP,
            target_port=443,
            target_protocol=ApplicationProtocol.HTTPS
        )

        # # Enable access logging
        # self.alb.log_access_logs(
        #     bucket="",
        #     prefix="",
        # )

        #######################################
        #           Configure ASG             #
        #######################################

        self.asg = AutoScalingGroup(
            scope=self,
            vpc=self.vpc,
            id=f"{construct_id}-asg",
            auto_scaling_group_name=f"{construct_id}-asg",
            min_capacity=1,
            max_capacity=2,
            desired_capacity=1,
            allow_all_outbound=False,
            machine_image=MachineImage.latest_amazon_linux(),
            instance_type=InstanceType(instance_type_identifier="c5.large"),
            vpc_subnets=SubnetSelection(subnet_group_name=self.subnet_group_names["private"]),
            user_data=UserData.add_commands(user_data),
            # block_devices=[
            #     BlockDevice(
            #         device_name="/dev/xvda",
            #         volume=BlockDeviceVolume.ebs(
            #                 volume_size=2,
            #                 encrypted=True,
            #                 delete_on_termination=True,
            #                 volume_type=EbsDeviceVolumeType.GP2
            #         )
            #     )
            # ]
        )

        # Configure ASG traffic from ALB
        self.asg.connections.allow_from(
            self.alb,
            Port.tcp(443),
            "Enable ALB access to port 443 of EC2 in ASG"
        )

        # Attach inline policies - DynamoDB | DENY
        self.asg.role.attach_inline_policy(
            policy=Policy(
                scope=self,
                id=f"{construct_id}-thea-ec2-inline-policy",
                policy_name=f"{construct_id}-thea-ec2-inline-policy",
                statements=[
                    PolicyStatement(
                        effect=Effect.DENY,
                        resources=[self.asg.auto_scaling_group_arn],
                        actions=[
                            "s3:*",
                            "SES:*",
                            "dynamodb:*"
                        ]
                    ),
                    PolicyStatement(
                        effect=Effect.ALLOW,
                        resources=[self.asg.auto_scaling_group_arn],
                        actions=[
                            "S3:PutObject",
                            "S3:GetObject",
                            "S3:HeadObject",
                            "S3:DeleteObject",
                            "S3:DeleteObjects",
                            "S3:ListObjectsV2",
                            "S3:ListObjectVersions",
                            "SES:ListIdentities",
                            "SES:ListEmailIdentities",
                            "SES:VerifyEmailIdentity",
                            "SES:SendTemplatedEmail",
                            "SES:DeleteEmailIdentity",
                            "SES:SendTemplatedEmail",
                            "SES:DeleteIdentity",
                            "dynamodb:Query",
                            "dynamodb:PutItem",
                            "dynamodb:GetItem",
                            "dynamodb:UpdateItem",
                            # "dynamodb:DeleteItem"
                            
                        ]
                    )
                ]
            )
        )

        #######################################
        # Configure ALB listener & ASG scaler #
        #######################################

        # Create listener
        self.listener = self.alb.add_listener(
            id="https_listener",
            port=443,
            open=True, #TODO: Make this false and configure ALB to accept traffic only from CDN
            certificates=[ListenerCertificate("arn:aws:acm:ca-central-1:304843052975:certificate/4120d00a-e4f0-4125-b4b4-fe65e3328622")]
        )

        # Attach ASG to ALB
        self.listener.add_targets(
            "listener-target-group",
            port=443,
            targets=[self.asg],
            health_check=HealthCheck.ec2(
                grace=cdk.Duration.seconds(20)
            )
        )

        # Configure ASG simple scaling
        self.asg.scale_on_request_count(
            id=f"{construct_id}-simple-scaling-rule",
            target_requests_per_minute=1500
        )