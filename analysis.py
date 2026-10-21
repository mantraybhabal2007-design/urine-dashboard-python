"""Data loading and interpretation logic for the urine test-strip dashboard.

Kept free of Streamlit imports so it can be unit-tested on its own.
"""
from __future__ import annotations

from typing import IO

import numpy as np
import pandas as pd

ID_COLS = ["Patient_ID", "Test_ID"]
ANALYTES = [
    "Glucose_mg_dL",
    "Protein_mg_dL",
    "pH",
    "Ketones_mg_dL",
    "Blood_ery_uL",
    "Bilirubin_mg_dL",
    "Urobilinogen_mg_dL",
    "Nitrite",
    "Leucocytes_Leu_uL",
    "Specific_Gravity",
]
SENSOR_COLS = ["LED_Brightness_pct", "Reaction_Time_sec", "RGB_Average"]
REQUIRED = ID_COLS + ANALYTES + SENSOR_COLS

LABELS = {
    "Glucose_mg_dL": "Glucose (mg/dL)",
    "Protein_mg_dL": "Protein (mg/dL)",
    "pH": "pH",
    "Ketones_mg_dL": "Ketones (mg/dL)",
    "Blood_ery_uL": "Blood / Erythrocytes (/µL)",
    "Bilirubin_mg_dL": "Bilirubin (mg/dL)",
    "Urobilinogen_mg_dL": "Urobilinogen (mg/dL)",
    "Nitrite": "Nitrite",
    "Leucocytes_Leu_uL": "Leucocytes (/µL)",
    "Specific_Gravity": "Specific gravity",
    "LED_Brightness_pct": "LED brightness (%)",
    "Reaction_Time_sec": "Reaction time (s)",
    "RGB_Average": "RGB average",
}

# (step, number format) for manual entry widgets; decimals for display
INPUT_SPEC = {"pH": (0.1, "%.2f"), "Specific_Gravity": (0.001, "%.3f")}
DECIMALS = {"Specific_Gravity": 3, "pH": 2}

# Default cut-offs = the first clearly positive reading on a typical strip colour chart
# (e.g. glucose 50, protein 30, leucocytes 25), because stricter "lab normal" limits flag
# ~99% of this dataset. NaN = no bound on that side. Editable in the UI, as every strip
# brand has its own chart.
_DEFAULT_RANGES = [
    ("Glucose_mg_dL", np.nan, 50.0),
    ("Protein_mg_dL", np.nan, 30.0),
    ("pH", 4.5, 8.0),
    ("Ketones_mg_dL", np.nan, 10.0),
    ("Blood_ery_uL", np.nan, 10.0),
    ("Bilirubin_mg_dL", np.nan, 0.5),
    ("Urobilinogen_mg_dL", 0.2, 2.0),
    ("Leucocytes_Leu_uL", np.nan, 25.0),
    ("Specific_Gravity", 1.005, 1.030),
]

NOTES = {
    ("Glucose_mg_dL", "High"): "Glucose in urine can follow high blood sugar or a very sugary meal; worth confirming.",
    ("Protein_mg_dL", "High"): "Protein can be transient (exercise, fever) or relate to kidney function; repeat if persistent.",
    ("pH", "Low"): "Acidic urine can reflect diet, fasting or metabolic factors.",
    ("pH", "High"): "Alkaline urine can reflect diet, or sometimes a urinary infection.",
    ("Ketones_mg_dL", "High"): "Ketones appear with fasting, low-carbohydrate diets or poorly controlled diabetes.",
    ("Blood_ery_uL", "High"): "Red cells in urine have many possible causes (infection, stones, other); follow-up is advised if repeated.",
    ("Bilirubin_mg_dL", "High"): "Bilirubin can point to liver or bile-duct issues.",
    ("Urobilinogen_mg_dL", "High"): "Raised urobilinogen can relate to liver function or increased red-cell breakdown.",
    ("Urobilinogen_mg_dL", "Low"): "Low urobilinogen can occur with reduced bile flow or some medications.",
    ("Nitrite", "Positive"): "Nitrite is often associated with bacterial urinary infection.",
    ("Leucocytes_Leu_uL", "High"): "White cells suggest inflammation or infection of the urinary tract.",
    ("Specific_Gravity", "Low"): "Dilute urine — often high fluid intake.",
    ("Specific_Gravity", "High"): "Concentrated urine — often dehydration.",
}

NORMAL_STATES = {"Normal", "Negative"}


def load_data(source: IO[bytes], name: str) -> pd.DataFrame:
    """Read an .xlsx/.csv and check it has the expected columns."""
    df = pd.read_csv(source) if name.lower().endswith(".csv") else pd.read_excel(source)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("Missing expected column(s): " + ", ".join(missing))
    return df


def default_ranges() -> pd.DataFrame:
    return pd.DataFrame(_DEFAULT_RANGES, columns=["Analyte", "Low", "High"])


def classify(df: pd.DataFrame, ranges: pd.DataFrame) -> pd.DataFrame:
    """Per-row status for every analyte: Low / Normal / High (Positive / Negative for nitrite)."""
    out = pd.DataFrame(index=df.index)
    for _, r in ranges.iterrows():
        col = r["Analyte"]
        if col not in df.columns:
            continue
        s = pd.Series("Normal", index=df.index, dtype=object)
        if pd.notna(r["Low"]):
            s[df[col] < r["Low"]] = "Low"
        if pd.notna(r["High"]):
            s[df[col] > r["High"]] = "High"
        out[col] = s
    out["Nitrite"] = np.where(df["Nitrite"] == 1, "Positive", "Negative")
    return out[[c for c in ANALYTES if c in out.columns]]


def abnormal_flags(status: pd.DataFrame) -> pd.DataFrame:
    return ~status.isin(NORMAL_STATES)


def format_range(low, high) -> str:
    if pd.notna(low) and pd.notna(high):
        return f"{low:g} – {high:g}"
    if pd.notna(high):
        return f"≤ {high:g}"
    if pd.notna(low):
        return f"≥ {low:g}"
    return "—"


def format_value(col: str, v: float) -> str:
    if col == "Nitrite":
        return "Positive" if v == 1 else "Negative"
    return f"{v:.{DECIMALS.get(col, 2)}f}"


def interpret(sample: pd.DataFrame, population: pd.DataFrame, ranges: pd.DataFrame) -> pd.DataFrame:
    """Table for a single test: value, reference range, status, percentile in the dataset, note."""
    status = classify(sample, ranges).iloc[0]
    rng = ranges.set_index("Analyte")
    rows = []
    for col in ANALYTES:
        v = sample[col].iloc[0]
        st_ = status[col]
        if col == "Nitrite":
            ref = "Negative"
            pct = np.nan
        else:
            ref = format_range(rng.at[col, "Low"], rng.at[col, "High"]) if col in rng.index else "—"
            pct = float((population[col] < v).mean() * 100)
        rows.append(
            {
                "Parameter": LABELS[col],
                "Value": format_value(col, v),
                "Reference": ref,
                "Status": st_,
                "Percentile": pct,
                "Note": NOTES.get((col, st_), ""),
            }
        )
    return pd.DataFrame(rows)
