# 🧪 Urine Test Strip Dashboard

An interactive dashboard built with **Streamlit** to explore and interpret urine test strip data. It loads a dataset of 5,000 tests, summarises it with charts, lets you filter and search the records, and flags each test result as low, normal or high against editable reference ranges.

> ⚠️ **Disclaimer:** This is an educational project. The data is synthetic and the reference ranges are approximate. It is a screening aid, **not a medical diagnosis tool**.

---

## Features

| Tab | What it does |
|---|---|
| **📊 Overview** | Key numbers (total tests, % nitrite positive, % with at least one abnormal parameter, mean pH), abnormal rate per parameter, and summary statistics |
| **🔎 Data explorer** | Search by Patient/Test ID, filter by nitrite, abnormal count and numeric ranges, and download the filtered rows as CSV |
| **📈 Distributions** | Histograms with the reference range shaded, box plots by nitrite result, correlation heatmap, and a scatter plot of any two parameters |
| **🧾 Test analyzer** | Pick a `Test_ID` from the dataset or enter values by hand, and get a Low / Normal / High result for each parameter with a short explanation |

The sidebar also lets you **upload your own `.xlsx` / `.csv`** (same columns) and **edit the reference ranges** live.

---

## Dataset

5,000 rows and 15 columns (one sheet, `Urine_Data`).

| Group | Columns |
|---|---|
| Identifiers | `Patient_ID`, `Test_ID` |
| Strip analytes | `Glucose_mg_dL`, `Protein_mg_dL`, `pH`, `Ketones_mg_dL`, `Blood_ery_uL`, `Bilirubin_mg_dL`, `Urobilinogen_mg_dL`, `Nitrite` (0/1), `Leucocytes_Leu_uL`, `Specific_Gravity` |
| Sensor readings | `LED_Brightness_pct`, `Reaction_Time_sec`, `RGB_Average` |

There are no missing values. There is no diagnosis or label column, so the project focuses on exploration and rule-based flagging rather than prediction.

---

## Tech stack

- **Python 3.11**
- **Streamlit** for the web interface
- **pandas / NumPy** for data handling
- **Plotly** for interactive charts
- **openpyxl** for reading `.xlsx` files

---

## Project structure

```
urine_dashboard/
├── app.py            # Streamlit interface (tabs, charts, widgets)
├── analysis.py       # Data loading and flagging logic (no Streamlit code)
├── requirements.txt  # Dependencies
├── README.md
└── Urine_Test_Strip_Dataset_5000_Rows_15_Attributes.xlsx
```

Keeping the logic in `analysis.py` separate from the interface in `app.py` makes the logic easy to test on its own.

---

## Getting started

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. (Optional) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python -m streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) and opens it in your browser.

> Run it with `streamlit run`, not by pressing the Run/Play button in your editor. Streamlit needs its own server to show the page.

---

## How it works

1. **Load:** `load_data()` reads the Excel/CSV file and checks that all 15 expected columns exist.
2. **Classify:** `classify()` compares each value with its reference range and labels it `Low`, `Normal` or `High`. Nitrite is binary, so it is labelled `Positive` or `Negative`.
3. **Count:** every test gets an `Abnormal_Count`, the number of parameters outside their range. This drives the Overview and Explorer tabs.
4. **Interpret:** `interpret()` builds the single-test report, with value, reference range, status, percentile within the dataset, and a short note.

### Default reference ranges

The defaults are the first clearly positive reading on a typical strip colour chart. Stricter laboratory limits flagged about 99% of this dataset, which made the flags meaningless. Edit them in the sidebar to match your own strip chart.

| Parameter | Low | High |
|---|---|---|
| Glucose (mg/dL) | – | 50 |
| Protein (mg/dL) | – | 30 |
| pH | 4.5 | 8.0 |
| Ketones (mg/dL) | – | 10 |
| Blood / Erythrocytes (/µL) | – | 10 |
| Bilirubin (mg/dL) | – | 0.5 |
| Urobilinogen (mg/dL) | 0.2 | 2.0 |
| Leucocytes (/µL) | – | 25 |
| Specific gravity | 1.005 | 1.030 |
| Nitrite | Negative expected | – |

---

## Limitations

- The data is synthetic, so patterns in it do not represent real patients.
- The reference ranges are approximate and vary between strip brands.
- The flags are simple threshold rules, with no machine-learning model.

## Possible improvements

- Train a classifier if labelled data (e.g. confirmed infection) becomes available
- Add outlier detection for sensor readings
- Export a PDF report for a single test

---

## Authors

- Your Name
- Teammate Names

## License

Add a license of your choice (for example MIT) before publishing.
