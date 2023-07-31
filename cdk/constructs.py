# Builtin
from os import getenv
from typing import List, Optional

# Third Party
from constructs import Construct
from aws_cdk import (
    Environment,
    RemovalPolicy,
    aws_s3 as s3,
    aws_certificatemanager as cm,
    aws_cloudfront as cf,
    aws_iam as iam,
    aws_s3_deployment as s3_deploy,
    aws_route53 as route53
)


class MyEnvironment(Environment):
    def __init__(self, *, account: str = None, region: str = None) -> None:
        account = getenv("AWS_ACCOUNT_ID") if not account else account
        region = getenv("AWS_DEFAULT_REGION") if not region else region
        super().__init__(account=account, region=region)


class MyBucket(s3.Bucket):
    @property
    def cloudfront_oai_policy(self) -> Optional[iam.PolicyStatement]:
        if hasattr(self, "_cloudfront_oai_policy"):
            return self._cloudfront_oai_policy

    def __init__(
        self,
        scope: Construct,
        id: str,
        bucket_name: str,
        access_control=s3.BucketAccessControl.PRIVATE,
        **kwargs
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

    def add_cloudfront_oai_to_policy(
        self,
        actions: List[str],
        resources: List[str],
        principals: List[iam.CanonicalUserPrincipal],
    ) -> None:
        self._cloudfront_oai_policy = iam.PolicyStatement(
            actions=actions,
            resources=resources,
            principals=principals,
        )
        self.add_to_resource_policy(permission=self.cloudfront_oai_policy)


class MyCertificate(cm.Certificate):
    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name: str,
        validation=cm.CertificateValidation.from_dns(),
        subject_alternative_names: Optional[List[str]]=None,
    ) -> None:
        super().__init__(
            scope,
            id,
            domain_name=domain_name,
            subject_alternative_names=subject_alternative_names,
            validation=validation,
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


class MyViewerCertificate:
    @property
    def cert(self) -> cf.ViewerCertificate:
        if hasattr(self, "_cert"):
            return self._cert

    def __init__(
        self,
        certificate: cm.Certificate,
        aliases: List[str],
        security_policy: str = cf.SecurityPolicyProtocol.TLS_V1_2_2021,
        ssl_method: str = cf.SSLMethod.SNI,
    ) -> None:
        self._cert = cf.ViewerCertificate.from_acm_certificate(
            certificate=certificate,
            aliases=aliases,
            security_policy=security_policy,
            ssl_method=ssl_method,
        )


class MyDistribution(cf.CloudFrontWebDistribution):
    def __init__(
        self,
        scope: Construct,
        id: str,
        s3_bucket_source: s3.Bucket,
        origin_access_identity: cf.OriginAccessIdentity,
        allowed_methods: str,
        viewer_certificate: cf.ViewerCertificate,
    ) -> None:
        behaviors = [
            cf.Behavior(
                is_default_behavior=True,
                compress=True,
                allowed_methods=allowed_methods,
            )
        ]
        s3_origin_config = cf.S3OriginConfig(
            s3_bucket_source=s3_bucket_source,
            origin_access_identity=origin_access_identity,
        )
        origin_configs = [
            cf.SourceConfiguration(
                s3_origin_source=s3_origin_config,
                behaviors=behaviors,
            )
        ]
        super().__init__(
            scope,
            id,
            origin_configs=origin_configs,
            viewer_certificate=viewer_certificate,
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
    ) -> None:
        super().__init__(
            scope,
            id,
            sources=sources,
            destination_bucket=desination_bucket,
            distribution=distribution,
            distribution_paths=distribution_paths,
        )


class MyPolicyStatement(iam.PolicyStatement):
    def __init__(
        self,
        *,
        sid: str,
        effect: Optional[iam.Effect],
        principals: Optional[List[iam.IPrincipal]],
        actions: Optional[List[str]],
        resources: Optional[List[str]],
        **kwargs,
    ) -> None:
        super().__init__(
            sid=sid,
            effect=effect,
            principals=principals,
            actions=actions,
            resources=resources,
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
        **kwargs,
    ) -> None:
        super().__init__(scope, id, zone=zone, target=target, **kwargs)


class MyAAAARecord(route53.AaaaRecord):
    def __init__(
        self,
        scope: Construct,
        id: str,
        zone: route53.IHostedZone,
        target: route53.RecordTarget,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, zone=zone, target=target, **kwargs)
