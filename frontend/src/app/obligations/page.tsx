'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Obligation, ObligationStatus, RiskLevel } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Modal } from '@/components/ui/Modal';
import { formatCurrency, formatDate, getRiskColor, getRiskLabel, getStatusColor, cn } from '@/lib/utils';
import { AlertTriangle, CheckCircle, XCircle, Clock, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ObligationsPage() {
  const { user } = useAuth();
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedObligation, setSelectedObligation] = useState<Obligation | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const fetchObligations = async () => {
    try {
      const data = await api.getObligations();
      setObligations(data);
    } catch {
      toast.error('Failed to load obligations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObligations();
  }, []);

  const handleStatusChange = async (obligation: Obligation, newStatus: ObligationStatus) => {
    try {
      await api.updateObligationStatus(obligation.id, newStatus);
      toast.success(`Status updated to ${newStatus.replace('_', ' ')}`);
      setObligations(obligations.map((o) => (o.id === obligation.id ? { ...o, status: newStatus } : o)));
    } catch {
      toast.error('Failed to update status');
    }
  };

  const riskColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  const statusColors = {
    open: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    resolved: 'bg-green-100 text-green-800',
    dismissed: 'bg-gray-100 text-gray-800',
  };

  const typeLabels: Record<string, string> = {
    missing_document: 'Missing Document',
    unreported_income: 'Unreported Income',
    advance_tax: 'Advance Tax',
    reporting_requirement: 'Reporting Requirement',
    deadline: 'Deadline',
    verification_needed: 'Verification Needed',
  };

  const stats = {
    total: obligations.length,
    high: obligations.filter((o) => o.risk_level === 'high' && o.status === 'open').length,
    medium: obligations.filter((o) => o.risk_level === 'medium' && o.status === 'open').length,
    low: obligations.filter((o) => o.risk_level === 'low' && o.status === 'open').length,
    open: obligations.filter((o) => o.status === 'open').length,
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Tax Obligations</h1>
            <p className="text-gray-500 mt-1">Track and resolve detected tax obligations</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Obligations</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-xl">
                  <AlertTriangle className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">High Risk</p>
                  <p className="text-2xl font-bold text-red-600">{stats.high}</p>
                </div>
                <div className="p-3 bg-red-100 rounded-xl">
                  <AlertTriangle className="h-6 w-6 text-red-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Medium Risk</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.medium}</p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-xl">
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Open</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.open}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-xl">
                  <Clock className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
              </div>
            ) : obligations.length === 0 ? (
              <div className="p-8 text-center">
                <CheckCircle className="h-12 w-12 text-green-400 mx-auto mb-3" />
                <p className="text-gray-500">No obligations detected</p>
                <p className="text-sm text-gray-400 mt-1">Your tax records look clean!</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Risk</TableHead>
                      <TableHead>Est. Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {obligations.map((obligation, idx) => (
                      <TableRow key={(obligation as any).id ?? (obligation as any)._id ?? idx}>
                        <TableCell>
                          <div>
                            <p className="font-medium text-gray-900">{obligation.title}</p>
                            <p className="text-sm text-gray-500 truncate max-w-xs">{obligation.description}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="default">{typeLabels[obligation.obligation_type] || obligation.obligation_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={riskColors[obligation.risk_level] as any}>
                            {getRiskLabel(obligation.risk_level)} Risk
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {obligation.estimated_amount ? formatCurrency(obligation.estimated_amount) : '-'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={statusColors[obligation.status] as any}>
                            {obligation.status.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>{obligation.due_date ? formatDate(obligation.due_date) : '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => { setSelectedObligation(obligation); setShowDetailModal(true); }}>
                              <ArrowRight className="h-4 w-4" />
                            </Button>
                            {obligation.status === 'open' && (
                              <Button variant="ghost" size="sm" onClick={() => handleStatusChange(obligation, 'in_progress')}>
                                <Clock className="h-4 w-4" />
                              </Button>
                            )}
                            {obligation.status === 'in_progress' && (
                              <>
                                <Button variant="ghost" size="sm" onClick={() => handleStatusChange(obligation, 'resolved')}>
                                  <CheckCircle className="h-4 w-4 text-green-500" />
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => handleStatusChange(obligation, 'dismissed')}>
                                  <XCircle className="h-4 w-4 text-gray-500" />
                                </Button>
                              </>
                            )}
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
          isOpen={showDetailModal}
          onClose={() => { setShowDetailModal(false); setSelectedObligation(null); }}
          title={selectedObligation?.title}
          size="lg"
        >
          {selectedObligation && (
            <div className="space-y-6">
              <div className="flex flex-wrap gap-2">
                <Badge variant={riskColors[selectedObligation.risk_level] as any}>
                  {getRiskLabel(selectedObligation.risk_level)} Risk
                </Badge>
                <Badge variant={statusColors[selectedObligation.status] as any}>
                  {selectedObligation.status.replace('_', ' ')}
                </Badge>
                <Badge variant="info">{Math.round(selectedObligation.confidence * 100)}% Confidence</Badge>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                <p className="text-gray-600">{selectedObligation.description}</p>
              </div>

              {selectedObligation.estimated_amount && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Estimated Amount</h4>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(selectedObligation.estimated_amount)}</p>
                </div>
              )}

              {selectedObligation.due_date && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Due Date</h4>
                  <p className="text-gray-600">{formatDate(selectedObligation.due_date)}</p>
                </div>
              )}

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Recommended Action</h4>
                <p className="text-gray-600">{selectedObligation.recommended_action}</p>
              </div>

              {selectedObligation.related_transaction_ids.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Related Transactions</h4>
                  <p className="text-sm text-gray-500">{selectedObligation.related_transaction_ids.length} transaction(s) linked</p>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                {selectedObligation.status === 'open' && (
                  <Button onClick={() => handleStatusChange(selectedObligation, 'in_progress')}>
                    Mark In Progress
                  </Button>
                )}
                {selectedObligation.status === 'in_progress' && (
                  <>
                    <Button variant="secondary" onClick={() => handleStatusChange(selectedObligation, 'open')}>
                      Reopen
                    </Button>
                    <Button onClick={() => handleStatusChange(selectedObligation, 'resolved')}>
                      Mark Resolved
                    </Button>
                  </>
                )}
                {selectedObligation.status === 'resolved' && (
                  <Button variant="secondary" onClick={() => handleStatusChange(selectedObligation, 'open')}>
                    Reopen
                  </Button>
                )}
              </div>
            </div>
          )}
        </Modal>
      </div>
    </DashboardLayout>
  );
}