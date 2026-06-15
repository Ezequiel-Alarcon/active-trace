import { useState } from 'react';
import { forgotPassword } from '../services/authApi';
import type { ForgotRequest } from '../types/session';

interface ForgotState {
  submitted: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useForgot() {
  const [state, setState] = useState<ForgotState>({
    submitted: false,
    isLoading: false,
    error: null,
  });

  async function submit(payload: ForgotRequest) {
    setState({ submitted: false, isLoading: true, error: null });
    try {
      await forgotPassword(payload);
      // Always show neutral message regardless of outcome
      setState({ submitted: true, isLoading: false, error: null });
    } catch {
      // Still show neutral message to avoid account enumeration
      setState({ submitted: true, isLoading: false, error: null });
    }
  }

  return {
    submitted: state.submitted,
    isLoading: state.isLoading,
    error: state.error,
    submit,
  };
}
