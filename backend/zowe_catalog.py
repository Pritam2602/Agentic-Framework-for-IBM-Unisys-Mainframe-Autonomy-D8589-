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
        "DB2 System Catalog", "DB2",
        "READ", "REST",
        "List of DB2 databases with owner and status", "JSON",
        "DiscoveryAgent", "Read-only; no PII",
        "SYSTEM", "SYSTEM",
        True, None, "LOW", 0.95
    ),

    (
        "zowe db2 list tables", "metadata", "DB2",
        "DB2 System Catalog (SYSTABLES)", "DB2",
        "READ", "REST",
        "List of tables within a DB2 database", "JSON",
        "DiscoveryAgent", "Read-only metadata",
        "TABLE", "DATABASE",
        True, None, "LOW", 0.95
    ),

    (
        "zowe db2 execute query", "database", "DB2",
        "DB2 User Tables", "DB2",
        "READ", "REST",
        "Tabular query result set", "JSON",
        "IngestAgent", "PII risk; SELECT-only queries",
        "TABLE", "TABLE",
        True, None, "MEDIUM", 0.95
    ),

    # -------- CICS --------
    (
        "zowe cics list regions", "metadata", "CICS",
        "CICS Region Control Table", "CICS",
        "READ", "REST",
        "List of CICS regions and runtime status", "JSON",
        "DiscoveryAgent", "Read-only",
        "SYSTEM", "SYSTEM",
        True, None, "LOW", 0.97
    ),

    (
        "zowe cics list programs", "metadata", "CICS",
        "CICS Program Definition Table", "CICS",
        "READ", "REST",
        "List of CICS programs with enablement status", "JSON",
        "DiscoveryAgent", "Read-only",
        "PROGRAM", "SYSTEM",
        True, None, "LOW", 0.97
    ),

    (
        "zowe cics list transactions", "metadata", "CICS",
        "CICS Transaction Definition Table", "CICS",
        "READ", "REST",
        "List of CICS transactions and status", "JSON",
        "MonitoringAgent", "Read-only",
        "TRANSACTION", "SYSTEM",
        True, None, "LOW", 0.96
    ),

    (
        "zowe cics start program", "transaction", "CICS",
        "CICS Program Control Definition", "CICS",
        "EXECUTE", "REST",
        "Confirmation of program start", "JSON",
        "ControlAgent", "State-changing; admin required",
        "PROGRAM", "PROGRAM",
        False, None, "MEDIUM", 0.90
    ),

    (
        "zowe cics stop program", "transaction", "CICS",
        "CICS Program Control Definition", "CICS",
        "EXECUTE", "REST",
        "Confirmation of program stop", "JSON",
        "ControlAgent", "State-changing; admin required",
        "PROGRAM", "PROGRAM",
        False, None, "MEDIUM", 0.90
    ),

    # -------- IMS --------
    (
        "zowe ims list regions", "metadata", "IMS",
        "IMS Region Definition", "IMS",
        "READ", "REST",
        "List of IMS regions", "JSON",
        "DiscoveryAgent", "Read-only",
        "SYSTEM", "SYSTEM",
        True, None, "LOW", 0.96
    ),

    (
        "zowe ims list transactions", "metadata", "IMS",
        "IMS Transaction Definition Table", "IMS",
        "READ", "REST",
        "List of IMS transactions and status", "JSON",
        "MonitoringAgent", "Read-only",
        "TRANSACTION", "SYSTEM",
        True, None, "LOW", 0.96
    ),

    (
        "zowe ims start transaction", "transaction", "IMS",
        "IMS Transaction Control Block", "IMS",
        "EXECUTE", "REST",
        "Confirmation of transaction start", "JSON",
        "ControlAgent", "High privilege required",
        "TRANSACTION", "TRANSACTION",
        False, "transactionId", "HIGH", 0.90
    ),

    (
        "zowe ims stop transaction", "transaction", "IMS",
        "IMS Transaction Control Block", "IMS",
        "EXECUTE", "REST",
        "Confirmation of transaction stop", "JSON",
        "ControlAgent", "High privilege required",
        "TRANSACTION", "TRANSACTION",
        False, "transactionId", "HIGH", 0.90
    ),
    (
        "zowe jobs list", "jobs", "JOBS", "Job spool files", "JES2",
        "READ", "REST", "Active and recent job list with status", "JSON",
        "MonitoringAgent", "Read-only job query", "JOB", "SYSTEM",
        True, "jobId", "LOW", 0.98
    ),
    (
        "zowe jobs submit", "jobs", "JOBS", "JCL execution", "JES2",
        "EXECUTE", "REST", "Job submission confirmation with jobId", "JSON",
        "ControlAgent", "Job submission privilege required", "JOB", "JOB",
        False, "jobId", "MEDIUM", 0.98
    ),
    (
        "zowe jobs download", "jobs", "JOBS", "SYSOUT spool", "JES2",
        "READ", "REST", "Job output content", "TEXT",
        "AnalysisAgent", "Job exists", "JOB", "JOB",
        True, "jobId", "MEDIUM", 0.98
    ),
    (
	"zowe jobs delete", "jobs", "JOBS", "Job queue", "JES2", "EXECUTE", "REST",     	"Delete confirmation", "JSON", "CleanupAgent", "Delete privilege", "JOB",  	"JOB", False, None, "MEDIUM", 0.97
    ),
    (
        "zowe files list", "files", "FILES", "USS Directory", "z/OSMF",
        "READ", "REST", "File/directory listing", "JSON",
        "DiscoveryAgent", "USS read access", None, "SYSTEM",
        True, None, "LOW", 0.99
    ),
    (
        "zowe files upload", "files", "FILES", "USS file", "z/OSMF",
        "EXECUTE", "REST", "Upload status", "JSON",
        "DataAgent", "USS write access", None, None,
        False, None, "MEDIUM", 0.99
    ),
   (
        "zowe console issue", "console", "CONSOLE", "MVS operator console", "z/OSMF",
        "EXECUTE", "REST", "Console command response", "TEXT",
        "ControlAgent", "Operator console authority required", None, "SYSTEM",
        False, None, "HIGH", 0.97
    ),
    (
	"zowe console retrieve", "console", "CONSOLE", "Console reply", "z/OSMF", 	"READ", "REST", "Reply content", "TEXT", "MonitoringAgent", "Console read", 	None, "SYSTEM", True, "replyToken", "LOW", 0.97
    ),
   (
        "zowe tso start", "tso", "TSO", "TSO Address Space", "z/OSMF",
        "EXECUTE", "REST", "TSO session token", "JSON",
        "ScriptingAgent", "TSO execution privilege", None, "SYSTEM",
        False, "tsoAddressSpaceId", "MEDIUM", 0.96
    ),
   (
	"zowe tso send-input", "tso", "TSO", "REXX input", "z/OSMF", "EXECUTE", "REST", 	"Input status", "JSON", "ScriptingAgent", "TSO input", None, None, False, None, 	"MEDIUM", 0.95
    ),
   (
        "zowe zosmf info", "zosmf", "SYSTEM", "z/OSMF configuration", "z/OSMF",
        "READ", "REST", "z/OSMF version and services", "JSON",
        "DiscoveryAgent", "Read-only", None, "SYSTEM",
        True, None, "LOW", 0.99
    ),
    (
	"zowe ssh start", "ssh", "SSH", "USS shell", "z/OSMF", "EXECUTE", "REST", "SSH 	session", "JSON", "AutomationAgent", "SSH access", None, "SYSTEM", False, 	"sshSessionId", "MEDIUM", 0.94
    ),
        # -------- ZOWE PLUGIN MANAGEMENT --------

    (
        "zowe plugins list",
        "metadata",
        "PLATFORM",
        "Zowe Plugin Registry",
        "z/OSMF",
        "READ",
        "CLI",
        "List of installed Zowe plugins and versions",
        "JSON",
        "GovernanceAgent",
        "Read-only; no system impact",
        "SYSTEM",
        "SYSTEM",
        True,
        None,
        "LOW",
        0.98
    ),

    (
        "zowe plugins install",
        "workflow",
        "PLATFORM",
        "Zowe Plugin Registry",
        "z/OSMF",
        "EXECUTE",
        "CLI",
        "Confirmation of plugin installation",
        "TEXT",
        "InfraAgent",
        "Requires network access and install privileges",
        "SYSTEM",
        "SYSTEM",
        False,
        None,
        "MEDIUM",
        0.9
    ),

    (
        "zowe plugins update",
        "workflow",
        "PLATFORM",
        "Zowe Plugin Registry",
        "z/OSMF",
        "EXECUTE",
        "CLI",
        "Confirmation of plugin update",
        "TEXT",
        "InfraAgent",
        "State-changing; may affect compatibility",
        "SYSTEM",
        "SYSTEM",
        False,
        None,
        "MEDIUM",
        0.9
    ),

    (
        "zowe plugins uninstall",
        "workflow",
        "PLATFORM",
        "Zowe Plugin Registry",
        "z/OSMF",
        "EXECUTE",
        "CLI",
        "Confirmation of plugin removal",
        "TEXT",
        "InfraAgent",
        "State-changing; capability removal",
        "SYSTEM",
        "SYSTEM",
        False,
        None,
        "MEDIUM",
        0.9
    ),
        # -------- ZOWE LOGS --------

    (
        "zowe logs list",
        "metadata",
        "OBSERVABILITY",
        "Zowe System Logs",
        "z/OSMF",
        "READ",
        "CLI",
        "List of available Zowe and system logs",
        "JSON",
        "MonitoringAgent",
        "Read-only; diagnostic data only",
        "SYSTEM",
        "SYSTEM",
        True,
        None,
        "LOW",
        0.95
    ),

    (
        "zowe logs view",
        "metadata",
        "OBSERVABILITY",
        "Zowe Log Files",
        "z/OSMF",
        "READ",
        "CLI",
        "Detailed log content for a specified log source",
        "TEXT",
        "MonitoringAgent",
        "Read-only; may expose sensitive operational data",
        "SYSTEM",
        "SYSTEM",
        True,
        None,
        "LOW",
        0.94
    ),
        # -------- ZOWE FILES (DATASETS) --------

    (
        "zowe files list ds",
        "metadata",
        "FILES",
        "z/OS Datasets (PS/PDS/VSAM)",
        "z/OSMF",
        "READ",
        "REST",
        "List of datasets matching search criteria",
        "JSON",
        "DiscoveryAgent",
        "Read-only; dataset names may reveal structure",
        "DATASET",
        "SYSTEM",
        True,
        None,
        "LOW",
        0.97
    ),

    (
        "zowe files view ds",
        "data",
        "FILES",
        "z/OS Sequential or Partitioned Dataset",
        "z/OSMF",
        "READ",
        "REST",
        "Dataset content in text format",
        "TEXT",
        "IngestAgent",
        "May expose PII or business data; read-only enforced",
        "DATASET",
        "DATASET",
        True,
        None,
        "MEDIUM",
        0.95
    ),

    (
        "zowe files upload ds",
        "data",
        "FILES",
        "z/OS Dataset",
        "z/OSMF",
        "EXECUTE",
        "REST",
        "Confirmation of dataset upload",
        "TEXT",
        "ControlAgent",
        "State-changing; write access required",
        "DATASET",
        "DATASET",
        False,
        None,
        "HIGH",
        0.9
    ),
        # -------- ZOWE DAEMON --------

    (
        "zowe daemon status",
        "metadata",
        "PLATFORM",
        "Zowe Background Services",
        "z/OSMF",
        "READ",
        "CLI",
        "Current status of Zowe daemon and services",
        "JSON",
        "InfraAgent",
        "Read-only; platform diagnostic",
        "SYSTEM",
        "SYSTEM",
        True,
        None,
        "LOW",
        0.96
    ),

    (
        "zowe daemon start",
        "workflow",
        "PLATFORM",
        "Zowe Background Services",
        "z/OSMF",
        "EXECUTE",
        "CLI",
        "Confirmation of daemon startup",
        "TEXT",
        "InfraAgent",
        "State-changing; platform-level operation",
        "SYSTEM",
        "SYSTEM",
        False,
        None,
        "MEDIUM",
        0.9
    ),

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
