export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card animate-pulse">
      <div className="h-3 bg-border rounded w-1/3 mb-4" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-2.5 bg-border rounded w-full mb-2 last:w-2/3" />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 4 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2">
      <div className="h-3 bg-border rounded w-1/4 mb-4" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-8 bg-surface2 rounded w-full" />
      ))}
    </div>
  );
}
