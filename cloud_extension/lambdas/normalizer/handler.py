"""
Normalizer Lambda
Responsibility: Validates and normalizes raw telemetry from the SQS payload
                into a clean, structured format for downstream Bedrock inference.
Invoked by: Step Functions (first state in the mission workflow)
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REQUIRED_TELEMETRY_FIELDS = {"altitude_m", "battery_pct", "wind_resistance_ms", "motor_temp_c"}
REQUIRED_PERCEPTION_FIELDS = {"yolo_anomaly_detected", "anomaly_confidence"}


def handler(event, context):
    """
    Input:  Raw SQS message body forwarded by EventBridge Pipes to Step Functions.
    Output: Normalized telemetry payload ready for Bedrock classification.
    """
    logger.info("Normalizer invoked. Raw event: %s", json.dumps(event))

    try:
        # EventBridge Pipes forwards the SQS message body as a string
        body = event.get("body") or event
        if isinstance(body, str):
            body = json.loads(body)

        telemetry  = body.get("telemetry", {})
        perception = body.get("perception", {})
        timestamp  = body.get("timestamp", "")
        thing_name = body.get("thing_name", "")

        _validate_fields(telemetry, REQUIRED_TELEMETRY_FIELDS, "telemetry")
        _validate_fields(perception, REQUIRED_PERCEPTION_FIELDS, "perception")

        if not thing_name:
            raise ValueError("Missing required field: thing_name")

        normalized = {
            "thing_name": thing_name,
            "timestamp":  timestamp,
            "telemetry": {
                "altitude_m":         float(telemetry["altitude_m"]),
                "battery_pct":        float(telemetry["battery_pct"]),
                "wind_resistance_ms": float(telemetry["wind_resistance_ms"]),
                "motor_temp_c":       float(telemetry["motor_temp_c"]),
            },
            "perception": {
                "yolo_anomaly_detected": bool(perception["yolo_anomaly_detected"]),
                "anomaly_confidence":    float(perception["anomaly_confidence"]),
            },
        }

        logger.info("Normalization successful for thing: %s", thing_name)
        return normalized

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error("Normalization failed: %s", str(e))
        raise RuntimeError(f"Normalization failed: {str(e)}") from e


def _validate_fields(data: dict, required: set, section: str):
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing fields in {section}: {missing}")