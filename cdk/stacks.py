# Third Party
from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_cloudfront as cf,
    aws_route53 as route53,
    aws_certificatemanager as cm,
    aws_s3_deployment as s3_deploy,
    aws_route53_targets as targets,
    aws_cloudfront_origins as origins,
)

# Library
from cdk import constructs, enums


class MyStaticSiteStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_name: str,
        **kwargs,
    ) -> None:
        env = constructs.MyEnvironment(
            region=enums.CDKStackRegion.region.value
        )

        super().__init__(scope, id, env=env, stack_name=stack_name, **kwargs)

        # Create S3 buckets
        my_bucket = constructs.MyBucket(
            self,
            "my-domain-bucket",
            bucket_name=enums.MyDomainName.domain_name.value,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                    allowed_headers=["Authorization"],
                    max_age=3000,
                )
            ],
        )

        # Get Route 53 hosted zone
        zone = constructs.MyHostedZone(
            self,
            "my-hosted-zone",
            hosted_zone_id=enums.HOSTED_ZONE_ID,
            zone_name=enums.MyDomainName.domain_name.value,
        ).zone

        # Create domain certificate
        cert = constructs.MyCertificate(
            self,
            "my-domain-certificate",
            domain_name=enums.MyDomainName.domain_name.value,
            validation=cm.CertificateValidation.from_dns(zone),
            subject_alternative_names=[
                f"*.{enums.MyDomainName.domain_name.value}",
            ],
        )

        # Create Cloudfront user and grant read on root domain bucket
        cloudfront_oai = constructs.MyCloudFrontOAI(
            self,
            "my-cloudfront-oai",
            comment=f"CloudFront OAI for {enums.MyDomainName.domain_name.value}",
        )

        # Grant OAI read access to root domain bucket
        my_bucket.grant_read(cloudfront_oai)

        # Create CloudFront distribution
        distribution = constructs.MyDistribution(
            self,
            "my-cloudfront-distribution",
            default_behavior=cf.BehaviorOptions(
                compress=True,
                origin=origins.S3Origin(
                    bucket=my_bucket,
                    origin_access_identity=cloudfront_oai,
                ),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            domain_names=[
                f"{enums.MyDomainName.domain_name.value}",
                f"{enums.MyDomainName.subdomain_name.value}",
            ],
            default_root_object="index.html",
            certificate=cert,
        )

        # Create CloudFront distribution A records
        constructs.MyARecord(
            self,
            "my-cf-a-record",
            zone=zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution),
            ),
        )
        constructs.MyARecord(
            self,
            "my-subdomain-cf-a-record",
            zone=zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution),
            ),
            record_name="www",
        )

        # Deploy content to bucket
        constructs.MyBucketDeployment(
            self,
            "my-bucket-deployment",
            sources=[s3_deploy.Source.asset("./src")],
            desination_bucket=my_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
            storage_class=s3_deploy.StorageClass.INTELLIGENT_TIERING,
            server_side_encryption=s3_deploy.ServerSideEncryption.AES_256,
            cache_control=[
                s3_deploy.CacheControl.set_public(),
                s3_deploy.CacheControl.max_age(Duration.hours(1)),
            ],
        )