export function generateDemoSha256(): string {
  const chars = '0123456789abcdef';
  let hash = '';
  for (let i = 0; i < 64; i++) {
    hash += chars[Math.floor(Math.random() * chars.length)];
  }
  return hash;
}

export function truncateHash(hash: string, length: number = 16): string {
  if (hash.length <= length) return hash;
  return hash.slice(0, length) + '...';
}

export function formatTimestamp(date: Date = new Date()): string {
  return date.toISOString().replace('T', ' ').slice(0, 23) + 'Z';
}

export function generateNonce(): string {
  return Math.floor(Math.random() * 999999).toString();
}
