'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  CreditCard,
  FileText,
  AlertTriangle,
  Calendar,
  GitCompare,
  MessageCircle,
  Settings,
  Shield,
  Users,
  BarChart3,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Transactions', href: '/transactions', icon: CreditCard },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Obligations', href: '/obligations', icon: AlertTriangle },
  { name: 'Deadlines', href: '/deadlines', icon: Calendar },
  { name: 'Scenarios', href: '/scenarios', icon: GitCompare },
  { name: 'AI Assistant', href: '/assistant', icon: MessageCircle },
  { name: 'Reports', href: '/reports', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 lg:translate-x-0">
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-100">
          <Link href="/dashboard" className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">Tax Shield</span>
          </Link>
        </div>
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {item.name}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            Tax Shield v1.0.0
          </p>
        </div>
      </div>
    </aside>
  );
}