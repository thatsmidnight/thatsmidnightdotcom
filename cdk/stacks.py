# Third Party
from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    aws_route53 as route53,
    aws_s3_deployment as s3_deploy,
    aws_route53_targets as targets,
    aws_certificatemanager as cm,
)
from constructs import Construct

# My Libraries
from cdk import enums, constructs


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

        # Create origin access control for distribution to access bucket
        cloudfront_oac = constructs.MyCloudFrontOAC(
            self,
            "my-cloudfront-oac",
            name="MyCloudFrontOAC",
            description=f"CloudFront OAC for {enums.MyDomainName.domain_name.value}",
        )

        # Create CloudFront distribution
        distribution = constructs.MyDistribution(
            self,
            "my-cloudfront-distribution",
            bucket=my_bucket,
            domain_names=[
                f"{enums.MyDomainName.domain_name.value}",
                f"{enums.MyDomainName.subdomain_name.value}",
            ],
            certificate=cert,
        )

        # Create OAC policy document and add to bucket resource policy
        my_bucket.add_to_resource_policy(
            constructs.MyPolicyStatement(
                sid="AllowCloudFrontServicePrincipalReadOnly",
                principals=[
                    iam.ServicePrincipal(
                        service="cloudfront.amazonaws.com",
                        conditions={
                            "StringEquals": {
                                "AWS:SourceArn": Stack.of(self).format_arn(
                                    region="",
                                    service="cloudfront",
                                    account=self.account,
                                    resource="distribution",
                                    resource_name=distribution.distribution_id,
                                )
                            }
                        },
                    ),
                ],
                actions=[
                    enums.S3ResourcePolicyActions.get_object.value,
                ],
                resources=[f"{my_bucket.bucket_arn}/*"],
            )
        )
        bucket_policy = my_bucket.policy
        bucket_policy_document = bucket_policy.document

        # Remove the OAI permission from the bucket policy
        if isinstance(bucket_policy_document, iam.PolicyDocument):
            bucket_policy_document_json = bucket_policy_document.to_json()
            # Create updated policy without the OAI reference
            bucket_policy_updated_json = {
                "Version": "2012-10-17",
                "Statement": [],
            }
            for statement in bucket_policy_document_json["Statement"]:
                if "CanonicalUser" not in statement["Principal"]:
                    bucket_policy_updated_json["Statement"].append(statement)

        # Apply the updated bucket policy to the bucket
        bucket_policy_override = my_bucket.node.find_child(
            "Policy"
        ).node.default_child
        bucket_policy_override.add_override(
            "Properties.PolicyDocument", bucket_policy_updated_json
        )

        # Remove the created OAI reference (S3 origin property) for the distribution
        all_distribution_properties = distribution.node.find_all()
        for child in all_distribution_properties:
            if child.node.id == "S3Origin":
                child.node.try_remove_child("Resource")

        # Associate the created OAC with the distribution
        distribution_properties = distribution.node.default_child
        distribution_properties.add_override(
            "Properties.DistributionConfig.Origins.0.S3OriginConfig.OriginAccessIdentity",
            "",
        )
        distribution_properties.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId",
            cloudfront_oac.ref,
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
