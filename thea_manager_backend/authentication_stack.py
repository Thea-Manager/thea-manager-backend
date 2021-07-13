#!/usr/bin/env python

#TODO: Configure CORS to be more secure and limiting only to the domain you care about

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import path, getenv
from dotenv import load_dotenv

# CDK imports
from aws_cdk import core as cdk
from aws_cdk.aws_iam import (
    Role,
    Effect,
    ManagedPolicy,
    PolicyDocument,
    PolicyStatement,
    ServicePrincipal)
from aws_cdk.aws_cognito import (
    Mfa,
    UserPool,
    PasswordPolicy,
    MfaSecondFactor,
    AccountRecovery,
    StringAttribute,
    AutoVerifiedAttrs,
    StandardAttribute,
    StandardAttributes,
    VerificationEmailStyle)
from aws_cdk.aws_apigateway import (
    RestApi,
    JsonSchema,
    CorsOptions,
    EndpointType,
    StageOptions,
    JsonSchemaType,
    LambdaIntegration,
    MethodLoggingLevel,
    EndpointConfiguration
)

import aws_cdk.aws_lambda as lmb
import aws_cdk.aws_codedeploy as codedeploy
import aws_cdk.aws_cloudwatch as cloudwatch

# ---------------------------------------------------------------
#                             Globals
# ---------------------------------------------------------------

# Current directoy
current_directory = path.dirname(__file__)

# Env vars
load_dotenv(path.join(current_directory, "../.env"))

STAGE=getenv("STAGE")

# ---------------------------------------------------------------
#                    Serverless Authentication
# ---------------------------------------------------------------

class AuthenticationStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)        

        ######################################
        #  Config cognito pool & app client  #
        ######################################

        self.cognito_user_pool = UserPool(
            scope=self, 
            id="user-pool",
            user_pool_name=f"{STAGE}-user-pool",
            account_recovery=AccountRecovery.EMAIL_ONLY,
            auto_verify=AutoVerifiedAttrs(
                email=True,
                phone=False
            ),
            custom_attributes={
                "orgId":StringAttribute(
                    mutable=False
                ),
                "userType":StringAttribute(
                    mutable=False
                ),
                "username":StringAttribute(
                    mutable=True
                ),
                "profilePicture":StringAttribute(
                    mutable=True
                )
            },
            enable_sms_role=False,
            mfa=Mfa.REQUIRED,
            mfa_second_factor=MfaSecondFactor(
                otp=True,
                sms=False
            ),
            password_policy=PasswordPolicy(
                min_length=14,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
                temp_password_validity=cdk.Duration.days(90)
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
            sign_in_case_sensitive=False,
            self_sign_up_enabled=True,
            standard_attributes=StandardAttributes(
                address=StandardAttribute(required=False),
                birthdate=StandardAttribute(required=False),
                email=StandardAttribute(
                    mutable=False,
                    required=True
                ),
                family_name=StandardAttribute(required=False),
                fullname=StandardAttribute(
                    mutable=False,
                    required=True
                ),
                gender=StandardAttribute(required=False),
                given_name=StandardAttribute(required=False),
                last_update_time=StandardAttribute(required=False),
                locale=StandardAttribute(required=False),
                middle_name=StandardAttribute(required=False),
                nickname=StandardAttribute(required=False),
                phone_number=StandardAttribute(required=False),
                preferred_username=StandardAttribute(required=False),
                profile_page=StandardAttribute(required=False),
                profile_picture=StandardAttribute(required=False),
                timezone=StandardAttribute(required=False),
                website=StandardAttribute(required=False)
            ),
            user_verification={
                "email_subject": "Verify your email",
                "email_body": "Your verification code is {####}",
                "email_style": VerificationEmailStyle.CODE,
                "sms_message": "Your verification code is {####}"
            })

        self.app_client = self.cognito_user_pool.add_client(
            id="app-client",
            access_token_validity=cdk.Duration.days(1),
            generate_secret=True,
            id_token_validity=cdk.Duration.days(1),
            prevent_user_existence_errors=False,
            refresh_token_validity=cdk.Duration.days(1),
            user_pool_client_name=f"{STAGE}-app-client")

        ######################################
        #      Create & lambda handlers      #
        ######################################

        # Signup handler & alias
        signup_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-signup-handler",
            function_name=f"{STAGE}-signup-handler",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            description="Cognito user signs up to user pool",
            role=Role(
                scope=self,
                id="signup-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-signup":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:SignUp"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/signup")))

        signup_alias = lmb.Alias(
            scope=self,
            version=signup_handler.current_version,
            id=f"{STAGE}-signup-alias",
            alias_name="signup-alias",
        )

        # Confirm signup & alias
        confirm_signup_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-confirm-signup-handler",
            function_name=f"{STAGE}-confirm-signup-handler",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            description="Cognito user confirms signup to user pool",
            role=Role(
                scope=self,
                id="confirm-signup-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-confirm-signup":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:ConfirmSignUp"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/confirm-signup")))

        confirm_signup_alias = lmb.Alias(
            scope=self,
            version=confirm_signup_handler.current_version,
            id=f"{STAGE}-confirm-signup-alias",
            alias_name="confirm-signup-alias",
        )

        # Signin & alias
        signin_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-signin-handler",
            function_name=f"{STAGE}-signin-handler",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="signin-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-signin":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:InitiateAuth"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/signin")))

        signin_alias = lmb.Alias(
            scope=self,
            version=signin_handler.current_version,
            id=f"{STAGE}-signin-alias",
            alias_name="signin-alias",
        )

        # Confirm signin & alias
        confirm_signin_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-confirm-signin-handler",
            function_name=f"{STAGE}-confirm-signin-handler",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="confirm-signin-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-confirm-signin":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "dynamodb:*",
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "dynamodb:PutItem",
                                    "cognito:RespondToAuthChallenge"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/confirm-signin")))

        confirm_signin_alias = lmb.Alias(
            scope=self,
            version=confirm_signin_handler.current_version,
            id=f"{STAGE}-confirm-signin-alias",
            alias_name="confirm-signin-alias",
        )

        # Setup TOTP & alias
        setup_totp_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-setup-totp",
            function_name=f"{STAGE}-setup-totp",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="setup-totp-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-setup-totp":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:AssociateSoftwareToken"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/setup-totp")))

        setup_totp_alias = lmb.Alias(
            scope=self,
            version=setup_totp_handler.current_version,
            id=f"{STAGE}-setup-totp-alias",
            alias_name="setup-totp-alias",
        )

        # Get user details & alias
        get_user_details_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-get-user-details",
            function_name=f"{STAGE}-get-user-details",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="get-user-details-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-get-user-details":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "dynamodb:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "dynamodb:GetItem"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/get-user-details")))

        get_user_details_alias = lmb.Alias(
            scope=self,
            version=get_user_details_handler.current_version,
            id=f"{STAGE}-get-user-details-alias",
            alias_name="get-user-details-alias"
        )

        # Change password & alias
        change_password_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-change-password",
            function_name=f"{STAGE}-change-password",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="change-password-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-change-password":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:ChangePassword"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/change-password")))

        change_password_alias = lmb.Alias(
            scope=self,
            version=change_password_handler.current_version,
            id=f"{STAGE}-change-password-alias",
            alias_name="change-password-alias"
        )

        # Forgot password & alias
        forgot_password_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-forgot-password",
            function_name=f"{STAGE}-forgot-password",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="forgot-password-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-forgot-password":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:ForgotPassword"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/forgot-password")))

        forgot_password_alias = lmb.Alias(
            scope=self,
            version=forgot_password_handler.current_version,
            id=f"{STAGE}-forgot-password-alias",
            alias_name="forgot-password-alias"
        )

        # Confirm forgot password & alias
        confirm_forgot_password_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-confirm-forgot-password",
            function_name=f"{STAGE}-confirm-forgot-password",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="confirm-forgot-password-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-forgot-password":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:ConfirmForgotPassword"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/confirm-forgot-password")))

        confirm_forgot_password_alias = lmb.Alias(
            scope=self,
            version=confirm_forgot_password_handler.current_version,
            id=f"{STAGE}-confirm-forgot-password-alias",
            alias_name="confirm-forgot-password-alias"
        )

        # Resend confirmation code & alias
        resend_confirmation_code_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-resend-confirmation-code",
            function_name=f"{STAGE}-resend-confirmation-code",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="resend-confirmation-code-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cognito-resend-confirmation-code":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "cognito:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "cognito:ResendConfirmationCode"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/serverless-authentication/resend-confirmation-code")))

        resend_confirmation_code_alias = lmb.Alias(
            scope=self,
            version=resend_confirmation_code_handler.current_version,
            id=f"{STAGE}-resend-confirmation-code-alias",
            alias_name="resend-confirmation-code-alias"
        )

        ######################################
        #   Create & configure API Gateway   #
        ######################################

        # Create REST api gateway
        self.api_gateway = RestApi(
            scope=self,
            id="serverless-authentication",
            rest_api_name="authentication",
            description="Thea cognito serverless authentication api gateway",
            retain_deployments=True,
            deploy=True,
            endpoint_configuration=EndpointConfiguration(types=[EndpointType.REGIONAL]),
            deploy_options=StageOptions(
                cache_data_encrypted=True,
                cache_ttl=cdk.Duration.minutes(5),
                caching_enabled=False,
                data_trace_enabled=True,
                logging_level=MethodLoggingLevel.INFO,
                metrics_enabled=False,
                throttling_burst_limit=5000,
                throttling_rate_limit=5000,
                stage_name=STAGE
            ),
            default_cors_preflight_options=CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST"]
            )
        )

        # Signup lambda integration
        signup = self.api_gateway.root.add_resource("signup")
        signup_lambda_integration = LambdaIntegration(
            handler=signup_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/signup/schema.json"), "r")))}
        )
        signup.add_method("POST", signup_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-signup",
            model_name=f"{STAGE}Signup",
            description="Default schema for signup route",
            schema=JsonSchema(
                title=f"{STAGE}-signup",
                type=JsonSchemaType.OBJECT,
                properties={
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "password":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "userAttributes":JsonSchema(
                        type=JsonSchemaType.OBJECT,
                        properties={
                            "name":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "preferred_username":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "custom:type":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "custom:organization":JsonSchema(
                                type=JsonSchemaType.STRING
                            )
                        }
                    )
                }
            )
        )

        # Confirm signup lambda integration
        confirm_signup = self.api_gateway.root.add_resource("confirm-signup")
        confirm_signup_lambda_integration = LambdaIntegration(
            handler=confirm_signup_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/confirm-signup/schema.json"), "r")))}
        )
        confirm_signup.add_method("POST", confirm_signup_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-confirm-signup",
            model_name=f"{STAGE}ConfirmSignup",
            description="Default schema for confirm signup route",
            schema=JsonSchema(
                title=f"{STAGE}-confirm-signup",
                type=JsonSchemaType.OBJECT,
                properties={
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "confirmationCode":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "userAttributes":JsonSchema(
                        type=JsonSchemaType.OBJECT,
                        properties={
                            "email":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "name":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "username":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "custom:role":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                            "custom:organization":JsonSchema(
                                type=JsonSchemaType.STRING
                            ),
                        }
                    )
                }
            )
        )

        # Signin lambda integration
        signin = self.api_gateway.root.add_resource("signin")
        signin_lambda_integration = LambdaIntegration(
            handler=signin_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/signin/schema.json"), "r")))}
        )
        signin.add_method("POST", signin_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-signin",
            model_name=f"{STAGE}Signin",
            description="Default schema for signin route",
            schema=JsonSchema(
                title=f"{STAGE}-signin",
                type=JsonSchemaType.OBJECT,
                properties={
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "password":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "authFlow":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                }
            )
        )

        # Confirm signin lambda integration
        confirm_signin = self.api_gateway.root.add_resource("confirm-signin")
        confirm_signin_lambda_integration = LambdaIntegration(
            handler=confirm_signin_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/confirm-signin/schema.json"),"r")))}
        )
        confirm_signin.add_method("POST", confirm_signin_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-confirm-signin",
            model_name=f"{STAGE}ConfirmSignin",
            description="Default schema for confirm signin route",
            schema=JsonSchema(
                title=f"{STAGE}-confirm-signin",
                type=JsonSchemaType.OBJECT,
                properties={
                    "mfaCode":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "sessionToken":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "challengeName":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                }
            )
        )

        # Setup TOTP lambda integration
        setup_totp = self.api_gateway.root.add_resource("setup-totp")
        setup_totp_lambda_integration = LambdaIntegration(
            handler=setup_totp_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/setup-totp/schema.json"),"r")))}
        )
        setup_totp.add_method("POST", setup_totp_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-setup-totp",
            model_name=f"{STAGE}SetupTotp",
            description="Default schema for setup totp route",
            schema=JsonSchema(
                title=f"{STAGE}-setup-totp",
                type=JsonSchemaType.OBJECT,
                properties={
                    "mfaCode":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "sessionCode":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "sessionToken":JsonSchema(
                        type=JsonSchemaType.STRING
                    )
                }
            )
        )

        # Get user details lambda integration
        get_user_details = self.api_gateway.root.add_resource("get-user-details")
        get_user_details_lambda_integration = LambdaIntegration(
            handler=get_user_details_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/get-user-details/schema.json"),"r")))}
        )
        get_user_details.add_method("POST", get_user_details_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-get-user-details",
            model_name=f"{STAGE}GetUserDetails",
            description="Default schema for getting user details route",
            schema=JsonSchema(
                title=f"{STAGE}-get-user-details",
                type=JsonSchemaType.OBJECT,
                properties={
                    "accesToken":JsonSchema(
                        type=JsonSchemaType.STRING
                    )
                }
            )
        )

        # Change password lambda integration
        change_password = self.api_gateway.root.add_resource("change-password")
        change_password_lambda_integration = LambdaIntegration(
            handler=change_password_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/change-password/schema.json"),"r")))}
        )
        change_password.add_method("POST", change_password_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-change-password",
            model_name=f"{STAGE}ChangePassword",
            description="Default schema for changing password route",
            schema=JsonSchema(
                title=f"{STAGE}-change-password",
                type=JsonSchemaType.OBJECT,
                properties={
                    "oldPassword":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "newPassword":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "accessToken":JsonSchema(
                        type=JsonSchemaType.STRING
                    )
                }
            )
        )

        # Forgot password lambda integration
        forgot_password = self.api_gateway.root.add_resource("forgot-password")
        forgot_password_lambda_integration = LambdaIntegration(
            handler=forgot_password_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/forgot-password/schema.json"),"r")))}
        )
        forgot_password.add_method("POST", forgot_password_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-forgot-password",
            model_name=f"{STAGE}ForgotPassword",
            description="Default schema for forgot password route",
            schema=JsonSchema(
                title=f"{STAGE}-forgot-password",
                type=JsonSchemaType.OBJECT,
                properties={
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    )
                }
            )
        )

        # Confirm forgot password lambda integration
        confirm_forgot_password = self.api_gateway.root.add_resource("confirm-forgot-password")
        confirm_forgot_password_lambda_integration = LambdaIntegration(
            handler=confirm_forgot_password_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/confirm-forgot-password/schema.json"),"r")))}
        )
        confirm_forgot_password.add_method("POST", confirm_forgot_password_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-confirm-forgot-password",
            model_name=f"{STAGE}ConfirmForgotPassword",
            description="Default schema for confirm forgot password route",
            schema=JsonSchema(
                title=f"{STAGE}-confirm-forgot-password",
                type=JsonSchemaType.OBJECT,
                properties={
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "newPassword":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "confirmationCode":JsonSchema(
                        type=JsonSchemaType.STRING
                    )
                }
            )
        )

        # Resend confirmation code lambda integration
        resend_confirmation_code = self.api_gateway.root.add_resource("resend-confirmation-code")
        resend_confirmation_code_lambda_integration = LambdaIntegration(
            handler=resend_confirmation_code_handler,
            allow_test_invoke=True,
            proxy=False,
            # request_templates={"application/json":str(load(open(path.join(current_directory, "lambdas/resend-confirmation-code/schema.json"),"r")))}
        )
        resend_confirmation_code.add_method("POST", resend_confirmation_code_lambda_integration)
        self.api_gateway.add_model(
            id=f"{STAGE}-resend-confirmation-code",
            model_name=f"{STAGE}ResendConfirmationCode",
            description="Default schema for resend confirmation code route",
            schema=JsonSchema(
                title=f"{STAGE}-resend-confirmation-code",
                type=JsonSchemaType.OBJECT,
                properties={
                    "username":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientId":JsonSchema(
                        type=JsonSchemaType.STRING
                    ),
                    "clientSecret":JsonSchema(
                        type=JsonSchemaType.STRING
                    )
                }
            )
        )

        ######################################
        #  Config per lambda failure Alarms  #
        #   create timed canary deployment   #
        ######################################

        # Zipped alias name & function
        zipped = [
            (f"{STAGE}-signup-alias", signup_alias),
            (f"{STAGE}-confirm-signup-alias", confirm_signup_alias),
            (f"{STAGE}-signin-alias", signin_alias),
            (f"{STAGE}-confirm-signin-alias", confirm_signin_alias),
            (f"{STAGE}-setup-totp-alias", setup_totp_alias),
            (f"{STAGE}-get-user-details-alias", get_user_details_alias),
            (f"{STAGE}-change-password-alias", change_password_alias),
            (f"{STAGE}-forgot-password-alias", forgot_password_alias),
            (f"{STAGE}-confirm-forgot-password-alias", confirm_forgot_password_alias),
            (f"{STAGE}-resend-confirmation-code-alias", resend_confirmation_code_alias)
        ]

        for name, alias in zipped:

            # Alarm configuration 
            failure_alarm = cloudwatch.Alarm(
                scope=self, 
                id=f"{name}-alarm",
                metric=cloudwatch.Metric(
                    metric_name='5XXError',
                    namespace=f'AWS/ApiGateway/Authentication/{name}',
                    dimensions={'ApiName': 'authentication'},
                    statistic='Sum',
                    period=cdk.Duration.minutes(1)),
                threshold=1,
                evaluation_periods=1)

            # Canary deployment
            codedeploy.LambdaDeploymentGroup(
                scope=self,
                id=f'{name}-deployment-group',
                alias=alias,
                deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_10_MINUTES,
                alarms=[failure_alarm])


        ######################################
        #      Create API gateway URL ref    #
        ######################################

        # Create reference for serverless authentication API gateway
        self.url_output = cdk.CfnOutput(
            scope=self,
            id="serverless-authentication-api-gateway-url",
            value=self.api_gateway.url
        )