import { Link } from "react-router-dom";

interface EmptyStateProps {
  title: string;
  message?: string;
  actionLabel?: string;
  actionTo?: string;
}

export default function EmptyState({ title, message, actionLabel, actionTo }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-4xl mb-4 opacity-30">📭</div>
      <h3 className="text-base font-medium mb-1">{title}</h3>
      {message && <p className="text-sm text-text-muted mb-4 max-w-sm">{message}</p>}
      {actionLabel && actionTo && (
        <Link to={actionTo} className="btn-primary">{actionLabel}</Link>
      )}
    </div>
  );
}
