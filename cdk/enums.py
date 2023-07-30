# Builtin
from enum import Enum
from typing import List


class BaseEnum(Enum):
    @classmethod
    def values(cls) -> List[str]:
        result = []
        for item in cls:
            result.append(item.value)
        return result


class MyDomainName(Enum):
    domain_name = "thatsmidnight.com"


class CDKStackRegion(Enum):
    region = "us-east-1"


class S3ResourcePolicyActions(BaseEnum):
    get_object = "s3:GetObject"
