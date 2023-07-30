from aws_cdk import App
from dotenv import load_dotenv

load_dotenv()

from cdk.stacks import MyStaticSiteStack

app = App()

stack_name = "my-static-website-stack"
MyStaticSiteStack(app, stack_name, stack_name=stack_name)

app.synth()
