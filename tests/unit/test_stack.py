import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk.stacks import MyStaticSiteStack as MyStack


def test_s3_bucket_created():
    app = core.App()
    stack = MyStack(app, "thatsmidnightdotcom", stack_name="test-stack-name")
    template = assertions.Template.from_stack(stack)

    template.has_resource("AWS::S3::Bucket", assertions.Match.any_value())
