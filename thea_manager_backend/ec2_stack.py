#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native Imports
from os import getenv

# CDK Imports - core
from aws_cdk import core as cdk

# CDK Imports - elastic load balancer
from aws_cdk.aws_elasticloadbalancingv2 import (
    ApplicationProtocol,
    ListenerCertificate,
    ApplicationLoadBalancer
)

# CDK Imports - auto scale group
from aws_cdk.aws_autoscaling import (
    HealthCheck,
    AutoScalingGroup
)

# CDK Imports - EC2
from aws_cdk.aws_ec2 import (
    Port,
    Peer,
    UserData,
    InstanceType,
    MachineImage,
    SecurityGroup,
    SubnetSelection
)

# CDK Imports - IAM
from aws_cdk.aws_iam import (
    Role,
    Policy,
    Effect,
    ManagedPolicy,
    PolicyDocument,
    PolicyStatement,
    ServicePrincipal
)

# CDK Imports - Log Groups
from aws_cdk.aws_logs import LogGroup


# ---------------------------------------------------------------
#                           Globals
# ---------------------------------------------------------------

STAGE=getenv("STAGE")
REGION=getenv("REGION")

# ---------------------------------------------------------------
#                           Configurations
# ---------------------------------------------------------------

user_data = f"sudo yum -y update;\
            yum install -y ruby aws-cli; \
            cd /home/ec2-user;\
            aws s3 cp s3://aws-codedeploy-{REGION}/latest/install . --region {REGION}; \
            sudo chmod +x install; \
            sudo ./install auto; \
            sudo yum install -y python-pip; \
            sudo pip install awscli"

# ---------------------------------------------------------------
#                           Custom EC2 stack
# ---------------------------------------------------------------


class CdkEc2Stack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #######################################
        #            Configure ALB            #
        #######################################

        self.vpc = vpc_stack.vpc

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
            desired_capacity=2,
            allow_all_outbound=True,
            machine_image=MachineImage.latest_amazon_linux(),
            instance_type=InstanceType(instance_type_identifier="t2.micro"),
            vpc_subnets=SubnetSelection(subnet_group_name=self.subnet_group_names["private"]),
            user_data=UserData.add_commands(user_data),
            role=Role(
                scope=self,
                id=f"{construct_id}-iam-roles",
                assumed_by=ServicePrincipal("ec2.amazonaws.com"),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSCodeDeployRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforAWSCodeDeploy")
                ]
            )
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
            id="http-listener",
            port=80,
            open=True
        )

        # Attach ASG to ALB
        self.listener.add_targets(
            id="listener-target-group",
            port=80,
            targets=[self.asg],
            health_check=HealthCheck.elb(
                grace=cdk.Duration.seconds(20)
            )
        )

        # Configure ASG simple scaling
        self.asg.scale_on_request_count(
            id=f"{construct_id}-simple-scaling-rule",
            target_requests_per_minute=1500
        )

        #######################################
        #      Configure Security Groups      #
        #######################################

        # ASG Security Groups
        self.asg.connections.allow_from(
            self.alb,
            Port.tcp(80),
            "Enable ASG inbound access to port 80 of ALB"
        )

        self.asg.connections.allow_from(
            self.alb,
            Port.tcp(443),
            "Enable ASG inbound access to port 443 of ALB"
        )

        self.asg.connections.allow_to(
            self.alb,
            Port.tcp(80),
            "Enable ASG outbound access to port 80 of ALB"
        )

        # ALB Security Groups
        self.alb.connections.allow_to(
            self.asg,
            Port.tcp(443),
            "Enable ALB outbound access to port 443 of ASG"
        )

        self.alb.connections.allow_from(
            self.asg,
            Port.tcp(443),
            "Enable ALB outbound access to port 443 of ASG"
        )

        #######################################
        #         Add Tags & log groups       #
        #######################################

        cdk.Tags.of(self.asg).add(
            key="deployment-group",
            value="thea-backend-server",
            include_resource_types=[
                "AWS::EC2::Instance",
                "AWS::AutoScaling::AutoScalingGroup"
            ]
        )

        self.log_group = LogGroup(
            scope=self,
            id="ec2-log-group",
            log_group_name="thea-backend-ec2-log-group"
        )

        #######################################
        #              CFN Output             #
        #######################################

        cdk.CfnOutput(
            scope=self,
            id="Output",
            value=self.alb.load_balancer_dns_name
        )