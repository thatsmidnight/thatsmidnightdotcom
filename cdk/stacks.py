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


# Shared environment static variable
MY_ENV = constructs.MyEnvironment(region=enums.CDKStackRegion.region.value)


class MyStaticSiteStack(Stack):
    DOMAIN_NAME = enums.MyDomainName.domain_name.value
    SUBDOMAIN_NAME = enums.MyDomainName.subdomain_name.value

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_name: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope, id, env=MY_ENV, stack_name=stack_name, **kwargs
        )

        # Create S3 buckets
        my_bucket = constructs.MyBucket(
            self,
            "my-domain-bucket",
            bucket_name=self.DOMAIN_NAME,
            website_index_document="index.html",
            website_error_document="404.html",
            access_control=s3.BucketAccessControl.PUBLIC_READ,
            block_public_access=None,
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

        # Get Route 53 hosted zone
        zone = constructs.MyHostedZone(
            self,
            "my-hosted-zone",
            hosted_zone_id=enums.HOSTED_ZONE_ID,
            zone_name=self.DOMAIN_NAME,
        ).zone

        # Create domain certificate
        cert = constructs.MyCertificate(
            self,
            "my-domain-certificate",
            domain_name=self.DOMAIN_NAME,
            validation=cm.CertificateValidation.from_dns(zone),
            subject_alternative_names=[self.SUBDOMAIN_NAME],
        )

        # Create Cloudfront user and grant read on root domain bucket
        cloudfront_oai = constructs.MyCloudFrontOAI(
            self, id, comment=f"CloudFront OAI for {self.DOMAIN_NAME}"
        )
        my_bucket.grant_read(cloudfront_oai)

        # Create viewer certificate
        viewer_cert = constructs.MyViewerCertificate(
            certificate=cert,
            aliases=[f"{self.DOMAIN_NAME}", f"{self.SUBDOMAIN_NAME}"],
        ).cert

        # Create response headers policy
        response_headers_policy = constructs.MyResponseHeadersPolicy(
            self,
            "my-response-headers-policy",
            response_headers_policy_name="my-static-site-security-headers",
            security_headers_behavior=cf.ResponseSecurityHeadersBehavior(
                strict_transport_security=cf.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(63072000),
                    include_subdomains=True,
                    override=True,
                    preload=True,
                ),
                content_security_policy=cf.ResponseHeadersContentSecurityPolicy(
                    content_security_policy="default-src 'none'; img-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'",
                    override=True,
                ),
                content_type_options=cf.ResponseHeadersContentTypeOptions(
                    override=True
                ),
                frame_options=cf.ResponseHeadersFrameOptions(
                    frame_option=cf.HeadersFrameOption.DENY, override=True
                ),
                referrer_policy=cf.ResponseHeadersReferrerPolicy(
                    referrer_policy=cf.HeadersReferrerPolicy.SAME_ORIGIN,
                    override=True,
                ),
                xss_protection=cf.ResponseHeadersXSSProtection(
                    protection=True,
                    mode_block=True,
                    override=True,
                ),
            ),
        )

        # Create CloudFront distribution
        distribution = constructs.MyDistribution(
            self,
            "my-cloudfront-distribution",
            default_behavior=cf.BehaviorOptions(
                compress=True,
                origin=origins.S3Origin(my_bucket),
                response_headers_policy=response_headers_policy,
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            domain_names=[f"{self.DOMAIN_NAME}", f"{self.SUBDOMAIN_NAME}"],
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
        sources = [s3_deploy.Source.asset("./src")]
        constructs.MyBucketDeployment(
            self,
            "my-bucket-deployment",
            sources=sources,
            desination_bucket=my_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )
