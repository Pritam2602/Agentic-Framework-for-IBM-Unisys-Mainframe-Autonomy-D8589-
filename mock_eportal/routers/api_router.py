"""
api_router.py - REST API endpoints for Unisys ePortal data access
Aligned with AWS CardDemo entities: Customer, Account, Card, Transaction
"""

import time
import random
from fastapi import APIRouter, Query
from typing import Optional

from mock_eportal.services import CustomerService, AccountService, CardService, TransactionService

router = APIRouter(prefix="/api/unisys", tags=["unisys-data"])

# Initialize services
customer_service = CustomerService()
account_service = AccountService()
card_service = CardService()
transaction_service = TransactionService()


def _simulate_latency():
    """Simulate realistic mainframe response latency (50-200ms)"""
    time.sleep(random.uniform(0.05, 0.2))


# ================================================================
# CUSTOMER ENDPOINTS (CardDemo Customer Entity)
# ================================================================

@router.get("/customer")
async def get_customer(
    customerId: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customerType: Optional[str] = Query(None, description="Filter by type: individual/corporate"),
):
    """
    Retrieve customer data from Unisys DMSII database.
    Represents AWS CardDemo Customer entity.
    Simulates DMSII FIND on CUSTOMER dataset.
    """
    _simulate_latency()

    if customerId:
        record = customer_service.get_by_id(customerId)
        data = [record] if record else []
    elif status:
        data = customer_service.get_by_status(status)
    elif customerType:
        data = customer_service.get_by_type(customerType)
    else:
        data = customer_service.get_all()

    return {
        "source": "unisys_eportal",
        "entity": "customer",
        "carddemo_entity": "CUSTOMER",
        "count": len(data),
        "data": data
    }


# ================================================================
# ACCOUNT ENDPOINTS (CardDemo Account Entity) - NEW
# ================================================================

@router.get("/account")
async def get_account(
    accountNumber: Optional[str] = Query(None, description="Filter by account number"),
    customerId: Optional[str] = Query(None, description="Filter by customer ID"),
    accountStatus: Optional[str] = Query(None, description="Filter by status: ACTIVE/INACTIVE/SUSPENDED/CLOSED"),
    accountType: Optional[str] = Query(None, description="Filter by type: CREDIT/SAVINGS/CHECKING"),
):
    """
    Retrieve account data from Unisys VSAM database.
    Represents AWS CardDemo Account entity (1:1:1 relationship with Customer and Card).
    Simulates VSAM READ on ACCOUNT file.
    """
    _simulate_latency()

    if accountNumber:
        record = account_service.get_by_account_number(accountNumber)
        data = [record] if record else []
    elif customerId:
        data = account_service.get_by_customer_id(customerId)
    elif accountStatus:
        data = account_service.get_by_status(accountStatus)
    elif accountType:
        data = account_service.get_by_type(accountType)
    else:
        data = account_service.get_all()

    return {
        "source": "unisys_eportal",
        "entity": "account",
        "carddemo_entity": "ACCOUNT",
        "relationship": "1:1 to Customer, 1:1 to Card, 1:* to Transaction",
        "count": len(data),
        "data": data
    }


# ================================================================
# CARD ENDPOINTS (CardDemo Card Entity) - NEW
# ================================================================

@router.get("/card")
async def get_card(
    cardNumber: Optional[str] = Query(None, description="Filter by card number"),
    customerId: Optional[str] = Query(None, description="Filter by customer ID"),
    accountNumber: Optional[str] = Query(None, description="Filter by account number"),
    cardStatus: Optional[str] = Query(None, description="Filter by status: ACTIVE/EXPIRED/BLOCKED/CANCELLED"),
    cardType: Optional[str] = Query(None, description="Filter by type: CREDIT/DEBIT"),
):
    """
    Retrieve card data from Unisys VSAM database.
    Represents AWS CardDemo Card entity (1:1 relationship with Customer and Account).
    Simulates VSAM READ on CARDS file.
    """
    _simulate_latency()

    if cardNumber:
        record = card_service.get_by_card_number(cardNumber)
        data = [record] if record else []
    elif customerId:
        data = card_service.get_by_customer_id(customerId)
    elif accountNumber:
        record = card_service.get_by_account_number(accountNumber)
        data = [record] if record else []
    elif cardStatus:
        data = card_service.get_by_status(cardStatus)
    elif cardType:
        data = card_service.get_by_type(cardType)
    else:
        data = card_service.get_all()

    return {
        "source": "unisys_eportal",
        "entity": "card",
        "carddemo_entity": "CARD",
        "relationship": "1:1 to Customer, 1:1 to Account",
        "count": len(data),
        "data": data
    }


# ================================================================
# TRANSACTION ENDPOINTS (CardDemo Transaction Entity)
# ================================================================

@router.get("/transaction")
async def get_transactions(
    accountNumber: Optional[str] = Query(None, description="Filter by account number"),
    transactionType: Optional[str] = Query(None, description="Filter by type: CREDIT/DEBIT/TRANSFER/PAYMENT"),
    startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    transactionStatus: Optional[str] = Query(None, description="Filter by status: POSTED/PENDING/DECLINED"),
):
    """
    Retrieve financial transaction records from Unisys MCP transaction processor.
    Represents AWS CardDemo Transaction entity.
    Simulates COBOL batch transaction processing.
    """
    _simulate_latency()

    if accountNumber:
        data = transaction_service.get_by_account_number(accountNumber)
    elif transactionType:
        data = transaction_service.get_by_type(transactionType)
    elif startDate and endDate:
        data = transaction_service.get_by_date_range(startDate, endDate)
    elif transactionStatus:
        data = transaction_service.get_by_status(transactionStatus)
    else:
        data = transaction_service.get_all()

    return {
        "source": "unisys_eportal",
        "entity": "transaction",
        "carddemo_entity": "TRANSACTION",
        "relationship": "Many to Account",
        "count": len(data),
        "data": data
    }


# ================================================================
# FEDERATION METADATA ENDPOINT
# ================================================================

@router.get("/federation-metadata")
async def get_federation_metadata():
    """
    Return metadata about CardDemo alignment and entity relationships.
    Enables Context Resolution Agent to understand entity relationships.
    """
    return {
        "system": "unisys_eportal",
        "federation_standard": "AWS CardDemo",
        "version": "1.0.0",
        "entities": {
            "customer": {
                "carddemo_name": "CUSTOMER",
                "count": len(customer_service.get_all()),
                "fields": customer_service.get_field_names()
            },
            "account": {
                "carddemo_name": "ACCOUNT",
                "count": len(account_service.get_all()),
                "fields": account_service.get_field_names(),
                "relationship": "1:1 to Customer"
            },
            "card": {
                "carddemo_name": "CARD",
                "count": len(card_service.get_all()),
                "fields": card_service.get_field_names(),
                "relationship": "1:1 to Customer and Account"
            },
            "transaction": {
                "carddemo_name": "TRANSACTION",
                "count": len(transaction_service.get_all()),
                "fields": transaction_service.get_field_names(),
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
