# Codebase Concerns

**Analysis Date:** 2025-05-15

## Tech Debt

**Local LLM Setup:**
- Issue: `llama-cpp-python` installation and model download are separate from the main `setup.py` flow.
- Files: `backend/scripts/setup_local_llm.py`, `setup.py`
- Impact: Developers might miss local LLM setup, causing fallback to cloud API or failure in offline scenarios.
- Fix approach: Integrate a prompt for local LLM setup into the main `setup.py`.

**Hardcoded Versions:**
- Issue: `transformers==4.38.1` is pinned in `requirements.txt` but other critical libraries like `ultralytics` are not pinned.
- Files: `backend/requirements.txt`
- Impact: Potential for breaking changes on fresh install if dependencies update.
- Fix approach: Pin all critical dependencies with exact versions.

## Known Bugs

**None detected during mapping.**

## Security Considerations

**Environment Variables:**
- Risk: `setup.py` copies `.env.example` to `.env` but does not prompt for secrets.
- Files: `setup.py`, `backend/.env.example`
- Current mitigation: Warning in terminal output.
- Recommendations: Add interactive prompts for required keys (e.g., `GEMINI_API_KEY`) during setup.

## Performance Bottlenecks

**Sequential Model Execution:**
- Problem: Running multiple AI models (SAM, YOLO, GLPN) sequentially in a single process.
- Files: `backend/nutrisnap/pipeline.py` (assumed)
- Cause: VRAM constraints (4GB).
- Improvement path: Explore quantization or model distillation for lower VRAM footprints.

**Model Download Size:**
- Problem: ~1.05 GB download required for first-time setup.
- Files: `backend/scripts/download_models.py`
- Cause: High-fidelity models.
- Improvement path: Provide "lite" model options for faster setup.

## Fragile Areas

**Windows DLL Patching:**
- Files: `backend/scripts/setup_local_llm.py`
- Why fragile: Manually copying DLLs between `torch` and `llama_cpp` is brittle and may break with updates to either library.
- Safe modification: Investigate better wheel packaging or environment configuration.

## Scaling Limits

**VRAM (4GB):**
- Current capacity: Fits the current pipeline with cache clearing.
- Limit: Adding more models or using larger variants will cause OOM.
- Scaling path: Multi-GPU support or moving inference to dedicated worker nodes.

## Dependencies at Risk

**llama-cpp-python:**
- Risk: Installation depends on specific hardware backends and often requires manual compilation or specific wheel indices.
- Impact: High failure rate for new developer setups.
- Migration plan: Standardize on a containerized environment (Docker) for all AI dependencies.

## Missing Critical Features

**Unified Setup Entry:**
- Problem: `setup_local_llm.py` is not invoked by `setup.py`.
- Blocks: Seamless "one-click" developer experience.

## Test Coverage Gaps

**AI Inference Pipelines:**
- What's not tested: End-to-end inference accuracy and performance under load.
- Files: `backend/nutrisnap/`
- Risk: Regressions in model accuracy or performance bottlenecks go unnoticed.
- Priority: Medium

---

*Concerns audit: 2025-05-15*
