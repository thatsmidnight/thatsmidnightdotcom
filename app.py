from aws_cdk import App

from cdk.stacks import MyStaticSiteStack

app = App()

stack_name = "my-static-website-stack"
stack = MyStaticSiteStack(app, stack_name, stack_name=stack_name)

app.synth()
