import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support, confusion_matrix, roc_curve
import seaborn as sns

def compute_metrics(y_true, y_proba, threshold=0.5):
    auc = roc_auc_score(y_true, y_proba)
    y_pred = (y_proba >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    return {'auc':auc, 'precision':precision, 'recall':recall, 'f1':f1, 'confusion_matrix':cm}

def plot_roc(y_true, y_proba, out_path=None):
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    plt.figure()
    plt.plot(fpr, tpr, label=f'AUC={roc_auc_score(y_true,y_proba):.3f}')
    plt.plot([0,1],[0,1],'k--')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.legend()
    if out_path:
        plt.savefig(out_path)
    return plt

def plot_confusion_matrix(cm, labels=['0','1'], out_path=None):
    plt.figure()
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    if out_path:
        plt.savefig(out_path)
    return plt
