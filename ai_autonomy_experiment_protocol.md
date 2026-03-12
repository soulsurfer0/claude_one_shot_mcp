# AI Autonomous Build Experiment Protocol

This document defines the experimental procedure for evaluating whether a modern LLM coding agent can autonomously build a complete software system from a single prompt.

The goal is to produce a **repeatable, controlled experiment** that evaluates the claims that modern AI coding agents can independently plan, implement, test, and deliver a working system.

This protocol accompanies:

- `CLAUDE_CODE_MASTER_PROMPT.md`
- `LLM_BUILD_EVAL_RUBRIC.md`

---

# Purpose of the Experiment

The experiment evaluates two independent capabilities:

1. **Engineering Capability**

Can the model correctly design and implement the requested system?

2. **Operational Autonomy**

Can the agent complete the task with minimal human interaction?

These capabilities must be measured separately.

---

# Experiment Target

The AI agent must autonomously build a **Retrieval-Augmented Generation (RAG) backend exposed as an MCP server**.

Required capabilities:

- document ingestion
- deterministic chunking
- embedding generation
- vector storage using pgvector
- semantic retrieval
- MCP tool interface
- automated test suite

The final deliverable must be a **fully functioning repository**.

---

# Experiment Environment

The experiment is executed inside an AI coding agent environment such as:

- Claude Code
- Cursor Agent
- equivalent autonomous development agent

The agent must have access to:

- repository filesystem
- terminal
- package installation
- test execution
- database access

Recommended environment configuration:

- Python 3.12
- PostgreSQL 16
- pgvector extension enabled

---

# Allowed Human Interaction

The experiment is designed to minimize human intervention.

The following human actions are allowed:

1. Provide the initial prompt
2. Review and approve the implementation plan
3. Start the implementation phase

No further intervention should occur unless the experiment is terminated.

---

# Disallowed Human Interaction

The following actions invalidate the autonomy portion of the experiment:

- manually fixing code
- editing files
- resolving runtime errors
- modifying tests
- installing missing dependencies
- guiding debugging steps

If any of the above actions occur, the run must be recorded as **"human-assisted"** rather than autonomous.

---

# Required Agent Permissions

To avoid artificial autonomy failures, the agent environment should grant automatic approval for:

- reading files
- writing files
- modifying repository files
- executing terminal commands
- installing dependencies
- running tests

These permissions must be pre-authorized before the experiment begins.

If the agent repeatedly requests approval for these actions, the environment configuration should be considered a **protocol violation**.

---

# Disallowed Agent Actions

To keep the experiment focused, the agent should not perform the following actions:

- pushing to remote git repositories
- interacting with external CI systems
- modifying system-level OS configuration
- installing global software outside the project environment

All work must remain inside the project workspace.

---

# Experiment Phases

The experiment proceeds through the following phases.

---

## Phase 1 — Planning

The agent receives the master prompt.

The agent must:

- analyze the problem
- produce `IMPLEMENTATION_PLAN.md`

The plan must include:

- project objective
- repository structure
- schema design
- staged implementation plan
- testing strategy
- smoke test strategy
- risk assessment

The experiment pauses until the human reviewer approves the plan.

This phase measures **planning quality**.

---

## Phase 2 — Autonomous Implementation

After plan approval, the agent proceeds without further guidance.

The agent must:

- create the repository structure
- implement all modules
- implement database schema
- implement ingestion pipeline
- implement embeddings
- implement retrieval
- implement MCP server
- implement tests

The agent must iterate autonomously until all tests pass.

This phase measures **implementation capability**.

---

## Phase 3 — Self-Verification

The agent must validate the system through automated checks.

Required checks:

1. dependency installation
2. test suite execution
3. ingestion smoke test
4. embedding generation
5. retrieval validation
6. MCP server startup

The agent must fix any discovered issues without assistance.

This phase measures **debugging capability**.

---

# Smoke Test Procedure

The agent must perform the following smoke tests.

1. Create multiple sample documents.
2. Ingest those documents.
3. Confirm chunk records exist.
4. Confirm embedding records exist.
5. Execute semantic search queries.
6. Confirm relevant results are returned.

The MCP server must also start successfully.

---

# Completion Conditions

The experiment is considered complete only when:

- all tests pass
- smoke tests pass
- MCP server starts successfully
- documentation reflects final system state

---

# Failure Conditions

The experiment is considered a failure if:

- the agent stops before completion
- the agent cannot fix failing tests
- the system cannot run end-to-end

---

# Evaluation Method

After completion, evaluate the run using:

`LLM_BUILD_EVAL_RUBRIC.md`

The rubric measures:

- planning quality
- architecture
- ingestion determinism
- chunking correctness
- embedding pipeline
- retrieval correctness
- MCP server implementation
- test suite quality
- autonomous debugging capability

---

# Recording Results

Each run should record the following:

- agent environment
- model used
- total runtime
- number of approval prompts encountered
- rubric score

Example record:

Environment: Claude Code
Model: Claude reasoning model
Runtime: 42 minutes
Approval prompts: 17
Rubric score: 48 / 60

---

# Purpose of This Protocol

This protocol converts a subjective "AI coding demonstration" into a **controlled engineering experiment**.

It allows different AI agents and models to be compared under consistent conditions.

The result is a more meaningful evaluation of real autonomous software engineering capability.

