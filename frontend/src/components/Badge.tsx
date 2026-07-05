import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'info' | 'purple';
  icon?: ReactNode;
  size?: 'sm' | 'md';
}

export function Badge({ children, variant = 'default', icon, size = 'md' }: BadgeProps) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        ${variantClasses[variant]}
        ${sizeClasses[size]}
      `}
    >
      {icon && <span>{icon}</span>}
      {children}
    </span>
  );
}
