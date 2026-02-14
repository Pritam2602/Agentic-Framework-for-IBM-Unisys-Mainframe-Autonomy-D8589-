import sqlite3

conn = sqlite3.connect("zowe_capability_catalog.db")

cursor = conn.cursor()

#cat check                 CHECK (category IN ('batch', 'workflow', 'metadata')),
#cmd fam check             CHECK (command_family IN ('JOB', 'WORKFLOW', 'DATASET', 'SYSTEM')),
#artifact_granularity      CHECK (artifact_granularity IN ('JOB', 'WORKFLOW', 'STEP')),
#subsystem check           CHECK (subsystem IN ('JES2', 'JES3', 'z/OSMF')),
#data_scope check          CHECK (data_scope IN ('SYSTEM', 'JOB', 'WORKFLOW', 'STEP')),



# zowe_capability table
cursor.execute("""
        CREATE TABLE IF NOT EXISTS zowe_capability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
        
            zowe_command TEXT NOT NULL UNIQUE,
        
            category TEXT NOT NULL,
        
            command_family TEXT NOT NULL,
        
            subsystem TEXT NOT NULL,
        
            ibm_artifact TEXT NOT NULL,
        
            artifact_granularity TEXT NOT NULL,
        
            data_scope TEXT NOT NULL,
        
            operation TEXT NOT NULL
                CHECK (operation IN ('READ', 'EXECUTE')),

            access_pattern TEXT,
            produces_identifier TEXT,

            mutability TEXT NOT NULL
                CHECK (mutability IN ('IMMUTABLE', 'MUTABLE')),
        
            idempotent INTEGER
                CHECK (idempotent IN (0, 1)),
        
            deterministic INTEGER
                CHECK (deterministic IN (0, 1)),
        
            execution_cost TEXT NOT NULL
                CHECK (execution_cost IN ('LOW', 'MEDIUM', 'HIGH')),
        
            data_returned TEXT NOT NULL,
        
            response_format TEXT NOT NULL
                CHECK (response_format IN ('JSON', 'TEXT')),
        
            intended_agent TEXT NOT NULL,
        
            constraints TEXT,
        
            confidence_level REAL
                CHECK (confidence_level >= 0 AND confidence_level <= 1),
            
            description TEXT,
               
            output_file TEXT NOT NULL
        );
""")


# preconditions table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS zowe_capability_precondition (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        capability_id INTEGER NOT NULL,
        precondition TEXT NOT NULL,
    
        FOREIGN KEY (capability_id)
            REFERENCES zowe_capability(id)
            ON DELETE CASCADE
    );
""")

# Indexing required fields in 

# ------    1. capability table   ------------
cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_category   
        ON zowe_capability(category);
        
        CREATE INDEX IF NOT EXISTS idx_operation
        ON zowe_capability(operation);
        
        CREATE INDEX IF NOT EXISTS idx_execution_cost
        ON zowe_capability(execution_cost);
        
        CREATE INDEX IF NOT EXISTS idx_zowe_capability_command_family
        ON zowe_capability(command_family);
        
        CREATE INDEX IF NOT EXISTS idx_zowe_capability_mutability
        ON zowe_capability(mutability);
""")

# ------   2. preconditioning table   -------
cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_precondition
        ON zowe_capability_precondition(precondition);
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_capability_precondition_unique
        ON zowe_capability_precondition(capability_id, precondition);
""")

conn.commit()


# Zowe Commands and their Details

# ------   Job Command Details   ------
job_commands = [
    (
    'zowe zos-jobs submit data-set','batch','JOB','JES2','JCL data set','JOB','JOB','EXECUTE',None,'jobId','MUTABLE',0,0,'HIGH','Job identifier (JOBID)','JSON','ZoweExecutionAgent','Executes batch job',0.95,
    'Submit JCL dataset job','{"jobId":"JOB12345","status":"SUBMITTED"}'
    ),

    (
    'zowe zos-jobs submit local-file','batch','JOB','JES2','JCL local file','JOB','JOB','EXECUTE',None,'jobId','MUTABLE',0,0,'HIGH','Job identifier (JOBID)','JSON',
    'ZoweExecutionAgent','Executes batch job',0.95,'Submit local JCL job','{"jobId":"JOB12345","status":"SUBMITTED"}'
    ),

    (
    'zowe zos-jobs list jobs','batch','JOB','JES2','Job metadata','JOB','SYSTEM','READ',None,None,'IMMUTABLE',1,1,'LOW','List of jobs','JSON',
    'ZoweMonitoringAgent','Read-only job metadata',0.97,'List jobs',
    '{"jobs":[{"jobId":"JOB12345","status":"ACTIVE"}]}'
    ),

    (
    'zowe zos-jobs list spool-files','batch','JOB','JES2','Spool metadata','JOB','JOB','READ',None,None,'IMMUTABLE',1,1,'LOW','Spool files','JSON',
    'ZoweMonitoringAgent','Read-only spool metadata',0.96,'List spool files',
    '{"spoolFiles":[{"ddName":"JESMSGLG"}]}'
    ),

    (
    'zowe zos-jobs view job-status','batch','JOB','JES2','Job status','JOB','JOB','READ',None,None,'IMMUTABLE',1,1,'LOW','Job status','JSON','ZoweMonitoringAgent','Read-only job status',0.97,'View job status',
    '{"jobId":"JOB12345","status":"COMPLETE","rc":"0000"}'
    ),

    (
    'zowe zos-jobs view job-log','batch','JOB','JES2','Job log','JOB','JOB','READ',None,None,'IMMUTABLE',1,1,'LOW','Job log output','TEXT','ZoweParsingAgent','Job log text',0.95,'View job log',
    '{"jobId":"JOB12345","log":"IEFBR14 EXECUTED"}'
    ),

    (
    'zowe zos-jobs view spool-file','batch','JOB','JES2','Spool file','JOB','JOB','READ',None,None,'IMMUTABLE',1,1,'LOW','Spool file content','TEXT','ZoweParsingAgent','Spool file text',0.95,'View spool file',
    '{"ddName":"SYSOUT","content":"SPOOL CONTENT"}'
    ),

    (
    'zowe zos-jobs cancel job','batch','JOB','JES2','Job control','JOB','JOB','EXECUTE',None,None,'MUTABLE',0,0,'MEDIUM','Cancel confirmation','JSON','ZoweExecutionAgent','Cancels job',0.94,'Cancel job',
    '{"jobId":"JOB12345","status":"CANCELLED"}'
    ),

    (
    'zowe zos-jobs delete job','batch','JOB','JES2','Job deletion','JOB','JOB','EXECUTE',None,None,'MUTABLE',0,0,'MEDIUM','Delete confirmation','JSON','ZoweExecutionAgent','Deletes job',0.94,'Delete job',
    '{"jobId":"JOB12345","deleted":true}'
    )
]

job_preconditions = [
    ("JOB_SUBMITTED", "zowe zos-jobs list spool-files"),
    ("JOB_SUBMITTED", "zowe zos-jobs view job-status"),
    ("JOB_COMPLETED", "zowe zos-jobs view job-log"),
    ("JOB_COMPLETED", "zowe zos-jobs view spool-file"),
    ("JOB_RUNNING",   "zowe zos-jobs cancel job"),
    ("JOB_COMPLETED", "zowe zos-jobs delete job"),
]

# ------   Workflow Commands Details  ------
workflow_commands = [
    (
    'zowe zos-workflows list workflows','workflow','WORKFLOW','z/OSMF','Workflow metadata','WORKFLOW','SYSTEM','READ',None,None,'IMMUTABLE',1,1,'LOW','Workflows','JSON','ZoweMonitoringAgent','List workflows',0.97,'List workflows',
    '{"workflows":[{"workflowId":"WF1001","status":"CREATED"}]}'
    ),

    (
    'zowe zos-workflows create workflow','workflow','WORKFLOW','z/OSMF','Workflow definition','WORKFLOW','WORKFLOW','EXECUTE',None,'workflowId','MUTABLE',0,0,'MEDIUM','Workflow ID','JSON','ZoweExecutionAgent','Create workflow',0.95,'Create workflow',
    '{"workflowId":"WF1001","status":"CREATED"}'
    ),

    (
    'zowe zos-workflows start workflow','workflow','WORKFLOW','z/OSMF','Workflow instance','WORKFLOW','WORKFLOW','EXECUTE',None,'workflowId','MUTABLE',0,0,'MEDIUM','Workflow ID','JSON','ZoweExecutionAgent','Start workflow',0.95,'Start workflow',
    '{"workflowId":"WF1001","status":"RUNNING"}'
    ),

    (
    'zowe zos-workflows delete workflow','workflow','WORKFLOW','z/OSMF','Workflow instance','WORKFLOW','WORKFLOW','EXECUTE',None,None,'MUTABLE',0,0,'MEDIUM','Delete confirmation','JSON','ZoweExecutionAgent','Delete workflow',0.94,'Delete workflow',
    '{"workflowId":"WF1001","deleted":true}'
    ),

    (
    'zowe zos-workflows view workflow','workflow','WORKFLOW','z/OSMF','Workflow state','WORKFLOW','WORKFLOW','READ',None,None,'IMMUTABLE',1,1,'LOW','Workflow details','JSON','ZoweMonitoringAgent','View workflow',0.96,'View workflow',
    '{"workflowId":"WF1001","status":"RUNNING"}'
    ),

    (
    'zowe zos-workflows view workflow-definition','workflow','WORKFLOW','z/OSMF','Workflow definition','WORKFLOW','WORKFLOW','READ',None,None,'IMMUTABLE',1,1,'LOW','Workflow definition','JSON','ZoweParsingAgent','View definition',0.96,'View workflow definition',
    '{"workflowId":"WF1001","steps":5}'
    )
]

workflow_preconditions = [
    ("WORKFLOW_CREATED", "zowe zos-workflows start workflow"),
    ("WORKFLOW_STARTED", "zowe zos-workflows view workflow"),
    ("WORKFLOW_STARTED", "zowe zos-workflows delete workflow"),
]

# ------   DB2 Plugin Command Details ------
db2_commands = [
    (
    'zowe db2 list databases','metadata','DB2','DB2','DB2 Catalog','DATABASE','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','DB2 databases','JSON','DiscoveryAgent','List DB2 databases',0.95,'List DB2 databases',
    '{"databases":[{"name":"DSNDB04"}]}'
    ),

    (
    'zowe db2 list tables','metadata','DB2','DB2','DB2 SYSTABLES','TABLE','DATABASE','READ','REST',None,'IMMUTABLE',1,1,'LOW','DB2 tables','JSON','DiscoveryAgent','List DB2 tables',0.95,'List DB2 tables',
    '{"tables":[{"name":"EMPLOYEE"}]}'
    ),

    (
    'zowe db2 execute query','database','DB2','DB2','User tables','TABLE','TABLE','READ','REST',None,'IMMUTABLE',1,1,'MEDIUM','Query result','JSON','IngestAgent','Execute DB2 query',0.95,'Execute DB2 query',
    '{"rows":[{"id":1,"name":"John"}]}'
    )
]

# ------   CICS Plugin Command Details ------
cics_cmmds = [
    (
    'zowe cics list regions','metadata','CICS','CICS','CICS Region Control Table','SYSTEM','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','CICS regions','JSON','DiscoveryAgent','Read-only',0.97,'List CICS regions',
    '{"regions":[{"region":"CICSPROD","status":"ACTIVE"}]}'
    ),

    (
    'zowe cics list programs','metadata','CICS','CICS','Program Definition Table','PROGRAM','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','CICS programs','JSON','DiscoveryAgent','Read-only',0.97,'List CICS programs',
    '{"programs":[{"program":"PAYROLL","enabled":true}]}'
    ),

    (
    'zowe cics list transactions','metadata','CICS','CICS','Transaction Definition Table','TRANSACTION','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','CICS transactions','JSON','MonitoringAgent','Read-only',0.96,'List CICS transactions',
    '{"transactions":[{"tranId":"TX01","status":"ENABLED"}]}'
    ),

    (
    'zowe cics start program','transaction','CICS','CICS','Program Control','PROGRAM','PROGRAM','EXECUTE','REST',None,'MUTABLE',0,0,'MEDIUM','Start confirmation','JSON','ControlAgent','Start program',0.90,'Start CICS program',
    '{"program":"PAYROLL","status":"STARTED"}'
    ),

    (
    'zowe cics stop program','transaction','CICS','CICS','Program Control','PROGRAM','PROGRAM','EXECUTE','REST',None,'MUTABLE',0,0,'MEDIUM','Stop confirmation','JSON','ControlAgent','Stop program',0.90,'Stop CICS program',
    '{"program":"PAYROLL","status":"STOPPED"}'
    )
]

# ------ IMS plugin Command Details ------
ims_cmds = [
    (
    'zowe ims list regions','metadata','IMS','IMS','IMS Region Definition','SYSTEM','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','IMS regions','JSON','DiscoveryAgent','Read-only',0.96,'List IMS regions',
    '{"regions":[{"region":"IMS1","status":"ACTIVE"}]}'
    ),

    (
    'zowe ims list transactions','metadata','IMS','IMS','IMS Transaction Table','TRANSACTION','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','IMS transactions','JSON','MonitoringAgent','Read-only',0.96,'List IMS transactions',
    '{"transactions":[{"tranId":"IMS01","status":"READY"}]}'
    ),

    (
    'zowe ims start transaction','transaction','IMS','IMS','Transaction Control Block','TRANSACTION','TRANSACTION','EXECUTE','REST','transactionId','MUTABLE',0,0,'HIGH','Start confirmation','JSON','ControlAgent','Start IMS transaction',0.90,'Start IMS transaction',
    '{"transactionId":"IMS01","status":"STARTED"}'
    ),

    (
    'zowe ims stop transaction','transaction','IMS','IMS','Transaction Control Block','TRANSACTION','TRANSACTION','EXECUTE','REST','transactionId','MUTABLE',0,0,'HIGH','Stop confirmation','JSON','ControlAgent','Stop IMS transaction',0.90,'Stop IMS transaction',
    '{"transactionId":"IMS01","status":"STOPPED"}'
    )
]

# ====== Plugin_managment Commands Details   =======
plugin_mngmt_cmds = [
    (
    'zowe plugins list','metadata','PLATFORM','z/OSMF','Plugin Registry','SYSTEM','SYSTEM','READ','CLI',None,'IMMUTABLE',1,1,'LOW','Installed plugins','JSON','GovernanceAgent','Read-only',0.98,'List plugins',
    '{"plugins":[{"name":"db2","version":"1.0.0"}]}'
    ),

    (
    'zowe plugins install','workflow','PLATFORM','z/OSMF','Plugin Registry','SYSTEM','SYSTEM','EXECUTE','CLI',None,'MUTABLE',0,0,'MEDIUM','Install confirmation','TEXT','InfraAgent','Install plugin',0.90,'Install plugin',
    '{"plugin":"db2","status":"INSTALLED"}'
    ),

    (
    'zowe plugins update','workflow','PLATFORM','z/OSMF','Plugin Registry','SYSTEM','SYSTEM','EXECUTE','CLI',None,'MUTABLE',0,0,'MEDIUM','Update confirmation','TEXT','InfraAgent','Update plugin',0.90,'Update plugin',
    '{"plugin":"db2","status":"UPDATED"}'
    ),

    (
    'zowe plugins uninstall','workflow','PLATFORM','z/OSMF','Plugin Registry','SYSTEM','SYSTEM','EXECUTE','CLI',None,'MUTABLE',0,0,'MEDIUM','Uninstall confirmation','TEXT','InfraAgent','Uninstall plugin',0.90,'Uninstall plugin',
    '{"plugin":"db2","status":"REMOVED"}'
    )
]

# -------- ZOWE LOGS --------
log_cmds = [
    (
    'zowe logs list','metadata','OBSERVABILITY','z/OSMF','System Logs','SYSTEM','SYSTEM','READ','CLI',None,'IMMUTABLE',1,1,'LOW','Log sources','JSON','MonitoringAgent','Read-only',0.95,'List logs',
    '{"logs":[{"source":"ZOWE","entries":120}]}'
    ),

    (
    'zowe logs view','metadata','OBSERVABILITY','z/OSMF','Log Files','SYSTEM','SYSTEM','READ','CLI',None,'IMMUTABLE',1,1,'LOW','Log content','TEXT','MonitoringAgent','Read-only',0.94,'View log',
    '{"log":"Zowe service started successfully"}'
    )
]

# =======   Datasets Details   =======
dataset_cmds = [
    (
    'zowe files list ds','metadata','FILES','z/OSMF','z/OS Datasets','DATASET','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','Dataset list','JSON','DiscoveryAgent','Read-only dataset list',0.97,'List datasets',
    '{"datasets":[{"name":"USER.DATA","volume":"VOL001"}]}'
    ),

    (
    'zowe files view ds','data','FILES','z/OSMF','Sequential Dataset','DATASET','DATASET','READ','REST',None,'IMMUTABLE',1,1,'MEDIUM','Dataset content','TEXT','IngestAgent','May expose business data',0.95,'View dataset',
    '{"dataset":"USER.DATA","content":"SAMPLE CONTENT"}'
    ),

    (
    'zowe files upload ds','data','FILES','z/OSMF','Dataset Upload','DATASET','DATASET','EXECUTE','REST',None,'MUTABLE',0,0,'HIGH','Upload confirmation','TEXT','ControlAgent','Upload dataset',0.90,'Upload dataset',
    '{"dataset":"USER.DATA","status":"UPLOADED"}'
    )
]

# -------- ZOWE DAEMON --------
deamon_cmds = [
    (
    'zowe daemon status','metadata','PLATFORM','z/OSMF','Background Services','SYSTEM','SYSTEM','READ','CLI',None,'IMMUTABLE',1,1,'LOW','Daemon status','JSON','InfraAgent','Platform diagnostic',0.96,'Daemon status',
    '{"daemon":"Zowe","status":"RUNNING"}'
    ),

    (
    'zowe daemon start','workflow','PLATFORM','z/OSMF','Background Services','SYSTEM','SYSTEM','EXECUTE','CLI',None,'MUTABLE',0,0,'MEDIUM','Start confirmation','TEXT','InfraAgent','Start daemon',0.90,'Start daemon',
    '{"daemon":"Zowe","status":"STARTED"}'
    )
]

# ------   TSO Command Details   ------
tso_cmds = [
    (
    'zowe tso start','tso','TSO','z/OSMF','TSO Address Space','SYSTEM','SYSTEM','EXECUTE','REST','tsoAddressSpaceId','MUTABLE',0,0,'MEDIUM','TSO session token','JSON','ScriptingAgent','Start TSO session',0.96,'Start TSO session',
    '{"tsoAddressSpaceId":"TSO123","status":"ACTIVE"}'
    ),

    (
    'zowe tso send-input','tso','TSO','z/OSMF','REXX Input','SYSTEM','SYSTEM','EXECUTE','REST',None,'MUTABLE',0,0,'MEDIUM','Input status','JSON','ScriptingAgent','Send TSO input',0.95,'Send TSO input',
    '{"status":"INPUT_ACCEPTED"}'
    )
]

# ------   Mainframe Info Commnad Details   -------
zosmf_info = [
    (
    'zowe zosmf info','zosmf','SYSTEM','z/OSMF','z/OSMF Info','SYSTEM','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','System info','JSON','DiscoveryAgent','Read-only',0.99,'Get z/OSMF info',
    '{"version":"2.5","services":["files","jobs","workflows"]}'
    )
]

# ------   ssh Cammand Details   -------
ssh  = [
    (
    'zowe ssh start','ssh','SSH','z/OSMF','USS Shell','SYSTEM','SYSTEM','EXECUTE','REST','sshSessionId','MUTABLE',0,0,'MEDIUM','SSH session','JSON','AutomationAgent','Start SSH session',0.94,'Start SSH session',
    '{"sshSessionId":"SSH123","status":"CONNECTED"}'
    )
]

# ------   Console Cammand Details   -------
console_cmd = [
    (
    'zowe console issue','console','CONSOLE','z/OSMF','MVS Console','SYSTEM','SYSTEM','EXECUTE','REST',None,'MUTABLE',0,0,'HIGH','Console response','TEXT','ControlAgent','Issue console command',0.97,'Issue console command',
    '{"response":"COMMAND EXECUTED"}'
    ),

    (
    'zowe console retrieve','console','CONSOLE','z/OSMF','Console Reply','SYSTEM','SYSTEM','READ','REST','replyToken','IMMUTABLE',1,1,'LOW','Console reply','TEXT','MonitoringAgent','Retrieve console reply',0.97,'Retrieve console reply',
    '{"replyToken":"R123","message":"JOB COMPLETED"}'
    )
]

# ------   File Cammand Details   -------
files_cmds = [
    (
    'zowe files list','files','FILES','z/OSMF','USS Directory','SYSTEM','SYSTEM','READ','REST',None,'IMMUTABLE',1,1,'LOW','USS listing','JSON','DiscoveryAgent','List USS files',0.99,'List USS files',
    '{"files":[{"name":"file.txt","type":"FILE"}]}'
    ),

    (
    'zowe files upload','files','FILES','z/OSMF','USS File','SYSTEM','SYSTEM','EXECUTE','REST',None,'MUTABLE',0,0,'MEDIUM','Upload confirmation','JSON','DataAgent','Upload USS file',0.99,'Upload USS file',
    '{"file":"file.txt","status":"UPLOADED"}'
    )
]


# ALL available Commnads 
zowe_cmds = [
    *job_commands,
    *workflow_commands,
    *db2_commands,
    *cics_cmmds,
    *ims_cmds,
    *plugin_mngmt_cmds,
    *log_cmds,
    *dataset_cmds,
    *deamon_cmds,
    *tso_cmds,
    *zosmf_info,
    *ssh,
    *console_cmd,
    *files_cmds,
]

# ====== Insert Job and workflow commands =======
cursor.executemany("""
    INSERT OR IGNORE INTO zowe_capability (
        zowe_command,
        category,
        command_family,
        subsystem,
        ibm_artifact,
        artifact_granularity,
        data_scope,
        operation,
        access_pattern,
        produces_identifier,
        mutability,
        idempotent,
        deterministic,
        execution_cost,
        data_returned,
        response_format,
        intended_agent,
        constraints,
        confidence_level,
        description,
        output_file
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", zowe_cmds)

cursor.executemany("""
    INSERT OR IGNORE INTO zowe_capability_precondition (capability_id, precondition)
        SELECT id, ?
        FROM zowe_capability
        WHERE zowe_command = ?
    """, job_preconditions)

cursor.executemany("""
    INSERT OR IGNORE INTO zowe_capability_precondition (capability_id, precondition)
    SELECT id, ?
    FROM zowe_capability
    WHERE zowe_command = ?
""", workflow_preconditions)

conn.commit()
conn.close()

print("Zowe Catalog created successfully.")