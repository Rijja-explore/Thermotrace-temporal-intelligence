# Pilot 001 Label Quality Report V2

## 1. Completeness
- **Total events**: 40
- **Reviewer 1 completed**: 0
- **Reviewer 2 completed**: 0
- **Events completed by both**: 0
- **Incomplete rows**: 80/80 (100%)
- **Invalid labels**: 0
- **Duplicate event IDs**: 0
- **Missing confidence**: 80/80 (100%)
- **Missing evidence summary**: 80/80 (100%)
- **Missing evidence URLs**: 80/80 (100%)
- **Rows marked review_complete=TRUE but lacking required fields**: 0

## 2. Inter-Rater Agreement
Using only events reviewed by BOTH reviewers (n=0):
- **Raw agreement**: N/A
- **Cohen's kappa**: N/A
- **6x6 confusion matrix**: N/A
- **Disagreement count**: 0
- **Disagreement percentage**: N/A
- **Per-class agreement**: N/A

## 3. Disagreements
Since there are 0 completed reviews, there are 0 substantive disagreements.
An empty file was generated: `ml/data/pilot_001_disagreements.csv`

## 4. Consensus
The consensus workflow classified all 40 events as `incomplete`.
- **consensus**: 0
- **disagreement_requires_adjudication**: 0
- **incomplete**: 40
*Output*: `ml/data/pilot_001_consensus_labels.csv` and `ml/data/pilot_001_adjudication_queue.csv` have been generated.

## 5. Class Distribution
- **Reviewer 1 distribution**: 0 across all classes
- **Reviewer 2 distribution**: 0 across all classes
- **Agreed/consensus distribution**: 0 across all classes
- **Unresolved disagreements**: 0
- **Unknown count and percentage**: 0 (0%)
*Note: Every taxonomy class has zero representation because no labels have been provided.*

## 6. Evidence Quality
For completed reviews (n=0):
- **Evidence-summary completion rate**: N/A
- **Evidence-URL completion rate**: N/A
- **Number of weak/ambiguous evidence cases**: N/A
- **Number of conflicting-evidence cases**: N/A
- **Unsupported reasoning**: N/A

## 7. Taxonomy/Protocol Analysis
Because the pilot contains exactly 0 labels, it is impossible to analyze boundary difficulties, reviewer error, or taxonomy boundaries. The failure is entirely at the protocol execution level: human reviewers have not accessed or completed the worksheet.

## 8. Statistical Caution
There is no data to generalize. 

## 9. Decision Gate
**HUMAN_REVIEW_NOT_EXECUTED**
The pilot cannot be evaluated or approved because it was not performed. The data handoff process to the human reviewers has been restructured into independent CSVs with a robust intake validator to ensure successful execution.
