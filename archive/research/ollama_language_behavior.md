# Ollama Multilingual Behavior with JSON Output

**Date:** 2025-12-26
**Context:** Bulgarian real estate extraction with qwen2.5:1.5b
**Problem:** LLM returns Bulgarian enum values despite prompts requesting English values

---

## Summary of Findings

### 1. API Endpoint Comparison: `/api/generate` vs `/api/chat`

| Feature | `/api/generate` | `/api/chat` |
|---------|-----------------|-------------|
| System message | `system` parameter (separate) | First message with `role: "system"` |
| Conversation history | `context` parameter (opaque) | Full `messages` array |
| JSON schema support | Yes (via `format`) | Yes (via `format`) |
| Response structure | `{"response": "..."}` | `{"message": {"content": "..."}}` |

**Recommendation:** Switch to `/api/chat` for better control over system-level instructions. The explicit `role: "system"` message provides clearer instruction hierarchy.

**Source:** [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md), [Issue #2774](https://github.com/ollama/ollama/issues/2774)

### 2. `format: json` Behavior

The `format` parameter controls **structure**, not **content language**:

- **What it does:** Uses GBNF grammars via llama.cpp to ensure valid JSON syntax
- **What it doesn't do:** Control the language of values within JSON fields
- **How it works:** During token sampling, invalid tokens (per grammar) are masked with probability 0

**Key insight:** `format: "json"` only ensures syntactically valid JSON. To constrain enum values, you must pass a full JSON schema with explicit `enum` properties.

**Source:** [Ollama Structured Outputs Blog](https://ollama.com/blog/structured-outputs), [How Ollama's Structured Outputs Work](https://blog.danielclayton.co.uk/posts/ollama-structured-outputs/)

### 3. JSON Schema Enum Enforcement

The recommended approach is to pass `model_json_schema()` from Pydantic instead of just `"json"`:

```python
# Current implementation (weak)
format="json"

# Recommended implementation (strong)
format=MappedFields.model_json_schema()
```

When using a full JSON schema with enums, Ollama generates a GBNF grammar that **constrains tokens to only valid enum values**. This is enforced at the grammar level, not just the prompt level.

**Example:** If your schema has:
```json
{"construction": {"type": "string", "enum": ["brick", "panel", "epk"]}}
```

The grammar will only allow tokens that produce "brick", "panel", or "epk" - Bulgarian equivalents cannot be generated.

**Source:** [Ollama Python Structured Outputs](https://deepwiki.com/ollama/ollama-python/4.4-structured-outputs), [Instructor Ollama Guide](https://python.useinstructor.com/integrations/ollama/)

### 4. System Message for Language Control

Even with schema enforcement, adding explicit language instructions improves reliability:

```python
messages=[
    {
        "role": "system",
        "content": "You are a real estate data extractor. ALWAYS respond in English. "
                   "Use ONLY the exact enum values specified in the schema. "
                   "Never translate values to Bulgarian."
    },
    {"role": "user", "content": prompt}
]
```

**Source:** [Supercharging Ollama System Prompts](https://johnwlittle.com/supercharging-ollama-mastering-system-prompts-for-better-results/)

### 5. Model Comparison: qwen2.5 1.5b vs 3b

| Aspect | qwen2.5:1.5b | qwen2.5:3b |
|--------|--------------|------------|
| VRAM | ~1.2 GB | ~2.4 GB |
| Performance | Good for edge | Comparable to qwen2-7b |
| Instruction following | Adequate | Significantly better |
| Multilingual | 29+ languages | 29+ languages |
| Structured output | Good | Better |
| JSON extraction | May deviate from instructions | More reliable |

**Recommendation:** qwen2.5:3b is the better choice if resources permit. The improved instruction-following capability directly addresses the Bulgarian value leakage problem. The 3b model "outperforms Phi3.5-mini-Instruct and MiniCPM3-4B" despite having fewer parameters.

**Source:** [Qwen2.5 LLM Blog](https://qwenlm.github.io/blog/qwen2.5-llm/), [Qwen2.5-3B-Instruct Model Card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)

---

## Recommended API Changes

### Priority 1: Use JSON Schema Instead of `format: "json"`

**Current code:**
```python
response = requests.post(
    f"{self.base_url}/api/generate",
    json={
        "model": model,
        "prompt": prompt,
        "format": "json",  # Only ensures valid JSON syntax
        ...
    }
)
```

**Recommended code:**
```python
from llm.schemas import MappedFields, ExtractedDescription

response = requests.post(
    f"{self.base_url}/api/chat",
    json={
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a Bulgarian real estate data extractor. "
                           "Extract information and return JSON. "
                           "CRITICAL: Use ONLY English enum values as specified. "
                           "Never use Bulgarian words for enum fields."
            },
            {"role": "user", "content": prompt}
        ],
        "format": schema_class.model_json_schema(),  # Full schema with enums
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": max_tokens}
    }
)
```

### Priority 2: Include Schema in Prompt (Belt and Suspenders)

Best practice per Ollama documentation: include the JSON schema in the prompt text as well:

```python
prompt = f"""Extract real estate data from this Bulgarian text.

TEXT:
{content}

REQUIRED OUTPUT FORMAT (use EXACT field names and enum values):
{json.dumps(schema_class.model_json_schema(), indent=2)}
"""
```

### Priority 3: Consider 3b Model for Critical Extractions

```yaml
# config/ollama.yaml
tasks:
  field_mapping:
    primary_model: qwen2.5:3b      # Better instruction following
    fallback_model: qwen2.5:1.5b   # Cost fallback
```

---

## Prompt Strategy Recommendations

### For Bulgarian Input with English Enum Output

1. **System message:** Set language expectations at the system level
2. **Schema enforcement:** Pass full JSON schema with enum constraints
3. **In-prompt schema:** Include schema in prompt text for grounding
4. **Temperature:** Keep at 0.0 for deterministic enum selection
5. **Post-processing:** Keep `_translate_values()` as safety net (defense in depth)

### Optimized Prompt Template

```python
SYSTEM_MESSAGE = """You are a Bulgarian real estate data extraction system.

CRITICAL RULES:
1. Extract information from Bulgarian text
2. Return ONLY valid JSON matching the provided schema
3. Use ONLY English enum values (never Bulgarian translations)
4. Return null for missing information
5. Estimate confidence based on extraction certainty"""

FIELD_MAPPING_PROMPT = """Extract structured data from this real estate listing.

BULGARIAN TEXT:
{content}

Return JSON with these fields (use EXACT enum values):
- construction: "brick" | "panel" | "epk" | null
- heating: "district" | "gas" | "electric" | "air_conditioner" | null
- price_eur, price_bgn, area_sqm, floor, total_floors: numbers or null
- neighborhood, address: Bulgarian strings or null
- confidence: 0.0-1.0"""
```

---

## Live Test Results (2025-12-26)

Tests run on `qwen2.5:1.5b` with standardized Bulgarian input:

| Variation | Score | Notes |
|-----------|-------|-------|
| **V4: Explicit English** | **5/5** | Best - "RESPOND IN ENGLISH ONLY" |
| V2: English prompt + BG hints | 4/5 | furnishing wrong |
| V1: Bulgarian prompt (current) | 2/5 | rooms, construction, furnishing wrong |
| V3a: Chat API + BG system | ~2/5 | Similar to V1 |
| V3b: Chat API + EN system | ~3/5 | Better but not perfect |

**Key insight**: The prompt language matters more than the API endpoint. Using an English prompt with explicit "RESPOND IN ENGLISH ONLY" constraint outperforms all Bulgarian prompt variations.

---

## Implementation Checklist

1. [x] Research API options and `format: json` behavior
2. [x] Create and run test script with variations
3. [ ] Switch prompts to English with explicit constraint
4. [ ] Pass `model_json_schema()` instead of `"json"` to format parameter
5. [ ] Add system message with language instructions
6. [ ] Keep `_translate_values()` fallback as safety net
7. [ ] Test with qwen2.5:3b model (optional improvement)

---

## References

- [Ollama Structured Outputs Documentation](https://docs.ollama.com/capabilities/structured-outputs)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen2.5 Model Comparison](https://qwenlm.github.io/blog/qwen2.5-llm/)
- [LLM Enum Constraints with Instructor](https://ohmeow.com/posts/2024-07-06-llms-and-enums.html)
- [JSON Schema Enum Specification](https://json-schema.org/understanding-json-schema/reference/enum)
