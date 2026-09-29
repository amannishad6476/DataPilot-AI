# DATA PILOT AI
> **"From Natural Language to Actionable Data."**

An autonomous, enterprise-grade AI Data Intelligence Platform that translates natural language data collection requests into dynamic Directed Acyclic Graph (DAG) pipelines, executes them across permitted source connectors and automation engines, validates data integrity with RFC standards, deduplicates entities via fuzzy similarity matching, and delivers actionable datasets backed by 100% verifiable source evidence.

---

## 🌟 Hackathon Key Differentiators

Unlike traditional scrapers that rely on hardcoded keyword-to-script mappings or static mock workflows, **DATA PILOT AI** provides:

1. **Genuinely Dynamic AI DAG Planner**:
   - The LLM dynamically analyzes the domain, criteria, constraints, and requested schema.
   - Decomposes requests into a typed, dependency-graphed DAG (`steps`, `depends_on`, `action`, `target_fields`).
   - Formulates explainable **AI Planning Directives & Rationale** displayed directly on the DAG canvas.
   - Functions with OpenAI (`gpt-4o`), Google Gemini (`gemini-2.5-flash`), or the offline-capable **Dynamic Semantic Planner** with zero configuration required.

2. **Permitted Source Connector Registry & SSRF Firewall**:
   - Strictly prevents arbitrary, uncontrolled external requests.
   - All executions pass through the **ConnectorRegistry** (`BaseSourceConnector`) enforcing domain whitelists, rate limits, robots.txt compliance, and an egress SSRF firewall blocking private subnets (RFC 1918), loopback, link-local, and cloud metadata (`169.254.169.254`).
   - Built-in connectors:
     - `PublicWebPageConnector`: Live HTTP fetch, HTML parsing, JSON-LD microdata, and contact extraction.
     - `JsonFeedConnector`: Public REST API and open-data catalog ingestion.
     - `N8nWebhookConnector`: Multi-app workflow dispatch and exportable n8n workflow template.

3. **Three Explicit Execution Modes**:
   - `DEMO SANDBOX`: Deterministic local simulation demonstrating full normalization, validation, and deduplication without external network dependencies.
   - `REAL CONNECTOR`: Live HTTP extraction against permitted public web portals with resilient fallback protection.
   - `N8N AUTOMATION`: Dispatches parameters to an external n8n self-hosted or cloud webhook workflow.

4. **Self-Healing Fallback & Audit Stream**:
   - If an external source encounters timeouts, DNS resolution errors, or HTTP failures, the engine activates resilient fallback mechanisms, preserving partial data and logging audit notices.
   - Emits a real-time `TimelineEvent` audit stream tracking progression, levels, and durations.
   - Supports graceful user cancellation (`POST /api/runs/{run_id}/cancel`).

5. **Multi-Stage RFC Data Validation & Normalization Audit**:
   - Validates RFC 5322 email syntax, E.164 phone digit formats, and accessible HTTP/HTTPS URL protocols.
   - Granular field-level statuses: `VALID`, `INVALID`, `MISSING`, or `NEEDS_REVIEW`.
   - Detailed normalization audit trail tracks transformations applied to each field (e.g. `added_https_scheme`, `e164_standardized`, `stripped_tracking_parameters`).

6. **Similarity-Based Deduplication (Beyond Exact Matching)**:
   - Canonical root web domain extraction (e.g. `tcs.com` vs `www.tcs.com/careers`).
   - Computes Jaro-Winkler string similarity and token Jaccard overlap on entity names.
   - Merges complementary attributes so the final consolidated record retains the richest contact data.

7. **Data Quality & Mathematical Confidence Analytics**:
   - Real, calculated metrics (zero fabricated statistics):
     - Valid Pass Rate (`%`)
     - Evidence Coverage (`%`)
     - Deduplication Reduction Yield (`%`)
     - Average Mathematical Confidence Score
     - Confidence Breakdown (`HIGH`, `MEDIUM`, `LOW` distributions)
     - Flagged issues identified and cleaned

8. **Run History, Non-Destructive Re-run & Side-by-Side Comparison**:
   - Complete execution archive with per-run telemetry and status tracking.
   - Non-destructive re-runs spawn fresh run instances with unique UUIDs.
   - Select any two runs to perform side-by-side comparative analysis: record deltas, confidence shifts, and entity drift (new entities, persistent entities, absent entities).

9. **Source Connectors & Gateway Health Dashboard**:
   - Dedicated health monitoring dashboard (`/connectors`) displaying total requests, success rates, average latency, and live ping testing.

10. **Enterprise Hardening & Production Reliability**:
    - **AI Safety & Policy Engine Boundary**: Treats LLMs as untrusted planners, statically validating DAG acyclicity, allowlisting execution actions, and rejecting SSRF URLs or prompt injection payloads.
    - **Per-Connector Circuit Breaker**: State-machine resilience (`CLOSED` / `OPEN` / `HALF_OPEN`) preventing thread starvation on failing external endpoints.
    - **Multi-Tenancy & RBAC**: Complete tenant isolation with role hierarchy (`OWNER` > `ADMIN` > `MEMBER` > `VIEWER`) and seamless zero-config fallback for local development.
    - **Memory-Efficient Streaming Exports**: Low-footprint chunked CSV and JSON stream generation for high-volume datasets.
    - **Self-Healing SQLite Schema Auto-Migration**: Dynamically ensures schema columns exist on startup without manual SQL scripts or data wipes.

---

## 🏗️ Architecture & Pipeline Flow

```
User Prompt (Natural Language)
       ↓
Dynamic AI Planner (Intent, Schema, Validation & Deduplication Reasoning)
       ↓
DAG Workflow Visualizer (@xyflow/react Interactive Graph)
       ↓
Source Connector Execution (DEMO SANDBOX | REAL CONNECTOR | N8N AUTOMATION)
       ↓
Raw Data Collection (HTML / JSON / Webhook)
       ↓
Normalization & Audit Logging (Canonical URLs, Cleaned Phones, Emails)
       ↓
RFC & Format Validation (Field-level VALID / INVALID / MISSING status)
       ↓
Fuzzy Similarity Deduplication (Jaro-Winkler, Levenshtein, Domain Key)
       ↓
Evidence Lineage & Citation Binding (100% Traceable Source URLs & Quotes)
       ↓
Actionable Dataset Table (Column Picker, Confidence Tabs, CSV/JSON Export)
       ↓
Analytics & Comparison Hub (Run Deltas, Entity Drift, Quality Metrics)
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
- **ORM / Database**: SQLAlchemy 2.0 with SQLite (Zero-config local) & PostgreSQL-ready models
- **Connectors**: HTTPX (Asynchronous HTTP/REST & Webhook querying)
- **Testing**: Pytest & Pytest-Asyncio

---

## 🚀 Quickstart Guide (Run Locally)

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed

---

### Step 1: Start the FastAPI Backend

1. Navigate to `backend/`:
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
   *Note: If no API keys are provided, the platform automatically runs using the built-in **Dynamic Semantic Planner** with zero setup!*

4. Run the FastAPI server:
   ```bash
   python run.py
   ```
   *The backend will start at `http://localhost:8000`. Interactive Swagger API docs are available at `http://localhost:8000/docs`.*

---

### Step 2: Start the Next.js Frontend

1. In a second terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

---

## 🧪 Automated Test Verification

To run the complete production backend test suite (37 tests across 12 test modules):

```powershell
$env:SQLALCHEMY_CYTHON="0"; .\backend\venv\Scripts\python.exe -m pytest -v
```

All 37 test suites pass cleanly with isolated fixtures:
- `test_health_check` & `test_e2e_workflow_lifecycle` (FastAPI test client)
- `test_policy_engine` (Plan validation, DAG cycle detection, unapproved actions, SSRF firewall, code injection filtering)
- `test_connectors_resilience` (Circuit breaker state machine CLOSED -> OPEN -> HALF_OPEN, SSRF IP/domain firewall)
- `test_auth_multitenant` (Role-based access control, tenant isolation, Bearer & API key authentication)
- `test_deduplicator_history` (Deterministic matching, fuzzy Jaro-Winkler/Jaccard, non-destructive merge history)
- `test_export_streaming` (Memory-efficient streaming chunk generators for CSV and JSON)
- `test_dag_orchestrator` (Topological waves, sibling concurrency with asyncio.gather, failure cascade isolation)
- `test_connectors` & `test_phase3` (SSRF prevention, live metadata extraction, n8n template generation, run comparison)
- `test_planner` & `test_real_executor` (Reasoning synthesis, resilient execution with fallback recovery)

To run the frontend production build:
```bash
cd frontend
npm run build
```

---

## 🎯 3-Minute Judge Demo Script

### 1. The Challenge (0:00 - 0:30)
- *"Organizations frequently need custom web data—leads, sponsors, market data. Traditional tools either require brittle custom scrapers or offer static mock dashboards with no real validation."*
- Open `http://localhost:3000` (DataPilot AI).

### 2. Natural Language to Dynamic DAG (0:30 - 1:15)
- Click the first example preset: *"Find 30 potential sponsors for a college technical fest in Lucknow. Collect company name, industry, website, public business email, phone, location and source. Remove duplicates and validate the results."*
- Click **"Generate Workflow"**.
- Point out the **AI Planning Rationale** card explaining the domain analysis, schema decisions, RFC rules, and deduplication keys.
- Explore the interactive React Flow DAG: click nodes to view step dependencies and field mappings in the inspector.

### 3. Execution & Resilient Fallback (1:15 - 2:00)
- Highlight the 3 execution modes: `DEMO SANDBOX`, `REAL CONNECTOR`, `N8N AUTOMATION`.
- Select `DEMO SANDBOX` (or `REAL CONNECTOR`), click **"Run Workflow"**.
- Watch the live execution progression, state changes, and live **Audit Trail Timeline Stream**.
- Show the graceful **Cancel** capability and resilient fallback handling.

### 4. Mathematical Quality & Evidence Drawer (2:00 - 2:40)
- Once execution completes, navigate to the **Intelligence Dataset** view (`/dataset/[id]`).
- Show the **Data Quality & Mathematical Confidence Analytics** card: Valid pass rate, evidence coverage, deduplication yield, and confidence breakdown.
- Demonstrate table filtering: switch confidence tabs (`HIGH`, `MEDIUM`, `LOW`), filter columns with the **Column Picker**, and sort.
- Click any row to open the **Evidence & Audit Trail Drawer**:
  - Show the per-field validation badges (`VALID`, `INVALID`, `MISSING`).
  - Point to the normalization audit tags (e.g. `added_https_scheme`, `e164_standardized`).
  - Click the direct source link with citation quotes proving zero fabricated data.
- Demonstrate CSV/JSON export.

### 5. Historical Comparison & Source Health (2:40 - 3:00)
- Navigate to **Runs & History** (`/history`):
  - Show historical runs and non-destructive **Re-run** button (spawns fresh run instance).
  - Select two completed runs with checkboxes and click **"Launch Comparison"**.
  - Show side-by-side metric deltas, confidence shifts, and entity drift analytics.
- Navigate to **Source Health** (`/connectors`):
  - Show live connector telemetry and test latency with the **Ping Test** button.
  - Highlight the active **SSRF Firewall** preventing private network access.

---

## 🔒 Security & Compliance

- **SSRF Protection**: Strict IP and domain validation blocks loopback (127.0.0.1, ::1), RFC 1918 private subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), link-local addresses, and cloud metadata (169.254.169.254).
- **Public Domain Access**: Complies strictly with public web access standards and `robots.txt`.
- **Zero Hallucination Guarantee**: All metrics, confidence scores, and validation states are deterministically calculated by backend engines. Demo data is explicitly marked as `DEMO SANDBOX DATA`.
- **Stateless & Secure**: No hardcoded API keys or credentials; parameters pass through strict Pydantic schemas.
