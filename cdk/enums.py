# Builtin
from enum import Enum
from os import getenv
from typing import List

# Third Party
from dotenv import load_dotenv

load_dotenv()


# Static
AWS_ACCOUNT_ID = getenv("AWS_ACCOUNT_ID")
AWS_ACCESS_KEY = getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")


# Enums
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
