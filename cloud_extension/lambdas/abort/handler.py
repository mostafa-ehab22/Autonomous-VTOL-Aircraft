"""
Abort Lambda
Responsibility: Dispatches the abort command to the VTOL by updating the IoT Device Shadow
                desired state. Embeds the Step Functions task token to enable the ACK loop.
Invoked by: Step Functions (Unsafe path, after Bedrock returns Abort verdict)
"""

import json
import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot_client = boto3.client("iot-data", region_name=os.environ.get("AWS_REGION", "eu-central-1"))


def handler(event, context):
    """
    Input:  Normalized telemetry payload + Step Functions task token.
    Output: Confirmation that the Device Shadow desired state was updated.

    The task token is embedded in the shadow payload so the VTOL can include
    it in its MQTT ACK, closing the waitForTaskToken callback loop.
    """
    logger.info("Abort Lambda invoked. Event: %s", json.dumps(event))

    thing_name = event.get("thing_name")
    task_token = event.get("taskToken")

    if not thing_name:
        raise ValueError("Missing required field: thing_name")
    if not task_token:
        raise ValueError("Missing required field: taskToken")

    shadow_payload = {
        "state": {
            "desired": {
                "command":    "ABORT",
                "task_token": task_token,
            }
        }
    }

    try:
        response = iot_client.update_thing_shadow(
            thingName=thing_name,
            payload=json.dumps(shadow_payload).encode("utf-8"),
        )
        logger.info(
            "Device Shadow updated for %s. HTTP status: %s",
            thing_name,
            response["ResponseMetadata"]["HTTPStatusCode"],
        )
    except iot_client.exceptions.ResourceNotFoundException:
        logger.error("Thing not found in IoT Core: %s", thing_name)
        raise
    except Exception as e:
        logger.error("Failed to update Device Shadow for %s: %s", thing_name, str(e))
        raise

    return {
        "status":     "ABORT_DISPATCHED",
        "thing_name": thing_name,
    }