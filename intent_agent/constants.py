"""
constants.py - Mappings, keywords, and configuration

CRITICAL RULES:
1. ENTITY vs FILTER: Entities are objects, identifiers are FILTERS
2. SYSTEM OWNERSHIP: shopping->Unisys, transactions->IBM, customer->IBM
3. ENTITY PRIORITY: shopping > transactions > customer
"""

# Entity mappings - BUSINESS OBJECTS ONLY, NOT IDENTIFIERS
ENTITY_MAPPINGS = {
    "shopping": "shopping",
    "shopping data": "shopping",
    "behavior": "shopping",
    "behavioral data": "shopping",
    "merchant": "shopping",
    "category spend": "shopping",
    "card usage": "shopping",
    "purchase": "shopping",
    "transaction": "transaction",
    "transactions": "transaction",
    "transfer": "transaction",
    "account": "account",
    "accounts": "account",
}

# Identifier/Filter field mappings (NOT entities)
IDENTIFIER_MAPPINGS = {
    "customer": "customerId",
    "customer id": "customerId",
    "customer-id": "customerId",
    "cid": "customerId",
    "account": "accountId",
    "account id": "accountId",
    "account-id": "accountId",
    "aid": "accountId",
    "merchant id": "merchantId",
    "merchant-id": "merchantId",
}

# Attribute synonyms to canonical names
ATTRIBUTE_MAPPINGS = {
    "account": "accountId",
    "account id": "accountId",
    "balance": "accountBalance",
    "amount": "transactionAmount",
    "date": "transactionDate",
    "merchant": "merchant",
    "category": "category",
    "shopping amount": "amount",
    "shopping date": "date",
    "spend": "spend",
    "transaction amount": "amount",
    "transaction date": "date",
    "spend amount": "amount",
}

# Metric phrases the user may ask for
METRIC_KEYWORDS = {
    "total_spend": ["total spend", "sum of spend", "total amount spent", "total purchase amount"],
    "average_spend": ["average spend", "avg spend", "mean spend"],
    "transaction_count": ["count transactions", "number of transactions", "transaction count"],
}

# Aggregation phrases
AGGREGATION_KEYWORDS = {
    "sum": ["total", "sum", "overall"],
    "avg": ["average", "avg", "mean"],
    "count": ["count", "number of"],
    "max": ["maximum", "highest", "max"],
    "min": ["minimum", "lowest", "min"],
}

# Default attributes for each entity (BUSINESS OBJECTS ONLY)
DEFAULT_ENTITY_ATTRIBUTES = {
    "transaction": ["transactionId", "transactionAmount", "transactionDate", "merchant", "category"],
    "account": ["accountId", "accountBalance", "accountType", "accountStatus"],
    "shopping": ["customerId", "merchant", "amount", "date", "category"],
}

# Task type keywords
TASK_KEYWORDS = {
    "fetch": ["get", "retrieve", "list", "show", "display", "pull", "view", "retrieve"],
    "reconcile": ["reconcile", "match", "compare", "verify", "validate", "check", "align"],
    "analyze": ["analyze", "report", "summary", "stat", "insight", "trend", "pattern"],
    "compare": ["compare", "difference", "diff", "versus", "vs", "between", "against"],
    "transform": ["convert", "transform", "map", "translate", "export", "parse"],
}

# System ownership - CRITICAL RULE
SYSTEM_KEYWORDS = {
    "ibm": ["ibm", "mainframe", "z/os", "zos", "zowe", "cobol", "jcl", "dataset", "job", "transaction"],
    "unisys": ["unisys", "eportal", "portal", "api", "rest", "http", "service", "shopping"],
}

# Entity priority for selection (CRITICAL RULE 3)
# When multiple entities detected, prefer in this order
ENTITY_PRIORITY = ["shopping", "transaction", "account", "customer"]

# System ownership by entity (CRITICAL RULE 2)
ENTITY_SYSTEM_MAPPING = {
    "shopping": "unisys",
    "transaction": "ibm",
    "account": "ibm",
    "customer": "ibm",
}
