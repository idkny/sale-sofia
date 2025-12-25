---
id: 20251201_ai_llm_market_ai
type: extraction
subject: ai_llm
source_repo: Market_AI
description: "LLMClient with model slots, Pydantic output schema, tenacity retry, primary/fallback"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [ai, llm, ollama, langchain, pydantic, retry, model-slots]
---

# SUBJECT: ai_llm/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `llm_client.py` (91 lines)

---

## 1. EXTRACTED CODE

### 1.1 Model Configuration with Slots

```python
OLLAMA_MODEL_CONFIG = {
    "intent_router": {
        "primary": "mistral:7b-instruct-q4_K_M",
        "fallback": "llama2:7b-chat-q4_K_M",
        "backend": "ollama",
        "hyperparameters": {"temperature": 0.7, "top_p": 1.0}
    },
    "researcher": {
        "primary": "mistral:7b-instruct-q4_K_M",
        "fallback": "llama2:7b-chat-q4_K_M",
        "context": "<8k+>",
        "hyperparameters": {"temperature": 0.5, "top_p": 1.0}
    },
    "strategist": {
        "primary": "mistral:7b-instruct-q4_K_M",
        "fallback": "llama2:7b-chat-q4_K_M",
        "hyperparameters": {"temperature": 0.4, "top_p": 0.9}
    },
    "copywriter": {
        "primary": "mistral:7b-instruct-q4_K_M",
        "fallback": "llama2:7b-chat-q4_K_M",
        "critic_pair": "<qa-critic-small>",
        "hyperparameters": {"temperature": 0.8, "top_p": 1.0}
    },
    "qa_critic": {
        "primary": "mistral:7b-instruct-q4_K_M",
        "fallback": "llama2:7b-chat-q4_K_M",
        "hyperparameters": {"temperature": 0.6, "top_p": 1.0}
    },
    "analytics_snapshot": {
        "primary": "mistral:7b-instruct-q4_K_M",
        "fallback": "llama2:7b-chat-q4_K_M",
        "hyperparameters": {"temperature": 0.7, "top_p": 1.0}
    },
    "embeddings": {
        "primary": "nomic-embed-text",
        "fallback": "nomic-embed-text",
    }
}
```

### 1.2 LLMClient Class

```python
import time
import logging
import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, ValidationError
from langchain_community.chat_models.ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential

from app_config import OLLAMA_HOST

class LLMClient:
    """A centralized client to interact with local LLMs via Ollama."""

    def __init__(self, model_slot: str):
        if model_slot not in OLLAMA_MODEL_CONFIG:
            raise ValueError(f"Invalid model_slot: {model_slot}. Not found in config.")
        self.model_config = OLLAMA_MODEL_CONFIG[model_slot]
        self.primary_model_name = self.model_config["primary"]
        self.fallback_model_name = self.model_config["fallback"]
        self.backend = self.model_config.get("backend", "ollama")

    def invoke(self, system_prompt: str, user_prompt: str, output_schema: BaseModel = None):
        """
        Generates a response from an LLM, handling retries and fallbacks.
        If output_schema is provided, it instructs the LLM to format its response as JSON
        and attempts to parse it into the given Pydantic model.
        """
        logging.info(f"LLMClient invoking for slot: {self.primary_model_name}")
        start_time = time.time()

        # Add JSON format instructions if schema provided
        if output_schema:
            schema_json = output_schema.schema_json(indent=2)
            escaped_schema_json = schema_json.replace("{", "{{").replace("}", "}}")
            json_format_instructions = f"\n\nYour response MUST be a valid JSON object that adheres to the following Pydantic schema:\n```json\n{escaped_schema_json}\n```"
            system_prompt += json_format_instructions

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt),
        ])

        # Create primary and fallback LLMs
        primary_llm = ChatOllama(
            model=self.primary_model_name,
            base_url=OLLAMA_HOST,
            format="json" if output_schema else "text"
        )
        fallback_llm = ChatOllama(
            model=self.fallback_model_name,
            base_url=OLLAMA_HOST,
            format="json" if output_schema else "text"
        )

        # Chain with fallback
        chain = prompt_template | primary_llm.with_fallbacks(fallbacks=[fallback_llm])

        @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=6))
        def invoke_with_retry():
            return chain.invoke({})

        try:
            response_content = invoke_with_retry().content

            if output_schema:
                # Parse JSON from response
                logging.debug(f"Raw LLM output for parsing:\n{response_content}")
                match = re.search(r'```json\n({.*})\n```', response_content, re.DOTALL)
                if match:
                    json_string = match.group(1)
                else:
                    json_string = response_content

                try:
                    parsed_response = output_schema.parse_raw(json_string)
                    response = parsed_response
                except (json.JSONDecodeError, ValidationError) as e:
                    logging.error(f"Failed to parse or validate JSON output: {e}")
                    raise ValueError(f"LLM output did not conform to the required JSON schema.") from e
            else:
                response = response_content

            duration_ms = int((time.time() - start_time) * 1000)
            logging.info(f"LLM invocation succeeded. Duration: {duration_ms}ms.")
            return response
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logging.error(f"LLM invocation failed. Duration: {duration_ms}ms.", exc_info=True)
            raise e
```

### 1.3 GPU Cleanup Function

```python
import torch

def gpu_cleanup():
    """
    Placeholder for GPU memory cleanup using torch.
    Called between heavy LLM calls to free up VRAM.
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logging.info("GPU cache cleared.")
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **Model slot pattern** | HIGH | Task-specific model configuration |
| **Primary/fallback** | HIGH | Resilient model selection |
| **Pydantic output schema** | HIGH | Structured LLM responses |
| **JSON parsing with regex** | MEDIUM | Handles ```json``` blocks |
| **Tenacity retry** | HIGH | Exponential backoff (2 attempts) |
| **LangChain fallbacks** | HIGH | `.with_fallbacks()` pattern |
| **Duration logging** | MEDIUM | Performance tracking |
| **GPU cleanup** | MEDIUM | VRAM management |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| `langchain_core.pydantic_v1` | Deprecated | Use `pydantic` v2 |
| `ChatOllama` from `langchain_community` | May change | Use `langchain-ollama` |
| Hardcoded hyperparameters | Not configurable | Move to external config |
| `schema_json()` | Pydantic v1 method | Use `model_json_schema()` |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. Model slot configuration pattern
2. Primary/fallback model chain
3. Pydantic output schema parsing
4. GPU cleanup function

**Integration Points:**
- `autobiz/tools/llm/llm_client.py` - Core LLM client
- `autobiz/core/config.py` - Model configurations
- `autobiz/agents/` - Agent-specific model slots

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| LLM client | Model slots + Pydantic output | MarketIntel (JSON mode) | **MERGE** - slots + JSON mode |
| Fallback | LangChain `.with_fallbacks()` | Auto-Biz (model factory) | **MERGE** - both patterns |
| Retry | Tenacity (2 attempts) | MarketIntel (exp backoff + jitter) | **USE MarketIntel** - more robust |
| GPU cleanup | `torch.cuda.empty_cache()` | Ollama-Rag (same) | **SAME** |

---

## 6. BEST VERSION RECOMMENDATION

**MERGE approach:**
1. **Model slots** from Market_AI (task-specific configs)
2. **JSON mode** from MarketIntel (native Ollama support)
3. **Retry with jitter** from MarketIntel (more robust)
4. **Pydantic output parsing** from Market_AI (structured responses)
5. **Model factory** from Auto-Biz (for dynamic switching)

---

## 7. DEPENDENCIES

```
langchain
langchain-community
torch
tenacity
pydantic
python-dotenv
```
