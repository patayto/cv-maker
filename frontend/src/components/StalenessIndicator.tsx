interface StalenessIndicatorProps {
  daysSinceUpdate: number | null;
  level: 'green' | 'yellow' | 'orange' | 'red' | 'gray';
  contactCount: number;
}

const COLORS = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  orange: 'bg-orange-500',
  red: 'bg-red-500',
  gray: 'bg-gray-400'
};

const LABELS = {
  green: 'Fresh',
  yellow: 'Aging',
  orange: 'Stale',
  red: 'Very Stale',
  gray: 'No activity'
};

export function StalenessIndicator({ daysSinceUpdate, level, contactCount }: StalenessIndicatorProps) {
  const tooltip = daysSinceUpdate !== null
    ? `${daysSinceUpdate} day${daysSinceUpdate !== 1 ? 's' : ''} since update - ${LABELS[level]}`
    : LABELS[level];

  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-3 h-3 rounded-full ${COLORS[level]}`}
        title={tooltip}
      />
      {contactCount > 0 && (
        <span className="text-xs text-gray-500" title={`${contactCount} contact${contactCount !== 1 ? 's' : ''} made`}>
          📧 {contactCount}
        </span>
      )}
    </div>
  );
}
