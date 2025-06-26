# Standard Library
from os import getenv
from enum import Enum
from typing import Any, List, Optional
from dataclasses import fields, dataclass, field

# Static
AWS_ACCOUNT_ID = getenv("AWS_ACCOUNT_ID")
AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")
HOSTED_ZONE_ID = getenv("HOSTED_ZONE_ID")


# Enums
class BaseEnum(Enum):
    @classmethod
    def values(cls) -> Optional[List[str]]:
        result = []
        for item in cls:
            result.append(item.value)
        return result


class MyDomainName(Enum):
    domain_name = "thatsmidnight.com"
    subdomain_name = "www.thatsmidnight.com"


class CDKStackRegion(Enum):
    region = "us-east-1"


class S3ResourcePolicyActions(BaseEnum):
    get_object = "s3:GetObject*"
    get_bucket = "s3:GetBucket*"
    list_all = "s3:List*"


class OriginAccessControlOriginType(Enum):
    mediastore = "mediastore"
    s3 = "s3"


class OriginAccessControlSigningBehavior(Enum):
    always = "always"
    never = "never"
    no_override = "no_override"


# Data classes
@dataclass
class DefaultValue:
    value: Any


@dataclass
class MyDataClassBase:
    def __post_init__(self):
        # Loop through the dataclass fields
        for field_ in fields(self):
            # if a field of this data class defines a default value of type
            # `DefaultVal`, then use its value in case the field after
            # initialization has either not changed or is None.
            if isinstance(field_.default, DefaultValue):
                field_value = getattr(self, field_.name)
                if (
                    isinstance(field_value, DefaultValue)
                    or field_value is None
                ):
                    setattr(self, field_.name, field_.default.value)


@dataclass
class OACConfigPropertyDataClass(MyDataClassBase):
    name: str
    origin_access_control_origin_type: OriginAccessControlOriginType = field(
        default_factory=lambda: OriginAccessControlOriginType.s3
    )
    signing_behavior: Any = field(
        default_factory=lambda: DefaultValue("always")
    )
    signing_protocol: Any = field(
        default_factory=lambda: DefaultValue("sigv4")
    )
    description: Any = field(default_factory=lambda: DefaultValue(None))
