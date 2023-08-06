#!/usr/bin/env python
# Standard Library
from os import getenv

# Third Party
from aws_cdk import App

if getenv("IS_LOCAL") == "true":
    # Try to load .env
    try:
        # Third Party
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError as e:
        print("Error -> ", e)

# My Libraries
from cdk.stacks import MyStaticSiteStack

# Initialize application
app = App()

# Initialize stack
stack_name = "my-static-website-stack"
MyStaticSiteStack(app, stack_name, stack_name=stack_name)

# Synthesize application stack
app.synth()
