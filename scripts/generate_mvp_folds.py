import json
import pandas as pd
from pathlib import Path
import numpy as np

def generate_mvp_folds():
    project_root = Path(__file__).resolve().parent.parent
    mvp_ids_path = project_root / "datasets/splits/mvp_subset_ids.txt"
    nutrition_csv = project_root / "datasets/raw/archive (4)/dish_nutrition_values.csv"
    output_dir = project_root / "datasets/splits/mvp"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not mvp_ids_path.exists():
        print(f"Error: {mvp_ids_path} not found.")
        return

    mvp_ids = [l.strip() for l in mvp_ids_path.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(mvp_ids)} MVP IDs.")

    # Load nutrition to enable (simple) stratification
    df = pd.read_csv(nutrition_csv)
    # Ensure dish_id is string and matched
    df['dish_id'] = df.iloc[:, 0].astype(str) # The first column is usually dish_id or unnamed index
    # Find calories column (might be 'calories' or 'total_calories')
    cal_col = 'total_calories' if 'total_calories' in df.columns else 'calories'
    
    mvp_df = df[df['dish_id'].isin(mvp_ids)].copy()
    print(f"Found nutrition data for {len(mvp_df)} dishes.")

    # Sort by calories to enable basic stratification
    mvp_df = mvp_df.sort_values(by=cal_col)
    sorted_ids = mvp_df['dish_id'].tolist()
    
    # If some IDs missing from CSV, add them at the end
    missing = [i for i in mvp_ids if i not in sorted_ids]
    sorted_ids.extend(missing)

    # Selection for hold-out test set (2 dishes)
    # Picking one mid-high and one low calorie dish for balance
    test_ids = ["dish_1562872223", "dish_1557861795"]
    cv_pool = [i for i in sorted_ids if i not in test_ids]
    
    print(f"Reserved for Test: {test_ids}")
    print(f"Pool for CV: {cv_pool}")

    # Save test_ids.txt
    with open(output_dir / "test_ids.txt", "w") as f:
        f.write("\n".join(test_ids) + "\n")
    
    folds = []
    for i in range(5):
        # Round-robin assignment for stratification
        val_ids = [cv_pool[j] for j in range(len(cv_pool)) if j % 5 == i]
        train_ids = [id for id in cv_pool if id not in val_ids]
        folds.append({
            "fold": i,
            "train": train_ids,
            "val": val_ids
        })
        print(f"Fold {i}: train={len(train_ids)}, val={len(val_ids)}")

    with open(output_dir / "cv_folds.json", "w") as f:
        json.dump(folds, f, indent=2)
    
    # Save a default val_ids.txt using Fold 0 for non-CV tools (like verify_results.py)
    with open(output_dir / "val_ids.txt", "w") as f:
        f.write("\n".join(folds[0]["val"]) + "\n")
    
    print(f"Saved MVP folds to {output_dir / 'cv_folds.json'}")
    print(f"Saved MVP test ids to {output_dir / 'test_ids.txt'}")
    print(f"Saved MVP val ids to {output_dir / 'val_ids.txt'}")

if __name__ == "__main__":
    generate_mvp_folds()
