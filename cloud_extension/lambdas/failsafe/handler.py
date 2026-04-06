"""
Failsafe Lambda
Responsibility: Triggered by the Step Functions CATCH block on any cloud infrastructure
                failure across the mission pipeline. Forces an RTL command directly
                to the VTOL via Device Shadow and alerts all stakeholders via SNS.
                Aircraft safety is never held hostage to cloud availability.
Invoked by: Step Functions (Cloud Failsafe path, CATCH on any pipeline error)

NOTE: The Step Functions ASL CATCH block must use ResultPath to merge the error
      into the original state input, preserving thing_name at the top level:
      "ResultPath": "$.error"
"""

import json
import logging
import os
import time
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot_client = boto3.client("iot-data",   region_name=os.environ.get("AWS_REGION", "eu-central-1"))
sns_client = boto3.client("sns",        region_name=os.environ.get("AWS_REGION", "eu-central-1"))
dynamodb   = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "eu-central-1"))

TABLE_NAME      = os.environ["FLIGHT_LOGS_TABLE_NAME"]
SNS_ALERT_TOPIC = os.environ["SNS_ALERT_TOPIC_ARN"]


def handler(event, context):
    """
    Input:  Step Functions CATCH payload. Original state input preserved via ResultPath.
    Output: RTL dispatched via Device Shadow, SNS alert fired, failsafe event logged to DynamoDB.

    Expected event structure (after ResultPath merge):
    {
        "thing_name": "<vtol_thing_name>",
        "error": {
            "Error": "<error type, e.g. States.TaskFailed, States.Timeout>",
            "Cause": "<error detail string>"
        }
    }
    """
    logger.info("Failsafe Lambda invoked. Event: %s", json.dumps(event))

    thing_name  = event.get("thing_name", "unknown")
    error_block = event.get("error", {})
    error_type  = error_block.get("Error", "UnknownError")
    error_cause = error_block.get("Cause", "Unknown infrastructure error")

    if thing_name == "unknown":
        logger.critical(
            "thing_name not found in CATCH payload. "
            "Verify Step Functions ASL uses ResultPath to preserve original input. "
            "Attempting RTL with unknown thing_name."
        )

    logger.warning(
        "Cloud failsafe triggered for %s. Error: %s | Cause: %s",
        thing_name,
        error_type,
        error_cause,
    )

    # Safety-critical: must execute first and must raise on failure
    _dispatch_rtl_via_shadow(thing_name)

    # Non-critical: log and continue on failure
    _publish_alert_to_sns(thing_name, error_type, error_cause)
    _log_failsafe_event(thing_name, error_type, error_cause)

    logger.info("Failsafe Lambda complete for thing: %s", thing_name)
    return {
        "status":     "FAILSAFE_EXECUTED",
        "thing_name": thing_name,
        "error_type": error_type,
    }


def _dispatch_rtl_via_shadow(thing_name: str):
    """
    Safety-critical. Raises on failure — RTL must be confirmed dispatched.
    Device Shadow persists the desired state even if VTOL is temporarily offline.
    The VTOL receives RTL_TRIGGERED on reconnection via Shadow delta subscription.
    """
    shadow_payload = {
        "state": {
            "desired": {
                "command": "RTL_TRIGGERED",
            }
        }
    }
    try:
        iot_client.update_thing_shadow(
            thingName=thing_name,
            payload=json.dumps(shadow_payload).encode("utf-8"),
        )
        logger.info("RTL command dispatched via Device Shadow for %s", thing_name)

    except ClientError as e:
        logger.critical(
            "CRITICAL: Failed to dispatch RTL via Shadow for %s: %s. "
            "Aircraft may not receive RTL command.",
            thing_name,
            str(e),
        )
        raise


def _publish_alert_to_sns(thing_name: str, error_type: str, error_cause: str):
    """Non-critical: logs and continues on failure."""
    message = {
        "event":       "CLOUD_FAILSAFE_TRIGGERED",
        "thing_name":  thing_name,
        "timestamp":   int(time.time()),
        "error_type":  error_type,
        "error_cause": error_cause,
        "action":      "RTL command dispatched via Device Shadow.",
        "note":        "Cloud infrastructure failure detected. RTL initiated as safety default.",
    }
    try:
        sns_client.publish(
            TopicArn=SNS_ALERT_TOPIC,
            Subject=f"FAILSAFE TRIGGERED: {thing_name} | Cloud Infrastructure Failure",
            Message=json.dumps(message),
        )
        logger.info("SNS failsafe alert published for %s", thing_name)

    except ClientError as e:
        logger.error(
            "Non-critical: Failed to publish SNS alert for %s: %s. RTL already dispatched.",
            thing_name,
            str(e),
        )


def _log_failsafe_event(thing_name: str, error_type: str, error_cause: str):
    """Non-critical: logs and continues on failure."""
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            "vtol_id":     thing_name,
            "timestamp":   int(time.time()),
            "verdict":     "FAILSAFE",
            "confidence":  0,
            "reasoning":   f"Cloud infrastructure failure. Error: {error_type}. Cause: {error_cause}",
            "error_type":  error_type,
            "error_cause": error_cause,
        })
        logger.info("Failsafe event logged to DynamoDB for %s", thing_name)

    except ClientError as e:
        logger.error(
            "Non-critical: Failed to log failsafe event to DynamoDB for %s: %s. RTL already dispatched.",
            thing_name,
            str(e),
        )