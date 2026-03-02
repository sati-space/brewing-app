interface DataRowProps {
  label: string;
  value: number;
  unit: string;
}

export function DataRow({ label, value, unit }: DataRowProps) {
  return (
    <div className="data-row">
      <span>{label}</span>
      <strong>
        {value} {unit}
      </strong>
    </div>
  );
}
