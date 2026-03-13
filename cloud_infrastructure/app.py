#!/usr/bin/env python3
import os
import aws_cdk as cdk

# Import your two modules
from cloud_infrastructure.database_stack import DatabaseStack
from cloud_infrastructure.messaging_stack import MessagingStack

app = cdk.App()

# Explicitly define the deployment environment based on your local CLI
vtol_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"), 
    region=os.environ.get("CDK_DEFAULT_REGION")
)

# 1. Deploy the Database Stack
DatabaseStack(app, "VtolDatabaseStack", env=vtol_env)

# 2. Deploy the Messaging Stack
MessagingStack(app, "VtolMessagingStack", env=vtol_env)

app.synth()