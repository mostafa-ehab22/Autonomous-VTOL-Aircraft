# 🌉 Integration Guide: MAVLink to AWS IoT Core

This guide outlines the communication bridge between the **Onboard Flight System** (ArduPilot/ROS2) and the **AWS Cloud Extension**.

---

## 🏗️ The Bridge Architecture

The telemetry pipeline follows a "Protocol Translation" pattern. Since AWS IoT Core requires MQTT over TLS (Port 8883), and ArduPilot speaks MAVLink (UDP/Serial), the Raspberry Pi acts as the translation gateway.

## 1. Onboard Data Ingestion

The **MAVLink Bridge Node** (ROS2) is responsible for:

- **Subscribing:** Listening to local ROS2 topics (e.g., `/mavros/global_position/global`).
- **Filtering:** Only forwarding mission-critical telemetry to the cloud to reduce bandwidth/cost.
- **Heartbeats:** Maintaining a 1Hz "I'm Alive" signal to the AWS Device Shadow.

## 2. Secure Communication (TLS 1.2)

AWS IoT Core requires certificate-based authentication. The following assets must be stored in the onboard `certs/` directory:

- `AmazonRootCA1.pem` (AWS Root Certificate)
- `certificate.pem.crt` (Device-specific certificate)
- `private.pem.key` (Device private key)

> [!IMPORTANT]
> **Clock Sync Required:** If the Raspberry Pi’s system clock is out of sync (common on hardware without RTC), TLS handshakes will fail. Always sync time via `chrony` or `ntp` before initiating the MQTT bridge.

## 3. MQTT Topic Structure

To ensure fleet-scale compatibility, we utilize a hierarchical topic structure:

| Topic                                    | Purpose                                   | Payload Type  |
| :--------------------------------------- | :---------------------------------------- | :------------ |
| `vtol/{drone_id}/telemetry`              | Real-time position, battery, and status   | JSON          |
| `vtol/{drone_id}/mission/request`        | Requests a safety check for a new mission | JSON          |
| `$aws/things/{thing_name}/shadow/update` | Syncs mission state (Abort/Continue)      | JSON (Shadow) |

## 4. The Acknowledgment Loop (Handshake)

To prevent "fire and forget" failures, the system utilizes a **Task Token** pattern via Step Functions:

1. **Cloud:** Updates the Device Shadow with a `desired` state (e.g., `command: "ABORT"` + `task_token: "xyz"`).
2. **VTOL:** Receives the delta update, executes the command, and publishes an ACK to an IoT Rule.
3. **Cloud:** The IoT Rule triggers a Lambda that sends `SendTaskSuccess` back to the Step Function to resume the mission workflow.

## 5. Failsafe: Connection Loss

If the Raspberry Pi loses 4G/5G connectivity:

- **Onboard:** ArduPilot remains in control. The ROS2 node caches critical events.
- **Cloud:** The Device Shadow marks the aircraft as `offline`.
- **Reconnection:** Upon re-establishing a link, the Pi syncs its local state with the Shadow's `reported` state to resume cloud-monitored tracking.

---

<div align="center">
  <sub>Part of the Autonomous VTOL graduation project — Alexandria University</sub>
</div>
