import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, verify2fa, extractAuthErrorCode } from '../services/authApi';
import { useAuth } from '../components/AuthProvider';
import type { LoginRequest } from '../types/session';

type LoginStep = 'credentials' | '2fa';

interface LoginState {
  step: LoginStep;
  error: string | null;
  isLoading: boolean;
  // Stored to pass along to 2FA step
  pendingCredentials: Omit<LoginRequest, 'totp_code'> | null;
}

export function useLogin() {
  const navigate = useNavigate();
  const { setSession } = useAuth();

  const [state, setState] = useState<LoginState>({
    step: 'credentials',
    error: null,
    isLoading: false,
    pendingCredentials: null,
  });

  async function submitCredentials(payload: LoginRequest) {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const response = await login(payload);
      setSession(response);
      navigate('/', { replace: true });
    } catch (err) {
      const code = extractAuthErrorCode(err);
      if (code === 'AUTH_2FA_REQUIRED') {
        setState({
          step: '2fa',
          error: null,
          isLoading: false,
          pendingCredentials: payload,
        });
      } else {
        setState((s) => ({
          ...s,
          isLoading: false,
          error: 'Credenciales inválidas. Verificá tus datos e intentá de nuevo.',
        }));
      }
    }
  }

  async function submit2fa(totpCode: string) {
    if (!state.pendingCredentials) return;
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const response = await verify2fa({
        ...state.pendingCredentials,
        totp_code: totpCode,
      });
      setSession(response);
      navigate('/', { replace: true });
    } catch (err) {
      const code = extractAuthErrorCode(err);
      const error =
        code === 'AUTH_2FA_INVALID'
          ? 'Código inválido. Intentá de nuevo.'
          : 'Error inesperado. Intentá de nuevo.';
      setState((s) => ({ ...s, isLoading: false, error }));
    }
  }

  return {
    step: state.step,
    error: state.error,
    isLoading: state.isLoading,
    submitCredentials,
    submit2fa,
  };
}
