import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import roc_auc_score
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from joblib import dump

def prepare_data(df, feature_cols, target_col='target'):
    X = df[feature_cols].fillna(0)
    y = df[target_col]
    return X, y

def train_models(X, y, random_state=42):
    # stratified split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=random_state)

    # handle imbalance with SMOTE on training set
    sm = SMOTE(random_state=random_state)
    X_res, y_res = sm.fit_resample(X_train, y_train)

    # random forest
    rf = RandomForestClassifier(random_state=random_state)
    rf_params = {'n_estimators':[100,200], 'max_depth':[5,10,None]}
    rf_cv = RandomizedSearchCV(rf, rf_params, n_iter=4, cv=3, scoring='roc_auc', random_state=random_state)
    rf_cv.fit(X_res, y_res)

    # xgboost
    xgb = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=random_state)
    xgb_params = {'n_estimators':[100,200], 'max_depth':[3,6], 'learning_rate':[0.05,0.1]}
    xgb_cv = RandomizedSearchCV(xgb, xgb_params, n_iter=4, cv=3, scoring='roc_auc', random_state=random_state)
    xgb_cv.fit(X_res, y_res)

    # ensemble via simple averaging
    def predict_proba_ensemble(Xv):
        p1 = rf_cv.predict_proba(Xv)[:,1]
        p2 = xgb_cv.predict_proba(Xv)[:,1]
        return (p1 + p2) / 2.0

    # evaluate
    proba = predict_proba_ensemble(X_test)
    auc = roc_auc_score(y_test, proba)

    # save models
    dump(rf_cv, 'models/rf_cv.joblib')
    dump(xgb_cv, 'models/xgb_cv.joblib')

    return {'rf':rf_cv, 'xgb':xgb_cv, 'auc':auc}
