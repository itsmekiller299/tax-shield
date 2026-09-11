'use client';

import Link from 'next/link';
import { Shield } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-2xl card p-6 sm:p-8">
        <Link href="/" className="inline-flex items-center gap-2 mb-6">
          <Shield className="h-8 w-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">Tax Shield</span>
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Privacy Policy</h1>
        <div className="space-y-3 text-sm text-gray-600">
          <p>Every request is authenticated and scoped to your account — you can only ever access your own financial records, and the assistant never reveals another user&apos;s information.</p>
          <p>Passwords are stored hashed, sessions use signed tokens, and chat history belongs to your user only. Voice input is transcribed in your browser; raw recordings are not stored.</p>
          <p>Financial calculations run on a deterministic in-app rule engine. No tax decisions are outsourced to third-party AI services.</p>
        </div>
        <Link href="/login" className="inline-block mt-6 text-sm text-primary-600 hover:text-primary-700 font-medium">Back to sign in</Link>
      </div>
    </div>
  );
}
