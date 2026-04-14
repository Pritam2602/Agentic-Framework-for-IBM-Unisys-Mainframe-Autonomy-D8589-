"""
constants.py - Mappings, keywords, and configuration
"""

# Entity synonyms to canonical names
ENTITY_MAPPINGS = {
    "payroll": "payroll",
    "payroll data": "payroll",
    "employee": "payroll",
    "salary": "payroll",
    "customer": "customer",
    "customer data": "customer",
    "account": "account",
    "transaction": "transaction",
    "transactions": "transaction",
}

# Attribute synonyms to canonical names
ATTRIBUTE_MAPPINGS = {
    "salary": "netSalary",
    "net salary": "netSalary",
    "pay": "netSalary",
    "employee": "employeeId",
    "employee id": "employeeId",
    "emp id": "employeeId",
    "name": "employeeName",
    "account": "accountId",
    "account id": "accountId",
    "balance": "accountBalance",
    "amount": "transactionAmount",
    "date": "transactionDate",
}

# Default attributes for each entity
DEFAULT_ENTITY_ATTRIBUTES = {
    "payroll": ["employeeId", "netSalary", "employeeName"],
    "customer": ["customerId", "customerName", "accountId"],
    "transaction": ["transactionId", "transactionAmount", "transactionDate"],
    "account": ["accountId", "accountBalance", "accountType"],
}

# Task type keywords
TASK_KEYWORDS = {
    "fetch": ["get", "retrieve", "list", "show", "display", "pull", "view"],
    "reconcile": ["reconcile", "match", "compare", "verify", "validate", "check"],
    "analyze": ["analyze", "analyze", "report", "summary", "stat", "insight"],
    "compare": ["compare", "difference", "diff", "versus", "vs", "between"],
    "transform": ["convert", "transform", "map", "translate", "export"],
}

# System keywords
SYSTEM_KEYWORDS = {
    "ibm": ["ibm", "mainframe", "z/os", "zos", "zowe", "cobol", "jcl", "dataset", "job"],
    "unisys": ["unisys", "eportal", "api", "rest", "http", "service"],
}
