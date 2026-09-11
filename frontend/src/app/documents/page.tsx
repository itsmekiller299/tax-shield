'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Document, DocumentType, VerificationStatus } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { formatDate, formatCurrency, getVerificationStatusColor, cn } from '@/lib/utils';
import { Upload, FileText, Eye, Download, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function DocumentsPage() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [formData, setFormData] = useState({
    file: null as File | null,
    document_type: 'other' as DocumentType,
    financial_year: '2024-25',
    related_transaction_id: '',
    related_investment_id: '',
    related_deduction_id: '',
  });

  const fetchDocuments = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.file) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    try {
      await api.uploadDocument(formData.file, {
        document_type: formData.document_type,
        financial_year: formData.financial_year,
        related_transaction_id: formData.related_transaction_id || undefined,
        related_investment_id: formData.related_investment_id || undefined,
        related_deduction_id: formData.related_deduction_id || undefined,
      });
      toast.success('Document uploaded');
      setShowModal(false);
      resetForm();
      fetchDocuments();
    } catch {
      toast.error('Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      file: null,
      document_type: 'other',
      financial_year: '2024-25',
      related_transaction_id: '',
      related_investment_id: '',
      related_deduction_id: '',
    });
  };

  const handleView = (doc: Document) => {
    const id = (doc as any).id ?? (doc as any)._id;
    if (id) window.open(api.downloadDocumentUrl(id), '_blank', 'noopener');
  };

  const handleDownload = async (doc: Document) => {
    const id = (doc as any).id ?? (doc as any)._id;
    if (!id) return;
    try {
      const token = api.getToken();
      const res = await fetch(api.downloadDocumentUrl(id), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.file_name || 'document';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download document');
    }
  };

  const handleDelete = async (doc: Document) => {
    const id = (doc as any).id ?? (doc as any)._id;
    if (!id) return;
    if (confirm(`Delete "${doc.file_name}"?`)) {
      try {
        await api.deleteDocument(id);
        toast.success('Document deleted');
        fetchDocuments();
      } catch {
        toast.error('Failed to delete document');
      }
    }
  };

  const verificationColors = {
    complete: 'bg-green-100 text-green-800',
    missing: 'bg-red-100 text-red-800',
    partial: 'bg-yellow-100 text-yellow-800',
    needs_review: 'bg-blue-100 text-blue-800',
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
            <p className="text-gray-500 mt-1">Manage your tax-related documents and receipts</p>
          </div>
          <Button onClick={() => setShowModal(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
              </div>
            ) : documents.length === 0 ? (
              <div className="p-8 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No documents uploaded yet</p>
                <Button variant="secondary" className="mt-4" onClick={() => setShowModal(true)}>
                  Upload your first document
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Financial Year</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Upload Date</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.map((doc, idx) => (
                      <TableRow key={(doc as any).id ?? (doc as any)._id ?? idx}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-gray-100 rounded-lg">
                              <FileText className="h-5 w-5 text-gray-600" />
                            </div>
                            <div>
                              <p className="font-medium">{doc.file_name}</p>
                              <p className="text-xs text-gray-500 capitalize">{doc.document_type.replace(/_/g, ' ')}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="capitalize">{doc.document_type.replace(/_/g, ' ')}</TableCell>
                        <TableCell>{doc.financial_year}</TableCell>
                        <TableCell>
                          <Badge variant={verificationColors[doc.verification_status] as any}>
                            {doc.verification_status.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatDate(doc.upload_date)}</TableCell>
                        <TableCell>{formatCurrency(doc.file_size / 1024)} KB</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => handleView(doc)} aria-label="View document">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDownload(doc)} aria-label="Download document">
                              <Download className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(doc)} aria-label="Delete document">
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
          onClose={() => { setShowModal(false); resetForm(); }}
          title="Upload Document"
          size="lg"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => setFormData({ ...formData, file: e.target.files?.[0] || null })}
                className="hidden"
                id="doc-upload"
              />
              <label htmlFor="doc-upload" className="cursor-pointer">
                <Upload className="h-10 w-10 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">Click to select file or drag and drop</p>
                <p className="text-sm text-gray-400 mt-1">PDF, JPG, PNG up to 10MB</p>
              </label>
              {formData.file && <p className="text-sm text-green-600 mt-2">Selected: {formData.file.name}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Document Type"
                name="document_type"
                value={formData.document_type}
                onChange={(e) => setFormData({ ...formData, document_type: e.target.value as DocumentType })}
                options={[
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
                ]}
                required
              />
              <Select
                label="Financial Year"
                name="financial_year"
                value={formData.financial_year}
                onChange={(e) => setFormData({ ...formData, financial_year: e.target.value })}
                options={[
                  { value: '2024-25', label: '2024-25' },
                  { value: '2023-24', label: '2023-24' },
                  { value: '2022-23', label: '2022-23' },
                ]}
                required
              />
            </div>

            <div className="border-t border-gray-100 pt-4">
              <p className="text-sm font-medium text-gray-700 mb-3">Link to (Optional)</p>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Transaction ID"
                  name="related_transaction_id"
                  value={formData.related_transaction_id}
                  onChange={(e) => setFormData({ ...formData, related_transaction_id: e.target.value })}
                  placeholder="Transaction ID"
                />
                <Input
                  label="Investment ID"
                  name="related_investment_id"
                  value={formData.related_investment_id}
                  onChange={(e) => setFormData({ ...formData, related_investment_id: e.target.value })}
                  placeholder="Investment ID"
                />
              </div>
              <Input
                label="Deduction ID"
                name="related_deduction_id"
                value={formData.related_deduction_id}
                onChange={(e) => setFormData({ ...formData, related_deduction_id: e.target.value })}
                placeholder="Deduction ID"
                className="max-w-md"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
              <Button type="button" variant="secondary" onClick={() => { setShowModal(false); resetForm(); }}>
                Cancel
              </Button>
              <Button type="submit" disabled={uploading || !formData.file} loading={uploading}>
                Upload
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}