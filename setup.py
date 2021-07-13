import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="thea_manager_backend",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "thea_manager_backend"},
    packages=setuptools.find_packages(where="thea_manager_backend"),

    install_requires=[
        "aws-cdk.core==1.112.0",
        "aws-cdk.aws-apigateway==1.112.0",
        "aws-cdk.aws-apigatewayv2-integrations==1.112.0",
        "aws-cdk.aws-apigatewayv2==1.112.0",
        "aws-cdk.aws-cloudwatch==1.112.0",
        "aws-cdk.aws-codedeploy==1.112.0",
        "aws-cdk.aws-codepipeline-actions==1.112.0",
        "aws-cdk.aws-codepipeline==1.112.0",
        "aws-cdk.aws-cognito==1.112.0",
        "aws-cdk.aws-iam==1.112.0",
        "aws-cdk.aws-lambda==1.112.0",
        "aws-cdk.pipelines==1.112.0",
        "aws_cdk.aws_autoscaling==1.112.0",
        "aws_cdk.aws_cloudfront==1.112.0",
        "aws_cdk.aws_cloudfront_origins==1.112.0",
        "aws_cdk.aws_dynamodb==1.112.0",
        "aws_cdk.aws_ec2==1.112.0",
        "aws_cdk.aws_elasticloadbalancingv2",
        "aws_cdk.aws_elasticloadbalancingv2==1.112.0",
        "aws_cdk.aws_elasticloadbalancingv2==1.112.0",
        "aws_cdk.aws_iam==1.112.0",
        "aws_cdk.aws_s3==1.112.0"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
