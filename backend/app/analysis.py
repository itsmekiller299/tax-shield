from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from app.models import (
    Transaction, Obligation, ObligationType, ObligationStatus, RiskLevel,
    Document, VerificationStatus, Deadline, DeadlineBase,
    IncomeCategory, ExpenseCategory, InvestmentType, TransactionType,
    TaxReadinessScore, DashboardSummary, DocumentType
)
from app.database import get_database
from bson import ObjectId
from app.models import PyObjectId


class TaxAnalysisEngine:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        return {
            "freelance_threshold": 50000,
            "advance_tax_threshold": 10000,
            "high_value_threshold": 100000,
            "missing_doc_severity": {
                IncomeCategory.SALARY: RiskLevel.MEDIUM,
                IncomeCategory.FREELANCE: RiskLevel.HIGH,
                IncomeCategory.BUSINESS: RiskLevel.HIGH,
                IncomeCategory.RENTAL: RiskLevel.MEDIUM,
                IncomeCategory.BANK_INTEREST: RiskLevel.LOW,
                IncomeCategory.DIVIDENDS: RiskLevel.LOW,
                IncomeCategory.CAPITAL_GAINS: RiskLevel.HIGH,
                IncomeCategory.OTHER: RiskLevel.MEDIUM,
            },
            "deduction_doc_requirements": {
                ExpenseCategory.INSURANCE: DocumentType.INSURANCE_RECEIPT,
                ExpenseCategory.LOAN_INTEREST: DocumentType.LOAN_CERTIFICATE,
                ExpenseCategory.EDUCATION: DocumentType.EXPENSE_BILL,
                ExpenseCategory.MEDICAL: DocumentType.EXPENSE_BILL,
                ExpenseCategory.DONATIONS: DocumentType.DONATION_RECEIPT,
                ExpenseCategory.RENT: DocumentType.RENT_RECEIPT,
            }
        }

    async def analyze_user_data(self, user_id: ObjectId, regime: str = "old") -> Tuple[List[Obligation], List[Deadline], TaxReadinessScore, DashboardSummary]:
        database = await get_database()

        transactions = await database.transactions.find({"user_id": user_id}).to_list(None)
        documents = await database.documents.find({"user_id": user_id}).to_list(None)
        investments = await database.investments.find({"user_id": user_id}).to_list(None)
        deductions = await database.deductions.find({"user_id": user_id}).to_list(None)

        transactions = [Transaction(**t) for t in transactions]
        documents = [Document(**d) for d in documents]

        # User's preferred regime (profile) overrides default
        try:
            user = await database.users.find_one({"_id": user_id})
            if user and user.get("preferred_tax_regime") in ("old", "new"):
                regime = user["preferred_tax_regime"]
        except Exception:
            pass

        obligations = await self._detect_obligations(user_id, transactions, documents, investments, deductions)
        deadlines = await self._generate_deadlines(user_id, obligations, transactions)
        readiness_score = self._calculate_readiness_score(transactions, documents, obligations, deadlines, deductions)
        recon = await self.reconcile_user(user_id)
        # Reconciliation mismatches become obligations (stable titles for upsert)
        for item in recon.get("items", []):
            if item["status"] != "matched":
                obligations.append(Obligation(
                    user_id=user_id,
                    title=f"AIS mismatch: {item['source']}",
                    description=f"AIS reports ₹{item['ais_amount']:,.0f} for {item['income_type']} vs internal ₹{item['internal_match']:,.0f} (diff ₹{item['difference']:,.0f}).",
                    obligation_type=ObligationType.VERIFICATION_NEEDED,
                    risk_level=RiskLevel.HIGH if abs(item["difference"]) > 50000 else RiskLevel.MEDIUM,
                    estimated_amount=abs(item["difference"]),
                    recommended_action=item["action"],
                    confidence=0.85,
                    related_transaction_ids=[],
                ))
        pay_cursor = database.tax_payments.find({"user_id": user_id}).to_list(None)
        payments = await pay_cursor
        tax_paid = round(sum(float(p.get("amount", 0)) for p in payments), 2)
        summary = self._generate_summary(transactions, deductions, investments, readiness_score, obligations, documents, deadlines, tax_paid=tax_paid, regime=regime, recon={"status": recon.get("status"), "score": recon.get("score"), "matched": recon.get("matched"), "mismatched": recon.get("mismatched"), "missing": recon.get("missing")})

        await self._save_obligations(user_id, obligations)
        await self._save_deadlines(user_id, deadlines)

        return obligations, deadlines, readiness_score, summary

    async def _detect_obligations(self, user_id: ObjectId, transactions: List[Transaction], 
                                  documents: List[Document], investments: List, deductions: List) -> List[Obligation]:
        obligations = []
        
        income_transactions = [t for t in transactions if t.transaction_type == TransactionType.INCOME]
        income_categories = set(t.category for t in income_transactions)
        
        if len(income_categories) >= 3:
            obligations.append(Obligation(
                user_id=user_id,
                title="Multiple Income Sources Detected",
                description=f"You have income from {len(income_categories)} different sources: {', '.join(income_categories)}. "
                           f"This may require additional reporting and advance tax payments.",
                obligation_type=ObligationType.REPORTING_REQUIREMENT,
                risk_level=RiskLevel.MEDIUM,
                estimated_amount=sum(t.amount for t in income_transactions),
                recommended_action="Review all income sources and ensure proper documentation for each.",
                confidence=0.9,
                related_transaction_ids=[str(t.id) for t in income_transactions]
            ))
        
        for transaction in income_transactions:
            category = transaction.category
            has_doc = any(
                d.related_transaction_id == transaction.id and d.verification_status == VerificationStatus.COMPLETE
                for d in documents
            )
            
            if not has_doc and category in self.rules["missing_doc_severity"]:
                risk = self.rules["missing_doc_severity"][category]
                obligations.append(Obligation(
                    user_id=user_id,
                    title=f"Missing Document for {category.replace('_', ' ').title()}",
                    description=f"₹{transaction.amount:,.0f} of {category.replace('_', ' ')} income recorded but no supporting document found.",
                    obligation_type=ObligationType.MISSING_DOCUMENT,
                    risk_level=risk,
                    estimated_amount=transaction.amount,
                    recommended_action=f"Upload {category.replace('_', ' ')} statement or certificate.",
                    confidence=0.85,
                    related_transaction_ids=[str(transaction.id)]
                ))
        
        freelance_income = [t for t in income_transactions if t.category == IncomeCategory.FREELANCE]
        if freelance_income:
            total_freelance = sum(t.amount for t in freelance_income)
            if total_freelance > self.rules["freelance_threshold"]:
                has_invoice = any(
                    d.document_type == DocumentType.INVOICE and d.verification_status == VerificationStatus.COMPLETE
                    for d in documents
                )
                if not has_invoice:
                    obligations.append(Obligation(
                        user_id=user_id,
                        title="Freelance Income Documentation Incomplete",
                        description=f"₹{total_freelance:,.0f} of freelance income detected. Invoices and expense records are recommended for tax compliance.",
                        obligation_type=ObligationType.MISSING_DOCUMENT,
                        risk_level=RiskLevel.HIGH,
                        estimated_amount=total_freelance,
                        recommended_action="Upload client invoices and maintain expense records for freelance work.",
                        confidence=0.87,
                        related_transaction_ids=[str(t.id) for t in freelance_income]
                    ))
        
        capital_gains = [t for t in income_transactions if t.category == IncomeCategory.CAPITAL_GAINS]
        for cg in capital_gains:
            has_purchase_doc = any(
                d.document_type == DocumentType.INVESTMENT_STATEMENT and d.verification_status == VerificationStatus.COMPLETE
                for d in documents
            )
            if not has_purchase_doc:
                obligations.append(Obligation(
                    user_id=user_id,
                    title="Capital Gain Purchase Documentation Missing",
                    description=f"Investment sale of ₹{cg.amount:,.0f} recorded but purchase documents not found. "
                               f"Cannot accurately calculate capital gains without purchase price.",
                    obligation_type=ObligationType.MISSING_DOCUMENT,
                    risk_level=RiskLevel.HIGH,
                    estimated_amount=cg.amount,
                    recommended_action="Upload investment purchase statements to calculate accurate capital gains.",
                    confidence=0.9,
                    related_transaction_ids=[str(cg.id)]
                ))
        
        for deduction in deductions:
            # Support both dict (raw DB) and Pydantic objects
            d_status = deduction.get("verification_status") if isinstance(deduction, dict) else getattr(deduction, "verification_status", None)
            d_cat = deduction.get("category") if isinstance(deduction, dict) else getattr(deduction, "category", None)
            d_amt = deduction.get("amount", 0) if isinstance(deduction, dict) else getattr(deduction, "amount", 0)
            d_id = deduction.get("_id") if isinstance(deduction, dict) else getattr(deduction, "id", None)
            if str(d_status) in [VerificationStatus.MISSING.value, VerificationStatus.NEEDS_REVIEW.value, str(VerificationStatus.MISSING), str(VerificationStatus.NEEDS_REVIEW)]:
                required_doc = self.rules["deduction_doc_requirements"].get(d_cat)
                if required_doc:
                    obligations.append(Obligation(
                        user_id=user_id,
                        title=f"Deduction Proof Needed: {str(d_cat).replace('_', ' ').title()}",
                        description=f"₹{d_amt:,.0f} claimed under {str(d_cat).replace('_', ' ')} "
                                    f"but supporting document is {d_status}.",
                        obligation_type=ObligationType.VERIFICATION_NEEDED,
                        risk_level=RiskLevel.MEDIUM,
                        estimated_amount=d_amt,
                        recommended_action=f"Upload {required_doc.value.replace('_', ' ')} to verify deduction eligibility.",
                        confidence=0.8,
                        related_transaction_ids=[str(d_id)] if d_id else []
                    ))
        
        total_income = sum(t.amount for t in income_transactions)
        if total_income > self.rules["advance_tax_threshold"] * 100:
            obligations.append(Obligation(
                user_id=user_id,
                title="Possible Advance Tax Liability",
                description=f"Total income of ₹{total_income:,.0f} may trigger advance tax payment obligations. "
                           f"Check if advance tax installments are due.",
                obligation_type=ObligationType.ADVANCE_TAX,
                risk_level=RiskLevel.MEDIUM,
                estimated_amount=total_income * 0.3,
                recommended_action="Calculate advance tax liability and schedule payments before due dates.",
                confidence=0.75,
                related_transaction_ids=[str(t.id) for t in income_transactions]
            ))
        
        for investment in investments:
            if investment.get("sale_date") and investment.get("purchase_value") is None:
                obligations.append(Obligation(
                    user_id=user_id,
                    title="Investment Sale Without Purchase Record",
                    description=f"Investment '{investment.get('name')}' was sold but purchase value is not recorded. "
                               f"Cannot determine capital gain/loss.",
                    obligation_type=ObligationType.VERIFICATION_NEEDED,
                    risk_level=RiskLevel.HIGH,
                    estimated_amount=investment.get("sale_value", 0),
                    recommended_action="Add purchase date and value for accurate capital gains calculation.",
                    confidence=0.9,
                    related_transaction_ids=[]
                ))
        
        return obligations

    async def _generate_deadlines(self, user_id: ObjectId, obligations: List[Obligation], 
                                  transactions: List[Transaction]) -> List[Deadline]:
        deadlines = []
        today = datetime.utcnow()
        financial_year_end = datetime(today.year + (1 if today.month > 3 else 0), 3, 31)
        
        filing_deadline = datetime(financial_year_end.year, 7, 31)
        if filing_deadline > today:
            deadlines.append(Deadline(
                user_id=str(user_id),
                title="Income Tax Return Filing",
                description="File your income tax return for the financial year",
                due_date=filing_deadline,
                deadline_type="filing",
                required_documents=["All income statements", "Deduction proofs", "Investment statements"],
                estimated_payment=None
            ))
        
        advance_tax_dates = [
            (datetime(financial_year_end.year - 1, 6, 15), "1st Installment (15%)"),
            (datetime(financial_year_end.year - 1, 9, 15), "2nd Installment (45%)"),
            (datetime(financial_year_end.year - 1, 12, 15), "3rd Installment (75%)"),
            (datetime(financial_year_end.year, 3, 15), "4th Installment (100%)"),
        ]
        
        for due_date, label in advance_tax_dates:
            if due_date > today:
                deadlines.append(Deadline(
                    user_id=str(user_id),
                    title=f"Advance Tax - {label}",
                    description=f"Pay {label} of estimated advance tax liability",
                    due_date=due_date,
                    deadline_type="advance_tax",
                    required_documents=["Income estimate", "Tax calculation worksheet"],
                    estimated_payment=None
                ))
        
        tds_dates = [
            (datetime(financial_year_end.year - 1, 5, 31), "Q1 TDS Return"),
            (datetime(financial_year_end.year - 1, 7, 31), "Q2 TDS Return"),
            (datetime(financial_year_end.year - 1, 10, 31), "Q3 TDS Return"),
            (datetime(financial_year_end.year, 1, 31), "Q4 TDS Return"),
        ]
        
        for due_date, label in tds_dates:
            if due_date > today:
                deadlines.append(Deadline(
                    user_id=user_id,
                    title=label,
                    description=f"File TDS return for {label}",
                    due_date=due_date,
                    deadline_type="tds",
                    required_documents=["TDS certificates", "Challan details"],
                    estimated_payment=None
                ))
        
        for obligation in obligations:
            if obligation.due_date and obligation.due_date > today:
                deadlines.append(Deadline(
                    user_id=user_id,
                    title=obligation.title,
                    description=obligation.description,
                    due_date=obligation.due_date,
                    deadline_type="obligation",
                    related_obligation_id=obligation.id,
                    required_documents=[obligation.recommended_action],
                    estimated_payment=obligation.estimated_amount
                ))
        
        return deadlines

    def _calculate_readiness_score(self, transactions: List[Transaction], documents: List[Document],
                                   obligations: List[Obligation], deadlines: List[Deadline],
                                   deductions: List) -> TaxReadinessScore:
        total_transactions = len(transactions)
        categorized_transactions = len([t for t in transactions if t.category])
        categorization_score = (categorized_transactions / total_transactions * 100) if total_transactions > 0 else 100
        
        total_docs_expected = total_transactions + len(deductions)
        docs_complete = len([d for d in documents if d.verification_status == VerificationStatus.COMPLETE])
        document_score = (docs_complete / total_docs_expected * 100) if total_docs_expected > 0 else 100
        
        high_risk_obligations = len([o for o in obligations if o.risk_level == RiskLevel.HIGH])
        medium_risk_obligations = len([o for o in obligations if o.risk_level == RiskLevel.MEDIUM])
        total_obligations = len(obligations)
        alert_score = max(0, 100 - (high_risk_obligations * 20 + medium_risk_obligations * 10))
        
        upcoming_deadlines = len([d for d in deadlines if d.due_date > datetime.utcnow() and not d.is_completed])
        overdue_deadlines = len([d for d in deadlines if d.due_date <= datetime.utcnow() and not d.is_completed])
        deadline_score = max(0, 100 - (overdue_deadlines * 25 + upcoming_deadlines * 5))
        
        deductions_with_docs = len([d for d in deductions if str(d.get("verification_status") if isinstance(d, dict) else getattr(d, "verification_status", "")) in (VerificationStatus.COMPLETE.value, str(VerificationStatus.COMPLETE))])
        total_deductions = len(deductions)
        deduction_score = (deductions_with_docs / total_deductions * 100) if total_deductions > 0 else 100
        
        D = document_score
        C = categorization_score
        R = 100 - (high_risk_obligations * 15 + medium_risk_obligations * 7.5)
        T = deadline_score
        A = alert_score
        
        score = int(0.30 * D + 0.25 * C + 0.20 * R + 0.15 * T + 0.10 * A)
        score = max(0, min(100, score))
        
        breakdown = {
            "document_completeness": round(D, 1),
            "categorization_completeness": round(C, 1),
            "record_consistency": round(R, 1),
            "deadline_preparedness": round(T, 1),
            "alert_resolution": round(A, 1),
            # Spec-aligned aliases (Documentation 30 / Compliance 25 / Reconciliation 20 / Tax Accuracy 15 / Actionability 10)
            "documentation": round(D, 1),
            "compliance": round(C, 1),
            "reconciliation": round(R, 1),
            "tax_accuracy": round(T, 1),
            "actionability": round(A, 1),
        }
        
        factors = {
            "total_transactions": total_transactions,
            "categorized_transactions": categorized_transactions,
            "documents_uploaded": len(documents),
            "documents_verified": docs_complete,
            "total_obligations": total_obligations,
            "high_risk_obligations": high_risk_obligations,
            "medium_risk_obligations": medium_risk_obligations,
            "upcoming_deadlines": upcoming_deadlines,
            "overdue_deadlines": overdue_deadlines,
            "total_deductions": total_deductions,
            "verified_deductions": deductions_with_docs
        }
        
        explanation = self._generate_score_explanation(breakdown, factors)
        
        return TaxReadinessScore(
            score=score,
            breakdown=breakdown,
            explanation=explanation,
            factors=factors
        )

    def _generate_score_explanation(self, breakdown: dict, factors: dict) -> str:
        reasons = []
        if factors["documents_verified"] < factors["total_transactions"]:
            reasons.append(f"{factors['total_transactions'] - factors['documents_verified']} transaction(s) missing documents")
        if factors["high_risk_obligations"] > 0:
            reasons.append(f"{factors['high_risk_obligations']} high-risk obligation(s) detected")
        if factors["overdue_deadlines"] > 0:
            reasons.append(f"{factors['overdue_deadlines']} overdue deadline(s)")
        if factors["total_deductions"] > factors["verified_deductions"]:
            reasons.append(f"{factors['total_deductions'] - factors['verified_deductions']} deduction(s) need verification")
        
        if not reasons:
            return "Your tax records are well-organized and complete."
        
        return f"Your score reflects: {'; '.join(reasons)}."

    def _generate_summary(self, transactions: List[Transaction], deductions: List, investments: List,
                          readiness_score: TaxReadinessScore, obligations: List[Obligation],
                          documents: List[Document], deadlines: List[Deadline], tax_paid: float = 0,
                          regime: str = "old", recon: dict = None) -> DashboardSummary:
        income_transactions = [t for t in transactions if t.transaction_type == TransactionType.INCOME]
        expense_transactions = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
        
        total_income = sum(t.amount for t in income_transactions)
        total_deductions = sum(float(d.get("amount", 0) if isinstance(d, dict) else getattr(d, "amount", 0)) for d in deductions if str(d.get("verification_status") if isinstance(d, dict) else getattr(d, "verification_status", "")) in (VerificationStatus.COMPLETE.value, str(VerificationStatus.COMPLETE)))
        taxable_income = max(0, total_income - total_deductions)

        detailed = self.compute_tax_detailed(taxable_income, regime or "old")
        estimated_liability = round(detailed["base"] - detailed["rebate"] + detailed["surcharge"] + detailed["cess"], 2)

        income_breakdown = {}
        for t in income_transactions:
            cat = t.category
            income_breakdown[cat] = income_breakdown.get(cat, 0) + t.amount

        deduction_summary = {}
        for d in deductions:
            if isinstance(d, dict):
                cat = d.get("category", "other"); amt = d.get("amount", 0)
            else:
                cat = getattr(d, "category", "other"); amt = getattr(d, "amount", 0)
            deduction_summary[cat] = deduction_summary.get(cat, 0) + amt

        outstanding = max(0, round(estimated_liability - (tax_paid or 0), 2))
        return DashboardSummary(
            total_income=total_income,
            taxable_income=taxable_income,
            estimated_liability=estimated_liability,
            readiness_score=readiness_score.score,
            pending_obligations=len([o for o in obligations if str(getattr(o, "status", "open")) in ("open", "pending", "in_progress") and not getattr(o, "is_completed", False)]),
            missing_documents=len([d for d in documents if d.verification_status != VerificationStatus.COMPLETE]),
            upcoming_deadlines=len([d for d in deadlines if d.due_date > datetime.utcnow() and not d.is_completed]),
            income_breakdown=income_breakdown,
            deduction_summary=deduction_summary,
            tax_paid=round(tax_paid or 0, 2),
            outstanding_tax=outstanding,
            regime=regime or "old",
            base_tax=detailed["base"],
            cess=detailed["cess"],
            surcharge=detailed["surcharge"],
            rebate=detailed["rebate"],
            reconciliation=recon or {},
        )

    def _estimate_tax_liability(self, taxable_income: float, regime: str = "old") -> float:
        base, rebate, surcharge, cess = self.compute_tax_detailed(taxable_income, regime).values()
        return base - rebate + surcharge + cess

    def compute_tax_detailed(self, taxable_income: float, regime: str = "old") -> dict:
        """Deterministic slab tax + 87A rebate + surcharge + 4% cess. No AI, no external calls."""
        t = max(0, taxable_income)
        if regime == "new":
            slabs = [(300000, 0.0), (600000, 0.05), (900000, 0.10), (1200000, 0.15), (1500000, 0.20), (float("inf"), 0.30)]
            rebate_limit, rebate_max = 700000, 25000
        else:
            slabs = [(250000, 0.0), (500000, 0.05), (750000, 0.10), (1000000, 0.15), (1250000, 0.20), (1500000, 0.25), (float("inf"), 0.30)]
            rebate_limit, rebate_max = 500000, 12500
        base = 0.0
        prev = 0.0
        for limit, rate in slabs:
            if t <= prev:
                break
            base += (min(t, limit) - prev) * rate
            prev = limit
        rebate = 0.0
        if t <= rebate_limit:
            rebate = min(base, rebate_max)
        after_rebate = base - rebate
        surcharge = 0.0
        if t > 5000000:
            rate = 0.10 if t <= 10000000 else 0.15 if t <= 20000000 else 0.25
            if regime == "new":
                rate = min(rate, 0.25)
            surcharge = after_rebate * rate
        cess = (after_rebate + surcharge) * 0.04
        return {"base": round(base, 2), "rebate": round(rebate, 2), "surcharge": round(surcharge, 2), "cess": round(cess, 2)}

    def compute_scenario_liability(self, estimated_income: float, estimated_deductions: float, regime: str = "old") -> float:
        taxable = max(0, (estimated_income or 0) - (estimated_deductions or 0))
        return self._estimate_tax_liability(taxable, regime)

    async def reconcile_user(self, user_id: ObjectId) -> dict:
        """Compare internal income transactions vs AIS records and TDS vs Form 26AS."""
        database = await get_database()
        txs = await database.transactions.find({"user_id": user_id, "transaction_type": "income"}).to_list(None)
        ais = await database.ais_records.find({"user_id": user_id}).to_list(None)
        f26 = await database.form26as_records.find({"user_id": user_id}).to_list(None)
        internal_by_type: dict = {}
        for t in txs:
            k = str(t.get("category", "other"))
            internal_by_type[k] = internal_by_type.get(k, 0) + float(t.get("amount", 0))
        internal_total = round(sum(internal_by_type.values()), 2)
        ais_total = round(sum(float(a.get("amount", 0)) for a in ais), 2)
        tds_internal = round(sum(float(t.get("tax_deducted", 0)) for t in txs), 2)
        tds_26as = round(sum(float(f.get("tds", 0)) for f in f26), 2)
        items = []
        for a in ais:
            atype = str(a.get("income_type", "other"))
            amt = float(a.get("amount", 0))
            match = sum(float(t.get("amount", 0)) for t in txs if str(t.get("category")) == atype or str(t.get("source")) == str(a.get("source")))
            diff = round(amt - match, 2)
            status = "matched" if abs(diff) < 1 else ("missing" if match == 0 else "mismatched")
            items.append({"source": a.get("source"), "income_type": atype, "ais_amount": amt, "internal_match": round(match, 2), "difference": diff, "status": status,
                          "action": "No action needed." if status == "matched" else f"Review {atype}: difference ₹{diff:,.0f}. Verify evidence and correct the record."})
        tds_status = "matched" if abs(tds_internal - tds_26as) < 1 else "mismatched"
        matched = len([i for i in items if i["status"] == "matched"])
        mismatched = len([i for i in items if i["status"] == "mismatched"])
        missing = len([i for i in items if i["status"] == "missing"])
        score = 100 if not items else round(matched / len(items) * 100, 1)
        return {"internal_total": internal_total, "ais_total": ais_total, "income_difference": round(ais_total - internal_total, 2),
                "tds_internal": tds_internal, "tds_26as": tds_26as, "tds_difference": round(tds_26as - tds_internal, 2), "tds_status": tds_status,
                "items": items, "matched": matched, "mismatched": mismatched, "missing": missing, "score": score,
                "status": "matched" if (mismatched == 0 and missing == 0) else ("mismatched" if mismatched else "missing")}

    def derive_risks_and_actions(self, obligations: List[Obligation], deadlines: List[Deadline], recon: dict) -> tuple:
        risks, actions = [], []
        for o in obligations:
            rid = f"risk-{abs(hash(o.title)) % 10**8}"
            risks.append({"id": rid, "title": o.title, "severity": o.risk_level.value if hasattr(o.risk_level, 'value') else str(o.risk_level),
                          "obligation_type": str(o.obligation_type), "estimated_amount": o.estimated_amount, "status": "open" if not o.is_completed else "resolved"})
            actions.append({"id": f"action-{rid}", "risk_id": rid, "title": f"Resolve: {o.title}", "recommended_action": o.recommended_action,
                            "status": "pending", "related_obligation": o.title})
        for item in (recon.get("items") or []):
            if item["status"] != "matched":
                rid = f"risk-recon-{abs(hash(item['source'] + item['income_type'])) % 10**8}"
                risks.append({"id": rid, "title": f"Reconciliation {item['status']}: {item['source']}", "severity": "high" if abs(item["difference"]) > 50000 else "medium",
                              "obligation_type": "reconciliation", "estimated_amount": abs(item["difference"]), "status": "open"})
                actions.append({"id": f"action-{rid}", "risk_id": rid, "title": f"Reconcile {item['source']}", "recommended_action": item["action"], "status": "pending", "related_obligation": "reconciliation"})
        today = datetime.utcnow()
        for d in deadlines:
            if not d.is_completed and d.due_date <= today:
                risks.append({"id": f"risk-od-{str(d.id)}", "title": f"Overdue: {d.title}", "severity": "high", "obligation_type": "deadline", "estimated_amount": d.estimated_payment or 0, "status": "open"})
        seen, uniq = set(), []
        for r in risks:
            if r["title"] not in seen:
                seen.add(r["title"])
                uniq.append(r)
        return uniq, actions

    async def _save_obligations(self, user_id: ObjectId, obligations: List[Obligation]):
        database = await get_database()
        # Stable upsert by (user_id, title): preserves _id + user status across re-analysis
        existing = await database.obligations.find({"user_id": user_id}).to_list(None)
        by_title = {e.get("title"): e for e in existing}
        for o in obligations:
            d = o.model_dump(by_alias=True)
            prev = by_title.get(d.get("title"))
            if prev:
                d["_id"] = prev["_id"]
                if prev.get("status") not in (None, "open"):
                    d["status"] = prev["status"]
                    d["is_completed"] = prev.get("is_completed", False)
                await database.obligations.replace_one({"_id": prev["_id"]}, d)
            else:
                d.pop("_id", None)
                await database.obligations.insert_one(d)
        # Remove stale obligations no longer detected (but keep user-completed ones)
        current_titles = {o.title for o in obligations}
        for title, doc in by_title.items():
            if title not in current_titles and not doc.get("is_completed") and doc.get("status") in (None, "open"):
                await database.obligations.delete_one({"_id": doc["_id"]})

    async def _save_deadlines(self, user_id: ObjectId, deadlines: List[Deadline]):
        database = await get_database()
        existing = await database.deadlines.find({"user_id": user_id}).to_list(None)
        existing_ids = {d["title"] + str(d["due_date"]) for d in existing}
        
        new_deadlines = []
        for d in deadlines:
            key = d.title + str(d.due_date)
            if key not in existing_ids:
                new_deadlines.append(d.model_dump(by_alias=True))
        
        if new_deadlines:
            await database.deadlines.insert_many(new_deadlines)


analysis_engine = TaxAnalysisEngine()