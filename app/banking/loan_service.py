"""
Banking domain services - Loan processing with full business logic
"""
from typing import Dict, Any, List
from datetime import datetime
import uuid
from app.models.schemas import (
    LoanApplicationRequest, LoanEligibilityResult, LoanInterestResult,
    LoanApprovalResult, TraceEvent
)


class LoanEligibilityEngine:
    """Determines loan eligibility based on applicant profile"""
    
    def check_eligibility(self, application: LoanApplicationRequest) -> LoanEligibilityResult:
        """Check loan eligibility with business rules"""
        if application.age < 21 or application.age > 65:
            return LoanEligibilityResult(
                eligible=False, reason="Age must be between 21 and 65 years",
                max_loan_amount=0.0, recommended_term=0
            )
        
        if application.credit_score < 650:
            return LoanEligibilityResult(
                eligible=False, reason="Credit score must be at least 650",
                max_loan_amount=0.0, recommended_term=0
            )
        
        max_loan_amount = application.income * 12 * 5
        
        if application.loan_amount > max_loan_amount:
            return LoanEligibilityResult(
                eligible=False,
                reason=f"Requested loan amount exceeds maximum allowed ({max_loan_amount:,.2f})",
                max_loan_amount=max_loan_amount, recommended_term=application.loan_term_months
            )
        
        if application.loan_amount < 10000:
            recommended_term = min(application.loan_term_months, 24)
        elif application.loan_amount < 50000:
            recommended_term = min(application.loan_term_months, 60)
        else:
            recommended_term = min(application.loan_term_months, 120)
        
        return LoanEligibilityResult(
            eligible=True, reason="All eligibility criteria met",
            max_loan_amount=max_loan_amount, recommended_term=recommended_term
        )


class InterestCalculationEngine:
    """Calculates interest rates based on risk profile"""
    BASE_RATE = 4.5
    
    def calculate_interest(self, application: LoanApplicationRequest,
                          eligibility: LoanEligibilityResult) -> LoanInterestResult:
        """Calculate interest rate and monthly payment"""
        base_rate = self.BASE_RATE
        risk_adjustment = 0.0
        
        if application.credit_score < 700:
            risk_adjustment += 2.0
        elif application.credit_score < 750:
            risk_adjustment += 1.0
        else:
            risk_adjustment -= 0.5
        
        if application.loan_amount > 50000:
            risk_adjustment += 0.5
        
        if application.loan_term_months > 60:
            risk_adjustment += 0.25
        
        final_rate = base_rate + risk_adjustment
        monthly_rate = final_rate / 100 / 12
        num_payments = application.loan_term_months
        
        if monthly_rate == 0:
            monthly_payment = application.loan_amount / num_payments
        else:
            monthly_payment = (application.loan_amount * monthly_rate *
                             (1 + monthly_rate) ** num_payments) /                             ((1 + monthly_rate) ** num_payments - 1)
        
        total_payment = monthly_payment * num_payments
        total_interest = total_payment - application.loan_amount
        
        return LoanInterestResult(
            base_rate=base_rate, risk_adjustment=risk_adjustment, final_rate=final_rate,
            monthly_payment=round(monthly_payment, 2), total_interest=round(total_interest, 2)
        )


class LoanApprovalWorkflow:
    """Loan approval workflow orchestrator"""
    
    def process_approval(self, application: LoanApplicationRequest,
                        eligibility: LoanEligibilityResult,
                        interest: LoanInterestResult) -> LoanApprovalResult:
        """Process loan approval"""
        if eligibility.eligible:
            loan_id = f"LOAN-{uuid.uuid4().hex[:8].upper()}"
            return LoanApprovalResult(
                approved=True, loan_id=loan_id, approval_amount=application.loan_amount,
                interest_rate=interest.final_rate, monthly_payment=interest.monthly_payment,
                reason="Loan approved based on eligibility and risk assessment"
            )
        else:
            return LoanApprovalResult(
                approved=False, loan_id=None, approval_amount=0.0,
                interest_rate=0.0, monthly_payment=0.0, reason=eligibility.reason
            )


class LoanProcessingService:
    """Main loan processing service - orchestrates complete flow"""
    
    def __init__(self):
        self.eligibility_engine = LoanEligibilityEngine()
        self.interest_calculator = InterestCalculationEngine()
        self.approval_workflow = LoanApprovalWorkflow()
        self.execution_trace: List[TraceEvent] = []
    
    def process_loan_application(self, application: LoanApplicationRequest) -> Dict[str, Any]:
        """Process complete loan application"""
        self.execution_trace = []
        application_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        
        self._add_trace("intent_parsing", "Validating loan application data")
        self._add_trace("capability_matching", f"Application ID: {application_id}")
        
        self._add_trace("command_selection", "Running eligibility engine")
        eligibility = self.eligibility_engine.check_eligibility(application)
        self._add_trace("execution_planning",
                       f"Eligibility: {'Approved' if eligibility.eligible else 'Rejected'}")
        
        if not eligibility.eligible:
            self._add_trace("execution", f"Application rejected: {eligibility.reason}")
            return {
                "application_id": application_id, "status": "rejected",
                "eligibility": eligibility, "interest_calculation": None,
                "approval": None,
                "execution_trace": [trace.model_dump() for trace in self.execution_trace]
            }
        
        self._add_trace("execution", "Calculating interest rate and payment terms")
        interest = self.interest_calculator.calculate_interest(application, eligibility)
        self._add_trace("execution",
                       f"Interest rate: {interest.final_rate}%, Monthly payment: ${interest.monthly_payment}")
        
        self._add_trace("execution", "Processing approval workflow")
        approval = self.approval_workflow.process_approval(application, eligibility, interest)
        
        if approval.approved:
            self._add_trace("result_collection", f"Loan approved! Loan ID: {approval.loan_id}")
        else:
            self._add_trace("result_collection", f"Loan rejected: {approval.reason}")
        
        return {
            "application_id": application_id,
            "status": "approved" if approval.approved else "rejected",
            "eligibility": eligibility, "interest_calculation": interest,
            "approval": approval,
            "execution_trace": [trace.model_dump() for trace in self.execution_trace]
        }
    
    def _add_trace(self, stage: str, message: str, metadata: Dict[str, Any] = None):
        """Add execution trace"""
        trace = TraceEvent(timestamp=datetime.now(), stage=stage, message=message, metadata=metadata)
        self.execution_trace.append(trace)
