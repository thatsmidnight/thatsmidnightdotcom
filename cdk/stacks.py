# Builtin
from os import getenv

# Third Party
from constructs import Construct
from aws_cdk import Stack, Environment
from aws_cdk.aws_cloudfront import CloudFrontAllowedMethods
from aws_cdk.aws_s3_deployment import Source
from aws_cdk.aws_iam import Effect, AnyPrincipal
from aws_cdk.aws_s3 import (
    RedirectTarget,
    RedirectProtocol,
    BucketAccessControl,
)

# Library
from cdk import constructs, enums


class MyEnvironment(Environment):
    def __init__(self, *, account: str = None, region: str = None) -> None:
        account = getenv("AWS_ACCOUNT_ID") if not account else account
        region = getenv("AWS_DEFAULT_REGION") if not region else region
        super().__init__(account=account, region=region)


class MyStaticSiteStack(Stack):
    DOMAIN_NAME = enums.MyDomainName.domain_name.value
    SUBDOMAIN_NAME = enums.MyDomainName.subdomain_name.value
    MY_ENV = MyEnvironment(region=enums.CDKStackRegion.region.value)

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_name: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope, id, env=self.MY_ENV, stack_name=stack_name, **kwargs
        )

        # Create S3 buckets
        my_bucket = constructs.MyBucket(
            self,
            "my-domain-bucket",
            bucket_name=self.DOMAIN_NAME,
            website_index_document="index.html",
            website_error_document="404.html",
            public_read_access=True,
            access_control=BucketAccessControl.PUBLIC_READ,
        )
        my_sub_bucket = constructs.MyBucket(
            self,
            "my-subdomain-bucket",
            bucket_name=self.SUBDOMAIN_NAME,
            website_redirect=RedirectTarget(
                host_name=self.DOMAIN_NAME,
                protocol=RedirectProtocol.HTTP,
            ),
        )

        # Create public read policy
        my_bucket_policy = constructs.MyPolicyStatement(
            sid="PublicReadGetObject",
            effect=Effect.ALLOW,
            principals=[AnyPrincipal()],
            actions=[enums.S3ResourcePolicyActions.get_object.value],
            resources=[f"arn:aws:s3:::{my_bucket.bucket_name}/*"],
        )
        my_bucket.add_to_resource_policy(my_bucket_policy)

        # Create domain certificate
        cert = constructs.MyCertificate(
            self,
            "my-domain-certificate",
            domain_name=self.DOMAIN_NAME,
            subject_alternative_names=[self.SUBDOMAIN_NAME],
        )

        # Create Cloudfront user
        cloudfront_oai = constructs.MyCloudFrontOAI(
            self, id, comment=f"CloudFront OAI for {self.DOMAIN_NAME}"
        )

        # Add Cloudfront resource policy to bucket
        my_bucket.add_cloudfront_oai_to_policy(
            actions=enums.S3ResourcePolicyActions.values(),
            resources=[my_bucket.arn_for_objects("*")],
            principals=[cloudfront_oai.grant_principal],
        )

        # Create viewer certificate
        viewer_cert = constructs.MyViewerCertificate(
            certificate=cert,
            aliases=[f"{self.DOMAIN_NAME}", f"{self.SUBDOMAIN_NAME}"],
        ).cert

        # Create CloudFront distribution
        distribution = constructs.MyDistribution(
            self,
            "my-cloudfront-distribution",
            s3_bucket_source=my_bucket,
            origin_access_identity=cloudfront_oai,
            allowed_methods=CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
            viewer_certificate=viewer_cert,
        )

        # Create bucket deployment
        sources = [Source.asset("./src")]
        constructs.MyBucketDeployment(
            self,
            "my-bucket-deployment",
            sources=sources,
            desination_bucket=my_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )
