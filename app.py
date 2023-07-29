from aws_cdk import App

from cdk.stacks import MyStaticSiteStack

app = App()
stack = MyStaticSiteStack(app, "my-static-website-stack")

app.synth()
