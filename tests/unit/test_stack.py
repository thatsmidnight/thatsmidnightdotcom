# Third Party
from unittest.mock import patch
import aws_cdk as core
import aws_cdk.assertions as assertions

# My Libraries
from cdk.stacks import MyStaticSiteStack as MyStack


@patch("cdk.stacks.enums.HOSTED_ZONE_ID", new_callable=lambda: "Z1234567890ABC")
def test_s3_bucket_created(mocked_hosted_zone_id):
    app = core.App()
    stack = MyStack(app, "thatsmidnightdotcom", stack_name="test-stack-name")
    template = assertions.Template.from_stack(stack)

    template.has_resource("AWS::S3::Bucket", assertions.Match.any_value())
