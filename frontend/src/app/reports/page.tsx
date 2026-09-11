'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Printer, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ReportsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [regime, setRegime] = useState<'old' | 'new'>('old');
  const [report, setReport] = useState<any>(null);

  const loadReport = async (r: 'old' | 'new') => {
    setLoading(true);
    try {
      const [dashboard, readiness, transactions, obligations, deadlines, documents, deductions, taxDetail, recon, risks] =
        await Promise.all([
          api.getDashboard(r),
          api.getReadinessScore(),
          api.getTransactions(),
          api.getObligations(),
          api.getDeadlines(),
          api.getDocuments(),
          api.getDeductions(),
          api.getTaxDetail(r),
          api.getReconciliation().catch(() => null),
          api.getRisks().catch(() => ({ risks: [] })),
        ]);
      setReport({ dashboard, readiness, transactions, obligations, deadlines, documents, deductions, taxDetail, recon, risks: risks?.risks ?? [] });
    } catch {
      toast.error('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport(regime);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [regime]);

  const d = report?.dashboard;
  const t = report?.taxDetail;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Tax Readiness Report</h1>
            <p className="text-gray-500 mt-1">
              {user?.name ?? 'Taxpayer'} · FY {user?.financial_year ?? '2024-25'} · Generated {new Date().toLocaleDateString('en-IN')}
            </p>
          </div>
          <div className="flex items-center gap-2 print:hidden">
            <div className="flex rounded-lg border border-gray-200 overflow-hidden" role="group" aria-label="Tax regime">
              {(['old', 'new'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setRegime(r)}
                  className={`px-3 py-1.5 text-sm font-medium capitalize ${regime === r ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  {r} regime
                </button>
              ))}
            </div>
            <Button variant="secondary" size="sm" onClick={() => window.print()}>
              <Printer className="h-4 w-4 mr-1.5" /> Print / Save PDF
            </Button>
          </div>
        </div>

        {loading || !report ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Total Income', value: formatCurrency(d.total_income) },
                { label: 'Taxable Income', value: formatCurrency(d.taxable_income) },
                { label: 'Est. Liability', value: formatCurrency(d.estimated_liability) },
                { label: 'Readiness Score', value: `${d.readiness_score}/100` },
              ].map((s) => (
                <Card key={s.label}>
                  <CardContent className="p-5">
                    <p className="text-sm text-gray-500">{s.label}</p>
                    <p className="text-xl font-bold text-gray-900 mt-1">{s.value}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader><CardTitle>Tax Computation ({regime} regime)</CardTitle></CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableBody>
                    {[
                      ['Taxable income', formatCurrency(t?.taxable_income ?? d.taxable_income)],
                      ['Base slab tax', formatCurrency(t?.base ?? d.base_tax ?? 0)],
                      ['Less: 87A rebate', `− ${formatCurrency(t?.rebate ?? d.rebate ?? 0)}`],
                      ['Add: surcharge', formatCurrency(t?.surcharge ?? d.surcharge ?? 0)],
                      ['Add: health & education cess (4%)', formatCurrency(t?.cess ?? d.cess ?? 0)],
                      ['Total estimated liability', formatCurrency(t?.total_liability ?? d.estimated_liability)],
                      ['Tax paid', formatCurrency(d.tax_paid ?? 0)],
                      ['Outstanding', formatCurrency(t ? Math.max(0, (t.total_liability ?? 0) - (d.tax_paid ?? 0)) : (d.outstanding_tax ?? 0))],
                    ].map(([k, v]) => (
                      <TableRow key={k}>
                        <TableCell className="font-medium">{k}</TableCell>
                        <TableCell className="text-right">{v}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-2 gap-4">
              <Card>
                <CardHeader><CardTitle>Income Breakdown</CardTitle></CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableBody>
                      {Object.entries(d.income_breakdown ?? {}).map(([k, v]) => (
                        <TableRow key={k}>
                          <TableCell className="capitalize">{String(k).replace(/_/g, ' ')}</TableCell>
                          <TableCell className="text-right">{formatCurrency(v as number)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Readiness Breakdown</CardTitle></CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableBody>
                      {Object.entries(report.readiness?.breakdown ?? {}).slice(0, 5).map(([k, v]) => (
                        <TableRow key={k}>
                          <TableCell className="capitalize">{k.replace(/_/g, ' ')}</TableCell>
                          <TableCell className="text-right">{String(v)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <p className="text-sm text-gray-600 p-4">{report.readiness?.explanation}</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader><CardTitle>Open Obligations ({(report.obligations ?? []).length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Obligation</TableHead>
                      <TableHead>Risk</TableHead>
                      <TableHead>Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(report.obligations ?? []).slice(0, 20).map((o: any, i: number) => (
                      <TableRow key={o.id ?? o._id ?? i}>
                        <TableCell>
                          <p className="font-medium text-gray-900">{o.title}</p>
                          <p className="text-xs text-gray-500">{o.recommended_action}</p>
                        </TableCell>
                        <TableCell><Badge variant={o.risk_level === 'high' ? 'danger' : o.risk_level === 'medium' ? 'warning' : 'success'}>{o.risk_level}</Badge></TableCell>
                        <TableCell className="text-right">{formatCurrency(o.estimated_amount ?? 0)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Reconciliation & Deadlines</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm text-gray-700">
                <p>
                  Reconciliation: <strong>{report.recon?.status ?? '—'}</strong>
                  {report.recon ? ` (${report.recon.matched ?? 0} matched · ${report.recon.mismatched ?? 0} mismatched · ${report.recon.missing ?? 0} missing)` : ''}
                </p>
                <p>Upcoming deadlines: <strong>{(report.deadlines ?? []).filter((x: any) => !x.is_completed).length}</strong></p>
                {(report.deadlines ?? []).filter((x: any) => !x.is_completed).slice(0, 5).map((x: any, i: number) => (
                  <p key={x.id ?? x._id ?? i}>· {x.title} — due {formatDate(x.due_date)}</p>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 flex gap-2 text-xs text-gray-500">
                <FileText className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <p>TaxShield provides preliminary analysis based on the information available in the system. It does not provide legal, tax or financial advice and should not replace a qualified tax professional. Figures are estimates, not confirmed liabilities.</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
