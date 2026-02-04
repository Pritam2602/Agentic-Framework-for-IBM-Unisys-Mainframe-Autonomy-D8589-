import sqlite3

DB_NAME = "zowe_capability_catalog.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# =====================================================
# CLEAN BUILD
# =====================================================
cursor.executescript("""
DROP TABLE IF EXISTS zowe_capability_precondition;
DROP TABLE IF EXISTS zowe_capability;
""")

# =====================================================
# CREATE TABLES
# =====================================================
cursor.execute("""
CREATE TABLE zowe_capability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zowe_command TEXT NOT NULL UNIQUE,

    category TEXT NOT NULL,
    command_family TEXT NOT NULL,
    subsystem TEXT NOT NULL,

    ibm_artifact TEXT NOT NULL,
    artifact_granularity TEXT NOT NULL,
    data_scope TEXT NOT NULL,

    operation TEXT NOT NULL,
    mutability TEXT NOT NULL,
    idempotent INTEGER,
    execution_cost TEXT NOT NULL,
    deterministic INTEGER,

    data_returned TEXT NOT NULL,
    response_format TEXT NOT NULL,
    intended_agent TEXT NOT NULL,
    constraints TEXT,
    confidence_level REAL
);
""")

cursor.execute("""
CREATE TABLE zowe_capability_precondition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capability_id INTEGER NOT NULL,
    precondition TEXT NOT NULL,
    FOREIGN KEY (capability_id)
        REFERENCES zowe_capability(id)
        ON DELETE CASCADE
);
""")

# =====================================================
# ALL COMMAND DEFINITIONS 
# =====================================================

job_commands = [
("zowe zos-jobs submit data-set","batch","JOB","JES2","JCL data set","JOB","JOB","EXECUTE","MUTABLE",0,"HIGH",0,"Job identifier (JOBID)","JSON","ZoweExecutionAgent","Executes batch job; may impact system state",0.95),
("zowe zos-jobs submit local-file","batch","JOB","JES2","JCL local file","JOB","JOB","EXECUTE","MUTABLE",0,"HIGH",0,"Job identifier (JOBID)","JSON","ZoweExecutionAgent","Executes batch job; may impact system state",0.95),
("zowe zos-jobs list jobs","batch","JOB","JES2","Job metadata","JOB","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"List of jobs","JSON","ZoweMonitoringAgent","Read-only",0.97),
("zowe zos-jobs list spool-files","batch","JOB","JES2","SYSOUT metadata","JOB","JOB","READ","IMMUTABLE",1,"LOW",1,"Spool files","JSON","ZoweMonitoringAgent","Read-only",0.96),
("zowe zos-jobs view job-status","batch","JOB","JES2","Job status","JOB","JOB","READ","IMMUTABLE",1,"LOW",0,"Job RC","JSON","ZoweMonitoringAgent","Read-only",0.97),
("zowe zos-jobs view job-log","batch","JOB","JES2","Job log","JOB","JOB","READ","IMMUTABLE",1,"LOW",0,"Job log","TEXT","ZoweParsingAgent","Sensitive",0.95),
("zowe zos-jobs view spool-file","batch","JOB","JES2","Spool file","JOB","JOB","READ","IMMUTABLE",1,"LOW",0,"Spool content","TEXT","ZoweParsingAgent","Sensitive",0.95),
("zowe zos-jobs cancel job","batch","JOB","JES2","Cancel job","JOB","JOB","EXECUTE","MUTABLE",0,"MEDIUM",0,"Cancel confirm","JSON","ZoweExecutionAgent","Disruptive",0.94),
("zowe zos-jobs delete job","batch","JOB","JES2","Delete job","JOB","JOB","EXECUTE","MUTABLE",0,"MEDIUM",0,"Delete confirm","JSON","ZoweExecutionAgent","Irreversible",0.94)
]

workflow_commands = [
("zowe zos-workflows list workflows","workflow","WORKFLOW","z/OSMF","Workflow metadata","WORKFLOW","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Workflow list","JSON","ZoweMonitoringAgent","Read-only",0.97),
("zowe zos-workflows create workflow","workflow","WORKFLOW","z/OSMF","Workflow definition","WORKFLOW","WORKFLOW","EXECUTE","MUTABLE",0,"MEDIUM",0,"Workflow id","JSON","ZoweExecutionAgent","Create workflow",0.95),
("zowe zos-workflows start workflow","workflow","WORKFLOW","z/OSMF","Workflow instance","WORKFLOW","WORKFLOW","EXECUTE","MUTABLE",0,"MEDIUM",0,"Workflow instance","JSON","ZoweExecutionAgent","Start workflow",0.95),
("zowe zos-workflows delete workflow","workflow","WORKFLOW","z/OSMF","Workflow instance","WORKFLOW","WORKFLOW","EXECUTE","MUTABLE",0,"MEDIUM",0,"Delete confirm","JSON","ZoweExecutionAgent","Delete workflow",0.94),
("zowe zos-workflows view workflow","workflow","WORKFLOW","z/OSMF","Workflow state","WORKFLOW","WORKFLOW","READ","IMMUTABLE",1,"LOW",0,"Workflow details","JSON","ZoweMonitoringAgent","Read-only",0.96),
("zowe zos-workflows view workflow-definition","workflow","WORKFLOW","z/OSMF","Workflow definition","WORKFLOW","WORKFLOW","READ","IMMUTABLE",1,"LOW",1,"Workflow def","JSON","ZoweParsingAgent","Read-only",0.96)
]

db2_commands = [
("zowe db2 list databases","metadata","DB2","DB2","DB2 catalog","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"DB list","JSON","DiscoveryAgent","Read-only",0.95),
("zowe db2 list tables","metadata","DB2","DB2","DB2 tables","TABLE","DATABASE","READ","IMMUTABLE",1,"LOW",1,"Table list","JSON","DiscoveryAgent","Read-only",0.95),
("zowe db2 execute query","database","DB2","DB2","DB2 tables","TABLE","TABLE","READ","IMMUTABLE",1,"MEDIUM",1,"Query result","JSON","IngestAgent","PII risk",0.95)
]

cics_commands = [
("zowe cics list regions","metadata","CICS","CICS","CICS regions","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Regions","JSON","DiscoveryAgent","Read-only",0.97),
("zowe cics list programs","metadata","CICS","CICS","Programs","PROGRAM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Programs","JSON","DiscoveryAgent","Read-only",0.97),
("zowe cics list transactions","metadata","CICS","CICS","Transactions","TRANSACTION","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Transactions","JSON","MonitoringAgent","Read-only",0.96),
("zowe cics start program","transaction","CICS","CICS","Program","PROGRAM","PROGRAM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Start confirm","JSON","ControlAgent","Admin required",0.90),
("zowe cics stop program","transaction","CICS","CICS","Program","PROGRAM","PROGRAM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Stop confirm","JSON","ControlAgent","Admin required",0.90)
]

ims_commands = [
("zowe ims list regions","metadata","IMS","IMS","IMS regions","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Regions","JSON","DiscoveryAgent","Read-only",0.96),
("zowe ims list transactions","metadata","IMS","IMS","IMS txns","TRANSACTION","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Transactions","JSON","MonitoringAgent","Read-only",0.96),
("zowe ims start transaction","transaction","IMS","IMS","IMS txn","TRANSACTION","TRANSACTION","EXECUTE","MUTABLE",0,"HIGH",0,"Start confirm","JSON","ControlAgent","High privilege",0.90),
("zowe ims stop transaction","transaction","IMS","IMS","IMS txn","TRANSACTION","TRANSACTION","EXECUTE","MUTABLE",0,"HIGH",0,"Stop confirm","JSON","ControlAgent","High privilege",0.90)
]

other_commands = [
("zowe plugins list","metadata","PLATFORM","z/OSMF","Plugins","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Plugins","JSON","GovernanceAgent","Read-only",0.98),
("zowe plugins install","workflow","PLATFORM","z/OSMF","Plugin","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Install","TEXT","InfraAgent","State change",0.9),
("zowe plugins update","workflow","PLATFORM","z/OSMF","Plugin","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Update","TEXT","InfraAgent","State change",0.9),
("zowe plugins uninstall","workflow","PLATFORM","z/OSMF","Plugin","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Uninstall","TEXT","InfraAgent","State change",0.9),

("zowe logs list","metadata","OBSERVABILITY","z/OSMF","Logs","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Logs","JSON","MonitoringAgent","Read-only",0.95),
("zowe logs view","metadata","OBSERVABILITY","z/OSMF","Logs","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Log content","TEXT","MonitoringAgent","Sensitive",0.94),

("zowe files list ds","metadata","FILES","z/OSMF","Datasets","DATASET","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Dataset list","JSON","DiscoveryAgent","Read-only",0.97),
("zowe files view ds","data","FILES","z/OSMF","Dataset","DATASET","DATASET","READ","IMMUTABLE",1,"MEDIUM",1,"Dataset content","TEXT","IngestAgent","Sensitive",0.95),
("zowe files upload ds","data","FILES","z/OSMF","Dataset","DATASET","DATASET","EXECUTE","MUTABLE",0,"HIGH",0,"Upload","TEXT","ControlAgent","Write access",0.9),

("zowe daemon status","metadata","PLATFORM","z/OSMF","Daemon","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Status","JSON","InfraAgent","Read-only",0.96),
("zowe daemon start","workflow","PLATFORM","z/OSMF","Daemon","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Start","TEXT","InfraAgent","Platform op",0.9),

("zowe tso start","tso","TSO","z/OSMF","TSO","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"TSO token","JSON","ScriptingAgent","TSO access",0.96),
("zowe tso send-input","tso","TSO","z/OSMF","TSO","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Input","JSON","ScriptingAgent","TSO input",0.95),

("zowe zosmf info","zosmf","SYSTEM","z/OSMF","z/OSMF","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"z/OSMF info","JSON","DiscoveryAgent","Read-only",0.99),

("zowe ssh start","ssh","SSH","z/OSMF","USS shell","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"SSH session","JSON","AutomationAgent","SSH access",0.94),

("zowe console issue","console","CONSOLE","z/OSMF","Console","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"HIGH",0,"Console output","TEXT","ControlAgent","Operator auth",0.97),
("zowe console retrieve","console","CONSOLE","z/OSMF","Console","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Reply","TEXT","MonitoringAgent","Read-only",0.97),

("zowe files list","files","FILES","z/OSMF","USS dir","SYSTEM","SYSTEM","READ","IMMUTABLE",1,"LOW",1,"Files","JSON","DiscoveryAgent","Read-only",0.99),
("zowe files upload","files","FILES","z/OSMF","USS file","SYSTEM","SYSTEM","EXECUTE","MUTABLE",0,"MEDIUM",0,"Upload","JSON","DataAgent","Write access",0.99)
]

ALL_COMMANDS = job_commands + workflow_commands + db2_commands + cics_commands + ims_commands + other_commands

# =====================================================
# INSERT
# =====================================================
cursor.executemany("""
INSERT OR IGNORE INTO zowe_capability VALUES (
NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
)
""", ALL_COMMANDS)

# =====================================================
# INSERT PRECONDITIONS 
# =====================================================
job_preconditions = [
    ("JOB_SUBMITTED", "zowe zos-jobs list spool-files"),
    ("JOB_SUBMITTED", "zowe zos-jobs view job-status"),
    ("JOB_COMPLETED", "zowe zos-jobs view job-log"),
    ("JOB_COMPLETED", "zowe zos-jobs view spool-file"),
    ("JOB_RUNNING",   "zowe zos-jobs cancel job"),
    ("JOB_COMPLETED", "zowe zos-jobs delete job"),
]

workflow_preconditions = [
    ("WORKFLOW_CREATED", "zowe zos-workflows start workflow"),
    ("WORKFLOW_STARTED", "zowe zos-workflows view workflow"),
    ("WORKFLOW_STARTED", "zowe zos-workflows delete workflow"),
]

for state, cmd in job_preconditions + workflow_preconditions:
    cursor.execute("""
        INSERT INTO zowe_capability_precondition (capability_id, precondition)
        SELECT id, ?
        FROM zowe_capability
        WHERE zowe_command = ?
    """, (state, cmd))

conn.commit()
conn.close()

print("✅ Zowe catalog created with ALL commands")
