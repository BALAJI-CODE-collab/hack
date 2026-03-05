"""Model training and ensemble for poaching prediction."""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, auc, confusion_matrix, classification_report
from sklearn.metrics import f1_score
from sklearn.isotonic import IsotonicRegression
from imblearn.over_sampling import SMOTE
from imblearn.ensemble import BalancedBaggingClassifier
import xgboost as xgb
import joblib
import json
from pathlib import Path


class PoachedModelTrainer:
    """Train RF and XGBoost models for poaching prediction."""
    
    def __init__(self, features_df, test_size=0.2, random_state=42):
        """
        Initialize trainer.
        
        Args:
            features_df: Features dataframe with 'target' column
            test_size: Train-test split ratio
            random_state: Random seed for reproducibility
        """
        self.features_df = features_df.copy()
        self.test_size = test_size
        self.random_state = random_state
        
        # Remove non-feature columns
        self.X = features_df.drop(columns=['target', 'grid_id', 'week_start'], errors='ignore')
        self.y = features_df['target']
        
        # Handle missing values
        self.X = self.X.fillna(self.X.mean(numeric_only=True))
        self.X = self.X.select_dtypes(include=[np.number])
        
        # Train-test split
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=random_state, stratify=self.y
        )
        
        # Normalize features
        self.scaler = StandardScaler()
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        
        # SMOTE resampling (on training set only)
        print("Applying SMOTE to training data...")
        smote = SMOTE(random_state=random_state)
        self.X_train_smote, self.y_train_smote = smote.fit_resample(self.X_train_scaled, self.y_train)
        print(f"✓ Training set resampled: {len(self.y_train)} -> {len(self.y_train_smote)}")
        
        self.rf_model = None
        self.xgb_model = None
        self.stacker = None
        self.bagging_model = None
        self.ensemble_preds_train = None
        self.ensemble_preds_test = None
        self.ensemble_calibrated_train = None
        self.ensemble_calibrated_test = None
        self.calibrator = None
        self.threshold = 0.5
    
    def train_random_forest(self):
        """Train Random Forest with hyperparameter tuning."""
        print("\nTraining Random Forest...")
        
        # Hyperparameter grid
        param_dist = {
            'n_estimators': [50, 100, 200, 300, 400],
            'max_depth': [None, 10, 15, 20, 30],
            'min_samples_split': [2, 5, 10, 15],
            'min_samples_leaf': [1, 2, 4, 6],
            'max_features': ['sqrt', 'log2', 0.5],
            'class_weight': [None, 'balanced', 'balanced_subsample']
        }
        
        rf = RandomForestClassifier(random_state=self.random_state, n_jobs=-1, class_weight='balanced')
        
        # Random search
        search = RandomizedSearchCV(
            rf, param_dist, n_iter=30, cv=5, scoring='roc_auc', random_state=self.random_state, n_jobs=-1
        )
        search.fit(self.X_train_smote, self.y_train_smote)
        
        self.rf_model = search.best_estimator_
        
        # Evaluate
        rf_train_pred = self.rf_model.predict_proba(self.X_train_scaled)[:, 1]
        rf_test_pred = self.rf_model.predict_proba(self.X_test_scaled)[:, 1]
        
        train_auc = roc_auc_score(self.y_train, rf_train_pred)
        test_auc = roc_auc_score(self.y_test, rf_test_pred)
        
        print(f"✓ Best LR params: {search.best_params_}")
        print(f"✓ RF Train AUC: {train_auc:.4f}, Test AUC: {test_auc:.4f}")
        
        return rf_train_pred, rf_test_pred
    
    def train_xgboost(self):
        """Train XGBoost with hyperparameter tuning."""
        print("\nTraining XGBoost...")
        
        # Hyperparameter grid
        param_dist = {
            'n_estimators': [100, 200, 300, 400],
            'max_depth': [3, 5, 7, 9, 12],
            'learning_rate': [0.01, 0.03, 0.05, 0.1],
            'subsample': [0.6, 0.7, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0],
            'gamma': [0, 0.1, 0.5, 1.0],
            'min_child_weight': [1, 3, 5],
            'reg_lambda': [0.5, 1.0, 2.0]
        }
        
        xgb_model = xgb.XGBClassifier(
            random_state=self.random_state, 
            eval_metric='auc',
            scale_pos_weight=(len(self.y_train_smote) - self.y_train_smote.sum()) / self.y_train_smote.sum()
        )
        
        search = RandomizedSearchCV(
            xgb_model, param_dist, n_iter=30, cv=5, scoring='roc_auc', random_state=self.random_state, n_jobs=-1
        )
        search.fit(self.X_train_smote, self.y_train_smote)
        
        self.xgb_model = search.best_estimator_
        
        # Evaluate
        xgb_train_pred = self.xgb_model.predict_proba(self.X_train_scaled)[:, 1]
        xgb_test_pred = self.xgb_model.predict_proba(self.X_test_scaled)[:, 1]
        
        train_auc = roc_auc_score(self.y_train, xgb_train_pred)
        test_auc = roc_auc_score(self.y_test, xgb_test_pred)
        
        print(f"✓ Best XGB params: {search.best_params_}")
        print(f"✓ XGB Train AUC: {train_auc:.4f}, Test AUC: {test_auc:.4f}")
        
        return xgb_train_pred, xgb_test_pred

    def train_stacking(self):
        """Train a stacking meta-learner using RF and XGB as base learners."""
        print("\nTraining stacking meta-learner...")

        # Build estimators using the already-tuned models
        estimators = []
        if self.rf_model is not None:
            estimators.append(('rf', RandomForestClassifier(**self.rf_model.get_params())))
        if self.xgb_model is not None:
            estimators.append(('xgb', xgb.XGBClassifier(**self.xgb_model.get_params(), use_label_encoder=False, eval_metric='auc')))

        if not estimators:
            print("No base estimators available for stacking")
            return None, None

        final_est = LogisticRegression(max_iter=1000)
        stack = StackingClassifier(estimators=estimators, final_estimator=final_est, cv=5, n_jobs=-1, passthrough=False)

        # Fit stacking on SMOTE-resampled scaled training data
        stack.fit(self.X_train_smote, self.y_train_smote)
        self.stacker = stack

        stack_train_pred = stack.predict_proba(self.X_train_scaled)[:, 1]
        stack_test_pred = stack.predict_proba(self.X_test_scaled)[:, 1]

        train_auc = roc_auc_score(self.y_train, stack_train_pred)
        test_auc = roc_auc_score(self.y_test, stack_test_pred)
        print(f"✓ Stacker Train AUC: {train_auc:.4f}, Test AUC: {test_auc:.4f}")

        return stack_train_pred, stack_test_pred

    def train_bagging(self):
        """Train a balanced bagging classifier to handle class imbalance."""
        print("\nTraining Balanced Bagging classifier...")

        # Base estimator for bagging
        base = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=self.random_state)
        bag = BalancedBaggingClassifier(base_estimator=base, n_estimators=25, sampling_strategy='auto', replacement=False, random_state=self.random_state, n_jobs=-1)

        # Fit on original (unscaled) numeric features (inverse-transform scaled data)
        X_train_orig = pd.DataFrame(self.scaler.inverse_transform(self.X_train_scaled), columns=self.X_train.columns)
        X_train_orig = X_train_orig.fillna(0)

        bag.fit(X_train_orig, self.y_train)
        self.bagging_model = bag

        # Prepare test original
        X_test_orig = pd.DataFrame(self.scaler.inverse_transform(self.X_test_scaled), columns=self.X_test.columns)
        bag_train_pred = bag.predict_proba(X_train_orig)[:, 1]
        bag_test_pred = bag.predict_proba(X_test_orig)[:, 1]

        train_auc = roc_auc_score(self.y_train, bag_train_pred)
        test_auc = roc_auc_score(self.y_test, bag_test_pred)
        print(f"✓ Bagging Train AUC: {train_auc:.4f}, Test AUC: {test_auc:.4f}")

        return bag_train_pred, bag_test_pred
    
    def create_ensemble(self, rf_train_pred, rf_test_pred, xgb_train_pred, xgb_test_pred):
        """Create ensemble by averaging predictions."""
        print("\nCreating ensemble...")
        preds_train = [rf_train_pred, xgb_train_pred]
        preds_test = [rf_test_pred, xgb_test_pred]

        # stacking predictions (if available)
        if self.stacker is not None:
            try:
                stack_train_pred = self.stacker.predict_proba(self.X_train_scaled)[:, 1]
                stack_test_pred = self.stacker.predict_proba(self.X_test_scaled)[:, 1]
                preds_train.append(stack_train_pred)
                preds_test.append(stack_test_pred)
            except Exception:
                pass

        # bagging predictions (if available)
        if self.bagging_model is not None:
            try:
                # bagging was trained on unscaled features, so inverse-transform
                X_train_orig = pd.DataFrame(self.scaler.inverse_transform(self.X_train_scaled), columns=self.X_train.columns)
                X_test_orig = pd.DataFrame(self.scaler.inverse_transform(self.X_test_scaled), columns=self.X_test.columns)
                bag_train_pred = self.bagging_model.predict_proba(X_train_orig)[:, 1]
                bag_test_pred = self.bagging_model.predict_proba(X_test_orig)[:, 1]
                preds_train.append(bag_train_pred)
                preds_test.append(bag_test_pred)
            except Exception:
                pass

        # Average available model predictions
        self.ensemble_preds_train = np.mean(np.vstack(preds_train), axis=0)
        self.ensemble_preds_test = np.mean(np.vstack(preds_test), axis=0)
        
        ensemble_auc_train = roc_auc_score(self.y_train, self.ensemble_preds_train)
        ensemble_auc_test = roc_auc_score(self.y_test, self.ensemble_preds_test)

        # Calibrate ensemble probabilities using isotonic regression on train predictions
        try:
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.ensemble_calibrated_train = self.calibrator.fit_transform(self.ensemble_preds_train, self.y_train)
            self.ensemble_calibrated_test = self.calibrator.transform(self.ensemble_preds_test)
        except Exception:
            # Fallback to uncalibrated if calibration fails
            self.calibrator = None
            self.ensemble_calibrated_train = self.ensemble_preds_train
            self.ensemble_calibrated_test = self.ensemble_preds_test

        # Tune threshold on calibrated train predictions to maximize F1
        best_thr = 0.5
        best_f1 = -1
        for thr in np.linspace(0.01, 0.99, 99):
            preds = (self.ensemble_calibrated_train > thr).astype(int)
            f1 = f1_score(self.y_train, preds)
            if f1 > best_f1:
                best_f1 = f1
                best_thr = thr
        self.threshold = float(best_thr)

        print(f"✓ Ensemble Train AUC: {ensemble_auc_train:.4f}, Test AUC: {ensemble_auc_test:.4f}")
        print(f"✓ Calibration applied: {self.calibrator is not None}, threshold={self.threshold:.3f}, train F1={best_f1:.4f}")
    
    def train_all(self):
        """Train all models and create ensemble."""
        rf_train_pred, rf_test_pred = self.train_random_forest()
        xgb_train_pred, xgb_test_pred = self.train_xgboost()
        # Train stacking meta-learner on SMOTE-resampled data
        try:
            stack_train_pred, stack_test_pred = self.train_stacking()
        except Exception:
            stack_train_pred = stack_test_pred = None
        # Train bagging model
        try:
            bag_train_pred, bag_test_pred = self.train_bagging()
        except Exception:
            bag_train_pred = bag_test_pred = None
        self.create_ensemble(rf_train_pred, rf_test_pred, xgb_train_pred, xgb_test_pred)
        # second create_ensemble call not needed; ensemble created above
    
    def save_models(self, output_dir='models'):
        """Save trained models."""
        Path(output_dir).mkdir(exist_ok=True)
        
        joblib.dump(self.rf_model, f'{output_dir}/random_forest_model.pkl')
        joblib.dump(self.xgb_model, f'{output_dir}/xgboost_model.pkl')
        joblib.dump(self.scaler, f'{output_dir}/scaler.pkl')
        if self.bagging_model is not None:
            joblib.dump(self.bagging_model, f'{output_dir}/bagging_model.pkl')
        if self.calibrator is not None:
            joblib.dump(self.calibrator, f'{output_dir}/calibrator.pkl')
        # Save threshold to JSON
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(f'{output_dir}/threshold.json', 'w') as f:
            json.dump({'threshold': float(self.threshold)}, f)
        
        print(f"✓ Models saved to {output_dir}/")
    
    def evaluate(self):
        """Generate evaluation metrics."""
        # Use calibrated predictions and tuned threshold if available
        preds_prob = self.ensemble_calibrated_test if self.ensemble_calibrated_test is not None else self.ensemble_preds_test
        y_pred = (preds_prob > float(self.threshold)).astype(int)

        report = classification_report(self.y_test, y_pred, output_dict=True)
        cm = confusion_matrix(self.y_test, y_pred)
        auc_score = roc_auc_score(self.y_test, preds_prob)

        metrics = {
            'auc_score': auc_score,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'threshold': float(self.threshold)
        }
        
        print(f"\n{'='*60}")
        print("ENSEMBLE MODEL EVALUATION")
        print(f"{'='*60}")
        print(f"AUC Score: {auc_score:.4f}")
        print("\nConfusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(classification_report(self.y_test, y_pred, target_names=['No Poaching', 'Poaching']))
        print(f"{'='*60}\n")
        
        return metrics
    
    def get_feature_importance(self):
        """Get feature importance from RF and XGB."""
        rf_importance = pd.DataFrame({
            'feature': self.X.columns,
            'importance': self.rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        xgb_importance = pd.DataFrame({
            'feature': self.X.columns,
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return rf_importance, xgb_importance


if __name__ == '__main__':
    print("Model training module ready")
