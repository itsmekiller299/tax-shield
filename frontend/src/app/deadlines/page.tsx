'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Deadline } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { formatDate, getDaysUntil, cn } from '@/lib/utils';
import { Calendar, CheckCircle, AlertCircle, Clock, Filter } from 'lucide-react';
import toast from 'react-hot-toast';

export default function DeadlinesPage() {
  const { user } = useAuth();
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'overdue' | 'completed'>('all');

  const fetchDeadlines = async () => {
    try {
      const data = await api.getDeadlines();
      setDeadlines(data);
    } catch {
      toast.error('Failed to load deadlines');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeadlines();
  }, []);

  const handleToggleComplete = async (deadline: Deadline) => {
    try {
      await api.updateDeadlineStatus(deadline.id, !deadline.is_completed);
      toast.success(deadline.is_completed ? 'Marked as incomplete' : 'Marked as complete');
      setDeadlines(deadlines.map((d) => (d.id === deadline.id ? { ...d, is_completed: !d.is_completed } : d)));
    } catch {
      toast.error('Failed to update deadline');
    }
  };

  const filteredDeadlines = deadlines.filter((d) => {
    const days = getDaysUntil(d.due_date);
    const isOverdue = days < 0 && !d.is_completed;
    const isUpcoming = days >= 0 && days <= 30 && !d.is_completed;
    
    switch (filter) {
      case 'upcoming':
        return isUpcoming;
      case 'overdue':
        return isOverdue;
      case 'completed':
        return d.is_completed;
      default:
        return true;
    }
  }).sort((a, b) => {
    if (a.is_completed !== b.is_completed) return a.is_completed ? 1 : -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  const stats = {
    overdue: deadlines.filter((d) => !d.is_completed && getDaysUntil(d.due_date) < 0).length,
    upcoming: deadlines.filter((d) => !d.is_completed && getDaysUntil(d.due_date) >= 0 && getDaysUntil(d.due_date) <= 30).length,
    completed: deadlines.filter((d) => d.is_completed).length,
    total: deadlines.length,
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Deadlines</h1>
            <p className="text-gray-500 mt-1">Track important tax dates and filing deadlines</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Deadlines</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <div className="p-3 bg-gray-100 rounded-xl">
                  <Calendar className="h-6 w-6 text-gray-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Overdue</p>
                  <p className="text-2xl font-bold text-red-600">{stats.overdue}</p>
                </div>
                <div className="p-3 bg-red-100 rounded-xl">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Upcoming (30 days)</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.upcoming}</p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-xl">
                  <Clock className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Completed</p>
                  <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
                </div>
                <div className="p-3 bg-green-100 rounded-xl">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2">
              {(['all', 'upcoming', 'overdue', 'completed'] as const).map((f) => (
                <Button
                  key={f}
                  variant={filter === f ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setFilter(f)}
                  className="capitalize"
                >
                  {f}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent mx-auto" />
              </div>
            ) : filteredDeadlines.length === 0 ? (
              <div className="p-8 text-center">
                <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No deadlines found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Deadline</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Days Left</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Required Documents</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredDeadlines.map((deadline, idx) => {
                      const days = getDaysUntil(deadline.due_date);
                      const isOverdue = days < 0 && !deadline.is_completed;
                      const isUrgent = days >= 0 && days <= 7 && !deadline.is_completed;

                      return (
                        <TableRow key={(deadline as any).id ?? (deadline as any)._id ?? `${deadline.title}-${deadline.due_date}-${idx}`} className={deadline.is_completed ? 'bg-green-50' : ''}>
                          <TableCell>
                            <div>
                              <p className="font-medium text-gray-900">{deadline.title}</p>
                              <p className="text-sm text-gray-500">{deadline.description}</p>
                            </div>
                          </TableCell>
                          <TableCell className="capitalize">{deadline.deadline_type.replace(/_/g, ' ')}</TableCell>
                          <TableCell>{formatDate(deadline.due_date)}</TableCell>
                          <TableCell>
                            {deadline.is_completed ? (
                              <Badge variant="success">Completed</Badge>
                            ) : isOverdue ? (
                              <Badge variant="danger">{Math.abs(days)} days overdue</Badge>
                            ) : isUrgent ? (
                              <Badge variant="warning">{days} days left</Badge>
                            ) : (
                              <Badge variant="info">{days} days left</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {deadline.is_completed ? (
                              <Badge variant="success">
                                <CheckCircle className="h-3 w-3 mr-1" /> Completed
                              </Badge>
                            ) : (
                              <Badge variant="default">
                                <Clock className="h-3 w-3 mr-1" /> Pending
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {deadline.required_documents.slice(0, 3).map((doc, i) => (
                                <Badge key={i} variant="default" className="text-xs">{doc}</Badge>
                              ))}
                              {deadline.required_documents.length > 3 && (
                                <Badge variant="default" className="text-xs">+{deadline.required_documents.length - 3} more</Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleToggleComplete(deadline)}
                              className={deadline.is_completed ? 'text-green-600' : ''}
                            >
                              {deadline.is_completed ? (
                                <CheckCircle className="h-4 w-4" />
                              ) : (
                                <Clock className="h-4 w-4" />
                              )}
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}