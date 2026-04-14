# 🚀 AI-Driven Mainframe Data Federation Platform

An enterprise-grade **agentic system** that enables intelligent interaction with legacy mainframe systems (IBM & Unisys) using AI, schema understanding, and modern APIs.

---

## 🧠 Overview

This project builds a **multi-agent architecture** that bridges:

* 🏢 **IBM Mainframe Systems**

  * COBOL programs (parsed using ProLeap)
  * JCL job execution
  * Zowe command interface

* 🖥️ **Unisys Systems**

  * Simulated via a **Mock ePortal**
  * REST APIs + Schema + MCP endpoints

---

### 🎯 Goal

Enable users to query legacy systems in **natural language**, and automatically:

1. Understand intent
2. Locate relevant data sources
3. Plan execution
4. Fetch and unify results

---

## 🏗️ Architecture

```text
User
 ↓
Intent Agent
 ↓
Context Resolution Agent
 ↓
Planner Agent
 ↓
Execution Agents (IBM + Unisys)
 ↓
Schema & Mapping
 ↓
Federation Intelligence
 ↓
Final Output (UI Dashboard)
```

---

## 🤖 Core Components

---

### 🔹 1. Intent Agent

**Purpose:** Understand *what the user wants*

* Converts natural language → structured JSON
* Handles:

  * Task detection (fetch, compare, analyze)
  * Entity extraction (payroll, customer)
  * Attribute mapping (salary → netSalary)
  * Date normalization

✅ Example Output:

```json
{
  "task": "fetch",
  "entities": ["payroll"],
  "attributes": ["employeeId", "netSalary"],
  "filters": {
    "time_range": {
      "start": "2026-03-01",
      "end": "2026-03-31"
    }
  },
  "systems": ["unisys"],
  "confidence_score": 0.92
}
```

---

### 🔹 2. Context Resolution Agent

**Purpose:** Determine *where the data exists*

Uses:

* 📊 COBOL parsed JSON (ProLeap)
* 📄 JCL metadata
* ⚙️ Zowe command catalog
* 🌐 ePortal MCP schema

Output:

```json
{
  "ibm": {
    "program": "CBTRN01",
    "dataset": "TRANSACTION-FILE"
  },
  "unisys": {
    "api": "/api/unisys/payroll"
  }
}
```

---

### 🔹 3. Planner Agent

**Purpose:** Decide *how to execute*

* Combines intent + context
* Generates execution plan

```json
{
  "steps": [
    {
      "system": "ibm",
      "command": "zowe zos-jobs submit ds CBTRN.JCL"
    },
    {
      "system": "unisys",
      "api": "/api/unisys/payroll"
    }
  ]
}
```

---

### 🔹 4. Execution Agents

#### 🟦 IBM Agent

* Executes Zowe commands
* Runs JCL jobs
* Fetches datasets

#### 🟩 Unisys Agent

* Calls mock ePortal APIs
* Returns structured JSON

---

### 🔹 5. Schema & Mapping Agent

* Converts IBM + Unisys outputs → canonical schema
* Ensures consistency across systems

---

### 🔹 6. Federation Intelligence Agent

* AI-powered reasoning layer
* Matches entities across systems
* Generates insights and unified views

---

## 🧩 IBM Integration (CardDemo Dataset)

Uses the AWS CardDemo dataset:

* COBOL programs → business logic
* JCL jobs → execution flow
* DB2/datasets → data storage

### 🔹 COBOL Parsing (ProLeap)

Extracts:

* Program ID
* Variables
* File usage
* Call hierarchy

### 🔹 JCL Parsing

Extracts:

* Job steps
* Programs executed
* Input/output datasets

---

## 🌐 Mock ePortal (Unisys Simulation)

A FastAPI-based simulation of Unisys ePortal.

### 🔹 APIs

```
GET /api/unisys/payroll
GET /api/unisys/customer
```

### 🔹 Schema Endpoints

```
GET /schema/payroll
GET /schema/customer
```

### 🔹 MCP Endpoint

```
GET /mcp/tools
```

Example:

```json
{
  "tools": [
    {
      "name": "get_payroll",
      "endpoint": "/api/unisys/payroll",
      "output": ["employeeId", "netSalary"]
    }
  ]
}
```

---

## 💻 Frontend

A modern **agent orchestration dashboard** with:

* Execution Panel
* Agent pipeline visualization
* Intent / Context / Planner views
* Output panel with source tagging

---

## ⚙️ Tech Stack

* **Backend:** Python, FastAPI
* **AI/LLM:** LangChain, Gemini/OpenAI
* **Parsing:** ProLeap (COBOL), Custom JCL parser
* **Mainframe Access:** Zowe CLI/API
* **Frontend:** React (Dark UI Dashboard)
* **Deployment:** Render / Cloud

---

## 🚀 Getting Started

---

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/project-name.git
cd project-name
```

---

### 2️⃣ Setup Environment

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
GOOGLE_API_KEY=your_key
```

---

### 3️⃣ Run Backend

```bash
uvicorn app:app --reload
```

---

### 4️⃣ Run Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Example Query

```
Compare employee salaries between IBM and Unisys
```

---

## 🔥 Key Features

* ✅ Natural language → execution pipeline
* ✅ Legacy system integration (COBOL + JCL)
* ✅ Schema-aware reasoning (MCP)
* ✅ Multi-agent architecture
* ✅ Real-time execution visualization
* ✅ Modular and scalable design

---

## 📌 Future Enhancements

* 🔹 Real Zowe integration with live mainframe
* 🔹 Advanced federation (join across systems)
* 🔹 Authentication & role-based access
* 🔹 Performance optimization
* 🔹 Full MCP server implementation

---

## 👨‍💻 Contributors

* **S. Pritam**
* Team Members (IBM + Unisys integration)

---

## 📜 License

MIT License

---

# ⭐ Final Note

This project demonstrates how **AI + agentic architecture can modernize legacy enterprise systems**, enabling intelligent, scalable, and seamless data federation across heterogeneous platforms.
