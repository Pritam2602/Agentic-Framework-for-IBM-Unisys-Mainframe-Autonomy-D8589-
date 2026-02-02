import sqlite3

# 1. Connect to SQLite database (creates file if not exists)
conn = sqlite3.connect("zowe_capability_catalog.db")
cursor = conn.cursor()

# 2. Create catalog table
cursor.execute("""
CREATE TABLE IF NOT EXISTS zowe_capability_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    zowe_command TEXT NOT NULL,
    category TEXT NOT NULL,
    command_family TEXT NOT NULL,

    ibm_artifact TEXT NOT NULL,
    subsystem TEXT NOT NULL,

    operation TEXT NOT NULL,
    access_pattern TEXT,

    data_returned TEXT NOT NULL,
    response_format TEXT NOT NULL,

    intended_agent TEXT NOT NULL,
    constraints TEXT NOT NULL,

    artifact_granularity TEXT,
    data_scope TEXT,

    idempotent BOOLEAN,
    produces_identifier TEXT,

    execution_cost TEXT,
    confidence_level REAL
)
""")

# 3. Catalog entries (derived from the PDF)
catalog_entries = [

    # -------- DB2 --------
    (
        "zowe db2 list databases", "metadata", "DB2",
        "DB2", "DB2 System Catalog",
        "READ", "REST",
        "List of DB2 databases with owner and status", "JSON",
        "DiscoveryAgent", "Read-only; no PII",
        "SYSTEM", "SYSTEM",
        True, None, "LOW", 0.95
    ),

    (
        "zowe db2 list tables", "metadata", "DB2",
        "DB2", "DB2 System Catalog (SYSTABLES)",
        "READ", "REST",
        "List of tables within a DB2 database", "JSON",
        "DiscoveryAgent", "Read-only metadata",
        "TABLE", "DATABASE",
        True, None, "LOW", 0.95
    ),

    (
        "zowe db2 execute query", "database", "DB2",
        "DB2", "DB2 User Tables",
        "READ", "REST",
        "Tabular query result set", "JSON",
        "IngestAgent", "PII risk; SELECT-only queries",
        "TABLE", "TABLE",
        True, None, "MEDIUM", 0.95
    ),

    # -------- CICS --------
    (
        "zowe cics list regions", "metadata", "CICS",
        "CICS", "CICS Region Control Table",
        "READ", "REST",
        "List of CICS regions and runtime status", "JSON",
        "DiscoveryAgent", "Read-only",
        "SYSTEM", "SYSTEM",
        True, None, "LOW", 0.97
    ),

    (
        "zowe cics list programs", "metadata", "CICS",
        "CICS", "CICS Program Definition Table",
        "READ", "REST",
        "List of CICS programs with enablement status", "JSON",
        "DiscoveryAgent", "Read-only",
        "PROGRAM", "SYSTEM",
        True, None, "LOW", 0.97
    ),

    (
        "zowe cics list transactions", "metadata", "CICS",
        "CICS", "CICS Transaction Definition Table",
        "READ", "REST",
        "List of CICS transactions and status", "JSON",
        "MonitoringAgent", "Read-only",
        "TRANSACTION", "SYSTEM",
        True, None, "LOW", 0.96
    ),

    (
        "zowe cics start program", "transaction", "CICS",
        "CICS", "CICS Program Control Definition",
        "EXECUTE", "REST",
        "Confirmation of program start", "JSON",
        "ControlAgent", "State-changing; admin required",
        "PROGRAM", "PROGRAM",
        False, None, "MEDIUM", 0.90
    ),

    (
        "zowe cics stop program", "transaction", "CICS",
        "CICS", "CICS Program Control Definition",
        "EXECUTE", "REST",
        "Confirmation of program stop", "JSON",
        "ControlAgent", "State-changing; admin required",
        "PROGRAM", "PROGRAM",
        False, None, "MEDIUM", 0.90
    ),

    # -------- IMS --------
    (
        "zowe ims list regions", "metadata", "IMS",
        "IMS", "IMS Region Definition",
        "READ", "REST",
        "List of IMS regions", "JSON",
        "DiscoveryAgent", "Read-only",
        "SYSTEM", "SYSTEM",
        True, None, "LOW", 0.96
    ),

    (
        "zowe ims list transactions", "metadata", "IMS",
        "IMS", "IMS Transaction Definition Table",
        "READ", "REST",
        "List of IMS transactions and status", "JSON",
        "MonitoringAgent", "Read-only",
        "TRANSACTION", "SYSTEM",
        True, None, "LOW", 0.96
    ),

    (
        "zowe ims start transaction", "transaction", "IMS",
        "IMS", "IMS Transaction Control Block",
        "EXECUTE", "REST",
        "Confirmation of transaction start", "JSON",
        "ControlAgent", "High privilege required",
        "TRANSACTION", "TRANSACTION",
        False, "transactionId", "HIGH", 0.90
    ),

    (
        "zowe ims stop transaction", "transaction", "IMS",
        "IMS", "IMS Transaction Control Block",
        "EXECUTE", "REST",
        "Confirmation of transaction stop", "JSON",
        "ControlAgent", "High privilege required",
        "TRANSACTION", "TRANSACTION",
        False, "transactionId", "HIGH", 0.90
    )
]


# 4. Insert entries
cursor.executemany("""
INSERT INTO zowe_capability_catalog (
    zowe_command, category, command_family,
    ibm_artifact, subsystem,
    operation, access_pattern,
    data_returned, response_format,
    intended_agent, constraints,
    artifact_granularity, data_scope,
    idempotent, produces_identifier,
    execution_cost, confidence_level
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", catalog_entries)

# 5. Commit and close
conn.commit()
conn.close()

print("Zowe Capability Catalog created successfully.")
