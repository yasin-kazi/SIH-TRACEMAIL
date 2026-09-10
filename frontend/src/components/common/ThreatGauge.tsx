interface ThreatGaugeProps {
  score: number;
  size?: number;
}

export function ThreatGauge({ score, size = 96 }: ThreatGaugeProps) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? 'text-error' : score >= 50 ? 'text-[#f59e0b]' : 'text-tertiary';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle
          className="fill-none stroke-surface-container-high"
          cx="50" cy="50" r={radius}
          strokeWidth="8"
        />
        <circle
          className={`fill-none ${color} transition-all duration-1000 ease-out`}
          cx="50" cy="50" r={radius}
          stroke="currentColor"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className={`font-headline-lg font-bold tracking-tighter ${color}`}>{score}</span>
        <span className="font-label-caps text-on-surface-variant">THREAT INDEX</span>
      </div>
    </div>
  );
}
