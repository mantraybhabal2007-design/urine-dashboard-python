# Urine Test Strip Dashboard (Streamlit)

    pip install -r requirements.txt
    streamlit run app.py

Keep `app.py`, `analysis.py` and the .xlsx in the same folder. You can also upload any .xlsx/.csv
with the same 15 columns from the sidebar.

Tabs: Overview (KPIs, abnormal rates) · Data explorer (filters, search, CSV export) ·
Distributions (histograms with reference band, box plots, correlation, scatter) ·
Test analyzer (pick a Test_ID or type values; flags each analyte against editable reference ranges).

Screening aid only, not a diagnosis.
