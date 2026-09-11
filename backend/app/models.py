from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args):
        if not ObjectId.is_valid(str(v)):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class TransactionBase(BaseModel):
    date: datetime
    description: str
    amount: float
    transaction_type: str
    category: str
    source: Optional[str] = None
    tax_treatment: Optional[str] = None
    tax_deducted: float = 0
    frequency: Optional[str] = None
    confidence_score: float = 1.0

    @field_validator('date', mode='before')
    @classmethod
    def parse_date_string(cls, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            return datetime.fromisoformat(value)
        return value


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    document_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserBase(BaseModel):
    email: EmailStr
    name: str
    age: Optional[int] = None
    tax_jurisdiction: str = "India"
    financial_year: str = "2024-25"
    employment_type: Optional[str] = None
    preferred_tax_regime: Optional[str] = None
    risk_preference: str = "moderate"


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}




class UserInDB(User):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class IncomeCategory(str, Enum):
    SALARY = "salary"
    FREELANCE = "freelance"
    CAPITAL_GAINS = "capital_gains"
    BUSINESS = "business"
    RENTAL = "rental"
    BANK_INTEREST = "bank_interest"
    DIVIDENDS = "dividends"
    OTHER = "other"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationStatus(str, Enum):
    COMPLETE = "complete"
    MISSING = "missing"
    NEEDS_REVIEW = "needs_review"


class ObligationType(str, Enum):
    REPORTING_REQUIREMENT = "reporting_requirement"
    MISSING_DOCUMENT = "missing_document"
    VERIFICATION_NEEDED = "verification_needed"
    ADVANCE_TAX = "advance_tax"


class InvestmentType(str, Enum):
    MUTUAL_FUND = "mutual_fund"
    FIXED_DEPOSIT = "fixed_deposit"
    STOCKS = "stocks"
    BONDS = "bonds"
    PPF = "ppf"
    ELSS = "elss"
    OTHER = "other"


class DocumentType(str, Enum):
    INSURANCE_RECEIPT = "insurance_receipt"
    LOAN_CERTIFICATE = "loan_certificate"
    EXPENSE_BILL = "expense_bill"
    DONATION_RECEIPT = "donation_receipt"
    RENT_RECEIPT = "rent_receipt"
    INVOICE = "invoice"
    INVESTMENT_STATEMENT = "investment_statement"
    SALARY_SLIP = "salary_slip"
    FORM16 = "form16"
    OTHER = "other"


class ObligationBase(BaseModel):
    title: str
    description: str
    obligation_type: str
    risk_level: RiskLevel
    estimated_amount: float
    recommended_action: str
    confidence: float
    related_transaction_ids: list = []
    status: Optional[str] = "open"
    due_date: Optional[datetime] = None

    class Config:
        extra = "allow"


class ObligationCreate(ObligationBase):
    pass


class Obligation(ObligationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class DeductionBase(BaseModel):
    category: str
    amount: float
    verification_status: VerificationStatus
    required_documents: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    financial_year: Optional[str] = None

    @field_validator('date', mode='before', check_fields=False)
    @classmethod
    def parse_any_date(cls, value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return value
        return value

    class Config:
        extra = "allow"


class DeductionCreate(DeductionBase):
    pass


class Deduction(DeductionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    verified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class InvestmentBase(BaseModel):
    name: str
    amount: Optional[float] = 0
    category: Optional[str] = None
    investment_type: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_value: Optional[float] = None
    sale_date: Optional[datetime] = None
    sale_value: Optional[float] = None
    gain_loss: Optional[float] = None
    description: Optional[str] = None

    @field_validator('purchase_date', 'sale_date', 'date', mode='before', check_fields=False)
    @classmethod
    def parse_any_date(cls, value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return value
        return value

    class Config:
        extra = "allow"


class InvestmentCreate(InvestmentBase):
    pass


class Investment(InvestmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    assumptions: dict = {}
    estimated_income: float = 0
    estimated_deductions: float = 0
    estimated_liability: float = 0
    risk_level: RiskLevel = RiskLevel.LOW
    required_documents: List[str] = []
    is_current: bool = False

    class Config:
        extra = "allow"


class ScenarioCreate(ScenarioBase):
    pass


class Scenario(ScenarioBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class DocumentBase(BaseModel):
    document_type: str
    filename: Optional[str] = None
    file_name: Optional[str] = None
    upload_date: Optional[datetime] = None
    verification_status: VerificationStatus = VerificationStatus.MISSING
    related_transaction_id: Optional[str] = None
    financial_year: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    related_investment_id: Optional[str] = None
    related_deduction_id: Optional[str] = None

    @field_validator('related_transaction_id', 'related_investment_id', 'related_deduction_id', mode='before', check_fields=False)
    @classmethod
    def coerce_ref_id(cls, value):
        if value is None:
            return value
        if isinstance(value, ObjectId):
            return str(value)
        return value

    class Config:
        extra = "allow"


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class DeadlineBase(BaseModel):
    user_id: Optional[PyObjectId] = None
    title: str
    description: str
    due_date: datetime
    deadline_type: str
    related_obligation_id: Optional[PyObjectId] = None
    required_documents: List[str] = []
    estimated_payment: Optional[float] = None

    @field_validator('user_id', 'related_obligation_id', mode='before', check_fields=False)
    @classmethod
    def coerce_object_id(cls, value):
        if value is None or isinstance(value, ObjectId):
            return value
        try:
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
        except Exception:
            pass
        return value

    class Config:
        populate_by_name = True
        extra = "allow"
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Deadline(DeadlineBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class ExpenseCategory(str, Enum):
    FUEL = "fuel"
    TRAVEL = "travel"
    OFFICE = "office"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    LOAN_INTEREST = "loan_interest"
    EDUCATION = "education"
    MEDICAL = "medical"
    DONATIONS = "donations"
    RENT = "rent"
    RETIREMENT = "retirement"


class ObligationStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class TaxReadinessScore(BaseModel):
    score: int
    breakdown: dict
    explanation: str
    factors: dict


class DashboardSummary(BaseModel):
    total_income: float
    taxable_income: float
    estimated_liability: float
    readiness_score: int
    pending_obligations: int
    missing_documents: int
    upcoming_deadlines: int
    income_breakdown: dict
    deduction_summary: dict
    # Extended ledger / reconciliation fields (defaults keep backward compat)
    tax_paid: float = 0
    outstanding_tax: float = 0
    regime: str = "old"
    base_tax: float = 0
    cess: float = 0
    surcharge: float = 0
    rebate: float = 0
    reconciliation: dict = {}


class TaxPaymentBase(BaseModel):
    amount: float
    payment_date: Optional[datetime] = None
    payment_type: Optional[str] = "advance_tax"
    reference: Optional[str] = None
    financial_year: Optional[str] = None
    related_obligation_id: Optional[str] = None

    @field_validator('payment_date', mode='before', check_fields=False)
    @classmethod
    def parse_pay_date(cls, value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return value
        return value

    class Config:
        extra = "allow"


class TaxPaymentCreate(TaxPaymentBase):
    pass


class TaxPayment(TaxPaymentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class AISRecordBase(BaseModel):
    source: str
    income_type: Optional[str] = "other"
    amount: float
    financial_year: Optional[str] = "2024-25"
    transaction_date: Optional[datetime] = None

    class Config:
        extra = "allow"


class AISRecordCreate(AISRecordBase):
    pass


class AISRecord(AISRecordBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class Form26ASRecordBase(BaseModel):
    source: str
    section: Optional[str] = None
    amount_paid: float = 0
    tds: float = 0
    financial_year: Optional[str] = "2024-25"

    class Config:
        extra = "allow"


class Form26ASRecordCreate(Form26ASRecordBase):
    pass


class Form26ASRecord(Form26ASRecordBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"


class ChatMessageBase(BaseModel):
    role: str
    text: str
    language: Optional[str] = "en"
    intent: Optional[str] = None

    class Config:
        extra = "allow"


class ChatMessage(ChatMessageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "allow"
