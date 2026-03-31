# Known Concerns & Tech Debt

## Security
- The SQLite database has no native string or file-level encryption.
- No user-authorization headers or robust auth token structures are defined yet.

## Scalability
- **CPU/RAM Starvation**: Inference is done fully in a single local pool without external GPU clusters, bottlenecking heavy requests on user hardware limits.
- **Retraining Process**: There is currently no simple dynamic interface to append unrecognized foods. Training new classes mandates an entire extraction and iteration of the YOLO bounds offline via `ml/train_yolo.py`.
- **Storage**: `temp_uploads` must not accumulate stale UUID named assets over a long server lifecycle without a robust file-system eviction schedule.
