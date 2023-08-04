# Builtin
from os import getenv
from dataclasses import asdict
from typing import List, Optional

# Third Party
from constructs import Construct
from aws_cdk import (
    Environment,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_cloudfront as cf,
    aws_route53 as route53,
    aws_certificatemanager as cm,
    aws_s3_deployment as s3_deploy,
)

# Library
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


class MyOACConfigProperty(cf.CfnOriginAccessControl.OriginAccessControlConfigProperty):
    def __init__(
        self,
        oac_config_property_data_class=enums.OACConfigPropertyDataClass,
    ) -> None:
        super().__init__(**asdict(oac_config_property_data_class))


class MyCloudFrontOAC(cf.CfnOriginAccessControl):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **oac_config_property_data_class: enums.OACConfigPropertyDataClass,
    ) -> None:
        super().__init__(
            scope,
            id,
            origin_access_control_config=MyOACConfigProperty(
                enums.OACConfigPropertyDataClass(
                    **oac_config_property_data_class
                )
            ),
        )
        self.apply_removal_policy(RemovalPolicy.DESTROY)


class MyDistribution(cf.Distribution):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(
            scope,
            id,
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
