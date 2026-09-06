import json
import pandas as pd

LABELS_PATH = "ml/data/ground_truth/ai_assisted/ai_assisted_labels_v1.json"
OUTPUT_REPORT = "ml/reports/ai_assisted_label_summary_v1.md"

def main():
    with open(LABELS_PATH, "r") as f:
        records = json.load(f)
        
    df = pd.DataFrame(records)
    N = len(df)
    
    label_counts = df['ai_assisted_label'].value_counts().to_dict()
    conf_counts = df['ai_confidence'].value_counts().to_dict()
    review_counts = df['requires_human_review'].value_counts().to_dict()
    
    unknown_count = label_counts.get("unknown_requires_verification", 0)
    
    md = f"""# AI-Assisted Provisional Label Summary Report (N=1,500)

> **IMPORTANT SCIENTIFIC DISCLAIMER**:
> These are AI-assisted weak/provisional labels and are NOT human-verified ground truth.
> They are strictly used to prioritize candidates for human review and MUST NOT be used as verified ground truth for model accuracy evaluation.

---

## 1. Summary Statistics & Counts (N={N})

### Provisional Label Distribution
"""
    for l, cnt in label_counts.items():
        pct = (cnt / N) * 100
        md += f"- **`{l}`**: {cnt} events ({pct:.2f}%)\n"

    md += """
### Confidence Level Distribution
"""
    for c, cnt in conf_counts.items():
        pct = (cnt / N) * 100
        md += f"- **`{c}` Confidence**: {cnt} events ({pct:.2f}%)\n"

    md += f"""
### Human Review Requirement Breakdown
- **`requires_human_review = true`**: {review_counts.get(True, 0)} events ({(review_counts.get(True, 0)/N)*100:.2f}%)
- **`requires_human_review = false`**: {review_counts.get(False, 0)} events ({(review_counts.get(False, 0)/N)*100:.2f}%)
- **Provisional Unknowns (`unknown_requires_verification`)**: {unknown_count} events ({(unknown_count/N)*100:.2f}%)

---

## 2. Highest-Priority Human Review Ranking
Human domain annotators should prioritize review using `ml/data/ground_truth/ai_assisted/human_review_priority_v1.json`, which orders candidate review queue by:
1. `LOW` Confidence events
2. Provisional `unknown_requires_verification` cases
3. `requires_human_review = true` events
4. High FRP intensity spikes ($>100$ MW)
"""

    with open(OUTPUT_REPORT, "w") as f:
        f.write(md)
    print(f"Summary report written to {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()
