"""Urine Test Strip Dashboard  —  run with:  streamlit run app.py"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import analysis as an

st.set_page_config(page_title="Urine Test Strip Dashboard", page_icon="🧪", layout="wide")

DEFAULT_FILE = Path(__file__).parent / "Urine_Test_Strip_Dataset_5000_Rows_15_Attributes.xlsx"
STATUS_COLORS = {
    "High": "background-color:#fde2e2;color:#9b1c1c",
    "Low": "background-color:#fff1d6;color:#8a5a00",
    "Positive": "background-color:#fde2e2;color:#9b1c1c",
    "Normal": "background-color:#e3f5e8;color:#1b6b3a",
    "Negative": "background-color:#e3f5e8;color:#1b6b3a",
}


@st.cache_data(show_spinner="Loading dataset…")
def load_cached(raw: bytes, name: str) -> pd.DataFrame:
    return an.load_data(BytesIO(raw), name)


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🧪 Urine Strip Dashboard")
    upload = st.file_uploader("Dataset (.xlsx or .csv)", type=["xlsx", "csv"])
    st.caption("Leave empty to use the bundled 5,000-row dataset.")
    with st.expander("Reference ranges (editable)"):
        ranges = st.data_editor(
            an.default_ranges(),
            hide_index=True,
            disabled=["Analyte"],
            column_config={
                "Low": st.column_config.NumberColumn("Low", format="%g"),
                "High": st.column_config.NumberColumn("High", format="%g"),
            },
            key="ranges",
        )
        st.caption(
            "Defaults are the first clearly positive reading on a typical strip chart. "
            "Leave a cell empty for no bound; adjust to your strip manufacturer's chart."
        )

if upload is not None:
    raw, name = upload.getvalue(), upload.name
elif DEFAULT_FILE.exists():
    raw, name = DEFAULT_FILE.read_bytes(), DEFAULT_FILE.name
else:
    st.info("Upload a dataset in the sidebar to get started.")
    st.stop()

try:
    df = load_cached(raw, name)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not read the dataset: {exc}")
    st.stop()

status = an.classify(df, ranges)
flags = an.abnormal_flags(status)
df = df.assign(Abnormal_Count=flags.sum(axis=1))
numeric_cols = [c for c in an.ANALYTES + an.SENSOR_COLS if c != "Nitrite"]

tab_overview, tab_explorer, tab_dist, tab_analyzer = st.tabs(
    ["📊 Overview", "🔎 Data explorer", "📈 Distributions", "🧾 Test analyzer"]
)

# ----------------------------------------------------------------- overview
with tab_overview:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tests", f"{len(df):,}")
    k2.metric("Nitrite positive", f"{(df['Nitrite'] == 1).mean():.1%}")
    k3.metric("≥ 1 abnormal parameter", f"{(df['Abnormal_Count'] > 0).mean():.1%}")
    k4.metric("Mean pH", f"{df['pH'].mean():.2f}")

    left, right = st.columns(2)
    rate = (flags.mean() * 100).rename(index=an.LABELS).sort_values()
    fig = px.bar(
        rate, orientation="h", labels={"value": "% of tests outside range", "index": ""},
        title="Abnormal rate by parameter",
    )
    fig.update_layout(showlegend=False)
    left.plotly_chart(fig)

    counts = df["Abnormal_Count"].value_counts().sort_index()
    fig = px.bar(
        x=counts.index, y=counts.values,
        labels={"x": "Abnormal parameters in one test", "y": "Tests"},
        title="How many parameters are flagged per test",
    )
    right.plotly_chart(fig)

    st.subheader("Summary statistics")
    st.dataframe(df[numeric_cols + ["Nitrite"]].describe().T.round(3))

# ----------------------------------------------------------------- explorer
with tab_explorer:
    c1, c2, c3 = st.columns([2, 1, 1])
    query = c1.text_input("Search Patient / Test ID", placeholder="e.g. P10042 or UT20042")
    nit = c2.selectbox("Nitrite", ["All", "Positive", "Negative"])
    min_abn = c3.slider("Min. abnormal parameters", 0, len(an.ANALYTES), 0)

    with st.expander("Range filters"):
        picked = st.multiselect("Parameters to filter on", numeric_cols)
        bounds = {}
        for col in picked:
            lo, hi = float(df[col].min()), float(df[col].max())
            if lo < hi:
                bounds[col] = st.slider(an.LABELS[col], lo, hi, (lo, hi))

    mask = pd.Series(True, index=df.index)
    if query:
        mask &= df["Patient_ID"].str.contains(query, case=False, na=False) | df["Test_ID"].str.contains(
            query, case=False, na=False
        )
    if nit != "All":
        mask &= df["Nitrite"] == (1 if nit == "Positive" else 0)
    mask &= df["Abnormal_Count"] >= min_abn
    for col, (lo, hi) in bounds.items():
        mask &= df[col].between(lo, hi)

    view = df[mask]
    st.caption(f"{len(view):,} of {len(df):,} tests match")
    st.dataframe(view, height=480)
    st.download_button(
        "⬇ Download filtered rows (CSV)",
        view.to_csv(index=False).encode(),
        file_name="filtered_urine_tests.csv",
        mime="text/csv",
    )

# ------------------------------------------------------------ distributions
with tab_dist:
    col = st.selectbox("Parameter", numeric_cols, format_func=lambda c: an.LABELS[c])
    o1, o2 = st.columns(2)
    nbins = o1.slider("Histogram bins", 10, 100, 40)
    trim = o2.checkbox("Hide extreme outliers (above 99th percentile)", value=True)

    data = df
    if trim:
        cap = df[col].quantile(0.99)
        data = df[df[col] <= cap]
        st.caption(f"{len(df) - len(data):,} extreme values hidden.")

    fig = px.histogram(data, x=col, nbins=nbins, title=f"Distribution of {an.LABELS[col]}")
    rng = ranges.set_index("Analyte")
    if col in rng.index:
        lo, hi = rng.at[col, "Low"], rng.at[col, "High"]
        fig.add_vrect(
            x0=lo if pd.notna(lo) else data[col].min(),
            x1=hi if pd.notna(hi) else data[col].max(),
            fillcolor="green", opacity=0.12, line_width=0,
            annotation_text="reference range", annotation_position="top left",
        )
    st.plotly_chart(fig)

    b1, b2 = st.columns(2)
    box = px.box(
        data.assign(Nitrite=data["Nitrite"].map({0: "Negative", 1: "Positive"})),
        x="Nitrite", y=col, color="Nitrite", title=f"{an.LABELS[col]} by nitrite result",
    )
    b1.plotly_chart(box)

    corr = df[numeric_cols + ["Nitrite"]].corr()
    heat = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        aspect="auto", title="Correlation matrix",
    )
    b2.plotly_chart(heat)

    st.subheader("Compare two parameters")
    s1, s2 = st.columns(2)
    xa = s1.selectbox("X axis", numeric_cols, index=0, format_func=lambda c: an.LABELS[c])
    ya = s2.selectbox("Y axis", numeric_cols, index=1, format_func=lambda c: an.LABELS[c])
    sample = df.sample(min(2000, len(df)), random_state=0)
    sc = px.scatter(
        sample.assign(Nitrite=sample["Nitrite"].map({0: "Negative", 1: "Positive"})),
        x=xa, y=ya, color="Nitrite", opacity=0.6,
        title="Random sample of up to 2,000 tests",
    )
    st.plotly_chart(sc)

# ----------------------------------------------------------------- analyzer
with tab_analyzer:
    mode = st.radio("Input", ["Pick a test from the dataset", "Enter values manually"], horizontal=True)

    if mode.startswith("Pick"):
        tid = st.selectbox("Test ID", df["Test_ID"])
        row = df.loc[df["Test_ID"] == tid].iloc[0]
        st.caption(f"Patient: {row['Patient_ID']}")
        values = {c: row[c] for c in an.ANALYTES}
    else:
        values = {}
        cols = st.columns(3)
        for i, c in enumerate(an.ANALYTES):
            with cols[i % 3]:
                if c == "Nitrite":
                    values[c] = 1 if st.selectbox("Nitrite", ["Negative", "Positive"]) == "Positive" else 0
                else:
                    step, fmt = an.INPUT_SPEC.get(c, (0.1, "%.2f"))
                    values[c] = st.number_input(
                        an.LABELS[c], min_value=0.0, value=float(df[c].median()), step=step, format=fmt
                    )

    sample_df = pd.DataFrame([values])
    result = an.interpret(sample_df, df, ranges)
    n_flag = int((~result["Status"].isin(an.NORMAL_STATES)).sum())

    m1, m2 = st.columns(2)
    m1.metric("Parameters outside range", f"{n_flag} / {len(result)}")
    m2.metric("Overall", "All within range" if n_flag == 0 else "Review flagged items")

    shown = result.drop(columns="Note")
    shown["Percentile"] = shown["Percentile"].map(lambda p: "—" if pd.isna(p) else f"{p:.0f}th")
    st.dataframe(shown.style.map(lambda v: STATUS_COLORS.get(v, ""), subset=["Status"]), hide_index=True)

    flagged = result[~result["Status"].isin(an.NORMAL_STATES)]
    if flagged.empty:
        st.success("All parameters are within the reference ranges.")
    else:
        for _, r in flagged.iterrows():
            st.warning(f"**{r['Parameter']} — {r['Status']}.** {r['Note']}")

    st.caption(
        "Screening aid only, not a diagnosis. Reference cut-offs are approximate and adjustable; "
        "results should be interpreted alongside clinical context."
    )
