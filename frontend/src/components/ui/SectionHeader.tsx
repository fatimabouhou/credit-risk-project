import type { ReactNode } from "react";

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  right?: ReactNode;
}

export default function SectionHeader({ title, subtitle, right }: SectionHeaderProps) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">{title}</h2>
        {subtitle && <p className="mt-1.5 text-base text-text-muted">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}
