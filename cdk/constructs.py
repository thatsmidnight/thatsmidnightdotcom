# Standard Library
from os import getenv
from typing import List, Optional

# Third Party
from aws_cdk import (
    Environment,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_route53 as route53,
    aws_cloudfront as cf,
    aws_s3_deployment as s3_deploy,
    aws_certificatemanager as cm,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

# My Libraries
from cdk import enums


class MyEnvironment(Environment):
    def __init__(self, *, account: str = None, region: str = None) -> None:
        account = getenv("AWS_ACCOUNT_ID") if not account else account
        region = getenv("AWS_DEFAULT_REGION") if not region else region
        super().__init__(account=account, region=region)


class MyBucket(s3.Bucket):
    def __init__(
        self,
        scope: Construct,
        id: str,
        bucket_name: str,
        access_control=s3.BucketAccessControl.PRIVATE,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id,
            bucket_name=bucket_name,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            access_control=access_control,
            **kwargs,
        )


class MyCertificate(cm.Certificate):
    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name: str,
        validation: cm.CertificateValidation,
        subject_alternative_names: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            scope,
            id,
            domain_name=domain_name,
            validation=validation,
            subject_alternative_names=subject_alternative_names,
        )
        self.apply_removal_policy(RemovalPolicy.DESTROY)


class MyCloudFrontOAI(cf.OriginAccessIdentity):
    def __init__(
        self,
        scope: Construct,
        id: str,
        comment: str,
    ) -> None:
        super().__init__(scope, id, comment=comment)
        self.apply_removal_policy(RemovalPolicy.DESTROY)


class MyCloudFrontOAC(cf.CfnOriginAccessControl):
    def __init__(
        self,
        scope: Construct,
        id: str,
        name: str,
        origin_access_control_origin_type: Optional[
            enums.OriginAccessControlOriginType
        ] = "s3",
        signing_behavior: Optional[
            enums.OriginAccessControlSigningBehavior
        ] = "no-override",
        signing_protocol: Optional[str] = "sigv4",
        description: Optional[str] = None,
    ) -> None:
        super().__init__(
            scope,
            id,
            origin_access_control_config=cf.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=name,
                origin_access_control_origin_type=origin_access_control_origin_type,
                signing_behavior=signing_behavior,
                signing_protocol=signing_protocol,
                description=description,
            ),
        )
        self.apply_removal_policy(RemovalPolicy.DESTROY)


class MyBehaviorOptions(cf.BehaviorOptions):
    def __init__(
        self,
        bucket: MyBucket,
        compress: bool = True,
        viewer_protocol_policy: cf.ViewerProtocolPolicy = cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowed_methods: cf.AllowedMethods = cf.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cached_methods: cf.CachedMethods = cf.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        cache_policy: cf.CachePolicy = cf.CachePolicy.CACHING_OPTIMIZED,
        origin_request_policy: cf.OriginRequestPolicy = cf.OriginRequestPolicy.CORS_S3_ORIGIN,
        response_headers_policy: cf.ResponseHeadersPolicy = cf.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS,
        **kwargs,
    ) -> None:
        super().__init__(
            origin=origins.S3BucketOrigin(bucket),
            compress=compress,
            viewer_protocol_policy=viewer_protocol_policy,
            allowed_methods=allowed_methods,
            cached_methods=cached_methods,
            cache_policy=cache_policy,
            origin_request_policy=origin_request_policy,
            response_headers_policy=response_headers_policy,
            **kwargs,
        )


class MyDistribution(cf.Distribution):
    def __init__(
        self,
        scope: Construct,
        id: str,
        bucket: MyBucket,
        domain_names: List[str],
        certificate: MyCertificate,
        compress: bool = True,
        viewer_protocol_policy: cf.ViewerProtocolPolicy = cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        default_root_object: str = "index.html",
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id,
            domain_names=domain_names,
            default_root_object=default_root_object,
            certificate=certificate,
            default_behavior=MyBehaviorOptions(
                bucket=bucket,
                compress=compress,
                viewer_protocol_policy=viewer_protocol_policy,
            ),
            **kwargs,
        )
        self.apply_removal_policy(RemovalPolicy.DESTROY)


class MyBucketDeployment(s3_deploy.BucketDeployment):
    def __init__(
        self,
        scope: Construct,
        id: str,
        sources: List[s3_deploy.Source],
        desination_bucket: s3.Bucket,
        distribution: cf.CloudFrontWebDistribution,
        distribution_paths: List[str],
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id,
            sources=sources,
            destination_bucket=desination_bucket,
            distribution=distribution,
            distribution_paths=distribution_paths,
            **kwargs,
        )


class MyHostedZone:
    @property
    def zone(self) -> route53.IHostedZone:
        if hasattr(self, "_zone"):
            return self._zone

    def __init__(
        self, scope: Construct, id: str, hosted_zone_id: str, zone_name: str
    ) -> None:
        self._zone = route53.HostedZone.from_hosted_zone_attributes(
            scope, id, hosted_zone_id=hosted_zone_id, zone_name=zone_name
        )


class MyARecord(route53.ARecord):
    def __init__(
        self,
        scope: Construct,
        id: str,
        zone: route53.IHostedZone,
        target: route53.RecordTarget,
        record_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id,
            zone=zone,
            target=target,
            record_name=record_name,
            **kwargs,
        )


class MyResponseHeadersPolicy(cf.ResponseHeadersPolicy):
    def __init__(
        self,
        scope: Construct,
        id: str,
        response_headers_policy_name: str,
        security_headers_behavior: cf.ResponseSecurityHeadersBehavior,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id,
            response_headers_policy_name=response_headers_policy_name,
            security_headers_behavior=security_headers_behavior,
            **kwargs,
        )


class MyPolicyStatement(iam.PolicyStatement):
    def __init__(
        self,
        sid: str,
        actions: List[str],
        resources: List[str],
        **kwargs,
    ) -> None:
        super().__init__(
            sid=sid,
            actions=actions,
            resources=resources,
            **kwargs,
        )
