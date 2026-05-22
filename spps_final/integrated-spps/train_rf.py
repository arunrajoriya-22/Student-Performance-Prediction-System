"""
train_rf.py — NEW FILE (Integrated into Original Project)
Trains Random Forest models using the EXISTING dataset.csv from the original project.
Run this ONCE after your original train_model.py to enable multi-model support.

Usage: py train_rf.py
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble        import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import StandardScaler
from sklearn.metrics         import (r2_score, mean_squared_error,
                                     mean_absolute_error, accuracy_score)

print("=" * 50)
print("  Random Forest — Model Training")
print("=" * 50)

# ── Load existing dataset from original project ──
DATASET = 'dataset.csv'
if not os.path.exists(DATASET):
    print("❌ dataset.csv not found. Run train_model.py first.")
    exit(1)

df = pd.read_csv(DATASET)
print(f"✅ Dataset loaded: {len(df)} records")

FEATURES = ['study_hours','attendance','prev_sem_marks','internal_marks',
            'assignment_pct','participation','sleep_hours','internet_hours']

X      = df[FEATURES]
y_reg  = df['final_percentage']
y_clf  = df['performance_category']

# ── Split (same seed as original for consistency) ──
X_train, X_test, yr_train, yr_test, yc_train, yc_test = train_test_split(
    X, y_reg, y_clf, test_size=0.2, random_state=42
)

# ── RF needs its own scaler (saved separately) ──
rf_scaler   = StandardScaler()
X_train_s   = rf_scaler.fit_transform(X_train)
X_test_s    = rf_scaler.transform(X_test)

# ── Random Forest Regressor ──
print("\n🌲 Training Random Forest Regressor...")
rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_reg.fit(X_train_s, yr_train)
yr_pred_rf = rf_reg.predict(X_test_s)
rf_r2  = round(r2_score(yr_test, yr_pred_rf), 4)
rf_mse = round(mean_squared_error(yr_test, yr_pred_rf), 4)
rf_mae = round(mean_absolute_error(yr_test, yr_pred_rf), 4)
print(f"   R² : {rf_r2}  |  MSE : {rf_mse}  |  MAE : {rf_mae}")

# ── Random Forest Classifier ──
print("\n🌲 Training Random Forest Classifier...")
rf_clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf_clf.fit(X_train_s, yc_train)
yc_pred_rf = rf_clf.predict(X_test_s)
rf_acc = round(accuracy_score(yc_test, yc_pred_rf) * 100, 2)
print(f"   Accuracy : {rf_acc}%")

# ── Feature importance from RF Classifier ──
fi = dict(zip(FEATURES, np.round(rf_clf.feature_importances_ * 100, 2).tolist()))
print("\n📊 Feature Importance (RF Classifier):")
for feat, imp in sorted(fi.items(), key=lambda x: -x[1]):
    print(f"   {feat:20s}: {imp:.1f}%")

# ── Save models ──
with open('rf_regressor.pkl',  'wb') as f: pickle.dump(rf_reg,   f)
with open('rf_classifier.pkl', 'wb') as f: pickle.dump(rf_clf,   f)
with open('rf_scaler.pkl',     'wb') as f: pickle.dump(rf_scaler, f)

print("\n✅ Saved: rf_regressor.pkl, rf_classifier.pkl, rf_scaler.pkl")
print("✅ Restart app.py — Random Forest will be loaded automatically.")
print("=" * 50)
