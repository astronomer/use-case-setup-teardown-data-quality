"""This script generates a synthetic dataset of rose characteristics for three varieties:
Damask Rose (Rosa damascena)
Tea Rose (Rosa odorata)
Moss Rose (Rosa centifolia)."""

import pandas as pd
import numpy as np

np.random.seed(42)
n_samples = 300


def digit_to_month(digit):
    if not (1 <= digit <= 12):
        raise ValueError("The digit must be between 1 and 12.")

    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    return months[digit - 1]


damask_petal = np.random.uniform(6, 9, n_samples)
damask_stem = np.random.uniform(25, 45, n_samples)
damask_leaf = np.random.uniform(4, 6, n_samples)
damask_bloom = np.full(n_samples, 6) + np.random.randint(-1, 2, n_samples)
tea_petal = np.random.uniform(7.5, 9.5, n_samples)
tea_stem = np.random.uniform(35, 50, n_samples)
tea_leaf = np.random.uniform(5, 7, n_samples)
tea_bloom = np.random.randint(4, 9, n_samples)
moss_petal = np.random.uniform(7, 10, n_samples)
moss_stem = np.random.uniform(30, 45, n_samples)
moss_leaf = np.random.uniform(4.5, 6.5, n_samples)
moss_bloom = np.random.randint(6, 9, n_samples)

data = {
    "index": np.arange(3 * n_samples),
    "petal_size_cm": np.concatenate([damask_petal, tea_petal, moss_petal]),
    "stem_length_cm": np.concatenate([damask_stem, tea_stem, moss_stem]),
    "leaf_size_cm": np.concatenate([damask_leaf, tea_leaf, moss_leaf]),
    "blooming_month": np.concatenate([damask_bloom, tea_bloom, moss_bloom]),
    "rose_type": np.concatenate(
        [["damask"] * n_samples, ["tea"] * n_samples, ["moss"] * n_samples]
    ),
}

df = pd.DataFrame(data)
numeric_columns = ["petal_size_cm", "stem_length_cm", "leaf_size_cm"]
df[numeric_columns] = df[numeric_columns].applymap(lambda x: round(x, 1))
df["blooming_month"] = df["blooming_month"].apply(digit_to_month)

df.to_csv("roses_raw.csv", index=False)
