# Builtin
from typing import List, Optional

# Third Party
from constructs import Construct
from aws_cdk import RemovalPolicy
from aws_cdk.aws_s3 import (
    Bucket,
    BucketEncryption,
    BucketAccessControl,
)
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk.aws_cloudfront import (
    CloudFrontWebDistribution,
    OriginAccessIdentity,
    SecurityPolicyProtocol,
    SSLMethod,
    ViewerCertificate,
    SourceConfiguration,
    Behavior,
    S3OriginConfig,
)
from aws_cdk.aws_iam import (
    CanonicalUserPrincipal,
    Effect,
    IPrincipal,
    PolicyStatement,
)
from aws_cdk.aws_s3_deployment import BucketDeployment, Source


class MyBucket(Bucket):
    @property
    def cloudfront_oai_policy(self) -> Optional[PolicyStatement]:
        if hasattr(self, "_cloudfront_oai_policy"):
            return self._cloudfront_oai_policy

    def __init__(
        self,
        scope: Construct,
        id: str,
        bucket_name: str,
        access_control=BucketAccessControl.PRIVATE,
        **kwargs
    ) -> None:
        super().__init__(
            scope,
            id,
            bucket_name=bucket_name,
            encryption=BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            access_control=access_control,
            **kwargs,
        )

    def add_cloudfront_oai_to_policy(
        self,
        actions: List[str],
        resources: List[str],
        principals: List[CanonicalUserPrincipal],
    ) -> None:
        self._cloudfront_oai_policy = PolicyStatement(
            actions=actions,
            resources=resources,
            principals=principals,
        )
        self.add_to_resource_policy(permission=self.cloudfront_oai_policy)


class MyCertificate(Certificate):
    def __init__(
        self,
        scope: Construct,
        id: str,
        domain_name: str,
        validation=CertificateValidation.from_dns(),
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


class MyCloudFrontOAI(OriginAccessIdentity):
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
    def cert(self) -> ViewerCertificate:
        if hasattr(self, "_cert"):
            return self._cert

    def __init__(
        self,
        certificate: Certificate,
        aliases: List[str],
        security_policy: str = SecurityPolicyProtocol.TLS_V1_2_2021,
        ssl_method: str = SSLMethod.SNI,
    ) -> None:
        self._cert = ViewerCertificate.from_acm_certificate(
            certificate=certificate,
            aliases=aliases,
            security_policy=security_policy,
            ssl_method=ssl_method,
        )


class MyDistribution(CloudFrontWebDistribution):
    def __init__(
        self,
        scope: Construct,
        id: str,
        s3_bucket_source: Bucket,
        origin_access_identity: OriginAccessIdentity,
        allowed_methods: str,
        viewer_certificate: ViewerCertificate,
    ) -> None:
        behaviors = [
            Behavior(
                is_default_behavior=True,
                compress=True,
                allowed_methods=allowed_methods,
            )
        ]
        s3_origin_config = S3OriginConfig(
            s3_bucket_source=s3_bucket_source,
            origin_access_identity=origin_access_identity,
        )
        origin_configs = [
            SourceConfiguration(
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


class MyBucketDeployment(BucketDeployment):
    def __init__(
        self,
        scope: Construct,
        id: str,
        sources: List[Source],
        desination_bucket: Bucket,
        distribution: CloudFrontWebDistribution,
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


class MyPolicyStatement(PolicyStatement):
    def __init__(
        self,
        *,
        sid: str,
        effect: Optional[Effect],
        principals: Optional[List[IPrincipal]],
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
