#  Unisys ePortal - AWS CardDemo Alignment

## Overview

This document explains how the Unisys ePortal mock system has been **aligned with the AWS CardDemo dataset** to enable semantic federation and unified data representation across both IBM and Unisys systems.

---

##  Alignment Objectives

1. **Semantic Alignment**: Both systems represent the SAME business entities with consistent field naming
2. **Federation Ready**: Enables the Context Resolution Agent to map queries across systems
3. **CardDemo Compliance**: Follows AWS CardDemo's 1:1:1 relationship model
4. **Data Consistency**: Mock data reflects realistic credit card management scenarios

---

##  ENTITY MAPPING

### 1. Customer Entity

**Purpose**: Represents account holders (individual or corporate)

| Field | Unisys | CardDemo | Type | Notes |
|-------|--------|----------|------|-------|
| **ID** | `customerId` | `customerId` | string | Primary Key |
| **Name** | `customerName` | `customerName` | string | Full name or company name |
| **Email** | `email` | `email` | string | Contact email |
| **Phone** | `phone` | `phone` | string | Contact phone |
| **Status** | `status` | `status` | enum | ACTIVE/INACTIVE/SUSPENDED |
| **Type** | `customerType` | `customerType` | enum | INDIVIDUAL/CORPORATE |
| **Open Date** | `customerOpenDate` | `customerOpenDate` | date | Account opening date |
| **Address** | `address` | `address` | string | Physical address |
| **KYC** | `kyc_status` | `kyc_status` | enum | VERIFIED/PENDING |

**CardDemo Alignment**: Maps directly to CardDemo CUSTOMER entity

**Sample Data**:
```json
{
  "customerId": "CUST001",
  "customerName": "Acme Corporation",
  "email": "admin@acme.com",
  "phone": "+1-555-0101",
  "status": "ACTIVE",
  "customerType": "CORPORATE",
  "customerOpenDate": "2018-03-15",
  "address": "123 Business Ave, New York, NY 10001",
  "kyc_status": "VERIFIED"
}
```

---

### 2. Account Entity  NEW

**Purpose**: Represents financial accounts (checking/savings/credit)

| Field | Unisys | CardDemo | Type | Notes |
|-------|--------|----------|------|-------|
| **ID** | `accountNumber` | `accountNumber` | string | Primary Key |
| **Customer** | `customerId` | `customerId` | FK | Foreign key to Customer (1:1) |
| **Type** | `accountType` | `accountType` | enum | CREDIT/SAVINGS/CHECKING |
| **Balance** | `accountBalance` | `balance` | number | Current account balance |
| **Currency** | `currency` | `currency` | string | USD, EUR, etc. |
| **Open Date** | `accountOpenDate` | `openDate` | date | When account opened |
| **Status** | `accountStatus` | `status` | enum | ACTIVE/INACTIVE/SUSPENDED |
| **Interest** | `interestRate` | `interestRate` | number | Annual interest rate |
| **Credit Limit** | `creditLimit` | `creditLimit` | number | For credit accounts |

**CardDemo Alignment**: Maps to CardDemo ACCOUNT entity. Enforces 1:1 relationship with Customer.

**Sample Data**:
```json
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
  "availableCredit": 50000.00
}
```

---

### 3. Card Entity  NEW

**Purpose**: Represents credit/debit cards

| Field | Unisys | CardDemo | Type | Notes |
|-------|--------|----------|------|-------|
| **ID** | `cardNumber` | `cardNumber` | string | PAN (Primary Key) |
| **Customer** | `customerId` | `customerId` | FK | Foreign key to Customer |
| **Account** | `accountNumber` | `accountNumber` | FK | Foreign key to Account (1:1) |
| **Status** | `cardStatus` | `cardStatus` | enum | ACTIVE/EXPIRED/BLOCKED |
| **Type** | `cardType` | `cardType` | enum | CREDIT/DEBIT |
| **Expiry** | `expiryDate` | `expiryDate` | date | Card expiry date |
| **Holder** | `cardholderName` | `cardholderName` | string | Cardholder name |
| **Issued** | `issuedDate` | `issuedDate` | date | Card issue date |

**CardDemo Alignment**: Maps to CardDemo CARD entity. Enforces 1:1 relationship with Account.

**Sample Data**:
```json
{
  "cardNumber": "5412-7531-2489-0001",
  "customerId": "CUST001",
  "accountNumber": "ACC-10001",
  "cardStatus": "ACTIVE",
  "cardType": "CREDIT",
  "expiryDate": "2028-03-31",
  "cardholderName": "Acme Corporation",
  "issuedDate": "2018-02-15",
  "cardLimit": 500000.00
}
```

---

### 4. Transaction Entity

**Purpose**: Represents financial transactions

| Field | Unisys | CardDemo | Type | Notes |
|-------|--------|----------|------|-------|
| **ID** | `transactionId` | `transactionId` | string | Primary Key |
| **Account** | `accountNumber` | `accountNumber` | FK | Foreign key to Account |
| **Amount** | `transactionAmount` | `transactionAmount` | number | Transaction amount |
| **Date** | `transactionDate` | `transactionDate` | date | Transaction date |
| **Type** | `transactionType` | `transactionType` | enum | CREDIT/DEBIT/TRANSFER |
| **Description** | `transactionDescription` | `description` | string | Transaction details |
| **Status** | `transactionStatus` | `status` | enum | POSTED/PENDING |
| **Currency** | `currency` | `currency` | string | Transaction currency |

**CardDemo Alignment**: Maps to CardDemo TRANSACTION entity. Maintains 1:* relationship with Account.

**Sample Data**:
```json
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
}
```

---

##  REMOVED ENTITIES

###  Payroll (DEPRECATED)

**Reason**: Not part of AWS CardDemo scope

CardDemo is a credit card / account management system. Payroll/HR data is out of scope.

**Migration**: Payroll entity, service, schema, and API endpoints have been removed.

---

##  RELATIONSHIP MODEL

### CardDemo 1:1:1 Constraint

```
     1:1           1:1      
  CUSTOMER       ACCOUNT         CARD     
                            
                                    
                                    
                                 1:*
                                    
                             
                              TRANSACTION  
                             
       
       (Foreign Key Relationships)
```

**Rules:**
- Each CUSTOMER has exactly ONE ACCOUNT (1:1)
- Each ACCOUNT has exactly ONE CARD (1:1)
- Each ACCOUNT has MANY TRANSACTIONs (1:*)
- Each TRANSACTION references exactly ONE ACCOUNT
- Each CARD references exactly ONE ACCOUNT and ONE CUSTOMER

---

##  API ENDPOINTS

### Customer API

```bash
GET /api/unisys/customer
GET /api/unisys/customer?customerId=CUST001
GET /api/unisys/customer?status=ACTIVE
GET /api/unisys/customer?customerType=CORPORATE
```

### Account API (NEW)

```bash
GET /api/unisys/account
GET /api/unisys/account?accountNumber=ACC-10001
GET /api/unisys/account?customerId=CUST001
GET /api/unisys/account?accountStatus=ACTIVE
GET /api/unisys/account?accountType=CREDIT
```

### Card API (NEW)

```bash
GET /api/unisys/card
GET /api/unisys/card?cardNumber=5412-7531-2489-0001
GET /api/unisys/card?customerId=CUST001
GET /api/unisys/card?accountNumber=ACC-10001
GET /api/unisys/card?cardStatus=ACTIVE
```

### Transaction API

```bash
GET /api/unisys/transaction
GET /api/unisys/transaction?accountNumber=ACC-10001
GET /api/unisys/transaction?transactionType=CREDIT
GET /api/unisys/transaction?startDate=2026-03-01&endDate=2026-03-31
```

### Federation Metadata

```bash
GET /api/unisys/federation-metadata
```

Returns entity relationships and CardDemo alignment info.

---

##  MCP TOOLS

All MCP tools now reference CardDemo entities:

| Tool | Endpoint | CardDemo Entity | Params |
|------|----------|-----------------|--------|
| `get_customer` | `/api/unisys/customer` | CUSTOMER | customerId, status, customerType |
| `get_account` | `/api/unisys/account` | ACCOUNT | accountNumber, customerId, accountStatus |
| `get_card` | `/api/unisys/card` | CARD | cardNumber, customerId, accountNumber |
| `get_transaction` | `/api/unisys/transaction` | TRANSACTION | accountNumber, transactionType, dateRange |

---

##  SCHEMA ENDPOINTS

### Schema Discovery

```bash
GET /schema/customer          # CardDemo Customer schema
GET /schema/account           # CardDemo Account schema (NEW)
GET /schema/card              # CardDemo Card schema (NEW)
GET /schema/transaction       # CardDemo Transaction schema
GET /schema/all               # All schemas with relationships
```

### Entity Relationships

```bash
GET /schema/entity-relationships  # CardDemo 1:1:1 constraint model
```

---

##  MOCK DATA

**Record Counts:**
- Customers: 10 records
- Accounts: 10 records (1:1 with customers)
- Cards: 10 records (1:1 with accounts)
- Transactions: 15 records (various accounts)

**Data Characteristics:**
- Realistic business entities (Acme Corp, Northeast Banking, etc.)
- Realistic financial amounts (balances, interest rates)
- Realistic dates (ranging from 2016 to 2026)
- Status variations (ACTIVE, SUSPENDED, INACTIVE, BLOCKED)
- Diverse account types (CREDIT, SAVINGS)

---

##  Federation Context Resolution

### How Systems Map

When a user queries "Show me Acme's account and card details":

1. **Intent Agent** extracts: customer=Acme, entities=[account, card]
2. **Context Resolution Agent**:
   - Looks up CUSTOMER: `customerId=CUST001` (IBM CardDemo schema)
   - Maps to Unisys ePortal: `customerId=CUST001`
   - Uses 1:1 relationship to find: `accountNumber=ACC-10001`
   - Uses 1:1 relationship to find: `cardNumber=5412-7531-2489-0001`
3. **Planner Agent** executes:
   - `GET /api/unisys/account?customerId=CUST001`
   - `GET /api/unisys/card?accountNumber=ACC-10001`
4. **Results** are unified and presented as integrated data

---

##  Benefits

 **Semantic Alignment**: Same business entity names across systems
 **Relationship Clarity**: Clear 1:1:1 model (no ambiguity)
 **Federation Ready**: Context Resolution Agent can map entities
 **Consistent Data**: Mock data matches realistic scenarios
 **Extensible**: Easy to add more fields without breaking relationships
 **CardDemo Compliant**: Follows AWS CardDemo data model

---

##  Testing Alignment

Run the ePortal server:
```bash
cd mock_eportal
python -m uvicorn app:app --port 8001 --reload
```

Test federation:
```bash
# Getting a customer
curl http://localhost:8001/api/unisys/customer?customerId=CUST001

# Following the relationship to their account
curl http://localhost:8001/api/unisys/account?customerId=CUST001

# Following the relationship to their card
curl http://localhost:8001/api/unisys/card?accountNumber=ACC-10001

# Getting their transactions
curl http://localhost:8001/api/unisys/transaction?accountNumber=ACC-10001

# Getting federation metadata
curl http://localhost:8001/api/unisys/federation-metadata
```

---

##  Reference Files

- Schema definitions: `mock_eportal/schema/*.json`
- Mock data: `mock_eportal/data/*.json`
- Entity mapping: `mock_eportal/entity_mapping.json`
- Services: `mock_eportal/services/*.py`
- Routes: `mock_eportal/routers/*.py`

---

**Last Updated**: 2026-04-17  
**Version**: 1.0.0  
**Federation Standard**: AWS CardDemo
