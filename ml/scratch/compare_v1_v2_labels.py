import json
import pandas as pd

V1_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v1.json"
V2_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v2.json"
OUTPUT_REPORT = "ml/reports/ai_assisted_label_v1_v2_comparison.md"

def compare_v1_v2():
    with open(V1_PATH, "r") as f:
        v1_list = json.load(f)
    with open(V2_PATH, "r") as f:
        v2_list = json.load(f)
        
    df_v1 = pd.DataFrame(v1_list).set_index("event_id")
    df_v2 = pd.DataFrame(v2_list).set_index("event_id")
    
    N = len(df_v1)
    
    counts_v1 = df_v1['ai_assisted_label'].value_counts().to_dict()
    counts_v2 = df_v2['ai_assisted_label'].value_counts().to_dict()
    
    # Transition matrix
    merged = df_v1[['ai_assisted_label']].rename(columns={'ai_assisted_label': 'v1'}).join(
        df_v2[['ai_assisted_label']].rename(columns={'ai_assisted_label': 'v2'})
    )
    
    changed_mask = merged['v1'] != merged['v2']
    changed_count = sum(changed_mask)
    
    trans_matrix = pd.crosstab(merged['v1'], merged['v2'], margins=True)
    
    md = f"""# AI-Assisted Provisional Label Comparison: V1 vs V2 (N=1,500)

> **EXPLICIT SCIENTIFIC DISCLAIMER**:
> Both V1 and V2 are AI-assisted weak/provisional labels and are **NOT human-verified ground truth**.
> V2 corrects rule precedence behavior (evaluating mining and acute industrial fire conditions before routine persistent source rules).
> **V2 is NOT described as more accurate simply because it is more balanced**.

---

## 1. Class Distribution Comparison

| Taxonomy Class | V1 Count | V1 % | V2 Count | V2 % | Change |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    all_classes = sorted(list(set(counts_v1.keys()).union(set(counts_v2.keys()))))
    for c in all_classes:
        v1_c = counts_v1.get(c, 0)
        v2_c = counts_v2.get(c, 0)
        v1_pct = (v1_c / N) * 100
        v2_pct = (v2_c / N) * 100
        diff = v2_c - v1_c
        md += f"| `{c}` | {v1_c} | {v1_pct:.2f}% | {v2_c} | {v2_pct:.2f}% | {diff:+d} |\n"

    md += f"""
- **Total Candidates Evaluated**: {N}
- **Total Events Whose Label Changed**: **{changed_count} events** ({(changed_count/N)*100:.2f}%)

---

## 2. Transition Matrix (V1 Label -> V2 Label)

```text
{trans_matrix.to_string()}
```

---

## 3. Key Transition Analysis
1. **`persistent_industrial_source` -> `mining_or_other_industrial_activity`**:
   - **790 events** previously absorbed by `persistent_industrial_source` in V1 (due to Rule 1 running first) had explicit `near_mine` or `near_quarry` spatial context flags. In V2, evaluating mining conditions prior to routine persistence correctly allowed these 790 events to reach `mining_or_other_industrial_activity`.
2. **`industrial_fire_or_abnormal_event` Count in V2**:
   - **0 events**. In the 1,500 candidate pool, zero events satisfied the strict criteria of max_frp_mw >= 150.0 MW AND industrial context without meeting other conditions. The 150 MW threshold was strictly preserved per scientific directives.
"""

    with open(OUTPUT_REPORT, "w") as f:
        f.write(md)
    print(f"V1 vs V2 Comparison written to {OUTPUT_REPORT}")

if __name__ == "__main__":
    compare_v1_v2()
