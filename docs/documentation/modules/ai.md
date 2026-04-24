# AI Layer Module

**Location:** `backend/ai/`

## Purpose

Format pre-analyzed JSON (traces, profiles, clusters) into readable prose using LLM. Primary provider: Groq (Llama 3.3 70B, free). Fallback: Ollama (local gemma3:4b, phi4-mini, qwen2.5:3b). Optional: Claude, OpenAI. No speculative analysis — only prose formatting of structured input.

## Public API

### `providers/groq.py`

**`GroqProvider`**
Groq API client via httpx.

**`async generate(user_prompt: str, system_prompt: str, json_context: dict) -> str`**
Call Groq API with user + system prompts. Returns formatted prose or raises `AIError`.

**Config:**
- Model: `llama-3.3-70b-versatile`
- Base URL: `https://api.groq.com/openai/v1`
- Temperature: 0.7
- Max tokens: 1024
- Timeout: 30s

**Error handling:** `AIError` on missing GROQ_API_KEY, HTTP error, or malformed response.

### `providers/ollama.py`

**`OllamaProvider`**
Local Ollama instance (localhost:11434).

**`async generate(user_prompt: str, system_prompt: str, json_context: dict) -> str`**
Call Ollama /api/generate endpoint. Falls back to user prompt alone if system prompt causes timeout.

**Config:**
- Models: gemma3:4b (default), phi4-mini:3.8b, qwen2.5:3b (configurable via settings)
- Base URL: http://localhost:11434 (configurable)
- Timeout: 60s
- Streaming: not used (waits for full response)

### `providers/claude.py`, `providers/openai.py`

**Stubs or minimal implementations.** Can be extended for Claude Opus / OpenAI GPT-4.

### `prompts/trace_report.py`

**`trace_report_system_prompt() -> str`**
```
"You are a blockchain forensics analyst. Format the provided trace data 
into a clear incident narrative. Quote specific values from the JSON context. 
Do not speculate beyond provided data. Flag any unconfirmed (mixer) exits."
```

**`trace_report_user_prompt(trace_json: dict) -> str`**
Template with JSON context embedded:
```
"Analyze this hack trace:\n\n{trace_json}\n\n
Format as: Incident summary. Hop-by-hop fund flow. Terminal destinations. 
Risk assessment."
```

### `prompts/profile_summary.py`

**System prompt:** "Summarize wallet risk profile based on provided signals."

**User prompt template:** Embed risk score, signals, counterparties, behavior tags, transactions.

**Output format:** 3-paragraph summary: overview · risk factors · conclusion.

### `prompts/cluster_explanation.py`

**System prompt:** "Explain why these wallets are clustered together."

**User prompt:** Embed cluster members, linking heuristics, confidence scores, evidence.

**Output:** Natural language explanation of clustering evidence (e.g., "All three wallets funded by the same source within 2 hours, with matching gas price patterns").

## Algorithm & Data Flow

```
Report generation (from API route):

async generate_report(job_id: str, report_type: str):
├─ fetch trace/profile/cluster data from cache/Neo4j
├─ build json_context dict with structured data
├─ select prompt template (trace_report, profile_summary, cluster_explanation)
├─ system_prompt = template.system_prompt()
├─ user_prompt = template.user_prompt(json_context)
├─ try:
│  ├─ ai_provider = GroqProvider() or OllamaProvider()
│  └─ prose = await ai_provider.generate(user_prompt, system_prompt, json_context)
├─ except AIError:
│  ├─ if guardrail_check(prose) fails: regenerate once
│  ├─ if still fails: fall back to templated_report(json_context)
├─ verify_numbers(prose, json_context) — regex check that all quoted values exist in context
└─ store prose in cache/db; return

GroqProvider.generate():
├─ build request: system + user prompts, model="llama-3.3-70b-versatile"
├─ POST to https://api.groq.com/openai/v1/chat/completions
├─ extract choices[0].message.content
└─ return prose or raise AIError

Fallback strategy:
├─ Primary: Groq (free, fast, quality)
├─ Secondary: Ollama (local, offline, smaller model)
├─ Tertiary: templated report (static prose + variable substitution)
```

## Dependencies

**Imports:**
- `httpx` — async HTTP (Groq, Ollama calls)
- `backend.config.settings` — API keys + endpoints
- `.prompts.*` — prompt templates

**Imported by:**
- `backend.api.routes.report` — POST `/report/{job_id}`
- Report sharing UI — render generated prose

## Extension Points

1. **Add new prompt template:** Create `prompts/{report_type}.py` with `system_prompt()` and `user_prompt()` functions.
2. **Add AI provider:** Implement `async generate()` in `providers/{provider}.py`; register in dispatcher.
3. **Guardrails:** Enhance `verify_numbers()` regex to check more patterns (addresses, block numbers, dates).
4. **Temperature/token tuning:** Parameterize in provider init or settings.

## Testing Guidance

**Unit tests:**
- Mock httpx responses; verify Groq/Ollama parsing
- Test prompt templates with synthetic data
- Test guardrail regex (verify numbers in output match context)
- Test fallback chain (Groq → Ollama → template)

**Integration:**
- Run with real Groq API key (or test key)
- Generate trace report for known Ronin hack
- Verify prose mentions specific wallets, values, and terminals
- Verify no speculative text ("probably", "might", "seems")
- Generate profile summary for high-risk wallet
- Verify score, signals, and tags mentioned

## Known Gaps & TODOs

- `groq.py` — May be incomplete (stub or partial implementation visible)
- `ollama.py` — Likely stubbed or minimal
- `claude.py`, `openai.py` — Stubs; not integrated
- No guardrail regex for addresses (0x format validation)
- No check for hallucinated data (LLM inventing addresses not in context)
- No streaming support (long reports fetched as single response)
- No retry logic for Groq timeouts
- Prompt templates may need refinement post-evaluation

## See Also

- `tracer.md`, `profiler.md`, `clustering.md` — produce JSON context for report generation
- `parser.md` — decoded calls may be included in trace report prose
