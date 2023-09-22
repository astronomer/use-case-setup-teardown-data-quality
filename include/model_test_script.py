"""Script to test modelling and plotting of the synthetic rose dataset."""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    f1_score,
    roc_curve,
    auc,
    classification_report,
)
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

print("Seaborn version:", sns.__version__)
print("Matplotlib version:", matplotlib.__version__)

data = pd.read_csv("roses_raw.csv")

data = pd.get_dummies(data, columns=["blooming_month"], drop_first=True)

X = data.drop(["rose_type", "index"], axis=1)
y = data["rose_type"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

clf = RandomForestClassifier()
clf.fit(X_train_scaled, y_train)
y_pred = clf.predict(X_test_scaled)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("F1-Score:", f1_score(y_test, y_pred, average="weighted"))
print(classification_report(y_test, y_pred))

fig, ax = plt.subplots(1, 2, figsize=(14, 6))
labels = clf.classes_
cm = confusion_matrix(y_test, y_pred, labels=labels)

print("Labels:", labels)
print("Confusion Matrix:\n", cm)

sns.heatmap(
    cm,
    annot=True,
    fmt="g",
    cmap="Blues",
    ax=ax[0],
    xticklabels=labels,
    yticklabels=labels,
)
ax[0].set_xlabel("Predicted labels")
ax[0].set_ylabel("True labels")
ax[0].set_title("Confusion Matrix")

fpr, tpr, thresholds = roc_curve(
    y_test, clf.predict_proba(X_test_scaled)[:, 1], pos_label=clf.classes_[1]
)
roc_auc = auc(fpr, tpr)

ax[1].plot(fpr, tpr, color="darkgreen", label=f"ROC curve (area = {roc_auc:.2f})")
ax[1].plot([0, 1], [0, 1], color="navy", linestyle="--")
ax[1].set_xlim([0.0, 1.0])
ax[1].set_ylim([0.0, 1.05])
ax[1].set_xlabel("False Positive Rate")
ax[1].set_ylabel("True Positive Rate")
ax[1].set_title("ROC")
ax[1].legend(loc="lower right")

plt.tight_layout()
plt.show()
