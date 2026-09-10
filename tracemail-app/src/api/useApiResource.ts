import { useEffect, useState } from 'react';

export function useApiResource<T>(load: () => Promise<T>, key: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true; setLoading(true); setError(null);
    load().then(value => active && setData(value)).catch(err => active && setError(err.message ?? 'Unable to load investigation data')).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [key]);
  return { data, error, loading, setData };
}
