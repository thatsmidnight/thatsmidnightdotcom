# Third Party
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_cloudfront as cf,
    aws_s3_deployment as s3_deploy,
    aws_iam as iam,
    aws_s3 as s3,
    aws_route53 as route53
)

# Library
from cdk import constructs, enums


class MyStaticSiteStack(Stack):
    DOMAIN_NAME = enums.MyDomainName.domain_name.value
    SUBDOMAIN_NAME = enums.MyDomainName.subdomain_name.value
    MY_ENV = constructs.MyEnvironment(
        region=enums.CDKStackRegion.region.value
    )

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
            access_control=s3.BucketAccessControl.PUBLIC_READ,
        )
        my_sub_bucket = constructs.MyBucket(
            self,
            "my-subdomain-bucket",
            bucket_name=self.SUBDOMAIN_NAME,
            website_redirect=s3.RedirectTarget(
                host_name=self.DOMAIN_NAME,
                protocol=s3.RedirectProtocol.HTTP,
            ),
        )

        # Create public read policy
        my_bucket_policy = constructs.MyPolicyStatement(
            sid="PublicReadGetObject",
            effect=iam.Effect.ALLOW,
            principals=[iam.AnyPrincipal()],
            actions=[enums.S3ResourcePolicyActions.get_object.value],
            resources=[f"arn:aws:s3:::{my_bucket.bucket_name}/*"],
        )
        my_bucket.add_to_resource_policy(my_bucket_policy)

        # Get Route 53 hosted zone
        zone = constructs.MyHostedZone(
            self,
            "my-hosted-zone",
            hosted_zone_id=enums.HOSTED_ZONE_ID,
            zone_name=self.DOMAIN_NAME,
        ).zone

        # Add 'A' record of S3 domain and subdomain
        constructs.MyARecord(
            self,
            "my-s3-domain-arecord",
            zone=zone,
            target=route53.RecordTarget.from_values(
                my_bucket.bucket_website_domain_name
            ),
        )

        # Add 'AAAA' record of S3 domain and subdomain
        constructs.MyAAAARecord(
            self,
            "my-s3-domain-aaaarecord",
            zone=zone,
            target=route53.RecordTarget.from_values(
                my_bucket.bucket_dual_stack_domain_name
            ),
        )

        # Create domain certificate
        # NOTE: You need to go to the console and MANUALLY update the hosted
        #   zone records with the certificate. The CDK deployment will hang
        #   until this is completed.
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
            allowed_methods=cf.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
            viewer_certificate=viewer_cert,
        )

        # TODO: Add 'CNAME' record of distribution

        # Create bucket deployment
        sources = [s3_deploy.Source.asset("./src")]
        constructs.MyBucketDeployment(
            self,
            "my-bucket-deployment",
            sources=sources,
            desination_bucket=my_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )
