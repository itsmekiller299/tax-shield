'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Scenario, RiskLevel } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { ScenarioComparisonChart } from '@/components/charts/ScenarioComparisonChart';
import { formatCurrency, getRiskColor, getRiskLabel, cn } from '@/lib/utils';
import { Plus, GitCompare, Trash2, Edit, CheckCircle, Radio } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ScenariosPage() {
  const { user } = useAuth();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    estimated_income: '',
    estimated_deductions: '',
    estimated_liability: '',
    risk_level: 'low' as RiskLevel,
    required_documents: '',
    assumptions: '{}',
    is_current: false,
  });

  const fetchScenarios = async () => {
    try {
      const data = await api.getScenarios();
      setScenarios(data);
    } catch {
      toast.error('Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        estimated_income: parseFloat(formData.estimated_income) || 0,
        estimated_deductions: parseFloat(formData.estimated_deductions) || 0,
        estimated_liability: parseFloat(formData.estimated_liability) || 0,
        risk_level: formData.risk_level,
        required_documents: formData.required_documents.split(',').map((d) => d.trim()).filter(Boolean),
        assumptions: formData.assumptions ? JSON.parse(formData.assumptions) : {},
        is_current: formData.is_current,
      };

      if (editingScenario) {
        await api.createScenario(data);
        toast.success('Scenario updated');
      } else {
        await api.createScenario(data);
        toast.success('Scenario created');
      }
      setShowModal(false);
      setEditingScenario(null);
      resetForm();
      fetchScenarios();
    } catch (error) {
      toast.error('Failed to save scenario');
    }
  };

  const handleCompare = async () => {
    if (selectedForCompare.length < 2) {
      toast.error('Select at least 2 scenarios to compare');
      return;
    }
    try {
      const result = await api.compareScenarios(selectedForCompare);
      setComparisonResult(result);
      setShowCompareModal(true);
    } catch {
      toast.error('Failed to compare scenarios');
    }
  };

  const [comparisonResult, setComparisonResult] = useState<any>(null);

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      estimated_income: '',
      estimated_deductions: '',
      estimated_liability: '',
      risk_level: 'low',
      required_documents: '',
      assumptions: '{}',
      is_current: false,
    });
  };

  const handleEdit = (scenario: Scenario) => {
    setEditingScenario(scenario);
    setFormData({
      name: scenario.name,
      description: scenario.description || '',
      estimated_income: scenario.estimated_income.toString(),
      estimated_deductions: scenario.estimated_deductions.toString(),
      estimated_liability: scenario.estimated_liability.toString(),
      risk_level: scenario.risk_level,
      required_documents: scenario.required_documents.join(', '),
      assumptions: JSON.stringify(scenario.assumptions, null, 2),
      is_current: scenario.is_current,
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this scenario?')) {
      // Note: DELETE endpoint not implemented in backend yet
      toast.error('Delete not implemented yet');
    }
  };

  const toggleCompareSelect = (id: string) => {
    setSelectedForCompare((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const currentScenario = scenarios.find((s) => s.is_current);
  const otherScenarios = scenarios.filter((s) => !s.is_current);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Scenario Comparison</h1>
            <p className="text-gray-500 mt-1">Compare financial decisions and their tax impact</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleCompare} disabled={selectedForCompare.length < 2}>
              <GitCompare className="h-4 w-4 mr-2" />
              Compare ({selectedForCompare.length})
            </Button>
            <Button onClick={() => { setEditingScenario(null); resetForm(); setShowModal(true); }}>
              <Plus className="h-4 w-4 mr-2" />
              New Scenario
            </Button>
          </div>
        </div>

        {currentScenario && (
          <Card className="border-primary-200">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                Current Scenario
                <Badge variant="success">Active</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Est. Income</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(currentScenario.estimated_income)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Est. Deductions</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(currentScenario.estimated_deductions)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Est. Liability</p>
                  <p className="text-2xl font-bold text-red-600">{formatCurrency(currentScenario.estimated_liability)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Alternative Scenarios</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
              </div>
            ) : otherScenarios.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500">No alternative scenarios created yet</p>
                <Button variant="secondary" className="mt-4" onClick={() => { setEditingScenario(null); resetForm(); setShowModal(true); }}>
                  Create your first scenario
                </Button>
              </div>
            ) : (
              <>
                <div className="mb-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">Compare</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Est. Income</TableHead>
                        <TableHead>Est. Deductions</TableHead>
                        <TableHead>Est. Liability</TableHead>
                        <TableHead>Risk</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {otherScenarios.map((scenario) => (
                        <TableRow key={scenario.id}>
                          <TableCell>
                            <label className="flex items-center justify-center">
                              <input
                                type="checkbox"
                                checked={selectedForCompare.includes(scenario.id)}
                                onChange={() => toggleCompareSelect(scenario.id)}
                                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                              />
                            </label>
                          </TableCell>
                          <TableCell className="font-medium">{scenario.name}</TableCell>
                          <TableCell>{formatCurrency(scenario.estimated_income)}</TableCell>
                          <TableCell>{formatCurrency(scenario.estimated_deductions)}</TableCell>
                          <TableCell>{formatCurrency(scenario.estimated_liability)}</TableCell>
                          <TableCell>
                            <Badge variant={getRiskColor(scenario.risk_level) as any}>
                              {getRiskLabel(scenario.risk_level)}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Button variant="ghost" size="sm" onClick={() => handleEdit(scenario)}>
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(scenario.id)}>
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {currentScenario && otherScenarios.length > 0 && (
                  <ScenarioComparisonChart
                    scenarios={[currentScenario, ...otherScenarios]}
                  />
                )}
              </>
            )}
          </CardContent>
        </Card>

        <Modal
          isOpen={showModal}
          onClose={() => { setShowModal(false); setEditingScenario(null); resetForm(); }}
          title={editingScenario ? 'Edit Scenario' : 'Create Scenario'}
          size="lg"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Scenario Name"
              name="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Maximize 80C Deductions"
              required
            />
            <Input
              label="Description"
              name="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="What does this scenario test?"
            />
            <div className="grid grid-cols-3 gap-4">
              <Input
                label="Est. Income (₹)"
                type="number"
                name="estimated_income"
                value={formData.estimated_income}
                onChange={(e) => setFormData({ ...formData, estimated_income: e.target.value })}
                placeholder="0"
                step="1000"
                min="0"
              />
              <Input
                label="Est. Deductions (₹)"
                type="number"
                name="estimated_deductions"
                value={formData.estimated_deductions}
                onChange={(e) => setFormData({ ...formData, estimated_deductions: e.target.value })}
                placeholder="0"
                step="1000"
                min="0"
              />
              <Input
                label="Est. Liability (₹)"
                type="number"
                name="estimated_liability"
                value={formData.estimated_liability}
                onChange={(e) => setFormData({ ...formData, estimated_liability: e.target.value })}
                placeholder="0"
                step="1000"
                min="0"
              />
            </div>
            <Select
              label="Risk Level"
              name="risk_level"
              value={formData.risk_level}
              onChange={(e) => setFormData({ ...formData, risk_level: e.target.value as RiskLevel })}
              options={[
                { value: 'low', label: 'Low' },
                { value: 'medium', label: 'Medium' },
                { value: 'high', label: 'High' },
              ]}
            />
            <Input
              label="Required Documents (comma-separated)"
              name="required_documents"
              value={formData.required_documents}
              onChange={(e) => setFormData({ ...formData, required_documents: e.target.value })}
              placeholder="ELSS proof, PPF receipt, etc."
            />
            <div>
              <label className="label">Assumptions (JSON)</label>
              <textarea
                name="assumptions"
                value={formData.assumptions}
                onChange={(e) => setFormData({ ...formData, assumptions: e.target.value })}
                className="input font-mono text-sm"
                rows={4}
                placeholder='{"regime": "old", "additional_80c": 100000}'
              />
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_current}
                onChange={(e) => setFormData({ ...formData, is_current: e.target.checked })}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Set as current scenario</span>
            </label>
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
              <Button type="button" variant="secondary" onClick={() => { setShowModal(false); setEditingScenario(null); resetForm(); }}>
                Cancel
              </Button>
              <Button type="submit">
                {editingScenario ? 'Update' : 'Create'} Scenario
              </Button>
            </div>
          </form>
        </Modal>

        <Modal
          isOpen={showCompareModal}
          onClose={() => setShowCompareModal(false)}
          title="Scenario Comparison"
          size="xl"
        >
          {comparisonResult && (
            <div className="space-y-6">
              <p className="text-sm text-gray-600 text-center italic">
                {comparisonResult.disclaimer}
              </p>
              <ScenarioComparisonChart scenarios={comparisonResult.comparison} />
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Metric</TableHead>
                      {comparisonResult.comparison.map((s: any, i: number) => (
                        <TableHead key={`${s.name}-${i}`}>{s.name}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Est. Income</TableCell>
                      {comparisonResult.comparison.map((s: any, i: number) => (
                        <TableCell key={`${s.name}-${i}`}>{formatCurrency(s.estimated_income)}</TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Est. Deductions</TableCell>
                      {comparisonResult.comparison.map((s: any, i: number) => (
                        <TableCell key={`${s.name}-${i}`}>{formatCurrency(s.estimated_deductions)}</TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Est. Liability</TableCell>
                      {comparisonResult.comparison.map((s: any, i: number) => (
                        <TableCell key={`${s.name}-${i}`}>{formatCurrency(s.estimated_liability)}</TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Risk Level</TableCell>
                      {comparisonResult.comparison.map((s: any, i: number) => (
                        <TableCell key={`${s.name}-${i}`}>
                          <Badge variant={getRiskColor(s.risk_level) as any}>
                            {getRiskLabel(s.risk_level)}
                          </Badge>
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Required Docs</TableCell>
                      {comparisonResult.comparison.map((s: any, i: number) => (
                        <TableCell key={`${s.name}-${i}`}>{s.required_documents.length} documents</TableCell>
                      ))}
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <Button variant="secondary" onClick={() => setShowCompareModal(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </DashboardLayout>
  );
}