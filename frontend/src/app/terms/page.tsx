'use client';

import Link from 'next/link';
import { Shield } from 'lucide-react';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-2xl card p-6 sm:p-8">
        <Link href="/" className="inline-flex items-center gap-2 mb-6">
          <Shield className="h-8 w-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">Tax Shield</span>
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Terms of Service</h1>
        <div className="space-y-3 text-sm text-gray-600">
          <p>TaxShield is a tax-readiness awareness platform. It organizes your financial information, checks expected evidence, reconciles records, and estimates your tax-readiness — it does not provide legal, tax, or financial advice.</p>
          <p>Estimates shown in the app (including scenario comparisons and the AI assistant&apos;s answers) are preliminary and based only on the information available in the system. Consult a qualified tax professional before making tax decisions.</p>
          <p>Your data belongs to you and is scoped to your authenticated account. Demo accounts may use sample data.</p>
        </div>
        <Link href="/login" className="inline-block mt-6 text-sm text-primary-600 hover:text-primary-700 font-medium">Back to sign in</Link>
      </div>
    </div>
  );
}
