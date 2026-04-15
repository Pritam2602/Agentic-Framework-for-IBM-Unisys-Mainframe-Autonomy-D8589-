"""
api_router.py - REST API endpoints for Unisys ePortal data access
"""

import time
import random
from fastapi import APIRouter, Query
from typing import Optional

from mock_eportal.services import PayrollService, CustomerService, TransactionService

router = APIRouter(prefix="/api/unisys", tags=["unisys-data"])

# Initialize services
payroll_service = PayrollService()
customer_service = CustomerService()
transaction_service = TransactionService()


def _simulate_latency():
    """Simulate realistic mainframe response latency (50-200ms)"""
    time.sleep(random.uniform(0.05, 0.2))


# ================================================================
# PAYROLL ENDPOINTS
# ================================================================

@router.get("/payroll")
async def get_payroll(
    employeeId: Optional[int] = Query(None, description="Filter by employee ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
):
    """
    Retrieve payroll data from Unisys MCP backend.
    Simulates COBOL PERFORM READ on PAYROLL-FILE.
    """
    _simulate_latency()

    if employeeId:
        record = payroll_service.get_by_employee_id(employeeId)
        data = [record] if record else []
    elif department:
        data = payroll_service.get_by_department(department)
    else:
        data = payroll_service.get_all()

    return {
        "source": "unisys_eportal",
        "entity": "payroll",
        "count": len(data),
        "data": data
    }


# ================================================================
# CUSTOMER ENDPOINTS
# ================================================================

@router.get("/customer")
async def get_customer(
    customerId: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customerType: Optional[str] = Query(None, description="Filter by type: individual/corporate"),
):
    """
    Retrieve customer data from Unisys DMSII database.
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
        "count": len(data),
        "data": data
    }


# ================================================================
# TRANSACTION ENDPOINTS
# ================================================================

@router.get("/transaction")
async def get_transactions(
    accountId: Optional[str] = Query(None, description="Filter by account ID"),
    transactionType: Optional[str] = Query(None, description="Filter by type: credit/debit"),
    startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Retrieve transaction data from Unisys MCP transaction processor.
    Simulates MCP COMS transaction handler.
    """
    _simulate_latency()

    if accountId:
        data = transaction_service.get_by_account(accountId)
    elif startDate and endDate:
        data = transaction_service.get_by_date_range(startDate, endDate)
    elif transactionType:
        data = transaction_service.get_by_type(transactionType)
    else:
        data = transaction_service.get_all()

    return {
        "source": "unisys_eportal",
        "entity": "transaction",
        "count": len(data),
        "data": data
    }
