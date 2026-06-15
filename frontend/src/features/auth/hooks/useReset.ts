import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { resetPassword, extractAuthErrorCode } from '../services/authApi';
import type { ResetRequest } from '../types/session';

interface ResetState {
  success: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useReset() {
  const navigate = useNavigate();
  const [state, setState] = useState<ResetState>({
    success: false,
    isLoading: false,
    error: null,
  });

  async function submit(payload: ResetRequest) {
    setState({ success: false, isLoading: true, error: null });
    try {
      await resetPassword(payload);
      setState({ success: true, isLoading: false, error: null });
      setTimeout(() => navigate('/login', { replace: true }), 1500);
    } catch (err) {
      const code = extractAuthErrorCode(err);
      const isExpiredOrInvalid =
        code === 'AUTH_RESET_EXPIRED' || code === 'AUTH_RESET_INVALID';
      setState({
        success: false,
        isLoading: false,
        error: isExpiredOrInvalid
          ? 'El enlace expiró o ya fue usado. Solicitá uno nuevo.'
          : 'Error inesperado. Intentá de nuevo.',
      });
    }
  }

  return {
    success: state.success,
    isLoading: state.isLoading,
    error: state.error,
    submit,
  };
}
