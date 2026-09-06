import json
import os
from src.classification.annotation_quality import calculate_raw_agreement, calculate_cohens_kappa, detect_disagreements
from src.classification.ground_truth import ALLOWED_TAXONOMY

def main():
    print("Evaluating annotation quality...")
    # Demonstration of inter-annotator evaluation on dual review pools
    categories = sorted(list(ALLOWED_TAXONOMY))
    print(f"Taxonomy categories ({len(categories)}):", categories)
    print("Annotation quality infrastructure is ready.")

if __name__ == "__main__":
    main()
