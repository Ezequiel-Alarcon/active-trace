import { Card } from '@/shared/ui';
import ForgotPasswordForm from '../components/ForgotPasswordForm';

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-sm shadow-sm">
        <div className="flex items-center gap-2 mb-6">
          <span className="h-5 w-5 rounded bg-blue-600" aria-hidden="true" />
          <span className="font-semibold text-gray-800">Active Trace</span>
        </div>
        <ForgotPasswordForm />
      </Card>
    </div>
  );
}
