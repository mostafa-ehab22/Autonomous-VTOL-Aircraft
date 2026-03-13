from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =======================================
        #   DATABASE: DynamoDB for Flight Logs
        # =======================================
        self.flight_logs_table = dynamodb.Table(
            self, "VtolFlightLogsTable",
            partition_key=dynamodb.Attribute(name="vtol_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.NUMBER),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            
            # ⚠️ Change to RemovalPolicy.RETAIN before real flight tests!
            removal_policy=RemovalPolicy.DESTROY, 
            point_in_time_recovery=True 
        )