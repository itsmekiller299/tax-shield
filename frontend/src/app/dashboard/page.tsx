'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { DashboardSummary, TaxReadinessScore, Obligation, Deadline } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ReadinessScoreGauge } from '@/components/charts/ReadinessScoreGauge';
import { IncomeBreakdownChart } from '@/components/charts/IncomeBreakdownChart';
import { formatCurrency, formatDate, getDaysUntil, getRiskColor, getRiskLabel, getStatusColor } from '@/lib/utils';
import {
  Shield,
  TrendingUp,
  AlertTriangle,
  Calendar,
  FileText,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [readinessScore, setReadinessScore] = useState<TaxReadinessScore | null>(null);
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSeedModal, setShowSeedModal] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const [summaryData, scoreData, obligationsData, deadlinesData] = await Promise.all([
        api.getDashboard(),
        api.getReadinessScore(),
        api.getObligations(),
        api.getDeadlines(),
      ]);
      setSummary(summaryData);
      setReadinessScore(scoreData);
      setObligations(obligationsData);
      setDeadlines(deadlinesData);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && !authLoading) {
      fetchDashboardData();
    }
  }, [user, authLoading]);

  const handleSeedDemo = async () => {
    try {
      await api.seedDemoData();
      toast.success('Demo data loaded!');
      fetchDashboardData();
      setShowSeedModal(false);
    } catch {
      toast.error('Failed to load demo data');
    }
  };

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
        </div>
      </DashboardLayout>
    );
  }

  const highRiskObligations = obligations.filter((o) => o.risk_level === 'high' && o.status === 'open').length;
  const upcomingDeadlines = deadlines.filter((d) => !d.is_completed && getDaysUntil(d.due_date) <= 30).length;
  const overdueDeadlines = deadlines.filter((d) => !d.is_completed && getDaysUntil(d.due_date) < 0).length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 mt-1">
              Welcome back, {user?.name}! Here&apos;s your tax readiness overview.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={fetchDashboardData} size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="secondary" onClick={() => setShowSeedModal(true)} size="sm">
              Load Demo Data
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Income</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {summary ? formatCurrency(summary.total_income) : '₹0'}
                  </p>
                </div>
                <div className="p-3 bg-primary-100 rounded-xl">
                  <TrendingUp className="h-6 w-6 text-primary-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Taxable Income</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {summary ? formatCurrency(summary.taxable_income) : '₹0'}
                  </p>
                </div>
                <div className="p-3 bg-green-100 rounded-xl">
                  <Shield className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Est. Tax Liability</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {summary ? formatCurrency(summary.estimated_liability) : '₹0'}
                  </p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-xl">
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 flex items-center justify-center">
              {readinessScore ? (
                <ReadinessScoreGauge score={readinessScore.score} size={100} showLabel={false} />
              ) : (
                <ReadinessScoreGauge score={0} size={100} showLabel={false} />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <IncomeBreakdownChart
              data={summary?.income_breakdown || {}}
              title="Income Sources"
            />

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Tax Readiness Breakdown</CardTitle>
                <Link href="/reports" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
                  View Details <ArrowRight className="h-4 w-4" />
                </Link>
              </CardHeader>
              <CardContent>
                {readinessScore && (
                  <div className="space-y-4">
                    {Object.entries(readinessScore.breakdown).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-primary-500" />
                          <span className="text-sm text-gray-700 capitalize">
                            {key.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary-500 transition-all duration-500"
                              style={{ width: `${value}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-900 w-10 text-right">
                            {value.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                    <div className="pt-4 border-t border-gray-100">
                      <p className="text-sm text-gray-600">{readinessScore.explanation}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>High Priority Alerts</CardTitle>
                <Badge variant={highRiskObligations > 0 ? 'high' : 'low'}>
                  {highRiskObligations} High Risk
                </Badge>
              </CardHeader>
              <CardContent>
                {obligations.filter((o) => o.risk_level === 'high' && o.status === 'open').length === 0 ? (
                  <div className="text-center py-8">
                    <Shield className="h-12 w-12 text-green-400 mx-auto mb-3" />
                    <p className="text-gray-500">No high-risk alerts</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {obligations
                      .filter((o) => o.risk_level === 'high' && o.status === 'open')
                      .slice(0, 3)
                      .map((obligation, oi) => (
                        <div key={(obligation as any).id ?? (obligation as any)._id ?? oi} className="p-3 bg-red-50 border border-red-100 rounded-lg">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{obligation.title}</p>
                              <p className="text-sm text-gray-600 mt-1">{obligation.description}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="high">{getRiskLabel(obligation.risk_level)} Risk</Badge>
                                <Badge variant="info">{Math.round(obligation.confidence * 100)}% confidence</Badge>
                              </div>
                            </div>
                          </div>
<Button variant="ghost" size="sm" className="mt-2" onClick={() => window.location.href = `/obligations`}>
                              View Details
                            </Button>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Upcoming Deadlines</CardTitle>
                <Badge variant={overdueDeadlines > 0 ? 'high' : upcomingDeadlines > 0 ? 'medium' : 'low'}>
                  {overdueDeadlines > 0 ? `${overdueDeadlines} Overdue` : `${upcomingDeadlines} Upcoming`}
                </Badge>
              </CardHeader>
              <CardContent>
                {deadlines.filter((d) => !d.is_completed).length === 0 ? (
                  <div className="text-center py-8">
                    <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">No upcoming deadlines</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {deadlines
                      .filter((d) => !d.is_completed)
                      .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
                      .slice(0, 5)
                      .map((deadline, di) => {
                        const days = getDaysUntil(deadline.due_date);
                        const isOverdue = days < 0;
                        const isUrgent = days <= 7 && days >= 0;
                        return (
                          <div
                            key={(deadline as any).id ?? (deadline as any)._id ?? di}
                            className={`p-3 rounded-lg border ${
                              isOverdue ? 'bg-red-50 border-red-100' : isUrgent ? 'bg-yellow-50 border-yellow-100' : 'bg-gray-50 border-gray-100'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-gray-900">{deadline.title}</p>
                                <p className="text-sm text-gray-600">{deadline.description}</p>
                              </div>
                              <div className="text-right">
                                <p className={`text-sm font-medium ${isOverdue ? 'text-red-600' : isUrgent ? 'text-yellow-600' : 'text-gray-600'}`}>
                                  {isOverdue ? `${Math.abs(days)} days overdue` : `${days} days left`}
                                </p>
                                <p className="text-xs text-gray-500">{formatDate(deadline.due_date)}</p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Link href="/transactions" className="flex items-center gap-2 w-full justify-start px-3 py-2 text-sm font-medium text-gray-900 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
                    <FileText className="h-4 w-4" />
                    Add Transaction
                  </Link>
                  <Link href="/documents" className="flex items-center gap-2 w-full justify-start px-3 py-2 text-sm font-medium text-gray-900 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
                    <FileText className="h-4 w-4" />
                    Upload Document
                  </Link>
                  <Link href="/scenarios" className="flex items-center gap-2 w-full justify-start px-3 py-2 text-sm font-medium text-gray-900 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
                    <Shield className="h-4 w-4" />
                    Create Scenario
                  </Link>
                  <Link href="/scenarios" className="flex items-center gap-2 w-full justify-start px-4 py-2 text-base font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors">
                    Compare Scenarios
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <Modal
          isOpen={showSeedModal}
          onClose={() => setShowSeedModal(false)}
          title="Load Demo Data"
          description="This will populate your account with sample financial data for demonstration purposes."
        >
          <div className="flex gap-3 justify-end">
            <Button variant="secondary" onClick={() => setShowSeedModal(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleSeedDemo}>
              Load Demo Data
            </Button>
          </div>
        </Modal>
      </div>
    </DashboardLayout>
  );
}