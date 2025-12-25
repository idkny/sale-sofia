---
id: 20251201_workflow_market_ai
type: extraction
subject: workflow
source_repo: Market_AI
description: "LangGraph StateGraph implementation with 8 agents, conditional edges, checkpointing"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [workflow, langgraph, state-machine, agents, hitl, orchestration]
---

# SUBJECT: workflow/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `marketing_graph.py` (612 lines)

---

## 1. EXTRACTED CODE

### 1.1 LangGraph State Schema (Pydantic)

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Sub-schemas for structured state
class ResearchDoc(BaseModel):
    source: str = Field(description="URL or reference of the research document")
    content: str = Field(description="Content snippet or summary of the document")

class KeywordSet(BaseModel):
    theme: str = Field(description="The overarching theme of the keyword set")
    keywords: List[str] = Field(description="A list of related keywords")

class CampaignBrief(BaseModel):
    brief_id: str = Field(description="A unique identifier for this brief")
    objective: str = Field(description="The primary goal of the campaign brief")
    target_audience: str = Field(description="Description of the target audience")
    key_messaging: str = Field(description="Key messages to convey")

class AdCopyDraft(BaseModel):
    draft_id: str = Field(description="A unique identifier for this draft")
    brief_id: str = Field(description="ID of the brief this draft is based on")
    copy_text: str = Field(description="The actual ad copy")
    version: int = Field(default=1, description="Version number of the draft")

# Main state schema
class MarketingGraphState(BaseModel):
    lead_objective: Optional[str] = Field(description="The initial objective from the lead/user")
    research_docs: List[ResearchDoc] = Field(default_factory=list, description="Collected research documents")
    keyword_sets: List[KeywordSet] = Field(default_factory=list, description="Generated sets of keywords")
    briefs: List[CampaignBrief] = Field(default_factory=list, description="Generated campaign briefs")
    drafts: List[AdCopyDraft] = Field(default_factory=list, description="Generated ad copy drafts")
    approvals: Dict[str, Any] = Field(default_factory=dict, description="Approval decisions and feedback")
    metrics_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Snapshot of performance metrics")
    session_id: Optional[str] = Field(default=None, description="A unique ID for the session for tracking")
```

### 1.2 Agent Input/Output Models

```python
class RouterInV1(BaseModel):
    query: str = Field(description="The user's initial query or objective")

class RouterOutV1(BaseModel):
    intent: str = Field(description="The classified intent of the query")
    key_entities: Dict[str, Any] = Field(description="Key entities extracted from the query")

class ResearchRequestV1(BaseModel):
    objective: str = Field(description="The research objective")
    topics: List[str] = Field(description="Specific topics to research")

class ResearchBundleV1(BaseModel):
    summary: str = Field(description="A summary of the research findings")
    documents: List[ResearchDoc] = Field(description="A list of research documents")

class QAReportV1(BaseModel):
    score: float = Field(description="Quality score from 0.0 to 1.0")
    feedback: str = Field(description="Detailed feedback and suggestions for improvement")

class ApprovalDecisionV1(BaseModel):
    approved: bool = Field(description="Decision of the human-in-the-loop")
    requested_changes: Optional[str] = Field(default=None, description="Specific changes requested if not approved")

class MetricsSnapshotV1(BaseModel):
    kpis: Dict[str, Any] = Field(description="Key Performance Indicators for the campaign")
```

### 1.3 StateGraph Definition

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Create the StateGraph with Pydantic schema
workflow = StateGraph(MarketingGraphState)

# Add agent nodes
workflow.add_node("intent_router", intent_router)
workflow.add_node("researcher", researcher)
workflow.add_node("strategist", strategist)
workflow.add_node("copywriter", copywriter)
workflow.add_node("qa_critic", qa_critic)
workflow.add_node("hitl_gate", hitl_gate)
workflow.add_node("publish", publish)
workflow.add_node("analytics_snapshot", analytics_snapshot)

# Define edges (happy path)
workflow.set_entry_point("intent_router")
workflow.add_edge("intent_router", "researcher")
workflow.add_edge("researcher", "strategist")
workflow.add_edge("strategist", "copywriter")
workflow.add_edge("copywriter", "qa_critic")
workflow.add_edge("qa_critic", "hitl_gate")

# Conditional edge for HITL approval
workflow.add_conditional_edges(
    "hitl_gate",
    should_continue,
    {
        "publish": "publish",
        "copywriter": "copywriter",  # Loop back for revisions
        END: END,
    },
)

# Final steps
workflow.add_edge("publish", "analytics_snapshot")
workflow.add_edge("analytics_snapshot", END)
```

### 1.4 Conditional Router Function

```python
def should_continue(state: MarketingGraphState) -> str:
    """
    Conditional logic to decide whether to continue to publishing or loop back for revisions.
    """
    logging.info("--- DECISION: CONTINUE OR REVISE? ---")
    if not state.drafts:
        return END

    last_draft_id = state.drafts[-1].draft_id
    last_approval = state.approvals.get(last_draft_id, {})

    if last_approval.get("approved"):
        logging.info("Decision: Approved. Proceeding to Publish.")
        return "publish"
    else:
        logging.info("Decision: Rejected. Routing back to Copywriter for revisions.")
        return "copywriter"
```

### 1.5 Agent Node Examples

```python
def intent_router(state: MarketingGraphState) -> dict:
    """Uses an LLM to classify the user's intent and extract key entities."""
    logging.info("--- 1. INTENT ROUTER ---")
    objective = state.lead_objective

    llm_client = LLMClient(model_slot="intent_router")
    system_prompt = (
        "You are an expert at understanding marketing objectives. "
        "Classify the intent and extract key entities."
    )

    try:
        response = llm_client.invoke(
            system_prompt=system_prompt,
            user_prompt=objective,
            output_schema=RouterOutV1
        )
        logging.info(f"Intent classified: {response.intent}")
    except Exception as e:
        logging.error(f"Error in intent_router: {e}")

    return {}  # State updates

def hitl_gate(state: MarketingGraphState) -> dict:
    """Human-in-the-Loop gate - simulates human approval step."""
    logging.info("--- 6. HUMAN-IN-THE-LOOP GATE ---")
    if not state.drafts:
        return {}

    last_draft = state.drafts[-1]
    decision = ApprovalDecisionV1(approved=True, requested_changes=None)

    approvals = state.approvals
    approvals[last_draft.draft_id] = decision.model_dump()
    return {"approvals": approvals}
```

### 1.6 Graph Compilation with Checkpointing

```python
if __name__ == "__main__":
    # Set up the checkpointer using a 'with' statement
    with SqliteSaver.from_conn_string(":memory:") as memory:
        # Compile the StateGraph with checkpointing
        graph = workflow.compile(checkpointer=memory)

        session_id = f"session_{uuid.uuid4()}"
        initial_state = {
            "lead_objective": "Create a marketing campaign for a new local coffee shop.",
            "session_id": session_id
        }

        config = {"configurable": {"thread_id": session_id}}

        # Stream execution
        for state_chunk in graph.stream(initial_state, config=config, recursion_limit=10):
            logging.info(state_chunk)
```

### 1.7 System Preamble / Guardrails Pattern

```python
SYSTEM_PREAMBLE = """\
# Brand Voice & Tone
You are the AirCentral Marketing Graph. Your voice must be:
- Austin-local: Reference local landmarks or culture where appropriate.
- Plain-English: Clear, simple, and easy for anyone to understand.
- Helpful & Respectful: Provide genuine value, never talk down to the user.
- Professional & Transparent: Be honest and straightforward.

# Prohibited Tactics & Claims
- **No Scare Tactics**: Do not use fear to motivate customers.
- **No Bait-and-Switch**: Be honest about what is offered.
- **No Unverifiable Superlatives**: Avoid phrases like "best in the world."
- **No Medical Claims**: Do not claim services prevent medical conditions.
- **No Guaranteed Energy Savings**: Do not promise specific savings.

# Mandatory Disclosures & Compliance
- All advertising materials must include the Texas ACR License number: {{TEXAS_ACR_LICENSE}}.
- All offers must include terms and conditions.
"""

# Usage in agents
final_system_preamble = SYSTEM_PREAMBLE.replace(
    "{{TEXAS_ACR_LICENSE}}", app_config.TEXAS_ACR_LICENSE or "NOT_CONFIGURED"
)
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **StateGraph pattern** | HIGH | Full LangGraph implementation with Pydantic |
| **8 agent nodes** | HIGH | Intent router, researcher, strategist, copywriter, qa_critic, hitl_gate, publish, analytics |
| **Conditional edges** | HIGH | should_continue router for approval/rejection |
| **SqliteSaver checkpointing** | HIGH | State persistence across interruptions |
| **Pydantic state schema** | HIGH | Type-safe state management |
| **Agent I/O models** | HIGH | Structured input/output for each agent |
| **System preamble pattern** | MEDIUM | Guardrails and compliance injection |
| **stream() execution** | MEDIUM | Observable step-by-step execution |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| `langchain_core.pydantic_v1` | Deprecated | Use `pydantic` directly |
| `:memory:` checkpointer | Not persistent | Use file-based SQLite |
| Hardcoded model names | Not configurable | Move to config file |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. StateGraph pattern for pipeline orchestration
2. Pydantic state schema for type safety
3. Conditional edges for approval workflows
4. Agent I/O models for structured communication
5. System preamble for guardrails/compliance

**Integration Points:**
- `autobiz/pipelines/` - Use StateGraph for complex pipelines
- `autobiz/agents/` - Agent node definitions
- `autobiz/core/` - State schemas, I/O models

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| Workflow orchestration | LangGraph StateGraph | None | **USE Market_AI** - unique |
| RAG in workflow | Chroma + OllamaEmbeddings | Ollama-Rag (hybrid) | **MERGE** - Ollama-Rag hybrid + Market_AI LangGraph |
| Agent structure | Function-based nodes | Auto-Biz CLI commands | **MERGE** - LangGraph for pipelines, CLI for manual |

---

## 6. BEST VERSION RECOMMENDATION

**Market_AI is the ONLY repo with LangGraph** - This is a critical unique pattern.

**Recommended approach:**
1. Port the StateGraph pattern directly
2. Use Pydantic models for state
3. Implement conditional edges for approval workflows
4. Replace RAG component with Ollama-Rag's hybrid retrieval
5. Add file-based SqliteSaver instead of :memory:

---

## 7. DEPENDENCIES

```
langgraph
langgraph-checkpoint-sqlite
pydantic
langchain
langchain-community
chromadb
```
