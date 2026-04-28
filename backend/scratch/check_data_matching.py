import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ids_path = Path("datasets/splits/mvp_subset_ids.txt")
features_dir = Path("datasets/processed/features")
dishes_csv = Path("datasets/interim/dishes.csv")
volumes_csv = Path("datasets/processed/volumes.csv")

ids = [line.strip() for line in ids_path.read_text().splitlines() if line.strip()]
dishes_df = pd.read_csv(dishes_csv)
dishes_df["dish_id"] = dishes_df["dish_id"].astype(str)
labels = dishes_df.set_index("dish_id")["total_mass"].to_dict()

volumes_df = pd.read_csv(volumes_csv)
volumes = volumes_df.set_index("filename")["volume"].to_dict()

samples = []
missing_label = 0
missing_volume = 0
total_files_found = 0

for did in ids:
    files = list(features_dir.glob(f"{did}_*_composite.pt"))
    total_files_found += len(files)
    for f in files:
        has_label = did in labels
        has_volume = f.name in volumes
        if has_label and has_volume:
            samples.append((f, labels[did], volumes[f.name]))
        else:
            if not has_label:
                missing_label += 1
            if not has_volume:
                missing_volume += 1
            # logger.warning(f"Missing label or volume for dish {did} / {f.name}. Label: {has_label}, Volume: {has_volume}")

print(f"Total IDs: {len(ids)}")
print(f"Total files found matching patterns: {total_files_found}")
print(f"Samples loaded: {len(samples)}")
print(f"Files missing labels: {missing_label}")
print(f"Files missing volumes: {missing_volume}")

if samples:
    print(f"Example sample: {samples[0]}")
