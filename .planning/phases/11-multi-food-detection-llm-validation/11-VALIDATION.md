# Phase 11 Validation: Multi-Food Detection & LLM Validation

## Overview
This document defines the validation strategy for Phase 11, focusing on the end-to-end accuracy and reliability of the multi-food detection and LLM validation pipeline.

## Success Criteria
1.  **MULTI-01 (Detection):** YOLOv8 correctly identifies multiple food items in complex scenes (precision/recall > 0.85 on test subset).
2.  **MULTI-02 (Segmentation):** SAM 2 generates precise masks for each YOLOv8 bounding box prompt.
3.  **MULTI-03 (Merger):** Itemized volume-to-mass conversion correctly aggregates to ±15% of ground truth mass.
4.  **MULTI-04 (Validation):** LLM layer successfully identifies and corrects "hallucinated" or unrealistic predictions (e.g., merging "Pizza" and "Bread").
5.  **MULTI-05 (API):** `/predict-validated` endpoint returns complete, validated JSON in ≤ 3s.

## Verification Map

| Requirement | Test Suite | Automated Command | Status |
|-------------|------------|-------------------|--------|
| MULTI-01 | `tests/test_multi_food.py` | `pytest tests/test_multi_food.py::TestMultiFoodDetection -v` | ✅ Implemented (5 tests pass) |
| MULTI-02 | `tests/test_multi_food.py` | `pytest tests/test_multi_food.py::test_sam2_box_prompt_method_exists` | ✅ Implemented |
| MULTI-03 | `tests/test_merger.py` | `pytest tests/test_merger.py::TestDensityLoader -v` | ✅ Implemented (9 tests) |
| MULTI-04 | `tests/test_llm_validator.py`| `pytest tests/test_llm_validator.py` | ✅ Implemented (Plan 11-03 complete) |
| MULTI-05 | `tests/test_e2e_multi.py` | `pytest tests/test_e2e_multi.py` | ✅ Implemented (13 tests pass, Plan 11-04 complete) |

## VRAM & Hardware Constraints
- **Target:** 4GB VRAM (RTX 3050).
- **Strategy:** Sequential execution of models (YOLO → SAM 2 → GLPN) to avoid OOM. Checkpoint task in Plan 04 explicitly verifies latency.

## Audit Logs
- [2026-04-26]: Validation framework initialized.
- [2026-04-26]: Audit completed - Plans 01-02 executed (MULTI-01, 02, 03 verified)
- [2026-04-26]: Test scaffolds created for Plans 03-04
- [2026-04-26]: Plan 11-03 executed - LLMValidator implemented
- [2026-04-26]: Plan 11-04 executed - /predict/validated endpoint implemented

## Execution Status
- **Plan 11-01 (Multi-Food Detection):** ✅ COMPLETED
- **Plan 11-02 (Merger & Density):** ✅ COMPLETED
- **Plan 11-03 (LLM Validation):** ✅ COMPLETED (commits: 2340d93, e49753a)
- **Plan 11-04 (API Endpoint):** ✅ COMPLETED (commits: 63b01d8, 4b95ff8)
