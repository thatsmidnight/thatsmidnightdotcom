#!/usr/bin/env python

# Builtin
from os import environ

# Third Party
from aws_cdk import App
from dotenv import load_dotenv

load_dotenv()

# Library
from cdk import enums
from cdk.stacks import MyStaticSiteStack

# Set environment variables
environ["AWS_ACCOUNT_ID"] = enums.AWS_ACCOUNT_ID
environ["AWS_ACCESS_KEY_ID"] = enums.AWS_ACCESS_KEY_ID
environ["AWS_SECRET_ACCESS_KEY"] = enums.AWS_SECRET_ACCESS_KEY


# Initialize application
app = App()

# Initialize stack
stack_name = "my-static-website-stack"
MyStaticSiteStack(app, stack_name, stack_name=stack_name)

# Synthesize application stack
app.synth()
