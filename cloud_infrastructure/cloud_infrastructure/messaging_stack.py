from aws_cdk import (
    Stack,
    Duration,
    aws_sqs as sqs,
)
from constructs import Construct

class MessagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ==========================================
        #   QUEUES: SQS for Telemetry Ingestion
        # ==========================================

        # Failsafe DLQ: Holds corrupted or unprocessable telemetry after 3 failed Lambda processing attempts
        # Retains failed messages for 14 days for manual debugging
        self.telemetry_dlq = sqs.Queue(
            self, "TelemetryDeadLetterQueue",
            retention_period=Duration.days(14) 
        )

        # SQS Main Ingestion Queue: Buffers incoming telemetry from the VTOL
        self.telemetry_queue = sqs.Queue(
            self, "TelemetryQueue",
            visibility_timeout=Duration.seconds(30), 
            retention_period=Duration.days(1),
            # Route to DLQ after 3 failed processing attempts by Lambda
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3, 
                queue=self.telemetry_dlq
            )
        )
