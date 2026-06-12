# 🧠 Ephemeral Learning & Data Optimization Strategy

To prevent the backend from being overwhelmed by AI learning data, OmniCore-AI implements the following strategy:

## 1. Ephemeral Learning Store (Redis-Based)
Instead of logging every trial-and-error request to a persistent database, we use a **Layered Memory Approach**:

- **Level 1: Session Cache (Redis)**
  - Stores the raw history of the current interaction.
  - **TTL**: 30 minutes.
  - **Purpose**: Immediate context for the agent.
  
- **Level 2: Pattern Aggregator (Asynchronous)**
  - A background worker analyzes failed requests in Redis.
  - Instead of saving "Request #101 failed", it saves: "Agent X has failed `stock.add` due to `TypeError` 5 times in 10 minutes".
  - **Storage**: Persisted in Core DB as a `LearningProfile` entry.
  - **Purpose**: Exponential learning. The system now knows the agent's weak points.

- **Level 3: Global Error Cache (Shared)**
  - Common mistakes made by *all* agents are cached globally.
  - **Purpose**: If Agent B makes the same mistake Agent A did, the system returns the pre-calculated correction immediately.

## 2. Resource Consumption Optimization
- **Learning Mode (Sandbox)**:
  - Bypasses the `DynamicDbManager` (no real DB connections).
  - Uses a `MockResponse` system that simulates DB behavior.
  - Result: Zero load on external databases and minimal CPU usage.
  
- **Production Mode**:
  - Uses `DynamicDbManager` with optimized connection pooling.
  - High-priority execution with strict rate limiting.

## 3. Token Cost Reduction
- **Semantic Compression**: The manifest is delivered in a compact JSON format.
- **Response Pruning**: In Production Mode, pedagogical guides are removed to save output tokens.
