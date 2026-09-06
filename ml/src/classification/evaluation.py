import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, balanced_accuracy_score, confusion_matrix

INDUSTRIAL_CLASSES = {
    "persistent_industrial_source",
    "industrial_fire_or_abnormal_event",
    "mining_or_other_industrial_activity"
}

def calculate_industrial_precision(y_true, y_pred) -> float:
    """
    Industrial class precision calculation:
    Precision across all industrial target classes ('persistent_industrial_source',
    'industrial_fire_or_abnormal_event', 'mining_or_other_industrial_activity').
    """
    if len(y_true) == 0:
        return 0.0
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yp in INDUSTRIAL_CLASSES and yt == yp)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yp in INDUSTRIAL_CLASSES and yt != yp)
    return float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0

def calculate_false_positive_reduction(y_true, baseline_preds, model_preds, target_class="wildfire_or_forest_fire") -> float:
    """
    Calculates false-positive reduction of model_preds relative to baseline_preds.
    FP_reduction = (Baseline_FPs - Model_FPs) / Baseline_FPs (if Baseline_FPs > 0 else 0.0).
    Calculated strictly from actual predictions.
    """
    baseline_fps = sum(1 for yt, yp in zip(y_true, baseline_preds) if yp == target_class and yt != target_class)
    model_fps = sum(1 for yt, yp in zip(y_true, model_preds) if yp == target_class and yt != target_class)
    
    if baseline_fps == 0:
        return 0.0
    return float((baseline_fps - model_fps) / baseline_fps)

def calculate_metrics(y_true, y_pred, y_probs=None, labels=None, baseline_preds=None):
    if y_true is None or y_pred is None or len(y_true) == 0:
        raise ValueError("y_true and y_pred must not be empty")
    if len(y_true) != len(y_pred):
        raise ValueError("Mismatched lengths between y_true and y_pred")
    
    unique_labels = list(set(y_true))
    if labels is None:
        labels = sorted(unique_labels)
        
    for y in y_true:
        if y not in labels:
            raise ValueError(f"Invalid label in y_true: {y}")
            
    metrics = {
        "macro_f1": float(f1_score(y_true, y_pred, average='macro', labels=labels, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "industrial_precision": calculate_industrial_precision(y_true, y_pred),
        "precision": {},
        "recall": {},
        "f1": {},
        "support": {}
    }
    
    if baseline_preds is not None:
        metrics["false_positive_reduction"] = calculate_false_positive_reduction(y_true, baseline_preds, y_pred)
        
    precisions = precision_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    recalls = recall_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    f1s = f1_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    
    for idx, label in enumerate(labels):
        metrics["precision"][label] = float(precisions[idx])
        metrics["recall"][label] = float(recalls[idx])
        metrics["f1"][label] = float(f1s[idx])
        metrics["support"][label] = int(sum([1 for y in y_true if y == label]))
        
    if y_probs is not None:
        if y_probs.shape[0] != len(y_true):
            raise ValueError("Malformed probability matrix: rows do not match length of y_true")
        if y_probs.shape[1] != len(labels):
            raise ValueError("Malformed probability matrix: columns do not match length of labels")
        if not np.allclose(np.sum(y_probs, axis=1), 1.0):
            raise ValueError("Probabilities do not approximately sum to 1")
            
        N = len(y_true)
        brier = 0.0
        for i in range(N):
            true_idx = labels.index(y_true[i])
            for c_idx in range(len(labels)):
                target = 1.0 if c_idx == true_idx else 0.0
                brier += (y_probs[i, c_idx] - target) ** 2
        metrics["brier_score"] = float(brier / N)
        
    return metrics

