import { getReportUrl } from '../services/api';

interface ReportButtonProps {
  eventId: string;
}

export default function ReportButton({ eventId }: ReportButtonProps) {
  const handleGenerate = () => {
    const url = getReportUrl(eventId);
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <button className="btn btn--primary" onClick={handleGenerate}>
      📄 Generate Report
    </button>
  );
}
