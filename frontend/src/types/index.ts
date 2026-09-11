export type TransactionType = 'income' | 'expense' | 'investment' | 'deduction';

export type IncomeCategory = 
  | 'salary' 
  | 'freelance' 
  | 'business' 
  | 'rental' 
  | 'bank_interest' 
  | 'dividends' 
  | 'capital_gains' 
  | 'other';

export type ExpenseCategory = 
  | 'insurance' 
  | 'loan_interest' 
  | 'education' 
  | 'medical' 
  | 'donations' 
  | 'retirement' 
  | 'business_expense' 
  | 'rent' 
  | 'other';

export type InvestmentType = 
  | 'mutual_fund' 
  | 'shares' 
  | 'fixed_deposit' 
  | 'bonds' 
  | 'cryptocurrency' 
  | 'real_estate' 
  | 'other';

export type DocumentType = 
  | 'salary_statement' 
  | 'bank_statement' 
  | 'investment_statement' 
  | 'insurance_receipt' 
  | 'loan_certificate' 
  | 'rent_receipt' 
  | 'donation_receipt' 
  | 'invoice' 
  | 'expense_bill' 
  | 'other';

export type VerificationStatus = 'complete' | 'missing' | 'partial' | 'needs_review';
export type RiskLevel = 'low' | 'medium' | 'high';
export type ObligationType = 'missing_document' | 'unreported_income' | 'advance_tax' | 'reporting_requirement' | 'deadline' | 'verification_needed';
export type ObligationStatus = 'open' | 'in_progress' | 'resolved' | 'dismissed';

export interface User {
  id: string;
  email: string;
  name: string;
  age?: number;
  tax_jurisdiction: string;
  financial_year: string;
  employment_type?: string;
  preferred_tax_regime?: string;
  risk_preference: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface Transaction {
  id: string;
  user_id: string;
  date: string;
  description: string;
  amount: number;
  transaction_type: TransactionType;
  category: string;
  source?: string;
  tax_treatment?: string;
  tax_deducted: number;
  frequency?: string;
  confidence_score: number;
  document_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Investment {
  id: string;
  user_id: string;
  investment_type: InvestmentType;
  name: string;
  purchase_date: string;
  purchase_value: number;
  sale_date?: string;
  sale_value?: number;
  gain_loss?: number;
  units?: number;
  isin?: string;
  document_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Deduction {
  id: string;
  user_id: string;
  category: ExpenseCategory;
  description: string;
  amount: number;
  date: string;
  financial_year: string;
  verification_status: VerificationStatus;
  document_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  user_id: string;
  file_name: string;
  document_type: DocumentType;
  financial_year: string;
  upload_date: string;
  verification_status: VerificationStatus;
  related_transaction_id?: string;
  related_investment_id?: string;
  related_deduction_id?: string;
  file_path: string;
  file_size: number;
  mime_type: string;
}

export interface Obligation {
  id: string;
  user_id: string;
  title: string;
  description: string;
  obligation_type: ObligationType;
  risk_level: RiskLevel;
  estimated_amount?: number;
  due_date?: string;
  status: ObligationStatus;
  recommended_action: string;
  confidence: number;
  related_transaction_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface Deadline {
  id: string;
  user_id: string;
  title: string;
  description: string;
  due_date: string;
  deadline_type: string;
  related_obligation_id?: string;
  required_documents: string[];
  estimated_payment?: number;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
}

export interface Scenario {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  assumptions: Record<string, any>;
  estimated_income: number;
  estimated_deductions: number;
  estimated_liability: number;
  risk_level: RiskLevel;
  required_documents: string[];
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaxReadinessScore {
  score: number;
  breakdown: {
    document_completeness: number;
    categorization_completeness: number;
    record_consistency: number;
    deadline_preparedness: number;
    alert_resolution: number;
  };
  explanation: string;
  factors: Record<string, any>;
}

export interface DashboardSummary {
  total_income: number;
  taxable_income: number;
  estimated_liability: number;
  readiness_score: number;
  pending_obligations: number;
  missing_documents: number;
  upcoming_deadlines: number;
  income_breakdown: Record<string, number>;
  deduction_summary: Record<string, number>;
}

export interface ScenarioComparison {
  comparison: Array<{
    name: string;
    estimated_income: number;
    estimated_deductions: number;
    estimated_liability: number;
    risk_level: RiskLevel;
    required_documents: string[];
    assumptions: Record<string, any>;
  }>;
  disclaimer: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export const INCOME_CATEGORIES: { value: IncomeCategory; label: string }[] = [
  { value: 'salary', label: 'Salary' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'business', label: 'Business' },
  { value: 'rental', label: 'Rental Income' },
  { value: 'bank_interest', label: 'Bank Interest' },
  { value: 'dividends', label: 'Dividends' },
  { value: 'capital_gains', label: 'Capital Gains' },
  { value: 'other', label: 'Other Income' },
];

export const EXPENSE_CATEGORIES: { value: ExpenseCategory; label: string }[] = [
  { value: 'insurance', label: 'Insurance' },
  { value: 'loan_interest', label: 'Loan Interest' },
  { value: 'education', label: 'Education' },
  { value: 'medical', label: 'Medical' },
  { value: 'donations', label: 'Donations' },
  { value: 'retirement', label: 'Retirement Contributions' },
  { value: 'business_expense', label: 'Business Expense' },
  { value: 'rent', label: 'Rent' },
  { value: 'other', label: 'Other' },
];

export const INVESTMENT_TYPES: { value: InvestmentType; label: string }[] = [
  { value: 'mutual_fund', label: 'Mutual Fund' },
  { value: 'shares', label: 'Shares/Stocks' },
  { value: 'fixed_deposit', label: 'Fixed Deposit' },
  { value: 'bonds', label: 'Bonds' },
  { value: 'cryptocurrency', label: 'Cryptocurrency' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'other', label: 'Other' },
];

export const DOCUMENT_TYPES: { value: DocumentType; label: string }[] = [
  { value: 'salary_statement', label: 'Salary Statement' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'investment_statement', label: 'Investment Statement' },
  { value: 'insurance_receipt', label: 'Insurance Receipt' },
  { value: 'loan_certificate', label: 'Loan Certificate' },
  { value: 'rent_receipt', label: 'Rent Receipt' },
  { value: 'donation_receipt', label: 'Donation Receipt' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'expense_bill', label: 'Expense Bill' },
  { value: 'other', label: 'Other' },
];