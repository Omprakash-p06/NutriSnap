"""Evaluation metrics for NutriSnap nutrition regression."""
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score as sk_r2
from scipy.stats import spearmanr


def calorie_mae(y_true, y_pred):
    """Mean Absolute Error for calorie predictions. Target: <= 65 kcal."""
    return mean_absolute_error(y_true, y_pred)


def calorie_mape(y_true, y_pred):
    """Mean Absolute Percentage Error for calorie predictions. Target: <= 30%."""
    # Avoid division by zero
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mask = y_true > 0
    if not np.any(mask):
        return 0.0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def r2_score(y_true, y_pred):
    """R-squared score for regression quality."""
    return sk_r2(y_true, y_pred)


def spearman_correlation(y_true, y_pred):
    """Spearman rank correlation — not fooled by systematic scale errors."""
    res = spearmanr(y_true, y_pred)
    return res.correlation


def prediction_bias(y_true, y_pred):
    """Mean signed error (positive = over-prediction)."""
    return np.mean(np.array(y_pred) - np.array(y_true))


def prediction_variance_ratio(y_true, y_pred):
    """Ratio of prediction variance to actual variance. 
    Low values (<0.1) indicate constant-prediction failure.
    """
    v_true = np.var(y_true)
    v_pred = np.var(y_pred)
    if v_true == 0:
        return 1.0
    return v_pred / v_true


def binned_mae(y_true, y_pred, bins=[0, 200, 800, 2000]):
    """Calculate MAE for different caloric ranges."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    results = {}
    
    for i in range(len(bins)-1):
        low, high = bins[i], bins[i+1]
        mask = (y_true >= low) & (y_true < high)
        if np.any(mask):
            results[f"{low}-{high} kcal"] = mean_absolute_error(y_true[mask], y_pred[mask])
        else:
            results[f"{low}-{high} kcal"] = None
            
    return results
