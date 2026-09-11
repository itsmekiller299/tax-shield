'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/lib/auth';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { User, Shield, Bell, Palette, Database, LogOut } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { user, logout, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security' | 'data'>('profile');
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    age: user?.age?.toString() || '',
    tax_jurisdiction: user?.tax_jurisdiction || 'India',
    financial_year: user?.financial_year || '2024-25',
    employment_type: user?.employment_type || '',
    preferred_tax_regime: user?.preferred_tax_regime || '',
    risk_preference: user?.risk_preference || 'moderate',
  });

  const handleSaveProfile = async () => {
    toast.success('Profile saved (demo mode)');
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'preferences', label: 'Preferences', icon: Shield },
    { id: 'security', label: 'Security', icon: Bell },
    { id: 'data', label: 'Data Management', icon: Database },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">Manage your account and preferences</p>
        </div>

        <Card>
          <CardContent className="p-0">
            <nav className="border-b border-gray-100" aria-label="Settings tabs">
              <ul className="flex flex-wrap -mb-px" role="tablist">
                {tabs.map((tab) => (
                  <li key={tab.id} role="presentation">
                    <button
                      role="tab"
                      aria-selected={activeTab === tab.id}
                      aria-controls={`${tab.id}-panel`}
                      id={`${tab.id}-tab`}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === tab.id
                          ? 'border-primary-600 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
                      }`}
                    >
                      <tab.icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>

            <div className="p-6">
              {activeTab === 'profile' && (
                <div id="profile-panel" role="tabpanel" aria-labelledby="profile-tab" className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="h-20 w-20 rounded-full bg-primary-100 flex items-center justify-center">
                      <User className="h-10 w-10 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{profileData.name || 'User'}</h3>
                      <p className="text-gray-500">{profileData.email}</p>
                      <p className="text-sm text-gray-400">Member since {user?.created_at ? formatDate(user.created_at) : 'Unknown'}</p>
                    </div>
                  </div>
                  <div className="border-t border-gray-100 pt-6 space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Input
                        label="Full Name"
                        value={profileData.name}
                        onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      />
                      <Input
                        label="Email"
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                        disabled
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Input
                        label="Age"
                        type="number"
                        value={profileData.age}
                        onChange={(e) => setProfileData({ ...profileData, age: e.target.value })}
                        min="18"
                        max="100"
                      />
                      <Select
                        label="Tax Jurisdiction"
                        value={profileData.tax_jurisdiction}
                        onChange={(e) => setProfileData({ ...profileData, tax_jurisdiction: e.target.value })}
                        options={[
                          { value: 'India', label: 'India' },
                          { value: 'US', label: 'United States' },
                          { value: 'UK', label: 'United Kingdom' },
                        ]}
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Select
                        label="Financial Year"
                        value={profileData.financial_year}
                        onChange={(e) => setProfileData({ ...profileData, financial_year: e.target.value })}
                        options={[
                          { value: '2024-25', label: '2024-25' },
                          { value: '2023-24', label: '2023-24' },
                          { value: '2022-23', label: '2022-23' },
                        ]}
                      />
                      <Select
                        label="Employment Type"
                        value={profileData.employment_type}
                        onChange={(e) => setProfileData({ ...profileData, employment_type: e.target.value })}
                        options={[
                          { value: 'salaried', label: 'Salaried Employee' },
                          { value: 'freelancer', label: 'Freelancer/Gig Worker' },
                          { value: 'business_owner', label: 'Business Owner' },
                          { value: 'investor', label: 'Investor' },
                          { value: 'landlord', label: 'Landlord' },
                          { value: 'other', label: 'Other' },
                        ]}
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Select
                        label="Preferred Tax Regime"
                        value={profileData.preferred_tax_regime}
                        onChange={(e) => setProfileData({ ...profileData, preferred_tax_regime: e.target.value })}
                        options={[
                          { value: '', label: 'Not specified' },
                          { value: 'old', label: 'Old Regime' },
                          { value: 'new', label: 'New Regime' },
                        ]}
                      />
                      <Select
                        label="Risk Preference"
                        value={profileData.risk_preference}
                        onChange={(e) => setProfileData({ ...profileData, risk_preference: e.target.value })}
                        options={[
                          { value: 'conservative', label: 'Conservative' },
                          { value: 'moderate', label: 'Moderate' },
                          { value: 'aggressive', label: 'Aggressive' },
                        ]}
                      />
                    </div>
                    <Button onClick={handleSaveProfile}>
                      Save Changes
                    </Button>
                  </div>
                </div>
              )}

              {activeTab === 'preferences' && (
                <div id="preferences-panel" role="tabpanel" aria-labelledby="preferences-tab" className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Notification Preferences</h3>
                    <div className="space-y-4">
                      {[
                        { id: 'email_alerts', label: 'Email Alerts', description: 'Receive email notifications for deadlines and obligations' },
                        { id: 'deadline_reminders', label: 'Deadline Reminders', description: 'Get reminded 7 days before tax deadlines' },
                        { id: 'obligation_alerts', label: 'Obligation Alerts', description: 'Notifications when new obligations are detected' },
                        { id: 'weekly_summary', label: 'Weekly Summary', description: 'Weekly tax readiness summary email' },
                      ].map((pref) => (
                        <label key={pref.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-900">{pref.label}</p>
                            <p className="text-sm text-gray-500">{pref.description}</p>
                          </div>
                          <input
                            type="checkbox"
                            defaultChecked
                            className="h-5 w-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="border-t border-gray-100 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Display Preferences</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Currency</label>
                        <Select
                          value="INR"
                          onChange={() => {}}
                          options={[
                            { value: 'INR', label: 'Indian Rupee (₹)' },
                            { value: 'USD', label: 'US Dollar ($)' },
                          ]}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Date Format</label>
                        <Select
                          value="DD/MM/YYYY"
                          onChange={() => {}}
                          options={[
                            { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
                            { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
                            { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
                          ]}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'security' && (
                <div id="security-panel" role="tabpanel" aria-labelledby="security-tab" className="space-y-6">
                  <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg">
                    <h3 className="font-medium text-blue-900 mb-2">Demo Mode Notice</h3>
                    <p className="text-blue-800 text-sm">
                      This is a demo version. Authentication and security features are simulated.
                      In production, this section would include password management, 2FA, and session controls.
                    </p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Password</h3>
                    <Button variant="secondary">Change Password</Button>
                  </div>
                  <div className="border-t border-gray-100 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Two-Factor Authentication</h3>
                    <Button variant="secondary">Enable 2FA</Button>
                  </div>
                  <div className="border-t border-gray-100 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Sessions</h3>
                    <p className="text-sm text-gray-500">Session management would appear here in production.</p>
                  </div>
                </div>
              )}

              {activeTab === 'data' && (
                <div id="data-panel" role="tabpanel" aria-labelledby="data-tab" className="space-y-6">
                  <div className="p-4 bg-yellow-50 border border-yellow-100 rounded-lg">
                    <h3 className="font-medium text-yellow-900 mb-2">Demo Mode Notice</h3>
                    <p className="text-yellow-800 text-sm">
                      Data export and deletion features are simulated in demo mode.
                    </p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h3>
                    <div className="flex flex-wrap gap-4">
                      <Button variant="secondary">Export Transactions (CSV)</Button>
                      <Button variant="secondary">Export All Data (JSON)</Button>
                    </div>
                  </div>
                  <div className="border-t border-gray-100 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Import Data</h3>
                    <Button variant="secondary">Import Transactions (CSV)</Button>
                  </div>
                  <div className="border-t border-gray-100 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Danger Zone</h3>
                    <div className="p-4 bg-red-50 border border-red-100 rounded-lg">
                      <p className="text-red-800 text-sm mb-4">
                        Deleting your account will permanently remove all your data. This action cannot be undone.
                      </p>
                      <Button variant="danger" onClick={logout}>
                        <LogOut className="h-4 w-4 mr-2" />
                        Sign Out
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}