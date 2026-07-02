interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-4xl mb-4 opacity-30">⚠️</div>
      <h3 className="text-base font-medium mb-1">Something went wrong</h3>
      <p className="text-sm text-red-400 mb-4 max-w-sm">{message}</p>
      {onRetry && (
        <button className="btn-primary" onClick={onRetry}>Retry</button>
      )}
    </div>
  );
}
