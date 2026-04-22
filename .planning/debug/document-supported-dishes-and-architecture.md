---
status: resolved
trigger: "Investigate issue: document-supported-dishes-and-architecture"
created: 2024-05-25T00:00:00Z
updated: 2024-05-25T00:00:00Z
---

## Current Focus

hypothesis: README.md and misc/strategy_final_2026-04-16.md are missing the 20 supported dishes list and the architecture diagram.
test: I will read the files to find the best place to add them.
expecting: I can insert the list and diagram link in the relevant sections.
next_action: complete task

## Symptoms

expected: README.md and strategy docs should list the 20 supported dishes and feature the architecture diagram (misc/nutrisnap_pipeline_2026-04-16.svg or similar).
actual: The list of 20 dishes and the diagram are missing from the main sections of README.md and strategy_final_2026-04-16.md.
errors: None
reproduction: Read README.md
started: Just noticed.

## Eliminated

## Evidence

- Found the sections in `README.md` and `misc/strategy_final_2026-04-16.md` where the MVP list and architecture diagram should be inserted.

## Resolution

root_cause: The documentation was lacking the explicitly listed 20 supported dishes for the MVP, and the architecture diagram was missing.
fix: Inserted the list of 20 supported MVP dishes into `README.md` and `misc/strategy_final_2026-04-16.md` before the metrics table. Inserted the architecture diagram `![Architecture Diagram](...)` under the Architecture sections of both files.
verification: Verified file contents locally.
files_changed: ["README.md", "misc/strategy_final_2026-04-16.md"]
