import { redirect } from 'next/navigation';

export default function NewTripIntakeRedirectPage() {
  redirect('/workbench?draft=new&tab=intake&capture_mode=call&entry=new');
}
