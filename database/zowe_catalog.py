import sqlite3

conn = sqlite3.connect("database/zowe_catalog.db")

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

# ============================================================================
# INTENT-AGENT CATALOG (zowe_capability_catalog)
# Used by the IntentAgent pipeline for intent classification and command mapping
# ============================================================================

# Drop old bad data if present
cursor.execute("DROP TABLE IF EXISTS catalog_fts")
cursor.execute("DROP TABLE IF EXISTS zowe_capability_catalog")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS zowe_capability_catalog (
        command_id          TEXT PRIMARY KEY,
        intent_type         TEXT NOT NULL,
        plugin_namespace    TEXT NOT NULL,
        command_template    TEXT NOT NULL,
        description         TEXT NOT NULL,
        keywords            TEXT NOT NULL,
        required_params     TEXT NOT NULL DEFAULT '[]',
        optional_params     TEXT NOT NULL DEFAULT '[]',
        risk_level          TEXT NOT NULL DEFAULT 'LOW'
                            CHECK(risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
        environment_gate    TEXT NOT NULL DEFAULT 'ALL'
                            CHECK(environment_gate IN ('ALL','PROD_RESTRICTED','DEV_ONLY')),
        active              INTEGER NOT NULL DEFAULT 1
    )
""")

# 30 intent-agent catalog entries with proper command IDs and intent types
intent_catalog_data = [
    ('CMD_JOB_SUBMIT_DS', 'JOB_SUBMIT', 'zowe-cli', 'zowe jobs submit ds "{{primaryIdentifier}}" --wfo', 'Submit a batch job from a partitioned dataset member or sequential JCL dataset', 'submit,run,execute,kick off,launch,start,job,jcl,batch,pds,member', '["primaryIdentifier"]', '["environment","subsystem"]', 'MEDIUM', 'ALL', 1),
    ('CMD_JOB_SUBMIT_LOCAL', 'JOB_SUBMIT', 'zowe-cli', 'zowe jobs submit lf "{{localFile}}" --wfo', 'Submit a batch job from a local JCL file on the workstation', 'submit,run,execute,job,local,file,jcl,upload and run', '["localFile"]', '["environment"]', 'MEDIUM', 'ALL', 1),
    ('CMD_JOB_CANCEL', 'JOB_CANCEL', 'zowe-cli', 'zowe jobs cancel job "{{primaryIdentifier}}"', 'Cancel a running or waiting batch job by job name or job ID', 'cancel,stop,abort,kill,terminate,halt,job', '["primaryIdentifier"]', '["subsystem"]', 'HIGH', 'ALL', 1),
    ('CMD_JOB_STATUS_SINGLE', 'JOB_STATUS', 'zowe-cli', 'zowe jobs view job-status-by-jobid "{{primaryIdentifier}}"', 'Retrieve the execution status of a single job by job name or job ID', 'status,check,is it running,what happened,view,job,single,specific', '["primaryIdentifier"]', '["owner","subsystem"]', 'LOW', 'ALL', 1),
    ('CMD_JOB_LIST_BY_PREFIX', 'JOB_LIST', 'zowe-cli', 'zowe jobs list jobs --prefix "{{primaryIdentifier}}" --owner "{{owner}}"', 'List multiple batch jobs matching a name prefix pattern, filterable by owner and status', 'list,show,find,search,all jobs,prefix,batch,queue,jes,multiple,jobs', '["primaryIdentifier"]', '["owner","status","maxCount","subsystem"]', 'LOW', 'ALL', 1),
    ('CMD_JOB_LIST_BY_OWNER', 'JOB_LIST', 'zowe-cli', 'zowe jobs list jobs --owner "{{owner}}"', 'List all jobs submitted by a specific TSO user ID or service account', 'list,show,jobs,owner,user,submitted by,service account,tso', '["owner"]', '["status","maxCount"]', 'LOW', 'ALL', 1),
    ('CMD_JOB_OUTPUT_RETRIEVE', 'JOB_OUTPUT_RETRIEVE', 'zowe-cli', 'zowe jobs view all-spool-content "{{primaryIdentifier}}"', 'Retrieve all spool output, JESMSGLG, JESJCL, and JESYSMSG for a completed job', 'output,spool,log,jesmsglg,jesjcl,jesysmsg,messages,results,rc,return code,retrieve,get output', '["primaryIdentifier"]', '["owner","ddName"]', 'LOW', 'ALL', 1),
    ('CMD_JOB_OUTPUT_DOWNLOAD', 'JOB_OUTPUT_RETRIEVE', 'zowe-cli', 'zowe jobs download output "{{primaryIdentifier}}" --directory "{{outputDir}}"', 'Download all spool files from a job to a local directory', 'download,save,export,output,spool,job,local,directory', '["primaryIdentifier"]', '["outputDir","owner"]', 'LOW', 'ALL', 1),
    ('CMD_DS_ALLOCATE_SEQ', 'DATASET_ALLOCATE', 'zowe-cli', 'zowe files create data-set-sequential "{{primaryIdentifier}}" --size "{{primarySpace}}{{spaceUnit}}"', 'Allocate a new sequential (PS) dataset on the mainframe', 'allocate,create,define,new,sequential,ps,dataset,file,mainframe', '["primaryIdentifier"]', '["primarySpace","spaceUnit","recordFormat","recordLength","blockSize"]', 'MEDIUM', 'ALL', 1),
    ('CMD_DS_ALLOCATE_PDS', 'DATASET_ALLOCATE', 'zowe-cli', 'zowe files create data-set-partitioned "{{primaryIdentifier}}" --size "{{primarySpace}}{{spaceUnit}}"', 'Allocate a new partitioned dataset (PDS or PDSE) on the mainframe', 'allocate,create,define,pds,pdse,partitioned,library,dataset,members', '["primaryIdentifier"]', '["primarySpace","spaceUnit","dirBlocks","recordFormat","recordLength"]', 'MEDIUM', 'ALL', 1),
    ('CMD_DS_ALLOCATE_VSAM', 'DATASET_ALLOCATE', 'zowe-cli', 'zowe files create data-set-vsam "{{primaryIdentifier}}" --data-set-organization {{vsamType}}', 'Allocate a new VSAM dataset (KSDS, ESDS, RRDS) on the mainframe', 'allocate,create,define,vsam,ksds,esds,rrds,cluster,dataset', '["primaryIdentifier","vsamType"]', '["primarySpace","spaceUnit","keyLength","keyOffset"]', 'MEDIUM', 'ALL', 1),
    ('CMD_DS_DELETE', 'DATASET_DELETE', 'zowe-cli', 'zowe files delete data-set "{{primaryIdentifier}}" --for-sure', 'Delete and uncatalog a sequential, PDS, or VSAM dataset from the mainframe', 'delete,scratch,uncatalog,remove,destroy,drop,dataset,file,purge', '["primaryIdentifier"]', '["environment"]', 'CRITICAL', 'PROD_RESTRICTED', 1),
    ('CMD_DS_DELETE_MEMBER', 'DATASET_DELETE', 'zowe-cli', 'zowe files delete data-set "{{primaryIdentifier}}({{memberName}})" --for-sure', 'Delete a specific member from a partitioned dataset', 'delete,remove,scratch,member,pds,library,jcl', '["primaryIdentifier","memberName"]', '[]', 'HIGH', 'ALL', 1),
    ('CMD_DS_LIST_HLQ', 'DATASET_LIST', 'zowe-cli', 'zowe files list ds "{{qualifier}}.*"', 'List all datasets under a high-level qualifier or dataset name pattern', 'list,show,browse,find,datasets,hlq,qualifier,pattern,prefix,all datasets', '["qualifier"]', '["maxLength"]', 'LOW', 'ALL', 1),
    ('CMD_DS_LIST_MEMBERS', 'DATASET_LIST', 'zowe-cli', 'zowe files list am "{{primaryIdentifier}}"', 'List all members within a partitioned dataset or PDS library', 'list,show,members,pds,library,contents,jcl,members of', '["primaryIdentifier"]', '[]', 'LOW', 'ALL', 1),
    ('CMD_DS_DOWNLOAD', 'DATASET_DOWNLOAD', 'zowe-cli', 'zowe files download ds "{{primaryIdentifier}}" --file "{{localFile}}"', 'Download a sequential dataset or PDS member to a local file', 'download,export,get,retrieve,pull,copy to local,dataset,file', '["primaryIdentifier"]', '["localFile","encoding"]', 'LOW', 'ALL', 1),
    ('CMD_DS_UPLOAD', 'DATASET_UPLOAD', 'zowe-cli', 'zowe files upload file-to-data-set "{{localFile}}" "{{primaryIdentifier}}"', 'Upload a local file to a mainframe sequential dataset or PDS member', 'upload,import,put,send,copy to mainframe,deploy,push,dataset', '["localFile","primaryIdentifier"]', '["encoding","memberName"]', 'MEDIUM', 'ALL', 1),
    ('CMD_DS_COPY', 'DATASET_COPY', 'zowe-cli', 'zowe files copy data-set "{{primaryIdentifier}}" "{{targetDataset}}"', 'Copy a sequential dataset or PDS to another dataset name', 'copy,duplicate,clone,replicate,dataset,from,to', '["primaryIdentifier","targetDataset"]', '["replace","memberName"]', 'MEDIUM', 'ALL', 1),
    ('CMD_DS_VIEW_MEMBER', 'DATASET_LIST', 'zowe-cli', 'zowe files view ds "{{primaryIdentifier}}({{memberName}})"', 'Display the contents of a PDS member or sequential dataset inline', 'view,browse,read,display,show contents,member,pds,parmlib,jcl', '["primaryIdentifier"]', '["memberName","encoding"]', 'LOW', 'ALL', 1),
    ('CMD_DS_GDG_LIST', 'DATASET_LIST', 'zowe-cli', 'zowe files list ds "{{primaryIdentifier}}.*"', 'List all generation datasets under a GDG base name', 'gdg,generation,generation data group,generations,list,base,datasets', '["primaryIdentifier"]', '[]', 'LOW', 'ALL', 1),
    ('CMD_DB2_EXPLAIN', 'DB2_QUERY_EXPLAIN', 'zowe-db2-plugin', 'zowe db2 execute sql --query "EXPLAIN ALL SET QUERYNO={{queryNo}} FOR {{sqlStatement}}" --subsystem {{subsystem}}', 'Explain the access path and optimizer plan for a DB2 SQL query', 'explain,access path,query plan,optimizer,db2,sql,performance,index,tablespace', '["subsystem","sqlStatement"]', '["queryNo","environment"]', 'LOW', 'ALL', 1),
    ('CMD_DB2_BIND_PLAN', 'DB2_BIND', 'zowe-db2-plugin', 'zowe db2 execute sql --query "BIND PLAN({{planName}}) PKLIST({{packageList}}) ISOLATION({{isolation}})" --subsystem {{subsystem}}', 'Bind or rebind a DB2 application plan on a specified subsystem', 'bind,rebind,plan,package,db2,application,isolation,cs,rr,ur', '["planName","subsystem"]', '["packageList","isolation","owner","qualifier"]', 'HIGH', 'PROD_RESTRICTED', 1),
    ('CMD_DB2_BIND_PACKAGE', 'DB2_BIND', 'zowe-db2-plugin', 'zowe db2 execute sql --query "BIND PACKAGE({{collection}}/{{packageName}}) MEMBER({{dbrmName}}) ISOLATION({{isolation}})" --subsystem {{subsystem}}', 'Bind a DBRM into a DB2 package within a collection', 'bind,package,dbrm,collection,db2,member,program,isolation', '["packageName","dbrmName","subsystem","collection"]', '["isolation","planName"]', 'HIGH', 'PROD_RESTRICTED', 1),
    ('CMD_DB2_RUNSTATS', 'DB2_RUNSTATS', 'zowe-db2-plugin', 'zowe db2 execute sql --query "RUNSTATS TABLESPACE {{tablespace}} TABLE ALL INDEX ALL" --subsystem {{subsystem}}', 'Run DB2 RUNSTATS utility to update catalog statistics for a tablespace', 'runstats,statistics,catalog stats,tablespace,db2,table,index,optimizer', '["tablespace","subsystem"]', '["tableList","shrlevel","environment"]', 'MEDIUM', 'ALL', 1),
    ('CMD_DB2_QUERY_CATALOG', 'DB2_QUERY_EXPLAIN', 'zowe-db2-plugin', 'zowe db2 execute sql --query "{{sqlStatement}}" --subsystem {{subsystem}}', 'Execute a read-only SQL query against DB2 catalog tables or application tables', 'catalog,statistics,sysibm,systables,syscolumns,show,query,select,db2,information', '["sqlStatement","subsystem"]', '["maxRows","environment"]', 'LOW', 'ALL', 1),
    ('CMD_USS_LIST', 'USS_FILE_LIST', 'zowe-cli', 'zowe files list uss "{{primaryIdentifier}}"', 'List files and directories in a Unix System Services (USS) path', 'list,show,uss,unix,files,directory,path,ls,z/os unix', '["primaryIdentifier"]', '["maxLength","group"]', 'LOW', 'ALL', 1),
    ('CMD_USS_READ', 'USS_FILE_READ', 'zowe-cli', 'zowe files view uss-file "{{primaryIdentifier}}"', 'Display the contents of a USS file on z/OS Unix System Services', 'read,view,cat,display,show,uss,unix,file,contents,z/os unix', '["primaryIdentifier"]', '["encoding"]', 'LOW', 'ALL', 1),
    ('CMD_USS_WRITE', 'USS_FILE_WRITE', 'zowe-cli', 'zowe files upload file-to-uss "{{localFile}}" "{{primaryIdentifier}}"', 'Upload a local file to a USS path on z/OS Unix System Services', 'write,upload,put,send,uss,unix,file,deploy,z/os unix', '["localFile","primaryIdentifier"]', '["encoding","permissions"]', 'MEDIUM', 'ALL', 1),
    ('CMD_CONFIG_PROFILE_LIST', 'CONFIG_PROFILE_LIST', 'zowe-cli', 'zowe config list', 'List all configured Zowe profiles and connection configurations', 'config,profiles,list,show,connections,mainframe,credentials,settings', '[]', '[]', 'LOW', 'ALL', 1),
    ('CMD_CONFIG_PROFILE_SET', 'CONFIG_PROFILE_SET', 'zowe-cli', 'zowe config set "{{configKey}}" "{{configValue}}"', 'Set or update a Zowe configuration property or default profile', 'set,configure,update,profile,default,connection,host,port,credentials', '["configKey","configValue"]', '[]', 'MEDIUM', 'ALL', 1),
]

cursor.executemany("""
    INSERT OR REPLACE INTO zowe_capability_catalog
    (command_id, intent_type, plugin_namespace, command_template, description,
     keywords, required_params, optional_params, risk_level, environment_gate, active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", intent_catalog_data)

# FTS5 full-text search index for fast keyword matching
# Drop all FTS shadow tables first to avoid malformed DB
for suffix in ['', '_data', '_idx', '_docsize', '_config', '_content']:
    cursor.execute(f"DROP TABLE IF EXISTS catalog_fts{suffix}")

cursor.execute("""
    CREATE VIRTUAL TABLE catalog_fts USING fts5(
        command_id,
        description,
        keywords,
        content='zowe_capability_catalog',
        content_rowid='rowid'
    )
""")

# Populate FTS index (table is freshly created, no need to DELETE first)
cursor.execute("""
    INSERT INTO catalog_fts(rowid, command_id, description, keywords)
    SELECT rowid, command_id, description, keywords FROM zowe_capability_catalog
""")

# ============================================================================
# AGENT RUNS TELEMETRY TABLE
# Records every IntentAgent pipeline execution for observability
# ============================================================================

cursor.execute("DROP TABLE IF EXISTS agent_runs")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_runs (
        run_id              TEXT PRIMARY KEY,
        created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        prompt_hash         TEXT NOT NULL,
        prompt_length_chars INTEGER NOT NULL,
        model_used          TEXT NOT NULL,
        model_provider      TEXT NOT NULL,
        model_temperature   REAL NOT NULL DEFAULT 0.0,
        latency_ms_total    INTEGER NOT NULL DEFAULT 0,
        latency_ms_llm      INTEGER,
        latency_ms_catalog  INTEGER,
        token_count_input   INTEGER,
        token_count_output  INTEGER,
        retry_count         INTEGER NOT NULL DEFAULT 0,
        intent_type         TEXT NOT NULL,
        selected_command_id TEXT,
        confidence          REAL NOT NULL DEFAULT 0.0,
        candidate_count     INTEGER NOT NULL DEFAULT 0,
        status              TEXT NOT NULL DEFAULT 'SUCCESS'
                            CHECK(status IN ('SUCCESS','UNKNOWN','SCHEMA_FAILURE',
                                             'CATALOG_UNAVAILABLE','HALLUCINATION_DETECTED')),
        requires_review     INTEGER NOT NULL DEFAULT 0,
        mcp_dispatched_at   TEXT,
        mcp_decision        TEXT,
        estimated_cost_usd  REAL,
        error_code          TEXT,
        error_message       TEXT,
        session_id          TEXT,
        operator_id_hash    TEXT,
        raw_output          TEXT,
        alternative_candidates TEXT
    )
""")

# ============================================================================
# CATALOG METADATA TABLE
# ============================================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalog_meta (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
""")

cursor.execute("""
    INSERT OR REPLACE INTO catalog_meta (key, value) VALUES ('schema_version', '2.0.0')
""")
cursor.execute("""
    INSERT OR REPLACE INTO catalog_meta (key, value) VALUES ('last_updated', datetime('now'))
""")

conn.commit()
conn.close()

print("Zowe Catalog created successfully (with intent-agent catalog + FTS + telemetry).")