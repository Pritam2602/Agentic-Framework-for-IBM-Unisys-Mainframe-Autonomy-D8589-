Agentic Framework for IBM–Unisys Mainframe Autonomy (D8589)
📌 Project Overview

This project implements a Zowe Capability Catalog as part of an agentic framework to enable explainable, safe, and structured interaction with IBM mainframe systems.
The catalog maps Zowe CLI commands to their underlying IBM subsystems and artifacts, enabling AI agents to reason about legacy systems without directly executing commands.

The current implementation focuses on catalog creation, persistence, API exposure, and visualization.

🎯 Objectives Achieved (Current Scope)

1. Design a fixed, structured catalog schema for Zowe capabilities
2. Map Zowe commands to IBM subsystems and artifacts
3. Persist catalog entries in SQLite
4. Expose catalog via a Flask REST API
5. Visualize catalog entries using a React frontend
6. Ensure the design supports agentic reasoning and governance

🧠 Key Concepts
Zowe Capability Catalog

A structured knowledge base that describes:

1. What a Zowe command does
2. Which IBM subsystem executes it
3. Which IBM artifact it accesses or modifies
4. Whether it is read-only or state-changing
5. Which agent should use it

Agentic Perspective

Agents do not execute commands blindly.
They first consult the catalog to:

1. Discover safe capabilities
2. Understand execution impact
3. Maintain explainability and audit trails

To create catalog and visulaize it:
1. open terminal -> cd backend -> python zowe_catalog.py
2. in same terminal and folder -> python app.py
3. open new terminal while the old one is still running
4. in new terminal -> cd frontend -> npm start