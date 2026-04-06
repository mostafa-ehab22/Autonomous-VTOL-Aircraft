#!/usr/bin/env python3

# Copyright 2026 Mostafa Ehab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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