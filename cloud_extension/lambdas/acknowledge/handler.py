"""
Acknowledge Lambda
Responsibility: Receives the VTOL acknowledgment via an IoT Rule after the aircraft
                executes the abort command. Validates the task token, calls
                SendTaskSuccess to resume the paused Step Functions execution,
                and logs the confirmed abort to DynamoDB.
Invoked by: IoT Core Rule (triggered by VTOL MQTT ACK on abort confirmation topic)
"""

import json
import logging
import os
import time
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn_client = boto3.client("stepfunctions", region_name=os.environ.get("AWS_REGION", "eu-central-1"))
dynamodb   = boto3.resource("dynamodb",    region_name=os.environ.get("AWS_REGION", "eu-central-1"))

TABLE_NAME = os.environ["FLIGHT_LOGS_TABLE_NAME"]


def handler(event, context):
    """
    Input:  IoT Rule forwards the VTOL ACK payload containing the task token.
    Output: SendTaskSuccess call to Step Functions, resuming the paused execution,
            and a confirmed abort log entry written to DynamoDB.

    Expected MQTT ACK payload from VTOL:
    {
        "task_token": "<token embedded by Abort Lambda>",
        "thing_name": "<vtol_thing_name>",
        "status":     "ABORT_EXECUTED"
    }
    """
    logger.info("Acknowledge Lambda invoked. Event: %s", json.dumps(event))

    task_token = event.get("task_token")
    thing_name = event.get("thing_name", "unknown")
    status     = event.get("status", "")

    if not task_token:
        logger.error("ACK received without task_token from %s. Cannot resume Step Functions.", thing_name)
        raise ValueError("Missing required field: task_token")

    if status != "ABORT_EXECUTED":
        logger.warning(
            "Unexpected ACK status from %s: %s. Proceeding with SendTaskSuccess.",
            thing_name,
            status,
        )

    output = json.dumps({
        "ack_received": True,
        "thing_name":   thing_name,
        "status":       status,
    })

    try:
        sfn_client.send_task_success(
            taskToken=task_token,
            output=output,
        )
        logger.info("SendTaskSuccess called for thing: %s", thing_name)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "TaskTimedOut":
            logger.error("Task token expired for %s. Step Functions execution already timed out.", thing_name)
        elif error_code == "InvalidToken":
            logger.error("Invalid task token received from %s.", thing_name)
        else:
            logger.error("Unexpected ClientError for %s: %s", thing_name, str(e))
        raise

    _log_confirmed_abort(thing_name, status)

    logger.info("Acknowledge Lambda complete for thing: %s", thing_name)
    return {
        "status":     "ACK_VALIDATED",
        "thing_name": thing_name,
    }


def _log_confirmed_abort(thing_name: str, status: str):
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        "vtol_id":   thing_name,
        "timestamp": int(time.time()),
        "verdict":   "Abort",
        "reasoning": "Abort command confirmed executed by VTOL.",
        "status":    status,
    })
    logger.info("Confirmed abort logged to DynamoDB for %s", thing_name)