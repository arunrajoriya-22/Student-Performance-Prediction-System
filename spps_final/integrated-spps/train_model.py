"""
train_model.py
Student Performance Prediction System
Generates dataset, trains ML models, saves artifacts
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pickle
import os
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, confusion_matrix, classification_report,
    r2_score, mean_squared_error, mean_absolute_error
)
import json

# ──────────────────────────────────────────────
# 1. SYNTHETIC DATASET GENERATION
# ──────────────────────────────────────────────
np.random.seed(42)
N = 800

study_hours        = np.random.uniform(1, 10, N)
attendance         = np.random.uniform(40, 100, N)
prev_sem_marks     = np.random.uniform(40, 100, N)
internal_marks     = np.random.uniform(10, 30, N)
assignment_pct     = np.random.uniform(30, 100, N)
participation      = np.random.randint(0, 2, N).astype(float)
sleep_hours        = np.random.uniform(4, 10, N)
internet_hours     = np.random.uniform(1, 8, N)

# Final percentage formula (realistic weighted combination + noise)
final_percentage = (
    0.25 * study_hours * 10 +
    0.20 * attendance * 0.8 +
    0.25 * prev_sem_marks * 0.7 +
    0.15 * internal_marks * 3 +
    0.10 * assignment_pct * 0.6 +
    0.05 * participation * 10 -
    0.03 * internet_hours * 5 +
    np.random.normal(0, 4, N)
)
final_percentage = np.clip(final_percentage, 0, 100)

# Classification: Fail < 40, Pass 40-74, Distinction >= 75
def classify(pct):
    if pct < 40:
        return 0   # Fail
    elif pct < 75:
        return 1   # Pass
    else:
        return 2   # Distinction

performance_category = np.array([classify(p) for p in final_percentage])

df = pd.DataFrame({
    'study_hours': np.round(study_hours, 2),
    'attendance': np.round(attendance, 2),
    'prev_sem_marks': np.round(prev_sem_marks, 2),
    'internal_marks': np.round(internal_marks, 2),
    'assignment_pct': np.round(assignment_pct, 2),
    'participation': participation.astype(int),
    'sleep_hours': np.round(sleep_hours, 2),
    'internet_hours': np.round(internet_hours, 2),
    'final_percentage': np.round(final_percentage, 2),
    'performance_category': performance_category
})

df.to_csv('dataset.csv', index=False)
print(f"✅ Dataset generated: {len(df)} records")
print(df['performance_category'].value_counts().rename({0:'Fail',1:'Pass',2:'Distinction'}))

# ──────────────────────────────────────────────
# 2. FEATURE / TARGET SPLIT
# ──────────────────────────────────────────────
FEATURES = ['study_hours','attendance','prev_sem_marks','internal_marks',
            'assignment_pct','participation','sleep_hours','internet_hours']

X = df[FEATURES]
y_reg = df['final_percentage']
y_clf = df['performance_category']

X_train, X_test, yr_train, yr_test, yc_train, yc_test = train_test_split(
    X, y_reg, y_clf, test_size=0.2, random_state=42)

# ──────────────────────────────────────────────
# 3. FEATURE SCALING
# ──────────────────────────────────────────────
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ──────────────────────────────────────────────
# 4. REGRESSION MODEL — Linear Regression
# ──────────────────────────────────────────────
reg_model = LinearRegression()
reg_model.fit(X_train_s, yr_train)
yr_pred = reg_model.predict(X_test_s)

r2  = r2_score(yr_test, yr_pred)
mse = mean_squared_error(yr_test, yr_pred)
mae = mean_absolute_error(yr_test, yr_pred)

print(f"\n📈 Regression Results")
print(f"   R² Score : {r2:.4f}")
print(f"   MSE      : {mse:.4f}")
print(f"   MAE      : {mae:.4f}")

# ──────────────────────────────────────────────
# 5. CLASSIFICATION MODEL — Logistic Regression
# ──────────────────────────────────────────────
clf_model = LogisticRegression(max_iter=1000, random_state=42)
clf_model.fit(X_train_s, yc_train)
yc_pred = clf_model.predict(X_test_s)

acc = accuracy_score(yc_test, yc_pred)
cm  = confusion_matrix(yc_test, yc_pred)

print(f"\n🔍 Classification Results")
print(f"   Accuracy : {acc:.4f}")
label_map = {0:'Fail', 1:'Pass', 2:'Distinction'}
present_classes = sorted(set(list(yc_test)+list(yc_pred)))
present_names = [label_map[c] for c in present_classes]
print(classification_report(yc_test, yc_pred, labels=present_classes, target_names=present_names))

# ──────────────────────────────────────────────
# 6. SAVE MODELS & SCALER
# ──────────────────────────────────────────────
with open('regression_model.pkl', 'wb') as f:
    pickle.dump(reg_model, f)
with open('classification_model.pkl', 'wb') as f:
    pickle.dump(clf_model, f)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("\n✅ Models saved: regression_model.pkl, classification_model.pkl, scaler.pkl")

# ──────────────────────────────────────────────
# 7. GRAPHS
# ──────────────────────────────────────────────
os.makedirs('static/graphs', exist_ok=True)

# 7a. Feature Importance (Linear Regression coefficients)
coef = reg_model.coef_
feat_labels = ['Study Hours','Attendance','Prev Marks','Internal Marks',
               'Assignment %','Participation','Sleep Hours','Internet Hours']
colors = ['#4CAF50' if c > 0 else '#f44336' for c in coef]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(feat_labels, coef, color=colors, edgecolor='white')
ax.set_xlabel('Coefficient Value', fontsize=12)
ax.set_title('Feature Importance (Linear Regression Coefficients)', fontsize=14, fontweight='bold')
ax.axvline(0, color='black', linewidth=0.8)
ax.bar_label(bars, fmt='%.2f', padding=3, fontsize=10)
fig.tight_layout()
fig.savefig('static/graphs/feature_importance.png', dpi=120)
plt.close()

# 7b. Confusion Matrix
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
plt.colorbar(im, ax=ax)
labels = ['Fail', 'Pass', 'Distinction']
tick_marks = np.arange(len(labels))
ax.set_xticks(tick_marks); ax.set_xticklabels(labels, fontsize=12)
ax.set_yticks(tick_marks); ax.set_yticklabels(labels, fontsize=12)
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
thresh = cm.max() / 2.
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, format(cm[i, j], 'd'), ha='center', va='center',
                color='white' if cm[i, j] > thresh else 'black', fontsize=14)
fig.tight_layout()
fig.savefig('static/graphs/confusion_matrix.png', dpi=120)
plt.close()

# 7c. Actual vs Predicted scatter
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(yr_test, yr_pred, alpha=0.5, color='#667eea', s=30)
mn, mx = yr_test.min(), yr_test.max()
ax.plot([mn, mx], [mn, mx], 'r--', linewidth=2, label='Perfect Prediction')
ax.set_xlabel('Actual Final %', fontsize=12)
ax.set_ylabel('Predicted Final %', fontsize=12)
ax.set_title('Actual vs Predicted (Linear Regression)', fontsize=13, fontweight='bold')
ax.legend()
fig.tight_layout()
fig.savefig('static/graphs/actual_vs_predicted.png', dpi=120)
plt.close()

# 7d. Performance category distribution
cat_counts = df['performance_category'].value_counts().sort_index()
cat_names = {0:'Fail', 1:'Pass', 2:'Distinction'}
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar([cat_names[i] for i in cat_counts.index], cat_counts.values,
              color=['#f44336','#2196F3','#4CAF50'], edgecolor='white', width=0.5)
ax.set_title('Student Performance Distribution', fontsize=14, fontweight='bold')
ax.set_ylabel('Number of Students')
ax.bar_label(bars, padding=3, fontsize=12)
fig.tight_layout()
fig.savefig('static/graphs/performance_distribution.png', dpi=120)
plt.close()

print("✅ Graphs saved to static/graphs/")

# ──────────────────────────────────────────────
# 8. SAVE METRICS FOR ABOUT PAGE
# ──────────────────────────────────────────────
metrics = {
    "regression": {"r2": round(r2, 4), "mse": round(mse, 4), "mae": round(mae, 4)},
    "classification": {
        "accuracy": round(acc * 100, 2),
        "confusion_matrix": cm.tolist()
    },
    "dataset": {
        "total": len(df),
        "train": len(X_train),
        "test": len(X_test),
        "fail": int((df['performance_category']==0).sum()),
        "pass": int((df['performance_category']==1).sum()),
        "distinction": int((df['performance_category']==2).sum())
    }
}
with open('metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print("✅ Metrics saved to metrics.json")
print("\n🎉 Training Complete!")
