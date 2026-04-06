"""
Continue Lambda
Responsibility: Handles the Safe mission path. Logs the mission result to DynamoDB,
                publishes a notification to the SNS Mission Log topic, and syncs the
                Device Shadow reported state to reflect an active mission.
Invoked by: Step Functions (Safe path, after Bedrock returns Continue verdict)
"""

import json
import logging
import os
import time
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb   = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "eu-central-1"))
sns_client = boto3.client("sns",       region_name=os.environ.get("AWS_REGION", "eu-central-1"))
iot_client = boto3.client("iot-data",  region_name=os.environ.get("AWS_REGION", "eu-central-1"))

TABLE_NAME        = os.environ["FLIGHT_LOGS_TABLE_NAME"]
SNS_MISSION_TOPIC = os.environ["SNS_MISSION_LOG_TOPIC_ARN"]


def handler(event, context):
    """
    Input:  Normalized telemetry payload + Bedrock verdict (Continue, confidence >= 0.75).
    Output: Confirmation of DynamoDB write, SNS publish, and Shadow sync.
    """
    logger.info("Continue Lambda invoked. Event: %s", json.dumps(event))

    thing_name = event.get("thing_name")
    timestamp  = event.get("timestamp", str(int(time.time())))
    telemetry  = event.get("telemetry", {})
    perception = event.get("perception", {})
    verdict    = event.get("verdict", {})

    if not thing_name:
        raise ValueError("Missing required field: thing_name")

    _log_to_dynamodb(thing_name, timestamp, telemetry, perception, verdict)
    _publish_to_sns(thing_name, timestamp, verdict)
    _sync_device_shadow(thing_name)

    logger.info("Continue Lambda complete for thing: %s", thing_name)
    return {
        "status":     "MISSION_CONTINUED",
        "thing_name": thing_name,
    }


def _log_to_dynamodb(thing_name, timestamp, telemetry, perception, verdict):
    table = dynamodb.Table(TABLE_NAME)
    item = {
        "vtol_id":    thing_name,
        "timestamp":  int(time.time()),
        "verdict":    "Continue",
        "confidence": verdict.get("confidence", 0.0),
        "reasoning":  verdict.get("reasoning", ""),
        "telemetry":  telemetry,
        "perception": perception,
    }
    table.put_item(Item=item)
    logger.info("Mission log written to DynamoDB for %s", thing_name)


def _publish_to_sns(thing_name, timestamp, verdict):
    message = {
        "event":      "MISSION_SAFE",
        "thing_name": thing_name,
        "timestamp":  timestamp,
        "verdict":    verdict,
    }
    sns_client.publish(
        TopicArn=SNS_MISSION_TOPIC,
        Subject=f"Mission Safe: {thing_name}",
        Message=json.dumps(message),
    )
    logger.info("SNS mission log published for %s", thing_name)


def _sync_device_shadow(thing_name):
    shadow_payload = {
        "state": {
            "reported": {
                "mission_status": "ACTIVE",
            }
        }
    }
    iot_client.update_thing_shadow(
        thingName=thing_name,
        payload=json.dumps(shadow_payload).encode("utf-8"),
    )
    logger.info("Device Shadow reported state synced to ACTIVE for %s", thing_name)