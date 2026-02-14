"""
Banking API endpoints
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import LoanApplicationRequest, LoanProcessingResponse
from app.banking.loan_service import LoanProcessingService

router = APIRouter(prefix="/api/banking", tags=["banking"])
loan_service = LoanProcessingService()


@router.post("/loan/process", response_model=LoanProcessingResponse)
async def process_loan_application(application: LoanApplicationRequest):
    """
    Process loan application through complete pipeline:
    - Eligibility check
    - Interest calculation  
    - Approval workflow
    """
    try:
        result = loan_service.process_loan_application(application)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
