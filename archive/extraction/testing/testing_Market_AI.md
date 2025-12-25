---
id: 20251201_testing_market_ai
type: extraction
subject: testing
source_repo: Market_AI
description: "pytest patterns with mocker, unit and integration tests for LLM and tools"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [testing, pytest, mock, unit, integration, tdd]
---

# SUBJECT: testing/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `tests/unit/`, `tests/integration/`

---

## 1. EXTRACTED CODE

### 1.1 Test Directory Structure

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_llm_client.py
│   ├── test_tools.py
│   └── test_utils.py
└── integration/
    ├── __init__.py
    └── test_graph.py
```

### 1.2 LLM Client Unit Tests

```python
import pytest
import tenacity
from llm_client import LLMClient
from langchain_core.pydantic_v1 import BaseModel, Field
from unittest.mock import MagicMock

# Define a dummy Pydantic model for testing structured output
class DummySchema(BaseModel):
    name: str = Field(description="A name")

def test_llm_client_invoke_success(mocker):
    """Test a successful invocation with a structured output schema."""
    mock_invoke = mocker.patch(
        'langchain_core.runnables.base.RunnableSequence.invoke',
        return_value=DummySchema(name="test")
    )
    mocker.patch("llm_client.ChatOllama")

    client = LLMClient(model_slot="intent_router")
    response = client.invoke("system", "user", output_schema=DummySchema)

    assert isinstance(response, DummySchema)
    assert response.name == "test"
    mock_invoke.assert_called_once()

def test_llm_client_invoke_failure_raises_exception(mocker):
    """Test that a failure in the LLM chain raises the final exception."""
    mock_invoke = mocker.patch(
        'langchain_core.runnables.base.RunnableSequence.invoke',
        side_effect=Exception("LLM Died")
    )
    mocker.patch("llm_client.ChatOllama")

    client = LLMClient(model_slot="intent_router")
    with pytest.raises(tenacity.RetryError):
        client.invoke("system", "user", output_schema=DummySchema)

    # The retry is configured for 2 attempts
    assert mock_invoke.call_count == 2

def test_llm_client_invalid_slot():
    """Test that creating a client with an invalid slot raises an error."""
    with pytest.raises(ValueError, match="Invalid model_slot"):
        LLMClient(model_slot="non_existent_slot")
```

### 1.3 Tools Unit Tests

```python
import pytest
import tenacity
from tools import web_search_tool

def test_web_search_tool_success(mocker):
    """Test a successful API call."""
    mocker.patch('tools.SERPAPI_KEY', 'dummy_key')
    mock_search = mocker.patch('tools.serpapi.search')
    mock_search.return_value = {"organic_results": [{"title": "Test Result"}]}

    result = web_search_tool(query="test query")

    assert result["ok"] is True
    assert len(result["data"]) == 1
    mock_search.assert_called_once()

def test_web_search_tool_api_error(mocker):
    """Test that the tool handles API errors gracefully after retries."""
    mocker.patch('tools.SERPAPI_KEY', 'dummy_key')
    mock_search = mocker.patch('tools.serpapi.search', side_effect=Exception("API Error"))

    result = web_search_tool(query="test query")

    assert result["ok"] is False
    assert "An error occurred" in result["data"]
    # Check that the error message contains RetryError
    assert "RetryError" in result["data"]
    # The retry is configured for 3 attempts
    assert mock_search.call_count == 3

def test_web_search_tool_no_api_key(mocker):
    """Test the tool's behavior when the API key is not configured."""
    mocker.patch('tools.SERPAPI_KEY', None)
    mock_search = mocker.patch('tools.serpapi.search')

    result = web_search_tool(query="test query")

    assert result["ok"] is False
    assert result["data"] == "SERPAPI_KEY is not configured."
    mock_search.assert_not_called()
```

### 1.4 Integration Tests (LangGraph)

```python
import pytest
from marketing_graph import workflow, MarketingGraphState, AdCopyDraft, ApprovalDecisionV1

@pytest.fixture
def sample_state():
    """Provides a sample MarketingGraphState for testing."""
    return MarketingGraphState(
        lead_objective="test objective",
        drafts=[AdCopyDraft(draft_id="draft_1", brief_id="brief_1", copy_text="test copy", version=1)],
        approvals={}
    )

def test_hitl_gate_approval_path(sample_state):
    """Tests that the graph correctly routes to 'publish' when approved."""
    sample_state.approvals["draft_1"] = ApprovalDecisionV1(approved=True).model_dump()

    from marketing_graph import should_continue
    next_node = should_continue(sample_state)
    assert next_node == "publish"

def test_hitl_gate_rejection_path(sample_state):
    """Tests that the graph routes back to 'copywriter' when rejected."""
    sample_state.approvals["draft_1"] = ApprovalDecisionV1(
        approved=False,
        requested_changes="Needs more pizzazz."
    ).model_dump()

    from marketing_graph import should_continue
    next_node = should_continue(sample_state)
    assert next_node == "copywriter"

def test_hitl_gate_no_decision(sample_state):
    """Tests default routing (rejection) when no approval is found."""
    from marketing_graph import should_continue
    # No approval decision made for "draft_1"
    next_node = should_continue(sample_state)
    assert next_node == "copywriter"
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **pytest-mock integration** | HIGH | mocker fixture for patching |
| **Pydantic test schemas** | HIGH | DummySchema for structured output tests |
| **Retry count verification** | HIGH | Tests verify exact retry attempts |
| **Tool contract testing** | HIGH | Tests ok/data/cost fields |
| **Conditional edge testing** | HIGH | Tests LangGraph routing logic |
| **Fixture pattern** | HIGH | sample_state for reusable test data |
| **Error path testing** | HIGH | Tests failure scenarios |
| **Missing config testing** | HIGH | Tests behavior without API key |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| `langchain_core.pydantic_v1` | Deprecated | Use `pydantic` v2 |
| No async tests | Sync only | Add async test support |
| No database tests | Missing | Add SQLite test fixtures |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. pytest-mock patterns
2. Pydantic test schema pattern
3. Tool contract testing
4. Conditional edge testing for workflows
5. Fixture patterns

**Integration Points:**
- `autobiz/tests/unit/` - Unit tests
- `autobiz/tests/integration/` - Integration tests
- `autobiz/tests/fixtures/` - Test fixtures

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| Testing | Full pytest examples | None extracted | **USE Market_AI** - unique |

---

## 6. BEST VERSION RECOMMENDATION

**Market_AI is the ONLY repo with extracted test patterns.**

**Recommended test structure for AutoBiz:**

```
autobiz/tests/
├── conftest.py          # Shared fixtures
├── unit/
│   ├── test_llm_client.py
│   ├── test_tools.py
│   ├── test_database.py
│   └── test_extractors.py
└── integration/
    ├── test_pipelines.py
    └── test_workflows.py
```

---

## 7. TEST PATTERNS SUMMARY

| Pattern | Description | Example |
|---------|-------------|---------|
| **Mock patching** | `mocker.patch('module.function')` | Mock API calls |
| **Side effects** | `side_effect=Exception("Error")` | Test error handling |
| **Return values** | `return_value={"key": "value"}` | Mock successful responses |
| **Call count** | `mock.call_count == N` | Verify retry behavior |
| **Assert called** | `mock.assert_called_once()` | Verify function was called |
| **Fixtures** | `@pytest.fixture` | Reusable test data |
| **Raises** | `pytest.raises(ValueError)` | Test exception handling |
| **Match** | `match="pattern"` | Verify exception message |

---

## 8. DEPENDENCIES

```
pytest
pytest-mock
```
