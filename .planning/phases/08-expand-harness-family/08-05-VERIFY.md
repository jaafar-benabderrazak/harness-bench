# streaming_react Ollama Compatibility Verification

**Backend:** ollama
**Outcome:** FAIL
**Elapsed:** 4.5s
**Detail:** Bad stop_reason='error', elapsed=4.5s, error='ResponseError: model requires more system memory (23.4 GiB) than is available (6.9 GiB) (status code: 500)'

**Implication for plan 08-06 registration:**
- Register `streaming_react` with `task_type=[]` in `HARNESSES_BY_TASK_TYPE` (excluded from local-model matrix). Document the exclusion in HARNESSES_FROZEN.md when the freeze tag moves in plan 08-07.

**Reference:** Ollama issue #13840 — Generation stops after tool call with Ollama (GLM-4.7-Flash) — https://github.com/ollama/ollama/issues/13840
