# 🎯 Project Overview
![AWS](https://img.shields.io/badge/⛅_AWS-232F3E)
![RaspberryPi](https://img.shields.io/badge/Raspberry_Pi-A22846?logo=raspberrypi)
![ROS2](https://img.shields.io/badge/ROS2-0A7D4B?logo=ros)
![ArduPilot](https://img.shields.io/badge/✈️_ArduPilot-B8860B)

A full-stack autonomous VTOL *(Vertical Take-Off and Landing)* aircraft system combining **onboard embedded flight control** with a **stateless, event-driven AWS cloud extension** for AI-driven mission decision making. 

Designed to scale from one aircraft to a **fleet of thousands** with **zero architectural changes**. 
The system lives in two separate parts:
  
<div align="center">
  
| | ✈️ Onboard System | 🌥️ Cloud Extension |
|---|:---:|:---:|
| 🔧 **What** | Embedded flight control & perception | Serverless AWS mission intelligence |
| 🖥️ **Runs on** | Raspberry Pi + Pixhawk | AWS (eu-central-1) |
| ⚡ **Handles** | Anything time-critical | Anything cognitive |
| 🛠️ **Key tech** | ROS2, ArduPilot, YOLO11 | Bedrock, Step Functions, IoT Core |

</div>

> [!IMPORTANT]
The two parts are **independent by design**. Enabling **horizontal scaling** with **no code modifications**.
> - Onboard system handles everything **time-critical**.
> - Cloud handles everything **cognitive**. <br>


<div align="center">

# ✈️ Part 1: Autonomous VTOL System 

</div>

<div align="center">
  <img src="docs/onboard_architecture.jpeg" alt="Onboard Architecture" width="99%"/>
</div>

## 🧱 System Architecture

The onboard system is structured into three functional layers plus a dedicated validation layer, each with a clear and isolated responsibility boundary:
### 1️⃣ Perception Layer (AI & Vision)
- **Roboflow** → Real-world annotated dataset for model training
- **YOLO11** → Real-time object detection and classification
- **OpenCV** → Frame capture and preprocessing pipeline

### 2️⃣ High-Level Logic Layer (Decision Making on Raspberry Pi)
- **Raspberry Pi** → Onboard compute for decision making
- **ROS2 Jazzy** → Middleware for inter-process communication
- **Custom Packages & Nodes** → OOP-designed mission logic modules
- **MAVLink Bridge (Serial/UDP)** → Bidirectional communication with Pixhawk

### 3️⃣ Low-Level Control Layer (Flight Dynamics on Pixhawk RTOS)
- **ArduPilot Firmware (Pixhawk)** → Flight controller running on RTOS
- **EKF3** → Extended Kalman Filter for state estimation (position, velocity, attitude)
- **TECS** → Total Energy Control System for speed and altitude management
- **L1 Controller** → Lateral navigation and path following

### 4️⃣ Validation & Safety (Pre-flight & In-flight Guardrails)
- **SITL Simulation (Linux)** → Software-in-the-loop testing before hardware deployment 
- **Pre-Arm Checks** → Validates sensor health and system readiness before flight 
- **Geofence Failsafe** → Enforces geographic boundaries and triggers RTL on breach 

<div align="center">

# 🌥️ Part 2: Cloud Extension Architecture

<div align="center">
  <img src="docs/cloud_architecture.png" alt="Cloud Architecture" width="99%"/>
</div>

</div>

## 🎯 Why a Cloud Extension?

The Cloud Extension was architected to transition the aircraft from a standalone prototype into a resilient, fleet-ready system without touching the onboard flight stack.

By separating **Tactical Flight Logic** from **Strategic Mission Intelligence**, the aircraft's "reflexes" remain local and deterministic, while its "decisions" benefit from LLM-level reasoning, durable state persistence, and fleet-scale orchestration.

> [!NOTE]
> **Onboard (Reflexes):** Time-critical YOLO11 inference, deterministic ROS2, and low-latency flight safety.<br>
> **Cloud (Strategy):** Mission-level AI reasoning, global state persistence, and cross-platform fleet orchestration.

<div align="center">

| Responsibility | Before (Pi Only) | After (Cloud Extension) |
|---|:---:|:---:|
| 🧠 Strategic mission reasoning | Static rule-based logic | **AWS Bedrock (AI)** |
| 📋 State & mission logging | Local files / SQLite | **DynamoDB** |
| 🔔 Pilot notifications | Ground Control Station only | **SNS (Mobile/Email)** |
| 🔄 Mission state management | In-memory / local | **Device Shadow (with offline sync)** |
| 📨 Message reliability | None | **SQS + Dead Letter Queue** |

</div>

## 🔍 Architectural Impact

This isn't just a compute offload: every responsibility moved to the cloud directly eliminates a real in-flight failure mode that could compromise the mission, corrupt critical data, or worse, endanger the aircraft itself:

<div align="center">

| Limitation (Pi Only) | Cloud Upgrade | Architectural Impact |
|---|:---:|---|
| **No Strategic Reasoning:** Safety classification relied on static rules | 🧠 **Amazon Bedrock** | Dynamic AI layer for adaptive, edge-case safety classification |
| **Local SD Logging:** Flight logs corrupt or lost on crash | 🗄️ **Amazon DynamoDB** | Logs stream to a highly available database → data survives physical destruction |
| **Dropped Telemetry:** Network drops cause lost commands with no retry | 📨 **SQS + Dead Letter Queue** | Failed telemetry retried automatically → zero commands silently dropped |
| **Local State Only:** Mid-air reboot causes the drone to forget its mission | 🪞 **AWS IoT Device Shadow** | Cloud maintains a virtual copy → reconnections instantly restore mission state |
| **Silent Failures:** Safety alerts visible only on local GCS | 🔔 **SNS (Mobile/Email)** | Instant push notifications to all stakeholders on any safety breach |

</div>

## 💰 Cost Analysis

This entire cloud architecture is designed with a **"Pay-as-you-go" serverless model**. By utilizing event-driven triggers, no infrastructure runs 24/7 and no idle containers. When the fleet is grounded, 
the cost is **$0.00**. 

### 📉 Estimated Cost per Flight

Total cost for a single mission execution is the sum of its serverless components:
```
Total Cost = C_IoT + C_Lambda + C_Bedrock + C_StepFunctions + C_SNS + C_DynamoDB
```

<div align="center">

| Service | Estimated Usage (1 Mission) | Estimated Cost (USD) |
|---|:---:|:---:|
| 📡 AWS IoT Core | 100 MQTT Messages + 2 Shadow Updates | ~$0.00012 |
| 🧠 Amazon Bedrock | 300 Input + 100 Output Tokens (Nova Lite) | ~$0.000042 |
| ⚙️ Step Functions | 12 State Transitions | ~$0.00030 |
| ⚡ AWS Lambda | 4 Invocations (128MB, avg. 200ms) | ~$0.000016 |
| 📨 SQS + SNS | < 1,000 requests | < $0.00001 |
| **💰 Total** | **1 Complete Mission Cycle** | **~$0.00049** |

</div>

> [!TIP]
> Can run **2,000+ missions for $1.00 USD**, making this one of the most cost-efficient autonomous fleet architectures possible.

### 🛠️ Cost Optimization Strategies

To maintain this efficiency, the following optimizations are implemented:

1. 🧠 **Model Selection:** <br> **Amazon Nova Lite** over Claude 3.5 Sonnet **reduces inference cost by ~90%** while maintaining sufficient reasoning for safety classification.
2. 📡 **Basic Ingest:** <br> Telemetry that doesn't require the Message Broker is routed via **Basic Ingest** to **eliminate 100% of the IoT Core messaging fee.**
3. 🗑️ **Log Retention:** <br> CloudWatch logs configured with a **7-day expiration** to prevent storage costs from accumulating over time.

## 🚀 Scaling to a Fleet (1,000+ VTOLs)

Unlike monolithic designs, this architecture scales horizontally with **zero code changes**, every service was chosen with fleet-scale in mind from day one:

- 🔀 **Stateless Concurrency ```(Step Functions & Lambda)```:** <br> Every VTOL triggers an isolated execution. 10 or 10,000 drones run simultaneously with zero compute contention.
- 🛡️ **Spike Absorption ```(Amazon SQS)```:** <br> Acts as a buffer for network reconnections, absorbing sudden telemetry dumps and feeding the pipeline at a controlled rate.
- 🧠 **Elastic AI ```(Amazon Bedrock)```:** <br> Dynamically scales to process concurrent LLM safety classifications in the cloud, eliminating the latency of edge-device queuing.
- 📡 **Mass Device Sync ```(AWS IoT Core)```:** <br> Built for millions of connections, maintaining a dedicated, offline-resilient Device Shadow for every aircraft.
- 🌍 **Global Replication ```(AWS CDK)```:** <br> Full Infrastructure as Code (IaC) allows one-click deployment of the entire stack to any AWS Region.

> [!IMPORTANT]
> **Nothing safety-critical moves to the cloud.** All flight controls, perception & failsafes remain fully onboard.

## 🧱 AWS Cloud Architecture

### 📡 Ingestion & Queuing
- **AWS IoT Core** → Secure MQTT ingestion; Device Shadow for offline state sync
- **Amazon SQS** → Telemetry buffer with Dead Letter Queue (DLQ) after 3 retries
- **EventBridge Pipes** → Serverless SQS-to-Step Functions router (No intermediary Lambda)

### ⚙️ Orchestration & Intelligence
- **AWS Step Functions** → Deterministic mission workflow with branching logic and async callbacks
- **Amazon Bedrock** → LLM-powered strategic decision layer (Safe/Unsafe classification)
- **AWS Lambda** → Payload normalization, command dispatch, and task token validation
- **Amazon DynamoDB** → NoSQL persistence for immutable mission logs and event history

### 🔔 Alerting & Feedback
- **Amazon SNS** → Dual-topic push alerting: Mission Log (safe) vs. Alert (unsafe)
- **AWS IoT Device Shadow** → Offline-resilient bidirectional sync; aborts execute on reconnection
- **Amazon S3** → Long-term telemetry archive with Glacier lifecycle policies

### 👀 Observability & Security
- **Amazon CloudWatch** → Centralized metrics, monitoring, and automated alarms
- **AWS CloudTrail** → Immutable API audit logs for security and compliance
- **AWS X-Ray** → Distributed tracing across the serverless pipeline
- **AWS IAM** → Strict least-privilege access control across all services

## 🧠 AI Selection: Bedrock vs. SageMaker

While SageMaker *(including Serverless Inference)* was evaluated, Amazon Bedrock was selected as the **Strategic Safety Classifier** at the cloud decision layer for the following reasons:

### 🏗️ Foundation vs. Custom

<div align="center">
  
| | ⛅ Bedrock | 🧪 SageMaker Serverless |
|---|---|---|
| **Deployment** | Managed API with zero pipeline setup | Requires custom model weights & container management |
| **Cold-Start** | Bypassed via managed endpoint | Inherent latency risk for time-critical safety audits |
| **Model Access** | Immediate access to Nova / Claude FMs | Custom training pipeline required |

</div>

### 💰 Cost & Simplicity

- **$0.00 idle cost**: pure **"Pay-as-you-fly"** billing model
- No containerized inference logic to maintain
- No model artifact versioning overhead
- Team focus stays on **mission integration**, not infrastructure

### 🛡️ Bedrock System Prompt (Safety Classifier)

Injected directly at the Bedrock layer, it hardcodes the aircraft's physical flight limits and guarantees JSON-compliant output for Step Functions:

```ini
You are the Strategic Safety Classifier for an autonomous VTOL aircraft. 
Your ONLY job is to evaluate incoming flight telemetry and perception data,
and output a strict JSON response determining if the mission should 'Continue' or 'Abort'.

CRITICAL SAFETY RULES:
1. If 'yolo_anomaly_detected' is true AND 'altitude_m' < 50, you MUST Abort.
  (Rationale: Low-altitude anomalies present immediate collision risk).
2. If 'battery_pct' < 20.0, you MUST Abort regardless of other factors.
  (Rationale: Insufficient reserve for safe RTL).
3. If 'wind_resistance_ms' > 15.0, you MUST Abort.
  (Rationale: Exceeds stable flight envelope).
4. If the data is ambiguous or conflicting, default to Abort to ensure physical safety.

OUTPUT CONSTRAINTS:
- You must respond ONLY with valid, unformatted JSON.
- Do not include markdown tags (```json), conversational text, or greetings.
- Use the exact schema: {"verdict": "Continue" | "Abort", "confidence": float, "reasoning": "string"}
```

### 📋 I/O Contract (JSON Schema)

**Input - Structured Telemetry:**
```json
{
  "timestamp": "2026-03-19T15:34:55Z",
  "telemetry": {
    "altitude_m": 120.5,
    "battery_pct": 42.1,
    "wind_resistance_ms": 14.2,
    "motor_temp_c": 65.0
  },
  "perception": {
    "yolo_anomaly_detected": true,
    "anomaly_confidence": 0.88
  }
}
```

**Output - Mission Verdict:**
```json
{
  "verdict": "Abort",
  "confidence": 0.95,
  "reasoning": "Compound risk: Anomaly detected + High wind (14.2m/s) at 42% battery."
}
```

> [!WARNING]
> ### Safety-First Failsafe Logic
> *Aircraft safety is **never held hostage to network availability:***
> - **Cloud Timeout:** No verdict is received within `3 seconds`, ROS 2 controller triggers local **RTL** independently.
> - **Low Confidence:** Verdict confidence `< 0.75` is automatically treated as `Abort` by ROS 2 controller.


## 🔄 Mission Workflow Detail

**✅ Safe Path:**
```
Safety Check → SAFE
→ Amazon SNS (Log Mission Topic)
→ Mission Notifications (Mobile/Email)
→ Continue Mission (Sync State & Notify Pilot)
→ END
```

**❌ Unsafe Path:**
```
Safety Check → UNSAFE
→ Dispatch Abort Command (Update Shadow Device → VTOL receives abort command)
→ Amazon SNS (Log Alert Topic)
→ Wait State (30 seconds, waitForTaskToken)
→ ACK received via IoT Rule → Verify Acknowledgment (Validate Task Token)
→ END
```

⚠️ **Cloud Failsafe Path (Infrastructure Error):**
```
Amazon Bedrock (AI Decision Making) → CATCH: API Error / Timeout
→ Execute Failsafe (Trigger RTL Command)
→ Update Shadow State (Forces RTL command directly to VTOL via IoT Core)
→ Amazon SNS (Log Alert Topic — "AI Unreachable, RTL Initiated")
→ END
```
## 🌊 End-to-End System Flow: The Life of a Telemetry Packet

The complete lifecycle of a single mission decision, from raw sensor data to physical motor response:

### 👀 Sense (Edge)
- **YOLO11** (on Raspberry Pi) detects an anomaly mid-flight.
- **Pixhawk (ArduPilot)** simultaneously registers degraded battery voltage and elevated wind resistance via **EKF3**.

### 📡 Package & Transmit (The Bridge)
- The **ROS2 MAVLink Bridge** normalizes both perception and flight telemetry into a structured JSON payload.
- Published via **MQTT over TLS (Port 8883)** to **AWS IoT Core**: the single handoff point between edge and cloud.

### 📥 Buffer & Trigger (Cloud Entry)
- IoT Core routes the payload into the **Amazon SQS Mission Queue**, absorbing any network reconnect spikes.
- **EventBridge Pipes** polls the queue and triggers the **AWS Step Functions** state machine *(no intermediary Lambda required)*.

### 🧠 Reason & Decide (Cloud Brain)
- Step Functions invokes **Amazon Bedrock (Nova Lite)** with the telemetry JSON for safety classification.
- Bedrock returns: `{"verdict": "Abort", "confidence": 0.92}`.
- Since `confidence ≥ 0.75`, the verdict is trusted. Step Functions routes down the `UNSAFE` path.

### 🚨 Alert & Command (Cloud Exit)
- **SNS** fires an immediate alert to the pilot's mobile/email.
- A **Lambda** updates the **IoT Device Shadow** `desired` state to `RTL_TRIGGERED`, embedding a `.waitForTaskToken`. Step Functions pauses, waiting for physical confirmation from the aircraft.

### ⚡ Act (Edge Reflex)
- The ROS2 node, subscribed to its **Device Shadow delta**, instantly receives the state change.
- Translates `RTL_TRIGGERED` into a MAVLink `SET_MODE` command and sends it via serial to the **Pixhawk**.
- The Pixhawk takes physical control and begins Return-to-Launch.

### ✅ Acknowledge (The Loop Closes)
- The ROS2 node publishes an MQTT ACK back to **IoT Core**.
- An **IoT Rule** calls `SendTaskSuccess`, returning the task token to Step Functions.
- The execution resumes, logs the confirmed abort to **DynamoDB**, and reaches `END`.
  
> [!NOTE]
> Wait State uses Step Functions' `.waitForTaskToken` callback pattern. <br>
> Task token is embedded in the command sent to the VTOL. <br>
> VTOL acknowledges via ```MQTT → IoT Rule → SendTaskSuccess``` to resume execution.

## 🌉 Integration: How Onboard Meets Cloud

The bridge between the two systems is a single well-defined interface:

```
ArduPilot (Pixhawk)
    │
    │ MAVLink (Serial/UDP)
    ▼
ROS2 Node (MAVLink Bridge)
    │
    │ MQTT over TLS (Port 8883)
    ▼
AWS IoT Core
    │
    └─► Mission Queue → Step Functions → Bedrock Decision
    └─► Device Shadow ← Command Lambda (mission updates back to VTOL)
```

> [!TIP]
> ROS2 MAVLink bridge node handles **bidirectional flow**: publishing telemetry upstream to IoT Core, and receiving cloud-originated commands *(abort, reroute)* back down to the VTOL via Device Shadow delta updates. 
>
> 📖 See the full [Integration Guide](docs/integration_guide.md) here.

## 📂 Project Structure
```
AUTONOMOUS-VTOL-AIRCRAFT/
├── ⛅ cloud_infrastructure/       # AWS CDK Serverless Backend
│   ├── cloud_infrastructure/
│   │   ├── database_stack.py      # DynamoDB Flight Logs
│   │   └── messaging_stack.py     # SQS Mission Queue + DLQ
│   ├── app.py                     # CDK Entry Point
│   ├── cdk.json                   
│   └── requirements.txt           
├── 📖 docs/
│   ├── AWS_VTOL.drawio            # Editable Architecture Source                          
│   ├── cloud_architecture.png     
│   └── onboard_architecture.jpeg
├── .gitignore
├── LICENSE
└── README.md
```

## 🚀 Deployment

### Prerequisites
```bash
Python 3.11+
AWS CLI configured (aws configure)
AWS CDK installed (npm install -g aws-cdk)
```

### Deploy Cloud Stack
```bash
# Navigate to the cloud infrastructure directory
cd cloud_infrastructure

# Install dependencies
pip install -r requirements.txt

# Bootstrap AWS environment (first-time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all
```

> [!CAUTION]
> Change `RemovalPolicy.DESTROY` to `RemovalPolicy.RETAIN` in `database_stack.py` before any real flight deployment to prevent accidental deletion of flight logs.

---

# 🗺️ Roadmap 

### Onboard System
- [x] YOLO11 model training on Roboflow dataset
- [x] ROS2 workspace setup with MAVLink bridge node
- [ ] SITL simulation validation
- [ ] Geofence and failsafe parameter tuning
- [ ] Hardware integration on Pixhawk + Raspberry Pi

### Cloud Extension
- [x] AWS CDK infrastructure stack
- [x] Lambda functions (normalization, command, continuation)
- [ ] Step Functions state machine definition
- [ ] Bedrock prompt engineering for safety classification
- [ ] IoT Core rules + Device Shadow integration
- [ ] End-to-end integration test (SITL → Cloud → ACK loop)

## 📖 Documentation

<div align="center">

| Document | Description |
| :--- | :--- |
| 🏗️ [Source Files & Full Assets](docs/) | **Technical Source:** `.drawio` diagram and detailed guides |
| 🌥️ [Cloud Extension Diagram](docs/cloud_architecture.png) | AWS serverless backend architecture |
| ✈️ [Onboard System Diagram](docs/onboard_architecture.jpeg) | Embedded flight control & logic pipeline |
| 🌉 [Integration Guide](docs/integration_guide.md) | MAVLink telemetry to AWS IoT Core bridge |

</div>

</div>

## 🤝 Contributing

This is an active project. Issues and suggestions are welcome - feel free to open an issue for discussion.

## ⚖️ License

Distributed under the Apache License 2.0. See [LICENSE](LICENSE) for more information.

---

<div align="center">
  <sub>Built at Faculty of Engineering, Alexandria University, Egypt: Autonomous VTOL × AWS Serverless</sub>
</div>
