'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { AssistantChatPanel } from '@/components/assistant/AssistantChat';

export default function AssistantPage() {
  return (
    <DashboardLayout>
      <AssistantChatPanel />
    </DashboardLayout>
  );
}
