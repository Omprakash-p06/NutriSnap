from pathlib import Path

import pandas as pd
import torch

v_df = pd.read_csv("datasets/processed/volumes.csv")
d_df = pd.read_csv("datasets/interim/dishes.csv")
m_map = d_df.set_index("dish_id")["total_mass"].to_dict()
features_dir = Path("datasets/processed/features")

results = []
for _, row in v_df.iterrows():
    f = features_dir / row["filename"]
    if not f.exists():
        continue

    x = torch.load(f, weights_only=True)
    mask = x[3].numpy()
    depth = x[4].numpy()

    # Correct parsing of dish_id from filename
    did = "_".join(row["filename"].split("_")[:2])
    mass = m_map.get(did)

    if mass:
        # Simple volume: sum of heights (1 - depth) over mask
        vol_simple = ((1.0 - depth) * mask).sum()
        results.append(
            {"mass": mass, "vol_simple": vol_simple, "vol_old": row["volume"]}
        )

res_df = pd.DataFrame(results)
print("Correlation with mass:")
print(res_df.corr()["mass"])
