# Project Tech Stack and Setup Requirements

This document lists the complete technology stack required to set up and run the COMMUNICATOR AI Data Federation Platform after cloning the repository.

## Core Runtime

- Python 3.10 or later
- Node.js 18 or later
- npm
- Git

## Backend Stack

- FastAPI
- Uvicorn
- Pydantic v2
- python-dotenv
- HTTPX
- SQLAlchemy
- SQLite

SQLite is used for:

- Zowe command catalog: `database/zowe_catalog.db`
- Runtime observability storage: `data/observability.sqlite3`

The observability database is generated locally at runtime and is ignored by Git.

## AI and Agent Stack

- LangChain
- LangChain Core
- LangChain Community
- LangChain Google GenAI
- LangChain OpenAI
- Google Generative AI SDK
- Google API Python Client

## LLM Provider

The application uses Google Gemini through:

```text
langchain_google_genai.ChatGoogleGenerativeAI
```

Primary configured model:

```text
gemini-2.5-flash-lite
```

Runtime fallback models:

```text
gemini-2.5-flash-lite
gemini-3-flash-preview
gemini-2.0-flash-lite
```

Model settings:

- Temperature: `0`
- Retries: `0`

## Required Environment Variables

Create a `.env` file in the project root.

```env
GOOGLE_API_KEY=your_google_gemini_key
```

Alternatively:

```env
GEMINI_API_KEY=your_google_gemini_key
```

If no Gemini key is configured, deterministic fallback behavior is used where available.

## Optional Observability Environment Variables

LangSmith:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=communicator-federation
```

OpenTelemetry / Jaeger:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
```

## Frontend Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack React Query
- Headless UI
- Heroicons
- Framer Motion
- clsx

## Mock and Federation Services

- Mock IBM/CardDemo JSON datasets
- Mock Unisys ePortal service
- MCP SDK
- Mock z/OS simulator
- Zowe command catalog backed by SQLite
- Federation intelligence pipeline
- Discovery recommendation agent
- Fraud and risk federation logic

## Observability Stack

- Structlog
- Prometheus Client
- OpenTelemetry API
- OpenTelemetry SDK
- OpenTelemetry FastAPI instrumentation
- OTLP exporter
- Jaeger exporter
- LangSmith
- SQLite persistence
- Server-Sent Events
- Grafana dashboard JSON
- Prometheus alert rules

Observability files:

```text
observability/README.md
observability/grafana_dashboard.json
observability/prometheus_alerts.yml
```

Runtime observability endpoints:

```text
GET /metrics
GET /api/observability/summary
GET /api/observability/runs
GET /api/observability/events
GET /api/observability/stream
GET /api/observability/llm-usage
```

## Optional External Tools

These are not mandatory for the basic demo, but are useful for full observability and parser workflows.

- Prometheus
- Grafana
- Jaeger
- LangSmith account
- Java / OpenJDK 17
- Maven

Java and Maven are only needed if running the COBOL/JCL parser tools under:

```text
tools/cobol-jcl-parser
```

## Python Dependencies

Install backend dependencies from:

```bash
pip install -r requirements.txt
```

Main dependency groups:

- LangChain and LLM SDKs
- FastAPI backend
- Observability packages
- MCP SDK
- Data and validation libraries

## Frontend Dependencies

Install frontend dependencies from the `frontend` directory:

```bash
cd frontend
npm install
```

## Basic Setup Flow

Clone the repository:

```bash
git clone <repo-url>
cd <repo-folder>
```

Create and activate a Python virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Import AWS CardDemo sample data into the local IBM JSON files:

```bash
python scripts/import_aws_carddemo_data.py
```

This reads the AWS sample repo's ASCII files, writes `data/ibm/*.json`, and regenerates matching Unisys shopping enrichment.

Create `.env`:

```env
GOOGLE_API_KEY=your_google_gemini_key
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Run the Application

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Start the mock ePortal service:

```bash
python mock_eportal/mcp_server.py
```

## Verification Commands

Run the fraud federation verification:

```bash
python verify_fraud_use_case.py
```

Build the frontend:

```bash
cd frontend
npm run build
```

Check backend health:

```text
GET http://localhost:8000/api/pipeline/health
```

Check observability metrics:

```text
GET http://localhost:8000/metrics
```

## Useful Demo Queries

```text
Show shopping data for customer 1
```

```text
Analyze loyalty points versus total spend for customer 1
```

```text
Run fraud and risk assessment for customer 41
```

```text
Compare IBM total spend with Unisys observed shopping amount
```

```text
We know shopping data is available. Can you suggest related inventory exploration?
```

## Summary

At a high level, the project uses:

- Python + FastAPI for backend APIs
- React + Vite + TypeScript for frontend
- LangChain + Gemini for agentic intelligence
- SQLite + JSON datasets for local demo data
- MCP for mock Unisys ePortal capability access
- Prometheus, OpenTelemetry, Jaeger, LangSmith, and Grafana assets for observability
