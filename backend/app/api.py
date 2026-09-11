from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import csv
import io

from app.auth import get_current_active_user, create_access_token
from app.database import get_database
from app.models import (
    User, UserCreate, Token, Transaction, TransactionCreate,
    Investment, InvestmentCreate, Deduction, DeductionCreate,
    Document, DocumentCreate, Obligation, Deadline, Scenario, ScenarioCreate,
    DashboardSummary, TaxReadinessScore, IncomeCategory, ExpenseCategory,
    TransactionType, VerificationStatus, RiskLevel, ObligationStatus,
    InvestmentType, TaxPayment, TaxPaymentCreate, AISRecord, AISRecordCreate,
    Form26ASRecord, Form26ASRecordCreate,
)
from app.analysis import analysis_engine

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    database = await get_database()
    existing = await database.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user_data.model_dump()
    from app.auth import create_user
    user = await create_user(user_dict)
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(request: Request):
    """Login endpoint accepting JSON body or form data (frontend compat)."""
    from pydantic import BaseModel

    class LoginCredentials(BaseModel):
        email: str
        password: str

    email = password = None
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            user_data = await request.json()
            if isinstance(user_data, dict):
                email = user_data.get("email")
                password = user_data.get("password")
        else:
            form = await request.form()
            email = form.get("email")
            password = form.get("password")
            if not email or not password:
                try:
                    user_data = await request.json()
                    if isinstance(user_data, dict):
                        email = email or user_data.get("email")
                        password = password or user_data.get("password")
                except Exception:
                    pass
    except Exception:
        pass

    if not email or not password:
        raise HTTPException(status_code=400, detail="Invalid login credentials")

    from app.auth import authenticate_user
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/transactions", response_model=Transaction)
async def create_transaction(
    transaction: TransactionCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    if transaction.amount < 0:
        raise HTTPException(status_code=422, detail="amount must be non-negative")
    database = await get_database()
    transaction_dict = transaction.model_dump()
    transaction_dict["user_id"] = current_user.id
    transaction_dict["created_at"] = datetime.utcnow()
    transaction_dict["updated_at"] = datetime.utcnow()

    result = await database.transactions.insert_one(transaction_dict)
    transaction_dict["_id"] = result.inserted_id

    if request.query_params.get("analyze", "true").lower() not in ("false", "0", "no"):
        await analysis_engine.analyze_user_data(current_user.id)

    return Transaction(**transaction_dict)


@router.post("/transactions/bulk", response_model=dict)
async def bulk_create_transactions(
    transactions: List[TransactionCreate],
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    docs = []
    for t in transactions:
        if t.amount < 0:
            raise HTTPException(status_code=422, detail="amount must be non-negative")
        d = t.model_dump()
        d["user_id"] = current_user.id
        d["created_at"] = datetime.utcnow()
        d["updated_at"] = datetime.utcnow()
        docs.append(d)
    if docs:
        await database.transactions.insert_many(docs)
        await analysis_engine.analyze_user_data(current_user.id)
    return {"inserted": len(docs)}


@router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    transactions = await database.transactions.find({"user_id": current_user.id}).sort("date", -1).to_list(None)
    return [Transaction(**t) for t in transactions]


@router.post("/transactions/upload-csv")
async def upload_transactions_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    transactions_created = 0
    for row in reader:
        try:
            transaction_data = {
                "date": datetime.fromisoformat(row.get("date", "").replace("Z", "+00:00")),
                "description": row.get("description", ""),
                "amount": float(row.get("amount", 0)),
                "transaction_type": TransactionType(row.get("transaction_type", "income")),
                "category": row.get("category", "other"),
                "source": row.get("source"),
                "tax_treatment": row.get("tax_treatment"),
                "tax_deducted": float(row.get("tax_deducted", 0)),
                "frequency": row.get("frequency"),
                "user_id": current_user.id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await database.transactions.insert_one(transaction_data)
            transactions_created += 1
        except Exception:
            continue
    
    await analysis_engine.analyze_user_data(current_user.id)
    
    return {"message": f"Successfully uploaded {transactions_created} transactions"}


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    result = await database.transactions.delete_one({
        "_id": ObjectId(transaction_id),
        "user_id": current_user.id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    await analysis_engine.analyze_user_data(current_user.id)
    return {"message": "Transaction deleted"}


@router.post("/investments", response_model=Investment)
async def create_investment(
    investment: InvestmentCreate,
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    investment_dict = investment.model_dump()
    investment_dict["user_id"] = current_user.id
    investment_dict["created_at"] = datetime.utcnow()
    investment_dict["updated_at"] = datetime.utcnow()
    
    if investment_dict.get("sale_date") and investment_dict.get("purchase_value"):
        investment_dict["gain_loss"] = (investment_dict.get("sale_value", 0) - investment_dict["purchase_value"])
    
    result = await database.investments.insert_one(investment_dict)
    investment_dict["_id"] = result.inserted_id
    
    await analysis_engine.analyze_user_data(current_user.id)
    return Investment(**investment_dict)


@router.get("/investments", response_model=List[Investment])
async def get_investments(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    investments = await database.investments.find({"user_id": current_user.id}).to_list(None)
    return [Investment(**i) for i in investments]


@router.post("/deductions", response_model=Deduction)
async def create_deduction(
    deduction: DeductionCreate,
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    deduction_dict = deduction.model_dump()
    deduction_dict["user_id"] = current_user.id
    deduction_dict["created_at"] = datetime.utcnow()
    deduction_dict["updated_at"] = datetime.utcnow()
    
    result = await database.deductions.insert_one(deduction_dict)
    deduction_dict["_id"] = result.inserted_id
    
    await analysis_engine.analyze_user_data(current_user.id)
    return Deduction(**deduction_dict)


@router.get("/deductions", response_model=List[Deduction])
async def get_deductions(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    deductions = await database.deductions.find({"user_id": current_user.id}).to_list(None)
    return [Deduction(**d) for d in deductions]


@router.post("/documents", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    financial_year: str = Form(...),
    related_transaction_id: Optional[str] = Form(None),
    related_investment_id: Optional[str] = Form(None),
    related_deduction_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    content = await file.read()
    
    import os
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    document_dict = {
        "file_name": file.filename,
        "document_type": document_type,
        "financial_year": financial_year,
        "verification_status": VerificationStatus.COMPLETE,
        "related_transaction_id": ObjectId(related_transaction_id) if related_transaction_id else None,
        "related_investment_id": ObjectId(related_investment_id) if related_investment_id else None,
        "related_deduction_id": ObjectId(related_deduction_id) if related_deduction_id else None,
        "user_id": current_user.id,
        "file_path": file_path,
        "file_size": len(content),
        "mime_type": file.content_type,
        "upload_date": datetime.utcnow()
    }
    
    result = await database.documents.insert_one(document_dict)
    document_dict["_id"] = result.inserted_id
    
    if related_transaction_id:
        await database.transactions.update_one(
            {"_id": ObjectId(related_transaction_id)},
            {"$set": {"document_id": result.inserted_id}}
        )
    
    await analysis_engine.analyze_user_data(current_user.id)
    return Document(**document_dict)


@router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    documents = await database.documents.find({"user_id": current_user.id}).to_list(None)
    return [Document(**d) for d in documents]


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    import os
    from fastapi.responses import FileResponse
    database = await get_database()
    try:
        doc = await database.documents.find_one({"_id": ObjectId(document_id), "user_id": current_user.id})
    except Exception:
        doc = None
    if not doc or not doc.get("file_path") or not os.path.isfile(doc["file_path"]):
        raise HTTPException(status_code=404, detail="Document file not found")
    return FileResponse(doc["file_path"], filename=doc.get("file_name") or "document",
                        media_type=doc.get("mime_type") or "application/octet-stream")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    import os
    database = await get_database()
    try:
        doc = await database.documents.find_one({"_id": ObjectId(document_id), "user_id": current_user.id})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await database.documents.delete_one({"_id": doc["_id"]})
    try:
        if doc.get("file_path") and os.path.isfile(doc["file_path"]):
            os.remove(doc["file_path"])
    except Exception:
        pass
    await analysis_engine.analyze_user_data(current_user.id)
    return {"message": "Document deleted"}


@router.get("/obligations", response_model=List[Obligation])
async def get_obligations(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    obligations = await database.obligations.find({"user_id": current_user.id}).to_list(None)
    return [Obligation(**o) for o in obligations]


@router.patch("/obligations/{obligation_id}")
async def update_obligation_status(
    obligation_id: str,
    request: Request,
    status: Optional[ObligationStatus] = None,
    current_user: User = Depends(get_current_active_user)
):
    # Accept status via query param OR JSON body {status} (frontend compat)
    if status is None:
        try:
            body = await request.json()
            if isinstance(body, dict) and body.get("status"):
                status = ObligationStatus(body["status"])
        except Exception:
            pass
    if status is None:
        raise HTTPException(status_code=422, detail="status is required")
    database = await get_database()
    result = await database.obligations.update_one(
        {"_id": ObjectId(obligation_id), "user_id": current_user.id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Obligation not found")
    return {"message": "Obligation updated"}


@router.get("/deadlines", response_model=List[Deadline])
async def get_deadlines(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    deadlines = await database.deadlines.find({"user_id": current_user.id}).sort("due_date", 1).to_list(None)
    return [Deadline(**d) for d in deadlines]


@router.patch("/deadlines/{deadline_id}")
async def update_deadline_status(
    deadline_id: str,
    request: Request,
    is_completed: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    # Accept is_completed via query param OR JSON body (frontend compat)
    if is_completed is None:
        try:
            body = await request.json()
            if isinstance(body, dict) and "is_completed" in body:
                is_completed = bool(body["is_completed"])
        except Exception:
            pass
    if is_completed is None:
        raise HTTPException(status_code=422, detail="is_completed is required")
    database = await get_database()
    update_data = {"is_completed": is_completed}
    if is_completed:
        update_data["completed_at"] = datetime.utcnow()
    
    result = await database.deadlines.update_one(
        {"_id": ObjectId(deadline_id), "user_id": current_user.id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return {"message": "Deadline updated"}


@router.post("/scenarios", response_model=Scenario)
async def create_scenario(
    scenario: ScenarioCreate,
    current_user: User = Depends(get_current_active_user)
):
    database = await get_database()
    scenario_dict = scenario.model_dump()
    scenario_dict["user_id"] = current_user.id
    scenario_dict["created_at"] = datetime.utcnow()
    scenario_dict["updated_at"] = datetime.utcnow()
    
    if scenario_dict.get("is_current"):
        await database.scenarios.update_many(
            {"user_id": current_user.id, "is_current": True},
            {"$set": {"is_current": False}}
        )
    
    result = await database.scenarios.insert_one(scenario_dict)
    scenario_dict["_id"] = result.inserted_id
    return Scenario(**scenario_dict)


@router.get("/scenarios", response_model=List[Scenario])
async def get_scenarios(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    scenarios = await database.scenarios.find({"user_id": current_user.id}).sort("created_at", -1).to_list(None)
    return [Scenario(**s) for s in scenarios]


@router.post("/scenarios/compare")
async def compare_scenarios(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    # Accept bare list OR {scenario_ids: [...]} (frontend compat)
    scenario_ids: List[str] = []
    try:
        body = await request.json()
        if isinstance(body, list):
            scenario_ids = body
        elif isinstance(body, dict):
            scenario_ids = body.get("scenario_ids") or body.get("scenarioIds") or body.get("ids") or []
    except Exception:
        pass
    if not scenario_ids:
        raise HTTPException(status_code=422, detail="scenario_ids is required")
    database = await get_database()
    scenarios = []
    for sid in scenario_ids:
        scenario = await database.scenarios.find_one({"_id": ObjectId(sid), "user_id": current_user.id})
        if scenario:
            scenarios.append(Scenario(**scenario))
    
    if not scenarios:
        raise HTTPException(status_code=404, detail="No scenarios found")
    
    comparison = []
    for scenario in scenarios:
        regime = (scenario.assumptions or {}).get("regime", "old")
        computed = analysis_engine.compute_scenario_liability(scenario.estimated_income, scenario.estimated_deductions, regime)
        comparison.append({
            "name": scenario.name,
            "estimated_income": scenario.estimated_income,
            "estimated_deductions": scenario.estimated_deductions,
            "estimated_liability": scenario.estimated_liability,
            "computed_liability": computed,
            "risk_level": scenario.risk_level,
            "required_documents": scenario.required_documents,
            "assumptions": scenario.assumptions
        })

    return {"comparison": comparison, "disclaimer": "These are estimates based on provided data. Consult a tax professional for advice."}


@router.post("/tax-payments", response_model=TaxPayment)
async def create_tax_payment(payment: TaxPaymentCreate, current_user: User = Depends(get_current_active_user)):
    if payment.amount <= 0:
        raise HTTPException(status_code=422, detail="amount must be positive")
    database = await get_database()
    d = payment.model_dump()
    d["user_id"] = current_user.id
    d["payment_date"] = d.get("payment_date") or datetime.utcnow()
    d["created_at"] = datetime.utcnow()
    result = await database.tax_payments.insert_one(d)
    d["_id"] = result.inserted_id
    await analysis_engine.analyze_user_data(current_user.id)
    return TaxPayment(**d)


@router.get("/tax-payments", response_model=List[TaxPayment])
async def list_tax_payments(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    payments = await database.tax_payments.find({"user_id": current_user.id}).sort("payment_date", -1).to_list(None)
    return [TaxPayment(**p) for p in payments]


@router.post("/ais-records", response_model=AISRecord)
async def create_ais_record(record: AISRecordCreate, current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    d = record.model_dump()
    d["user_id"] = current_user.id
    d["created_at"] = datetime.utcnow()
    result = await database.ais_records.insert_one(d)
    d["_id"] = result.inserted_id
    await analysis_engine.analyze_user_data(current_user.id)
    return AISRecord(**d)


@router.get("/ais-records", response_model=List[AISRecord])
async def list_ais_records(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    records = await database.ais_records.find({"user_id": current_user.id}).to_list(None)
    return [AISRecord(**r) for r in records]


@router.post("/form26as-records", response_model=Form26ASRecord)
async def create_form26as_record(record: Form26ASRecordCreate, current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    d = record.model_dump()
    d["user_id"] = current_user.id
    d["created_at"] = datetime.utcnow()
    result = await database.form26as_records.insert_one(d)
    d["_id"] = result.inserted_id
    await analysis_engine.analyze_user_data(current_user.id)
    return Form26ASRecord(**d)


@router.get("/form26as-records", response_model=List[Form26ASRecord])
async def list_form26as_records(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    records = await database.form26as_records.find({"user_id": current_user.id}).to_list(None)
    return [Form26ASRecord(**r) for r in records]


@router.get("/reconciliation")
async def get_reconciliation(current_user: User = Depends(get_current_active_user)):
    return await analysis_engine.reconcile_user(current_user.id)


@router.get("/risks")
async def get_risks(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    obligations = [Obligation(**o) for o in await database.obligations.find({"user_id": current_user.id}).to_list(None)]
    deadlines = [Deadline(**d) for d in await database.deadlines.find({"user_id": current_user.id}).to_list(None)]
    recon = await analysis_engine.reconcile_user(current_user.id)
    risks, _ = analysis_engine.derive_risks_and_actions(obligations, deadlines, recon)
    return {"risks": risks, "count": len(risks)}


@router.get("/actions")
async def get_actions(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    obligations = [Obligation(**o) for o in await database.obligations.find({"user_id": current_user.id}).to_list(None)]
    deadlines = [Deadline(**d) for d in await database.deadlines.find({"user_id": current_user.id}).to_list(None)]
    recon = await analysis_engine.reconcile_user(current_user.id)
    _, actions = analysis_engine.derive_risks_and_actions(obligations, deadlines, recon)
    return {"actions": actions, "count": len(actions)}


@router.get("/tax-detail")
async def get_tax_detail(regime: str = "old", current_user: User = Depends(get_current_active_user)):
    _, _, _, summary = await analysis_engine.analyze_user_data(current_user.id)
    detailed = analysis_engine.compute_tax_detailed(summary.taxable_income, regime if regime in ("old", "new") else "old")
    return {"taxable_income": summary.taxable_income, "regime": regime, **detailed,
            "total_liability": round(detailed["base"] - detailed["rebate"] + detailed["surcharge"] + detailed["cess"], 2),
            "tax_paid": summary.tax_paid, "outstanding_tax": summary.outstanding_tax}


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(regime: str = "old", current_user: User = Depends(get_current_active_user)):
    obligations, deadlines, readiness_score, summary = await analysis_engine.analyze_user_data(current_user.id, regime if regime in ("old", "new") else "old")
    return summary


@router.get("/readiness-score", response_model=TaxReadinessScore)
async def get_readiness_score(current_user: User = Depends(get_current_active_user)):
    obligations, deadlines, readiness_score, _ = await analysis_engine.analyze_user_data(current_user.id)
    return readiness_score


@router.get("/demo/seed")
async def seed_demo_data(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    
    await database.transactions.delete_many({"user_id": current_user.id})
    await database.investments.delete_many({"user_id": current_user.id})
    await database.deductions.delete_many({"user_id": current_user.id})
    await database.documents.delete_many({"user_id": current_user.id})
    await database.obligations.delete_many({"user_id": current_user.id})
    await database.deadlines.delete_many({"user_id": current_user.id})
    await database.scenarios.delete_many({"user_id": current_user.id})
    
    demo_transactions = [
        {"date": datetime(2024, 4, 1), "description": "Salary Credit - April", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 5, 1), "description": "Salary Credit - May", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 6, 1), "description": "Salary Credit - June", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 7, 1), "description": "Salary Credit - July", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 8, 1), "description": "Salary Credit - August", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 9, 1), "description": "Salary Credit - September", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 10, 1), "description": "Salary Credit - October", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 11, 1), "description": "Salary Credit - November", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2025, 1, 1), "description": "Salary Credit - January", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2025, 2, 1), "description": "Salary Credit - February", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2025, 3, 1), "description": "Salary Credit - March", "amount": 58333, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.SALARY, "source": "Employer Pvt Ltd", "tax_deducted": 5000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 6, 15), "description": "Freelance Project - Client A", "amount": 75000, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.FREELANCE, "source": "Client A", "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 9, 20), "description": "Freelance Project - Client B", "amount": 75000, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.FREELANCE, "source": "Client B", "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2024, 12, 10), "description": "Bank Interest - Savings", "amount": 15000, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.BANK_INTEREST, "source": "HDFC Bank", "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"date": datetime(2025, 1, 15), "description": "Mutual Fund Redemption", "amount": 75000, "transaction_type": TransactionType.INCOME, "category": IncomeCategory.CAPITAL_GAINS, "source": "SBI Mutual Fund", "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
    ]
    
    await database.transactions.insert_many(demo_transactions)
    
    demo_investments = [
        {"investment_type": InvestmentType.MUTUAL_FUND, "name": "SBI Bluechip Fund", "purchase_date": datetime(2023, 1, 15), "purchase_value": 50000, "sale_date": datetime(2025, 1, 15), "sale_value": 75000, "gain_loss": 25000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"investment_type": InvestmentType.FIXED_DEPOSIT, "name": "HDFC FD", "purchase_date": datetime(2024, 4, 1), "purchase_value": 100000, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
    ]
    await database.investments.insert_many(demo_investments)
    
    demo_deductions = [
        {"category": ExpenseCategory.INSURANCE, "description": "Term Insurance Premium", "amount": 40000, "date": datetime(2024, 4, 15), "financial_year": "2024-25", "verification_status": VerificationStatus.COMPLETE, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"category": ExpenseCategory.LOAN_INTEREST, "description": "Education Loan Interest", "amount": 60000, "date": datetime(2024, 6, 30), "financial_year": "2024-25", "verification_status": VerificationStatus.NEEDS_REVIEW, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"category": ExpenseCategory.RETIREMENT, "description": "PPF Contribution", "amount": 50000, "date": datetime(2024, 12, 31), "financial_year": "2024-25", "verification_status": VerificationStatus.COMPLETE, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
    ]
    await database.deductions.insert_many(demo_deductions)
    
    demo_scenarios = [
        {"name": "Current Situation", "description": "Based on current income and deductions", "assumptions": {"regime": "new", "age": "30"}, "estimated_income": 850000, "estimated_deductions": 150000, "estimated_liability": 45000, "risk_level": RiskLevel.LOW, "required_documents": [], "is_current": True, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"name": "Scenario A: Maximize 80C", "description": "Invest additional ₹1L in ELSS/PPF", "assumptions": {"regime": "old", "additional_80c": 100000}, "estimated_income": 850000, "estimated_deductions": 250000, "estimated_liability": 30000, "risk_level": RiskLevel.LOW, "required_documents": ["ELSS investment proof", "PPF deposit receipt"], "is_current": False, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        {"name": "Scenario B: Sell MF Now", "description": "Realize capital gains this year", "assumptions": {"regime": "new", "realize_gains": True}, "estimated_income": 875000, "estimated_deductions": 150000, "estimated_liability": 52000, "risk_level": RiskLevel.MEDIUM, "required_documents": ["MF purchase statement", "MF sale statement"], "is_current": False, "user_id": current_user.id, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
    ]
    await database.scenarios.insert_many(demo_scenarios)
    
    await analysis_engine.analyze_user_data(current_user.id)
    
    return {"message": "Demo data seeded successfully"}

# ---------------- TaxShield Intelligent Assistant ----------------
_chat_hits: dict = {}


def _chat_rate_ok(uid: str, limit: int = 30, window: int = 60) -> bool:
    import time
    now = time.time()
    arr = _chat_hits.setdefault(uid, [])
    while arr and arr[0] < now - window:
        arr.pop(0)
    if len(arr) >= limit:
        return False
    arr.append(now)
    return True


@router.post("/chat/message")
async def chat_message(request: Request, current_user: User = Depends(get_current_active_user)):
    from app.chat import answer as chat_answer
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = (body.get("message") or body.get("text") or "").strip() if isinstance(body, dict) else ""
    if not text or len(text) > 2000:
        raise HTTPException(status_code=422, detail="message must be 1-2000 chars")
    if not _chat_rate_ok(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again shortly.")
    database = await get_database()
    out = await chat_answer(str(current_user.id), text, current_user, database, analysis_engine)
    await database.chat_messages.insert_many([
        {"user_id": current_user.id, "role": "user", "text": text, "language": out["language"], "intent": out["intent"], "created_at": datetime.utcnow()},
        {"user_id": current_user.id, "role": "assistant", "text": out["response"], "language": out["language"], "intent": out["intent"], "created_at": datetime.utcnow()},
    ])
    return out


@router.get("/chat/history")
async def chat_history(limit: int = 50, current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    msgs = await database.chat_messages.find({"user_id": current_user.id}).sort("created_at", -1).to_list(min(max(limit, 1), 100))
    return {"messages": [{"role": m["role"], "text": m["text"], "language": m.get("language"), "intent": m.get("intent"), "created_at": str(m.get("created_at"))} for m in reversed(msgs)]}


@router.post("/chat/voice/transcribe")
async def chat_voice_transcribe(request: Request, current_user: User = Depends(get_current_active_user)):
    """Provider-swappable STT: browser Web Speech API sends {transcript, lang};
    server detects language and returns normalized transcript (audio upload path reserved)."""
    from app.chat import detect_language
    ctype = request.headers.get("content-type", "")
    transcript, lang = "", None
    if "application/json" in ctype:
        try:
            body = await request.json()
            transcript = (body.get("transcript") or body.get("text") or "")
            lang = body.get("lang")
            if body.get("audio"):
                transcript = transcript or "(audio received; server STT provider not configured — browser transcription preferred)"
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            transcript = form.get("transcript") or ""
            lang = form.get("lang")
        except Exception:
            pass
    if not transcript:
        raise HTTPException(status_code=422, detail="transcript or audio is required")
    return {"transcript": transcript, "language": lang or detect_language(transcript), "provider": "browser-web-speech (swappable)"}


@router.post("/chat/voice/synthesize")
async def chat_voice_synthesize(request: Request, current_user: User = Depends(get_current_active_user)):
    """Returns text+lang for browser speechSynthesis (provider-swappable; no audio stored)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = (body.get("text") or "").strip() if isinstance(body, dict) else ""
    if not text or len(text) > 2000:
        raise HTTPException(status_code=422, detail="text must be 1-2000 chars")
    from app.chat import detect_language
    lang = detect_language(text)
    voice = {"en": "en-IN", "ta": "ta-IN", "hi": "hi-IN"}.get(lang[:2], "en-IN")
    return {"text": text, "language": lang, "voice": voice, "provider": "browser-speechSynthesis (swappable)"}


@router.get("/chat/context")
async def chat_context(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    return {"profile": {"email": current_user.email, "name": current_user.name,
                        "financial_year": current_user.financial_year, "tax_jurisdiction": current_user.tax_jurisdiction,
                        "employment_type": current_user.employment_type,
                        "preferred_tax_regime": current_user.preferred_tax_regime},
            "assessment_year": "2025-26"}


@router.get("/chat/readiness")
async def chat_readiness(current_user: User = Depends(get_current_active_user)):
    _, _, score, _ = await analysis_engine.analyze_user_data(current_user.id)
    return score.model_dump() if hasattr(score, "model_dump") else score


@router.get("/chat/alerts")
async def chat_alerts(current_user: User = Depends(get_current_active_user)):
    from app.models import Obligation, Deadline
    database = await get_database()
    obs = [Obligation(**o) for o in await database.obligations.find({"user_id": current_user.id}).to_list(200)]
    dls = [Deadline(**d) for d in await database.deadlines.find({"user_id": current_user.id}).to_list(200)]
    recon = await analysis_engine.reconcile_user(current_user.id)
    risks, actions = analysis_engine.derive_risks_and_actions(obs, dls, recon)
    return {"risks": risks, "actions": actions}


@router.get("/chat/documents")
async def chat_documents(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    docs = await database.documents.find({"user_id": current_user.id}).to_list(200)
    obs = await database.obligations.find({"user_id": current_user.id}).to_list(200)
    missing = [o["title"] for o in obs if "missing" in o.get("title", "").lower() or "proof" in o.get("title", "").lower()]
    return {"uploaded": len(docs), "missing": missing}


@router.get("/chat/deadlines")
async def chat_deadlines(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    return {"deadlines": await database.deadlines.find({"user_id": current_user.id}).sort("due_date", 1).to_list(200)}


@router.get("/chat/obligations")
async def chat_obligations(current_user: User = Depends(get_current_active_user)):
    database = await get_database()
    return {"obligations": await database.obligations.find({"user_id": current_user.id}).to_list(200)}


@router.post("/chat/scenario")
async def chat_scenario(request: Request, current_user: User = Depends(get_current_active_user)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    extra_deduction = float((body or {}).get("extra_deduction", 50000))
    _, _, _, summary = await analysis_engine.analyze_user_data(current_user.id)
    s = summary.model_dump()
    regime = s.get("regime", "old")
    cur = s.get("estimated_liability", 0)
    sc = analysis_engine.compute_scenario_liability(s.get("total_income", 0),
        (s.get("total_income", 0) - s.get("taxable_income", 0)) + extra_deduction, regime)
    return {"current_liability": cur, "scenario_liability": sc, "difference": round(sc - cur, 2),
            "estimate": True, "disclaimer": "This is an estimate, not a guaranteed tax result."}
