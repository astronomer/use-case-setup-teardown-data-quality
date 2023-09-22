"""
## Use the Astro Python SDK to ingest a relational table and classify roses

This DAG uses the @aql.dataframe decorator to ingest a relational table from Postgres as a
pandas DataFrame in a simple feature engineering, train, plot pattern.
See https://github.com/astronomer/use-case-setup-teardown-data-quality for the 
full example repo including the dataset.
"""

from airflow import Dataset
from airflow.decorators import dag, task
from airflow.models.baseoperator import chain
from pendulum import datetime
from astro import sql as aql
from astro.files import File
from astro.sql.table import Table, Metadata
import pandas as pd

POSTGRES_CONN_ID = "postgres_default"
TABLE_NAME = "roses"
SCHEMA_NAME = "public"
CSV_PATH = "/include/roses_raw.csv"


@aql.dataframe
def feature_engineering(df: pd.DataFrame):
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    # converting column names to str for the Scaler
    df.columns = [str(col).replace("'", "").replace('"', "") for col in df.columns]

    df = pd.get_dummies(df, columns=["blooming_month"], drop_first=True)
    X = df.drop(["rose_type", "index"], axis=1)

    y = df["rose_type"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()

    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=X_test.columns, index=X_test.index
    )

    train_data = pd.concat([X_train_scaled, y_train], axis=1)
    test_data = pd.concat([X_test_scaled, y_test], axis=1)

    return {
        "train_data": train_data,
        "test_data": test_data,
    }


@task
def train_model(input_data):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        classification_report,
        roc_curve,
    )

    train_data = input_data["train_data"]
    test_data = input_data["test_data"]

    X_train = train_data.drop(["rose_type"], axis=1)
    y_train = train_data["rose_type"]
    X_test = test_data.drop(["rose_type"], axis=1)
    y_test = test_data["rose_type"]

    clf = RandomForestClassifier(n_estimators=1000, random_state=23)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    fpr, tpr, thresholds = roc_curve(
        y_test, clf.predict_proba(X_test)[:, 1], pos_label=clf.classes_[1]
    )

    print("Accuracy:", acc)
    print("F1-Score:", f1)
    print(classification_report(y_test, y_pred))

    labels_df = pd.DataFrame(clf.classes_)
    true_vs_pred = pd.concat(
        [y_test, pd.Series(y_pred, index=y_test.index)],
        axis=1,
    )
    true_vs_pred.columns = ["y_test", "y_pred"]
    roc_df = pd.DataFrame({"fpr": fpr, "tpr": tpr, "thresholds": thresholds})

    return {
        "true_vs_pred": true_vs_pred,
        "labels_df": labels_df,
        "accuracy": acc,
        "f1_score": f1,
        "roc_df": roc_df,
    }


@task
def plot_results(input):
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import (
        confusion_matrix,
        auc,
    )

    true_vs_pred = input["true_vs_pred"]
    labels_df = input["labels_df"]
    acc = input["accuracy"]
    f1 = input["f1_score"]
    tpr = input["roc_df"]["tpr"]
    fpr = input["roc_df"]["fpr"]

    y_test = true_vs_pred["y_test"]
    y_pred = true_vs_pred["y_pred"]

    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    labels = labels_df.iloc[:, 0].to_list()
    cm = confusion_matrix(y_test, y_pred, labels=labels)

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

    roc_auc = auc(fpr, tpr)
    label_text = (
        f"ROC curve (area = {roc_auc:.2f})"
        f"\nAccuracy = {acc:.2f}"
        f"\nF1 Score = {f1:.2f}"
    )

    ax[1].plot(fpr, tpr, color="darkgreen", label=label_text)
    ax[1].plot([0, 1], [0, 1], color="navy", linestyle="--")
    ax[1].set_xlim([0.0, 1.0])
    ax[1].set_ylim([0.0, 1.05])
    ax[1].set_xlabel("False Positive Rate")
    ax[1].set_ylabel("True Positive Rate")
    ax[1].set_title("ROC")
    ax[1].legend(loc="lower left", bbox_to_anchor=(0.10, 0.01))

    img = plt.imread("include/rosa_centifolia.png")
    ax_ratio = ax[1].get_data_ratio()
    img_ratio = img.shape[1] / img.shape[0]
    width = 0.2
    height = width * 1.3 / (img_ratio * ax_ratio)
    x_start = 0.78
    y_start = 0
    extent = [x_start, x_start + width, y_start, y_start + height]
    ax[1].imshow(img, aspect="auto", extent=extent, zorder=1)

    plt.tight_layout()
    plt.savefig("include/results.png")


@dag(
    start_date=datetime(2023, 8, 1),
    schedule=[Dataset(f"postgres://{SCHEMA_NAME}/{TABLE_NAME}")],
    catchup=False,
    tags=["classification"],
)
def rose_classification():
    roses_features = feature_engineering(
        df=Table(
            conn_id=POSTGRES_CONN_ID,
            name=TABLE_NAME,
            metadata=Metadata(
                schema=SCHEMA_NAME,
            ),
        )
    )

    plot_results(train_model(roses_features))

    aql.cleanup()


rose_classification()
