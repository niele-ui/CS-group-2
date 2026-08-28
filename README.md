[README.md](https://github.com/user-attachments/files/31568091/README.md)
# National Electricity Grid Network Analysis, GridCare-Lite & ClinicCare-Lite

CS 112 — Computer Programming for CS | Final Course Project | Summer 2026 | Ashesi University

**Team:** [Team Name / Number — fill in]
**GitHub repository (public):** https://github.com/niele-ui/CS-group-2

## Team Members

| Name | Student ID |
|---|---|
| Antipas Malual Mabeny | [fill in] |
| Diamond Obrempong Owusu Sekyere | [fill in] |
| Niele Afia Nyamekye | [fill in] |
| Ethan Elom Koku Agbenu | [fill in] |

## What Each Component Does

**grid-analysis/** — Generates and analyzes a synthetic West African electricity grid
dataset (utilities, substations, transmission lines). Covers data cleaning, exploratory
data analysis, network graph construction, centrality analysis, and N-1 contingency
testing, ending in an interactive Streamlit dashboard.

**gridcare-lite/** — A Flask application for grid operators to log outages, assign
technicians via work orders, track customer complaints, and view operational reports,
enforcing role-based access across Admin, Engineer, Technician, and Customer Service
roles.

**clinic-care-lite/** — A Flask application for clinics to assign health-related
administrative tasks to patients, let patients submit files against those tasks, and
let clinicians review submissions. Strictly non-diagnostic — see the scope statement in
`docs/CS112_Technical_Report.docx`, Section 6.

## Repository Structure

```
.
├── grid-analysis/          # data generation, cleaning, EDA, network analysis, dashboard
├── gridcare-lite/           # Flask app: outage-to-resolution workflow
│   ├── app.py
│   ├── workflow.py
│   ├── reports_dashboard.py
│   ├── seed_gridcare.py
│   ├── templates/
│   └── static/
├── clinic-care-lite/        # Flask app: task-to-review workflow
│   ├── app.py
│   ├── user.py
│   ├── health_task.py
│   ├── analytics.py
│   ├── seed_cliniccare.py
│   ├── templates/
│   ├── static/
│   └── data/
├── tests/
│   └── test_week4.py        # 19 tests covering both apps
├── docs/
│   ├── CS112_Technical_Report.docx
│   └── CS112_DataScience_Report.docx
├── slides/
│   └── CS112_Final_Presentation.pptx
├── video/                   # demo video goes here
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone https://github.com/niele-ui/CS-group-2.git
cd CS-group-2
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
If you hit a "permission denied" or "externally managed environment" error:
```bash
pip install -r requirements.txt --break-system-packages
```

Copy `.env.example` to `.env` and fill in real values before deploying anywhere beyond
local testing:
```bash
cp .env.example .env
```

## Running the Data Science Component

From inside `grid-analysis/`, run in order:
```bash
python generate_dataset.py       # creates utilities.csv, substations.csv, lines.csv
python merge_datasets.py         # creates merged_lines.csv
python network_analysis.py       # creates n1_contingency_results.csv — required before the dashboard
python eda.py                    # generates EDA charts
streamlit run dashboard.py       # opens the interactive dashboard
```
`dashboard.py` reads `n1_contingency_results.csv`, so `network_analysis.py` must run at
least once first or the dashboard will throw a `FileNotFoundError`.

## Running GridCare-Lite

```bash
cd gridcare-lite
python seed_gridcare.py    # creates and seeds gridcare.db with demo data
python app.py
```
Opens at `http://127.0.0.1:5000`.

**Demo login (Admin):** username `admin_afia`, password `demo_hash_1`
*(This is a plaintext demo placeholder, not a real hashed password — see Known
Limitations below.)*

## Running ClinicCare-Lite

```bash
cd clinic-care-lite
python seed_cliniccare.py  # creates and seeds data/*.json with demo accounts
python app.py
```
Opens at `http://127.0.0.1:5001`.

**Demo login (Clinician):** ID `10000000`, password `Cl1n!c2026`
**Demo login (Patient):** ID `20242026`, password `P@tient2026`

## Running Tests

From the repository root:
```bash
pip install bcrypt --break-system-packages   # if not already installed
python -m unittest tests/test_week4.py -v
```
Expected result: **19/19 tests passing.**

## Reproducibility

The dataset generator is explicitly seeded (`random.seed(42)`) and this seed has not
been changed at any point in the project. Every run, on any machine, produces the same
utilities, substations, and lines data, which is what makes the EDA and network analysis
findings in `docs/CS112_Technical_Report.docx` independently verifiable.

## Known Limitations

- **GridCare-Lite login** compares plaintext demo passwords directly rather than hashed
  ones. Real bcrypt hashing is implemented in `workflow.py`'s design but not yet wired
  into the seeded demo accounts — this is a known gap, not an oversight.
- **ClinicCare-Lite messaging** (`/messages` route) renders an empty thread; message
  storage and sending was never implemented in this build.
- **ClinicCare-Lite review turnaround time** cannot be computed because the data model
  does not separately timestamp when a review occurs versus when a submission was made.
- **GridCare-Lite** does not validate that a technician ID exists before assigning a work
  order to it — an assignment to a nonexistent technician currently succeeds silently.

## Project Scope Note

ClinicCare-Lite is strictly an **administrative and communication** system. It does not
diagnose, interpret symptoms, calculate risk, or recommend treatment — this boundary is
a compulsory project requirement maintained throughout the codebase.

## License

Academic project submitted for CS 112, Ashesi University. Not licensed for external use.
