'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Transaction, TransactionType, IncomeCategory, ExpenseCategory } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { Plus, Upload, Download, Filter, Search, Trash2, Edit } from 'lucide-react';
import toast from 'react-hot-toast';

export default function TransactionsPage() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [filters, setFilters] = useState({ type: '', category: '', search: '' });
  const [csvFile, setCsvFile] = useState<File | null>(null);

  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    amount: '',
    transaction_type: 'income' as TransactionType,
    category: 'salary',
    source: '',
    tax_treatment: '',
    tax_deducted: '0',
    frequency: '',
  });

  const fetchTransactions = async () => {
    try {
      const data = await api.getTransactions();
      setTransactions(data);
    } catch {
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTransaction) {
        await api.createTransaction({ ...formData, amount: parseFloat(formData.amount), tax_deducted: parseFloat(formData.tax_deducted) });
        toast.success('Transaction updated');
      } else {
        await api.createTransaction({ ...formData, amount: parseFloat(formData.amount), tax_deducted: parseFloat(formData.tax_deducted) });
        toast.success('Transaction added');
      }
      setShowModal(false);
      setEditingTransaction(null);
      resetForm();
      fetchTransactions();
    } catch {
      toast.error('Failed to save transaction');
    }
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setFormData({
      date: transaction.date.split('T')[0],
      description: transaction.description,
      amount: transaction.amount.toString(),
      transaction_type: transaction.transaction_type,
      category: transaction.category,
      source: transaction.source || '',
      tax_treatment: transaction.tax_treatment || '',
      tax_deducted: transaction.tax_deducted.toString(),
      frequency: transaction.frequency || '',
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this transaction?')) {
      try {
        await api.deleteTransaction(id);
        toast.success('Transaction deleted');
        fetchTransactions();
      } catch {
        toast.error('Failed to delete transaction');
      }
    }
  };

  const handleCsvUpload = async () => {
    if (!csvFile) return;
    try {
      await api.uploadTransactionsCsv(csvFile);
      toast.success('CSV uploaded successfully');
      setShowCsvModal(false);
      setCsvFile(null);
      fetchTransactions();
    } catch {
      toast.error('Failed to upload CSV');
    }
  };

  const resetForm = () => {
    setFormData({
      date: new Date().toISOString().split('T')[0],
      description: '',
      amount: '',
      transaction_type: 'income',
      category: 'salary',
      source: '',
      tax_treatment: '',
      tax_deducted: '0',
      frequency: '',
    });
  };

  const categories = formData.transaction_type === 'income'
    ? [
        { value: 'salary', label: 'Salary' },
        { value: 'freelance', label: 'Freelance' },
        { value: 'business', label: 'Business' },
        { value: 'rental', label: 'Rental Income' },
        { value: 'bank_interest', label: 'Bank Interest' },
        { value: 'dividends', label: 'Dividends' },
        { value: 'capital_gains', label: 'Capital Gains' },
        { value: 'other', label: 'Other' },
      ]
    : [
        { value: 'insurance', label: 'Insurance' },
        { value: 'loan_interest', label: 'Loan Interest' },
        { value: 'education', label: 'Education' },
        { value: 'medical', label: 'Medical' },
        { value: 'donations', label: 'Donations' },
        { value: 'retirement', label: 'Retirement' },
        { value: 'business_expense', label: 'Business Expense' },
        { value: 'rent', label: 'Rent' },
        { value: 'other', label: 'Other' },
      ];

  const filteredTransactions = transactions.filter((t) => {
    if (filters.type && t.transaction_type !== filters.type) return false;
    if (filters.category && t.category !== filters.category) return false;
    if (filters.search) {
      const search = filters.search.toLowerCase();
      if (!t.description.toLowerCase().includes(search) && !t.source?.toLowerCase().includes(search)) return false;
    }
    return true;
  });

  const typeColors = {
    income: 'bg-green-100 text-green-800',
    expense: 'bg-red-100 text-red-800',
    investment: 'bg-blue-100 text-blue-800',
    deduction: 'bg-purple-100 text-purple-800',
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
            <p className="text-gray-500 mt-1">Manage your income, expenses, and investments</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setShowCsvModal(true)}>
              <Upload className="h-4 w-4 mr-2" />
              Import CSV
            </Button>
            <Button onClick={() => { setEditingTransaction(null); resetForm(); setShowModal(true); }}>
              <Plus className="h-4 w-4 mr-2" />
              Add Transaction
            </Button>
          </div>
        </div>

        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <Input
                placeholder="Search transactions..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="max-w-xs"
              />
              <Select
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                options={[
                  { value: '', label: 'All Types' },
                  { value: 'income', label: 'Income' },
                  { value: 'expense', label: 'Expense' },
                  { value: 'investment', label: 'Investment' },
                  { value: 'deduction', label: 'Deduction' },
                ]}
                className="w-40"
              />
              <Select
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                options={[
                  { value: '', label: 'All Categories' },
                  { value: 'salary', label: 'Salary' },
                  { value: 'freelance', label: 'Freelance' },
                  { value: 'business', label: 'Business' },
                  { value: 'rental', label: 'Rental' },
                  { value: 'bank_interest', label: 'Bank Interest' },
                  { value: 'capital_gains', label: 'Capital Gains' },
                  { value: 'insurance', label: 'Insurance' },
                  { value: 'loan_interest', label: 'Loan Interest' },
                  { value: 'retirement', label: 'Retirement' },
                ]}
                className="w-48"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
              </div>
            ) : filteredTransactions.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500">No transactions found. Add your first transaction to get started.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">Tax Deducted</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTransactions.map((transaction, idx) => (
                      <TableRow key={(transaction as any).id ?? (transaction as any)._id ?? idx}>
                        <TableCell>{formatDate(transaction.date)}</TableCell>
                        <TableCell className="font-medium">{transaction.description}</TableCell>
                        <TableCell>
                          <Badge variant={typeColors[transaction.transaction_type] as any}>
                            {transaction.transaction_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="capitalize">{transaction.category.replace(/_/g, ' ')}</TableCell>
                        <TableCell>{transaction.source || '-'}</TableCell>
                        <TableCell className="text-right font-medium">
                          {transaction.transaction_type === 'expense' || transaction.transaction_type === 'deduction' ? '-' : '+'}{formatCurrency(transaction.amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {transaction.tax_deducted > 0 ? formatCurrency(transaction.tax_deducted) : '-'}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => handleEdit(transaction)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(transaction.id)}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        <Modal
          isOpen={showModal}
          onClose={() => { setShowModal(false); setEditingTransaction(null); resetForm(); }}
          title={editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
          size="lg"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Date"
                type="date"
                name="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
              <Select
                label="Type"
                name="transaction_type"
                value={formData.transaction_type}
                onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as TransactionType })}
                options={[
                  { value: 'income', label: 'Income' },
                  { value: 'expense', label: 'Expense' },
                  { value: 'investment', label: 'Investment' },
                  { value: 'deduction', label: 'Deduction' },
                ]}
                required
              />
            </div>
            <Input
              label="Description"
              name="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="e.g., Salary credit, Freelance payment"
              required
            />
            <Select
              label="Category"
              name="category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              options={categories}
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Amount (₹)"
                type="number"
                name="amount"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                placeholder="0.00"
                required
                step="0.01"
                min="0"
              />
              <Input
                label="Tax Deducted (₹)"
                type="number"
                name="tax_deducted"
                value={formData.tax_deducted}
                onChange={(e) => setFormData({ ...formData, tax_deducted: e.target.value })}
                placeholder="0.00"
                step="0.01"
                min="0"
              />
            </div>
            <Input
              label="Source / Payer"
              name="source"
              value={formData.source}
              onChange={(e) => setFormData({ ...formData, source: e.target.value })}
              placeholder="e.g., Employer name, Client name"
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Tax Treatment"
                name="tax_treatment"
                value={formData.tax_treatment}
                onChange={(e) => setFormData({ ...formData, tax_treatment: e.target.value })}
                placeholder="e.g., TDS, Exempt"
              />
              <Select
                label="Frequency"
                name="frequency"
                value={formData.frequency}
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                options={[
                  { value: '', label: 'One-time' },
                  { value: 'monthly', label: 'Monthly' },
                  { value: 'quarterly', label: 'Quarterly' },
                  { value: 'annual', label: 'Annual' },
                ]}
              />
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
              <Button type="button" variant="secondary" onClick={() => { setShowModal(false); setEditingTransaction(null); resetForm(); }}>
                Cancel
              </Button>
              <Button type="submit">
                {editingTransaction ? 'Update' : 'Add'} Transaction
              </Button>
            </div>
          </form>
        </Modal>

        <Modal
          isOpen={showCsvModal}
          onClose={() => { setShowCsvModal(false); setCsvFile(null); }}
          title="Import Transactions from CSV"
          description="Upload a CSV file with columns: date, description, amount, transaction_type, category, source, tax_treatment, tax_deducted, frequency"
        >
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="hidden"
                id="csv-upload"
              />
              <label htmlFor="csv-upload" className="cursor-pointer">
                <Download className="h-10 w-10 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">Click to select CSV file or drag and drop</p>
                <p className="text-sm text-gray-400 mt-1">CSV format required</p>
              </label>
              {csvFile && <p className="text-sm text-green-600 mt-2">Selected: {csvFile.name}</p>}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => { setShowCsvModal(false); setCsvFile(null); }}>
                Cancel
              </Button>
              <Button onClick={handleCsvUpload} disabled={!csvFile}>
                Import
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </DashboardLayout>
  );
}