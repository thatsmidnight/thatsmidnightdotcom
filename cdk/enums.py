# Builtin
from enum import Enum
from os import getenv
from typing import List

# Try to load a .env file (local only)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError as e:
    print("Error -> ", e)


# Static
AWS_ACCOUNT_ID = getenv("AWS_ACCOUNT_ID")
AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")
HOSTED_ZONE_ID = getenv("HOSTED_ZONE_ID")


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
    subdomain_name = "www.thatsmidnight.com"


class CDKStackRegion(Enum):
    region = "us-east-1"


class S3ResourcePolicyActions(BaseEnum):
    get_object = "s3:GetObject"
