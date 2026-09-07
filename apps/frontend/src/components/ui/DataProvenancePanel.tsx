import React from 'react';
import type { ThermoEvent } from '../../services/api';

export interface DataProvenancePanelProps {
  event: ThermoEvent;
}

export const DataProvenancePanel: React.FC<DataProvenancePanelProps> = ({ event }) => {
  const provenanceItems = [
    ['Data source', 'NASA FIRMS'],
    ['Sensor', 'MODIS · VIIRS 375m'],
    ['Model version', event.model_version || (event as any).engine_version || 'v2.1.0'],
    ['Data version', event.data_version || 'FIRMS-2024'],
    ['Imagery', event.satellite_context?.imagery_available ? 'Available' : 'Unavailable'],
    ['Acquisition', event.time_window?.end?.split('T')[0] || '—'],
  ];

  const cloudCover = event.satellite_context?.cloud_cover_pct;

  return (
    <div className="provenance-panel">
      <div className="provenance-panel__title">Data Provenance</div>
      <div className="provenance-grid">
        {provenanceItems.map(([k, v]) => (
          <div key={k} className="provenance-row">
            <span className="provenance-row__key">{k}</span>
            <span className="provenance-row__val">{v}</span>
          </div>
        ))}
      </div>
      {cloudCover !== undefined && cloudCover > 20 && (
        <div className="provenance-warning">
          ⚠ Cloud cover {cloudCover}% — optical imagery may not be available for visual confirmation
        </div>
      )}
    </div>
  );
};

export default DataProvenancePanel;
