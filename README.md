[README.md](https://github.com/user-attachments/files/31531170/README.md)
# National Electricity Grid Network Analysis, GridCare-Lite & ClinicCare-Lite

CS 112 — Computer Programming for CS | Final Course Project | Summer 2026 | Ashesi University

A three-part project combining data-science analysis of a synthetic West African electricity
grid with two lightweight applications built on top of it: **GridCare-Lite** (outage and
maintenance management for grid operators) and **ClinicCare-Lite** (administrative task and
review management for a clinic).

## Team

| Member | Role |
|---|---|
| Antipas Malual Mabeny | Network algorithms — shortest path, connectivity, centrality, N-1 contingency |
| Diamond Obrempong Owusu Sekyere | Advanced EDA — distributions, connectivity heatmap, capacity utilization |
| Niele Afia Nyamekye | GridCare-Lite & ClinicCare-Lite — application build, both workflows |
| Ethan Elom Koku Agbenu | Testing & report compilation |

## Repository Structure

```
.
├── data_science/
│   ├── generate_dataset.py        # seeded synthetic data generator
│   ├── utilities.csv              # 10 rows
│   ├── substations.csv            # 44 rows
│   ├── lines.csv                  # 55 rows
│   ├── network_analysis.py        # centrality, N-1 contingency (Antipas)
│   ├── eda.py                     # distributions, heatmap, capacity analysis (Diamond)
│   ├── merge_datasets.py          # integrates all three CSVs
│   ├── merged_lines.csv           # merge output
│   ├── n1_contingency_results.csv # N-1 contingency output (required by dashboard.py)
│   └── dashboard.py                # Streamlit dashboard (whole team)
│
├── GridCare-Lite/
│   ├── app.py                     # Flask app and routes
│   ├── workflow.py                # outage-to-resolution logic, complaints (Afia)
│   ├── reports_dashboard.py       # reports + role-access checks (Afia)
│   ├── templates/                 # login, dashboard, outages, reports, etc.
│   ├── static/styles.css
│   └── gridcare.db                # SQLite database (generated on first run)
│
├── ClinicCare-Lite/
│   ├── app.py                     # Flask app and routes
│   ├── user.py                    # User model, auth, password/ID validation
│   ├── health_task.py             # HealthTask, TaskSubmission models (Afia)
│   ├── analytics.py               # operational analytics (Afia)
│   ├── templates/                 # login, dashboards, tasks, messages, etc.
│   ├── static/styles.css
│   └── data/                      # users.json, tasks.json, submissions.json (generated)
│
├── tests/
│   └── test_week4.py              # 19 tests covering both apps (Ethan)
│
├── docs/
│   ├── CS112_DataScience_Report.docx   # 2-3 page data science report
│   └── CS112_Final_Presentation.pptx   # slide deck
│
├── requirements.txt
└── README.md
```

## Setup

1. **Clone the repository and create a virtual environment:**
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   python3 -m venv .venv
   source .venv/bin/activate        # on Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   If you hit a "permission denied" or "externally managed environment" error:
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

## Running the Data Science Component

Run these in order from inside `data_science/`:

```bash
python generate_dataset.py       # creates utilities.csv, substations.csv, lines.csv
python merge_datasets.py         # creates merged_lines.csv
python network_analysis.py       # creates n1_contingency_results.csv (required before the dashboard)
python eda.py                    # generates EDA charts
streamlit run dashboard.py       # opens the interactive dashboard in your browser
```

**Important:** `dashboard.py` reads `n1_contingency_results.csv`, so `network_analysis.py` must
be run at least once before the dashboard will load without a `FileNotFoundError`.

## Running GridCare-Lite

```bash
cd GridCare-Lite
python app.py
```
Opens at `http://127.0.0.1:5000`. First run creates `gridcare.db` automatically.

## Running ClinicCare-Lite

```bash
cd ClinicCare-Lite
python app.py
```
Opens at `http://127.0.0.1:5001`. First run needs an empty `data/users.json`,
`data/tasks.json`, and `data/submissions.json` (each containing just `{}`) if they don't
already exist.

## Running Tests

From the repository root:

```bash
pip install bcrypt --break-system-packages   # if not already installed
python -m unittest tests/test_week4.py -v
```

Expected result: **19/19 tests passing**, covering role-access violations, invalid status
transitions, duplicate records, unauthorised review access, unsupported/oversized file
uploads, and report accuracy across both apps.

## Sample Accounts

Test/demo accounts only — no real credentials are hard-coded in source. Seed your own via
each app's registration flow, or insert directly into `gridcare.db` / `data/users.json` for
a quick demo login before presenting.

## Project Scope Note

ClinicCare-Lite is strictly an **administrative and communication** system. It does not
diagnose patients, interpret symptoms, calculate risk, recommend treatment, or replace
clinical judgement — this boundary is a compulsory project requirement maintained throughout
the codebase.

## License

Academic project submitted for CS 112, Ashesi University. Not licensed for external use.
