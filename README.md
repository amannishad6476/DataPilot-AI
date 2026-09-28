# DATA PILOT AI
> **"From Natural Language to Actionable Data."**

An autonomous, AI-powered Data Intelligence Platform that dynamically understands natural-language data collection requests, constructs custom Directed Acyclic Graph (DAG) extraction workflows, visualizes them interactively, executes them with full RFC validation and fuzzy similarity deduplication, and delivers actionable datasets with 100% source evidence traceability.

---

## 🌟 Hackathon Key Differentiators

Unlike traditional scrapers that rely on hardcoded keyword-to-script mappings or static workflows pretending to be AI, **DATA PILOT AI** features:

1. **Genuinely Dynamic AI DAG Planner**:
   - The LLM dynamically analyzes the user's domain, requested fields, criteria, and constraints.
   - It synthesizes a unique, multi-stage Directed Acyclic Graph (`steps`, `depends_on`, `action`, `target_fields`) customized to the request.
   - Works with OpenAI, Google Gemini, or the offline-capable **Dynamic Semantic Planner** with zero configuration required.

2. **Similarity-Based Deduplication (Beyond Exact Matching)**:
   - Evaluates canonical root web domains (e.g. `tcs.com` vs `www.tcs.com/careers`).
   - Computes Jaro-Winkler string similarity and token Jaccard overlap on entity names (e.g. `Tata Consultancy Services Ltd` vs `Tata Consultancy Services (Lucknow Office)`).
   - Merges complementary attributes so the final record has the richest available contact data.

3. **Multi-Stage RFC Data Validation & Integrity Scoring**:
   - Validates RFC 5322 email syntax, E.164 phone digit criteria, and accessible HTTP/HTTPS URL formats.
   - Calculates a per-record confidence score (e.g., 98% verified) and flags issues transparently for review.

4. **100% Traceability & Citation Auditing**:
   - Every cell links directly to its verified public source URL.
   - Captures original text snippets and collection timestamps in the interactive **Evidence Drawer**.

5. **Clean Architectural Separation & Automation Ready**:
   - Complete decoupling between Planning, Engine, Processing, and Storage.
   - Built to easily connect **n8n execution engines** and real permitted search APIs.

---

## 🏗️ Architecture & Layer Separation

```
DATA PILOT AI
├── 1. Prompt Understanding      (FastAPI Natural Language Ingestion)
├── 2. Workflow Planning         (LLM Planner: OpenAI / Gemini / Dynamic Semantic Engine)
├── 3. Workflow Validation       (Strict Pydantic JSON Schema DAG Verification)
├── 4. Workflow Visualization    (Next.js + React Flow @xyflow/react Interactive DAG)
├── 5. Workflow Execution        (Pluggable BaseWorkflowExecutor: Demo Sandbox + Real Engine)
├── 6. Data Processing           (DataNormalizer: canonical URLs, cleaned phones, emails)
├── 7. Integrity Validation      (DataValidator: RFC email, phone format, URL reachability)
├── 8. Similarity Deduplication  (SimilarityDeduplicator: Jaro-Winkler, Levenshtein, Domain)
├── 9. Evidence & Traceability   (EvidenceRecord: public source URL, snippet proof, confidence)
├── 10. Dataset Management       (DatasetService: search, validity filter, dynamic sorting)
└── 11. Workflow History         (SQLAlchemy Models: archive, inspect, and one-click rerun)
```

---

## 💻 Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router, Turbopack)
- **Language**: TypeScript (Strict Mode)
- **Styling**: Tailwind CSS v4 (Dark B2B Intelligence theme)
- **Workflow Visualization**: React Flow (`@xyflow/react`)
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Validation**: Pydantic v2 & Pydantic-Settings
- **ORM / Database**: SQLAlchemy 2.0 with SQLite (Zero-config local) & PostgreSQL-ready schema
- **HTTP Client**: HTTPX (Asynchronous API querying)
- **Testing**: Pytest & Pytest-Asyncio

---

## 🚀 Quickstart Guide (Run Locally)

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed

---

### Step 1: Start the FastAPI Backend

1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. (Optional) Configure environment variables:
   Copy `.env.example` to `.env` if you want to connect external LLM providers:
   ```bash
   cp .env.example .env
   ```
   *Note: If no API keys are provided, the platform automatically runs using the high-intelligence **Dynamic Semantic Planner** with zero setup!*

4. Run the FastAPI server:
   ```bash
   python run.py
   ```
   *The backend will start at `http://localhost:8000`. Interactive Swagger API docs are available at `http://localhost:8000/docs`.*

---

### Step 2: Start the Next.js Frontend

1. Open a second terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and visit:
   ```
   http://localhost:3000
   ```

---

## 🧪 Running Automated Tests

To run the backend test suite verifying the dynamic planner, similarity deduplication, validation, and full end-to-end API lifecycle:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests -v
```

All 5 test suites pass cleanly:
- `test_health_check`
- `test_e2e_workflow_lifecycle`
- `test_similarity_deduplication`
- `test_dynamic_sponsor_planner`
- `test_dynamic_job_planner`

To run the frontend TypeScript build check:
```bash
cd frontend
npm run build
```

---

## 🎯 Demo Walkthrough: College Fest Sponsor Intelligence

1. **Submit Request**:
   On the landing page, select the preset prompt:
   > *"Find 30 potential sponsors for a college technical fest in Lucknow. Collect company name, industry, website, public business email, phone, location and source. Remove duplicates and validate the results."*

2. **Inspect Generated DAG**:
   Click **"Generate Workflow"**. The platform decomposes the request into an interactive DAG in React Flow:
   - `Request Ingestion` &rarr; `Dynamic Source Planner` &rarr; `Public Source Discovery` &rarr; `Primary Entity Extraction` &rarr; `Contact Enrichment` &rarr; `Data Normalization` &rarr; `RFC Validation` &rarr; `Similarity Deduplication` &rarr; `Evidence Merge` &rarr; `Dataset Delivery`
   - Click any node to view its parameters, dependencies, and target fields in the **Step Inspector Drawer**.

3. **Live Execution**:
   Click **"Run Workflow"**. Watch the nodes transition in real time:
   `Pending` &rarr; `Running (Pulsing Glow)` &rarr; `Completed (Green Check)`.
   Observe live counters:
   - Extracted: 33 raw candidate records
   - Merged: 3 near-duplicates (demonstrating fuzzy Levenshtein & domain matching)
   - Final: 30 verified sponsor records

4. **Explore Dataset & Citations**:
   - Filter between **"All Records"**, **"Verified Valid"**, and **"Needs Review"**.
   - Sort columns or search across companies (e.g. `fintech`, `lucknow`, `tcs`).
   - Click any row to open the **Evidence & Audit Trail Drawer**, displaying the exact source URL, snippet proof, and confidence score.
   - Click **"Export Dataset"** to download as CSV or JSON.

5. **History & Rerun**:
   Navigate to `/history` to review previous workflows, view past datasets, or trigger instant reruns.

---

## 🔒 Data Safety & Compliance
- Complies strictly with public web access standards and `robots.txt`.
- No login bypasses, CAPTCHA workarounds, or private data scraping.
- Enforces public business endpoints only.
