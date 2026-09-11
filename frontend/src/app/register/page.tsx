'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Shield, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    employment_type: '',
    tax_jurisdiction: 'India',
    financial_year: '2024-25',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const employmentTypes = [
    { value: 'salaried', label: 'Salaried Employee' },
    { value: 'freelancer', label: 'Freelancer/Gig Worker' },
    { value: 'business_owner', label: 'Business Owner' },
    { value: 'investor', label: 'Investor' },
    { value: 'landlord', label: 'Landlord' },
    { value: 'other', label: 'Other' },
  ];

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Invalid email format';
    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (formData.password !== formData.confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
    if (!formData.employment_type) newErrors.employment_type = 'Please select employment type';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });
      toast.success('Account created successfully!');
      router.push('/dashboard');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail
      ? Array.isArray(error.response.data.detail)
        ? error.response.data.detail.map((e: any) => e.msg).join(', ')
        : error.response.data.detail
      : 'Registration failed';
  toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <Shield className="h-10 w-10 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900">Tax Shield</span>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Create your account</h1>
          <p className="mt-2 text-gray-600">Start your tax readiness journey today</p>
        </div>

        <div className="card p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Full Name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              error={errors.name}
              placeholder="John Doe"
              autoComplete="name"
              required
            />

            <Input
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />

            <div className="relative">
              <Input
                label="Password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleChange}
                error={errors.password}
                placeholder="••••••••"
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-gray-400 hover:text-gray-600"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>

            <Input
              label="Confirm Password"
              name="confirmPassword"
              type={showPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleChange}
              error={errors.confirmPassword}
              placeholder="••••••••"
              autoComplete="new-password"
              required
            />

            <Select
              label="Employment Type"
              name="employment_type"
              value={formData.employment_type}
              onChange={handleChange}
              error={errors.employment_type}
              options={employmentTypes}
              placeholder="Select your employment type"
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Tax Jurisdiction"
                name="tax_jurisdiction"
                value={formData.tax_jurisdiction}
                onChange={handleChange}
                options={[
                  { value: 'India', label: 'India' },
                  { value: 'US', label: 'United States' },
                  { value: 'UK', label: 'United Kingdom' },
                ]}
              />
              <Select
                label="Financial Year"
                name="financial_year"
                value={formData.financial_year}
                onChange={handleChange}
                options={[
                  { value: '2024-25', label: '2024-25' },
                  { value: '2023-24', label: '2023-24' },
                  { value: '2022-23', label: '2022-23' },
                ]}
              />
            </div>

            <Button type="submit" className="w-full" size="lg" loading={loading}>
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          By continuing, you agree to our{' '}
          <Link href="/terms" className="text-primary-600 hover:underline">Terms of Service</Link>
          {' '}and{' '}
          <Link href="/privacy" className="text-primary-600 hover:underline">Privacy Policy</Link>
        </p>
      </div>
    </div>
  );
}