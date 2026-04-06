import aws_cdk as core
import aws_cdk.assertions as assertions

from cloud_infrastructure.cloud_infrastructure_stack import CloudInfrastructureStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cloud_infrastructure/cloud_infrastructure_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CloudInfrastructureStack(app, "cloud-infrastructure")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
