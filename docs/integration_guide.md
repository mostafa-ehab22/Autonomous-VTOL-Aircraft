# 🌉 Integration Guide: MAVLink to AWS IoT Core

This guide outlines the communication bridge between the **Onboard Flight System** (ArduPilot/ROS2) and the **AWS Cloud Extension**.

## 🏗️ The Bridge Architecture

Telemetry pipeline follows a "Protocol Translation" pattern. Since AWS IoT Core requires MQTT over TLS (Port 8883), and ArduPilot speaks MAVLink (UDP/Serial), the Raspberry Pi acts as the translation gateway.

## 1. Onboard Data Ingestion

The **MAVLink Bridge Node** (ROS2) is responsible for:

- **Subscribing:** Listening to local ROS2 topics (e.g., `/mavros/global_position/global`).
- **Filtering:** Only forwarding mission-critical telemetry to the cloud to reduce bandwidth/cost.
- **Publishing:** Streaming structured telemetry to AWS IoT Core at regular intervals.

## 2. Secure Communication (TLS)

AWS IoT Core requires certificate-based authentication. The following assets must be stored in the onboard `certs/` directory:

- `AmazonRootCA1.pem` (AWS Root Certificate)
- `certificate.pem.crt` (Device-specific certificate)
- `private.pem.key` (Device private key)

> [!IMPORTANT]
> **Clock Sync Required:** If the Raspberry Pi's system clock is out of sync (common on hardware without RTC), TLS handshakes will fail. Always sync time via `chrony` or `ntp` before initiating the MQTT bridge.

## 3. MQTT Topic Structure

To ensure fleet-scale compatibility and enforce Basic Ingest cost optimization, all topics use `{thing_name}` as the unique VTOL identifier. QoS levels are selected per topic based on delivery guarantees required:

| Topic | Purpose | Routing | QoS |
| :---- | :------- | :------ | :-- |
| `$aws/rules/MissionTelemetryRule/{thing_name}` | High-frequency telemetry uplink | Basic Ingest ($0 messaging fee) | 0 |
| `vtol/{thing_name}/mission/request` | Safety check request to Step Functions | Standard MQTT | 1 |
| `$aws/things/{thing_name}/shadow/update` | Cloud command sync (Abort/RTL) | Shadow Service | 1 |
| `$aws/things/{thing_name}/shadow/update/delta` | Receive cloud-originated commands | Shadow Delta (downstream) | 1 |

> [!NOTE]
> **QoS (Quality of Service)** controls MQTT message delivery guarantees:
> - **QoS 0 (At most once):** Sends once with no confirmation. Acceptable for high-frequency telemetry where losing one reading is not critical.
> - **QoS 1 (At least once):** Retries until acknowledged. Required for mission-critical commands where delivery must be guaranteed.
>
> *AWS IoT Core supports QoS 0 and QoS 1 only.*

## 4. The Acknowledgment Loop (Handshake)

To prevent "fire and forget" failures, the system utilizes a **Task Token** pattern via Step Functions:

1. **Cloud:** The **Abort Lambda** updates the Device Shadow `desired` state with `command: "ABORT"` and an embedded `task_token`.
2. **VTOL:** The ROS2 node, subscribed to the **Shadow delta topic**, receives the state change instantly and executes the abort maneuver.
3. **VTOL:** Publishes an MQTT ACK containing the task token back to IoT Core.
4. **Cloud:** An IoT Rule triggers the **Acknowledge Lambda**, which calls `SendTaskSuccess` to resume the paused Step Functions execution.

## 5. Failsafe: Connection Loss

If the Raspberry Pi loses 4G/5G connectivity:

- **Onboard:** ArduPilot remains in control. The ROS2 node caches critical events.
- **Cloud:** An IoT Rule subscribes to `$aws/events/presence/disconnected/{clientId}` to detect connection loss and updates the Device Shadow `reported` state to `offline`.
- **Reconnection:** Upon re-establishing a link, the Pi syncs its local state with the Shadow's `reported` state to resume cloud-monitored tracking.

---

<div align="center">
  <sub>Part of the Autonomous VTOL Aircraft graduation project - Alexandria University</sub>
</div>
