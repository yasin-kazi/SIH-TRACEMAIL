import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const MESSAGES: Record<string, { title: string; detail: string; icon: string; tone: string }> = {
  success: { title: 'Gmail connected', detail: 'Your Gmail connection is ready. Return to Cases to browse and analyze messages.', icon: 'check_circle', tone: 'text-primary' },
  denied: { title: 'Access denied', detail: 'Google sign-in was cancelled. No connection was created.', icon: 'cancel', tone: 'text-error' },
  invalid: { title: 'Connection check failed', detail: 'The sign-in link was reused or incomplete. Start the connection again.', icon: 'error', tone: 'text-error' },
  expired: { title: 'Connection link expired', detail: 'The sign-in attempt expired before it was completed. Start again.', icon: 'schedule', tone: 'text-error' },
  error: { title: 'Connection failed', detail: 'Google could not complete the sign-in. Verify the OAuth configuration and try again.', icon: 'error', tone: 'text-error' },
};

export default function ConnectStatus() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const signal = params.get('connect') ?? 'error';
  const message = MESSAGES[signal] ?? MESSAGES.error;

  useEffect(() => {
    const timer = setTimeout(() => navigate('/'), 2500);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="bg-surface-container-lowest rounded-2xl p-space-xl shadow-lg max-w-sm w-full text-center animate-fade-in">
        <div className={`w-12 h-12 mx-auto rounded-full bg-primary/10 flex items-center justify-center mb-4 ${message.tone}`}>
          <span className="material-symbols-outlined text-[28px]">{message.icon}</span>
        </div>
        <h1 className="font-title-sm text-title-sm text-on-surface">{message.title}</h1>
        <p className="font-body-sm text-body-sm text-on-surface-variant mt-2">{message.detail}</p>
        <p className="font-label-mono-sm text-label-mono-sm text-outline mt-4">Returning to Cases…</p>
      </div>
    </div>
  );
}