---
phase: 11-multi-food-detection-llm-validation
plan: 03
subsystem: verification
tags: [llm, validation, gemini, hallucination, safety-net]

# Dependency graph
requires:
  - phase: 11-multi-food-detection-llm-validation
    provides: MultiFoodDetector, FoodSegmenterSAM2, MultiFoodMerger
provides:
  - LLMValidator class for meal realism checking
  - Rule-based redundancy detection (REDUNDANCY_GROUPS)
  - JSON recovery from LLM markdown output
  - validate_meal_reality() convenience function
affects: [pipeline, api, nutrition output]

# Tech tracking
added: [llm_validator.py]
patterns: [llm-validation, json-recovery, redundancy-check]

key-files:
  created: [src/nutrisnap/verification/llm_validator.py]
  modified: [tests/test_llm_validator.py, tests/conftest.py]

key-decisions:
  - Use Gemini 2.0 Flash as primary with OpenRouter fallback
  - Rule-based redundancy pre-check before LLM call
  - Include reasoning field in all LLM responses
  - ValidationResult dataclass for structured output

patterns-established:
  - Volume/Mass plausibility checking (e.g., 5kg lettuce flagged)
  - Redundant label detection (Bread+Sandwich → merge)
  - LLM correction for unrealistic calories
  - JSON recovery handles markdown wrapper

requirements-completed: [MULTI-04]

# Metrics
duration: 10min
completed: 2026-04-26