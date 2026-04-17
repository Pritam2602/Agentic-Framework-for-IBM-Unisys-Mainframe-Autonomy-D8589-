#  Updated API Behaviors & Examples

## API Response Format Changes

All API responses now include CardDemo entity mapping information.

---

## 1. CUSTOMER API Response

### Endpoint
```bash
GET /api/unisys/customer?customerId=CUST001
```

### Response (Updated)
```json
{
  "source": "unisys_eportal",
  "entity": "customer",
  "carddemo_entity": "CUSTOMER",
  "count": 1,
  "data": [
    {
      "customerId": "CUST001",
      "customerName": "Acme Corporation",
      "email": "admin@acme.com",
      "phone": "+1-555-0101",
      "status": "ACTIVE",
      "customerType": "CORPORATE",
      "customerOpenDate": "2018-03-15",
      "address": "123 Business Ave, New York, NY 10001",
      "industry": "Technology",
      "registrationMethod": "DIRECT_SIGNUP",
      "kyc_status": "VERIFIED"
    }
  ]
}
```

**Changes**:
-  Added `carddemo_entity` field to show mapping
-  Updated field names to match CardDemo (customerOpenDate instead of registrationDate)
-  Added business context fields (address, industry, kyc_status)

---

## 2. ACCOUNT API Response (NEW)

### Endpoint
```bash
GET /api/unisys/account?accountNumber=ACC-10001
```

### Response (New Entity)
```json
{
  "source": "unisys_eportal",
  "entity": "account",
  "carddemo_entity": "ACCOUNT",
  "relationship": "1:1 to Customer, 1:1 to Card, 1:* to Transaction",
  "count": 1,
  "data": [
    {
      "accountNumber": "ACC-10001",
      "customerId": "CUST001",
      "accountType": "CREDIT",
      "accountBalance": 450000.00,
      "currency": "USD",
      "accountOpenDate": "2018-03-15",
      "accountStatus": "ACTIVE",
      "interestRate": 12.5,
      "creditLimit": 500000.00,
      "availableCredit": 50000.00,
      "lastStatementDate": "2026-03-01",
      "nextPaymentDueDate": "2026-03-20"
    }
  ]
}
```

**Features**:
-  New entity for CardDemo Account
-  Includes balance and interest calculation fields
-  Maintains 1:1 relationship with Customer
-  Tracks payment status

---

## 3. CARD API Response (NEW)

### Endpoint
```bash
GET /api/unisys/card?cardNumber=5412-7531-2489-0001
```

### Response (New Entity)
```json
{
  "source": "unisys_eportal",
  "entity": "card",
  "carddemo_entity": "CARD",
  "relationship": "1:1 to Customer and Account",
  "count": 1,
  "data": [
    {
      "cardNumber": "5412-7531-2489-0001",
      "customerId": "CUST001",
      "accountNumber": "ACC-10001",
      "cardStatus": "ACTIVE",
      "cardType": "CREDIT",
      "expiryDate": "2028-03-31",
      "cardholderName": "Acme Corporation",
      "issuedDate": "2018-02-15",
      "cardLimit": 500000.00,
      "dailyLimit": 50000.00,
      "lastUsedDate": "2026-03-15",
      "pin_enabled": true
    }
  ]
}
```

**Features**:
-  New entity for CardDemo Card
-  Maintains 1:1 relationship with Account
-  Includes card lifecycle fields (issued, expiry, status)

---

## 4. TRANSACTION API Response (Updated)

### Endpoint
```bash
GET /api/unisys/transaction?accountNumber=ACC-10001
```

### Response (Updated Format)
```json
{
  "source": "unisys_eportal",
  "entity": "transaction",
  "carddemo_entity": "TRANSACTION",
  "relationship": "Many to Account",
  "count": 3,
  "data": [
    {
      "transactionId": "TXN-20260301-001",
      "accountNumber": "ACC-10001",
      "transactionAmount": 15000.00,
      "transactionDate": "2026-03-01",
      "transactionType": "CREDIT",
      "transactionDescription": "Wire transfer from partner",
      "transactionStatus": "POSTED",
      "currency": "USD",
      "referenceNumber": "EFT-2026-00001"
    },
    {
      "transactionId": "TXN-20260305-004",
      "accountNumber": "ACC-10001",
      "transactionAmount": 3200.00,
      "transactionDate": "2026-03-05",
      "transactionType": "DEBIT",
      "transactionDescription": "Vendor payment - Office supplies",
      "transactionStatus": "POSTED",
      "currency": "USD",
      "referenceNumber": "WIR-2026-00003"
    },
    {
      "transactionId": "TXN-20260316-011",
      "accountNumber": "ACC-10001",
      "transactionAmount": 5500.00,
      "transactionDate": "2026-03-16",
      "transactionType": "CREDIT",
      "transactionDescription": "Interest credit",
      "transactionStatus": "POSTED",
      "currency": "USD",
      "referenceNumber": "INT-2026-00001"
    }
  ]
}
```

**Changes**:
-  Updated field names (`transactionDescription` instead of `description`)
-  Added `carddemo_entity` mapping
-  Changed `accountId` to `accountNumber` for consistency
-  Added reference tracking for batch operations

---

## 5. FEDERATION METADATA Response (NEW)

### Endpoint
```bash
GET /api/unisys/federation-metadata
```

### Response
```json
{
  "system": "unisys_eportal",
  "federation_standard": "AWS CardDemo",
  "version": "1.0.0",
  "entities": {
    "customer": {
      "carddemo_name": "CUSTOMER",
      "count": 10,
      "fields": [
        "customerId",
        "customerName",
        "email",
        "phone",
        "status",
        "customerType",
        "customerOpenDate",
        "address",
        "industry",
        "dateOfBirth",
        "registrationMethod",
        "kyc_status"
      ]
    },
    "account": {
      "carddemo_name": "ACCOUNT",
      "count": 10,
      "fields": [
        "accountNumber",
        "customerId",
        "accountType",
        "accountBalance",
        "currency",
        "accountOpenDate",
        "accountStatus",
        "interestRate",
        "creditLimit",
        "availableCredit",
        "lastStatementDate",
        "nextPaymentDueDate"
      ],
      "relationship": "1:1 to Customer"
    },
    "card": {
      "carddemo_name": "CARD",
      "count": 10,
      "fields": [
        "cardNumber",
        "customerId",
        "accountNumber",
        "cardStatus",
        "cardType",
        "expiryDate",
        "cardholderName",
        "issuedDate",
        "cardLimit",
        "dailyLimit",
        "lastUsedDate",
        "pin_enabled"
      ],
      "relationship": "1:1 to Customer and Account"
    },
    "transaction": {
      "carddemo_name": "TRANSACTION",
      "count": 15,
      "fields": [
        "transactionId",
        "accountNumber",
        "transactionAmount",
        "transactionDate",
        "transactionType",
        "transactionDescription",
        "transactionStatus",
        "currency",
        "referenceNumber"
      ],
      "relationship": "Many to Account"
    }
  },
  "relationships": {
    "customer_account": "1:1 (One customer has one account)",
    "account_card": "1:1 (One account has one card)",
    "account_transaction": "1:* (One account has many transactions)",
    "carddemo_constraint": "1:1:1 relationship enforced between Customer, Account, and Card"
  }
}
```

**Purpose**: Enables Context Resolution Agent to understand entity relationships without parsing schemas.

---

## 6. SCHEMA ENDPOINT Responses (Updated)

### Endpoint
```bash
GET /schema/account
```

### Response
```json
{
  "entity": "account",
  "description": "Financial account entity from AWS CardDemo",
  "source_system": "unisys_eportal",
  "mapped_to": "IBM CardDemo Account",
  "fields": [
    {
      "name": "accountNumber",
      "type": "string",
      "description": "Unique account identifier",
      "primary_key": true
    },
    {
      "name": "customerId",
      "type": "string",
      "description": "Foreign key to Customer"
    },
    {
      "name": "accountType",
      "type": "string",
      "description": "Account type (CREDIT/SAVINGS/CHECKING)"
    },
    {
      "name": "accountBalance",
      "type": "number",
      "description": "Current account balance"
    },
    {
      "name": "accountStatus",
      "type": "string",
      "description": "Account status (ACTIVE/INACTIVE/SUSPENDED/CLOSED)"
    },
    {
      "name": "interestRate",
      "type": "number",
      "description": "Applied interest rate (annual %)"
    }
  ],
  "filterable_fields": ["accountNumber", "customerId", "accountStatus", "accountType"],
  "relationship": "1:1 to Customer, 1:1 to Card, 1:* to Transaction",
  "carddemo_mapping": {
    "accountNumber": "ACCOUNT ID",
    "accountBalance": "ACCOUNT BALANCE",
    "accountStatus": "ACCOUNT STATUS",
    "interestRate": "INTEREST RATE (for batch interest calculations)"
  },
  "record_count": 10
}
```

---

## 7. MCP Tools Response (Updated)

### Endpoint
```bash
GET /mcp/tools
```

### Response (Partial)
```json
{
  "source": "unisys_eportal",
  "protocol": "mcp",
  "version": "1.0",
  "federation_standard": "AWS CardDemo",
  "relationship_model": "1:1:1 between Customer, Account, Card; 1:* to Transaction",
  "tools": [
    {
      "name": "get_customer",
      "description": "Retrieve customer records from Unisys DMSII database. Maps to AWS CardDemo Customer entity.",
      "endpoint": "/api/unisys/customer",
      "carddemo_entity": "CUSTOMER",
      "params": [...],
      "output_fields": ["customerId", "customerName", "email", "phone", "status", "customerType", ...],
      "schema_endpoint": "/schema/customer"
    },
    {
      "name": "get_account",
      "description": "Retrieve account records from Unisys VSAM database. Maps to AWS CardDemo Account entity.",
      "endpoint": "/api/unisys/account",
      "carddemo_entity": "ACCOUNT",
      "relationship": "1:1 to Customer (CardDemo constraint)",
      "params": [...],
      "output_fields": ["accountNumber", "customerId", "accountType", "accountBalance", ...],
      "schema_endpoint": "/schema/account"
    },
    {
      "name": "get_card",
      "description": "Retrieve card records from Unisys VSAM database. Maps to AWS CardDemo Card entity.",
      "endpoint": "/api/unisys/card",
      "carddemo_entity": "CARD",
      "relationship": "1:1 to Account and Customer (CardDemo constraint)",
      "params": [...],
      "output_fields": ["cardNumber", "customerId", "accountNumber", "cardStatus", ...],
      "schema_endpoint": "/schema/card"
    },
    {
      "name": "get_transaction",
      "description": "Retrieve financial transaction records from Unisys MCP transaction processor. Maps to AWS CardDemo Transaction entity.",
      "endpoint": "/api/unisys/transaction",
      "carddemo_entity": "TRANSACTION",
      "relationship": "Many to Account (CardDemo constraint)",
      "params": [...],
      "output_fields": ["transactionId", "accountNumber", "transactionAmount", ...],
      "schema_endpoint": "/schema/transaction"
    }
  ],
  "tool_count": 4,
  "federation_metadata_endpoint": "/api/unisys/federation-metadata"
}
```

---

## Summary of Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Customer Entities** | 1 (payroll) | Removed  |
| **Relevant Entities** | 3 (customer, transaction, ) | 4 (customer, account, card, transaction) |
| **Field Naming** | Arbitrary (creditLimit) | CardDemo Standard |
| **Relationships** | Implicit | Explicit in responses |
| **MCP Tools** | 3 | 4 |
| **API Endpoints** | /api/unisys/{payroll,customer,transaction} | /api/unisys/{customer,account,card,transaction} |
| **Federation** | Not aligned  | CardDemo aligned  |

---

##  How This Enables Federation

### Before (Non-Aligned)
```
User Query: "Show Acme's account balance and card status"

Intent Agent: [confused - different field names]

Context Resolution Agent: [can't map customerId  employeeId]

 Federation fails - Systems not semantically equivalent
```

### After (CardDemo Aligned)
```
User Query: "Show Acme's account balance and card status"

Intent Agent: "Customer=Acme, Entities=[account, card]"

Context Resolution Agent:
  - Looks up CUSTOMER (both systems): customerId=CUST001
  - Finds ACCOUNT: accountNumber=ACC-10001 (1:1 relationship)
  - Finds CARD: cardNumber=5412-7531-2489-0001 (1:1 relationship)

Planner Agent:
  - IBM: SELECT * FROM CUSTOMER WHERE CUSTOMER_ID='CUST001'
  - Unisys: GET /api/unisys/customer?customerId=CUST001
  - IBM: SELECT * FROM ACCOUNT WHERE ACCOUNT_NUMBER='ACC-10001'
  - Unisys: GET /api/unisys/account?accountNumber=ACC-10001
  - (repeat for card)

Result Aggregator: Merges IBM and Unisys results using shared IDs

 Unified data presented to user
```

---

**Version**: 1.0.0  
**Date**: 2026-04-17  
**Standard**: AWS CardDemo
