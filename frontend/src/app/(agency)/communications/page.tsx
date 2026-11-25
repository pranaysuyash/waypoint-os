import type { Metadata } from 'next';
import ChannelMessagesPanel from '@/components/inbox/ChannelMessagesPanel';

export const metadata: Metadata = {
  title: 'Waypoint OS — Communications',
  description: 'Manage traveler conversations and staff replies.',
};

export default function CommunicationsPage() {
  return (
    <div className='space-y-4 p-4 sm:p-6'>
      <h1 className='text-ui-xl font-semibold text-[#e6edf3]'>Communications</h1>
      <section aria-labelledby='whatsapp-heading' className='space-y-3'>
        <h2 id='whatsapp-heading' className='text-ui-sm font-semibold text-[#e6edf3]'>WhatsApp</h2>
        <ChannelMessagesPanel scope='whatsapp' />
      </section>
    </div>
  );
}
