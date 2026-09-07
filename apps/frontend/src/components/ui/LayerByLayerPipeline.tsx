import React, { useState } from 'react';

export interface PipelineLayer {
  id: number;
  level: string;
  name: string;
  tagline: string;
  source: string;
  status: string;
  icon: string;
  color: string;
  techStack: string[];
  summary: string;
  inputs: string[];
  processingSteps: string[];
  outputs: string[];
  xaiHook: string;
}

export const PIPELINE_LAYERS: PipelineLayer[] = [
  {
    id: 0,
    level: 'LAYER 0',
    name: 'NASA Spaceborne Earth Observation Telemetry',
    tagline: 'Raw orbital thermal-infrared photon collection from space',
    source: 'NASA EOSDIS / LANCE / Goddard Space Flight Center',
    status: 'ACTIVE DOWNLINK',
    icon: '🛰️',
    color: '#43D9E8',
    techStack: ['MODIS (Terra/Aqua)', 'VIIRS 375m (Suomi-NPP / NOAA-20)', 'NRT L1B/L2 Data'],
    summary: 'Satellites in sun-synchronous polar orbit capture raw radiant thermal emissions using high-gain mid-wave and long-wave infrared spectral bands (4µm and 11µm channels) as they pass over the Earth surface.',
    inputs: [
      'Top-of-Atmosphere (TOA) spectral radiances (W/m²·sr·µm)',
      'MODIS 4 µm (Band 21/22) & 11 µm (Band 31) channel data',
      'VIIRS I4 (3.74 µm) & I5 (11.45 µm) 375m imagery bands',
      'Satellite orbital ephemeris, scan angle & sensor zenith angle'
    ],
    processingSteps: [
      'Brightness temperature calculation via Planck blackbody inversion',
      'Fire Radiative Power (FRP) calculation using the Wooster / Kaufman empirical thermal method',
      'Pixel geolocation mapping to geodetic WGS84 coordinates (latitude/longitude)',
      'Sub-satellite point geometric alignment and timestamp stamping'
    ],
    outputs: [
      'Raw Thermal Detections Table (FRP in MW, Brightness Temp in K)',
      'Scan angle distortion metadata',
      'Observation timestamp (UTC / ISO 8601)'
    ],
    xaiHook: 'FRP (MW) and Brightness Temp (K) serve as fundamental baseline physical inputs for all downstream ML models.'
  },
  {
    id: 1,
    level: 'LAYER 1',
    name: 'Near-Real-Time (NRT) Quality Filtering & Atmospheric Cleaning',
    tagline: 'Removal of solar glint, cloud obscuration, and optical artifacts',
    source: 'NASA FIRMS NRT Ingest Pipeline & ThermoTrace Preprocessor',
    status: 'REAL-TIME FILTERING',
    icon: '⚡',
    color: '#4D8DFF',
    techStack: ['NumPy Vectorized Pipeline', 'Cloud Mask Alg.', 'Solar Glint De-aliasing'],
    summary: 'Eliminates false anomalies caused by reflective water bodies, bright sand, cloud edges, and solar specular reflection to ensure high-fidelity thermal detections.',
    inputs: [
      'Raw NASA FIRMS thermal anomaly feed',
      'MODIS/VIIRS Cloud Mask and Aerosol Optical Depth (AOD) products',
      'Solar azimuth and solar zenith angles'
    ],
    processingSteps: [
      'Solar glint filter: rejects pixels where glint angle < 15° over water/moist surfaces',
      'Cloud mask exclusion: flags pixels with >40% cloud optical thickness as degraded quality',
      'Scan-edge bowtie deletion: removes overlapping edge-of-scan duplicate detections',
      'Detection confidence assignment (nominal / high / low thresholding)'
    ],
    outputs: [
      'Curated, noise-free thermal detection stream',
      'Calibrated confidence scores (0-100%)',
      'Pixel validity mask'
    ],
    xaiHook: 'Filters out noisy outliers that could distort AI feature attribution and cause false positive alerts.'
  },
  {
    id: 2,
    level: 'LAYER 2',
    name: '4D Spatiotemporal Windowing & Persistence Clustering',
    tagline: 'Reconstructing historical thermal signatures over time and space',
    source: 'ThermoTrace Temporal Engine & PostGIS GeoDatabase',
    status: 'TEMPORAL MEMORY ACTIVE',
    icon: '⏱️',
    color: '#A78BFA',
    techStack: ['4D Space-Time DBSCAN', 'Rolling Temporal Windows (7d/30d/90d)', 'Z-Score Anomaly Engine'],
    summary: 'Aggregates individual satellite passes across rolling multi-day time windows to compute persistence ratios, baseline flaring frequency, and detect deviations from normal facility operations.',
    inputs: [
      'Clean thermal detection stream from Layer 1',
      'Historical 90-day archive of regional thermal observations',
      'Diurnal cycle schedule of regional industrial plants'
    ],
    processingSteps: [
      '4D DBSCAN clustering (Δdistance ≤ 1.5 km, Δtime ≤ 72 hours)',
      'Rolling persistence calculation: active detection days / total observation passes',
      'Facility baseline flaring distribution fitting (Gaussian KDE & median MW)',
      'Thermal Z-score surge computation: (Current FRP - Baseline Mean) / Baseline StdDev'
    ],
    outputs: [
      'Persistent thermal cluster tracks',
      'Persistence ratio (0.0 to 1.0)',
      'FRP Z-score and recurrence index',
      'Night-time vs Daytime detection ratio'
    ],
    xaiHook: 'Temporal persistence and Z-score deviations are dominant features in SHAP waterfall explanations.'
  },
  {
    id: 3,
    level: 'LAYER 3',
    name: 'Geospatial Context & Environmental Covariate Fusion',
    tagline: 'Fusing land cover, plant boundaries, and meteorological wind vectors',
    source: 'ESA WorldCover 10m + OSM / ISRO Bhuvan + ECMWF / GFS',
    status: 'FUSED 10M COVARIATES',
    icon: '🌍',
    color: '#4FD18B',
    techStack: ['ESA WorldCover 10m', 'ISRO Bhuvan Industrial Vector Layer', 'ECMWF Wind Vectors'],
    summary: 'Enriches thermal anomalies with high-resolution contextual data: precise industrial facility boundaries, surrounding land cover types, and real-time atmospheric wind velocity.',
    inputs: [
      'Spatiotemporal clusters from Layer 2',
      'ESA WorldCover 10m GeoTIFF raster (Built-up, Forest, Cropland, Water)',
      'OpenStreetMap & ISRO Bhuvan industrial boundary polygons',
      'NOAA GFS & ECMWF atmospheric wind vectors (speed & azimuth)'
    ],
    processingSteps: [
      'Point-in-polygon spatial intersection with industrial plant master registry',
      'Euclidean buffer distance calculation to nearest refinery stack / flare pit (m)',
      '10m Land cover fraction extraction within 500m radius of hotspot center',
      'Downwind smoke/flame plume projection using prevailing wind velocity'
    ],
    outputs: [
      'Facility proximity attribution (e.g. 180m from Jamnagar Stack #4)',
      'Land cover fractions (e.g. 88% Industrial Built-up, 12% Shrubland)',
      'Atmospheric dispersion trajectory vector'
    ],
    xaiHook: 'Allows the XAI engine to rule out agricultural burning when landcover is industrial built-up.'
  },
  {
    id: 4,
    level: 'LAYER 4',
    name: 'Hybrid ML & Explainable AI (XAI) Classification Engine',
    tagline: 'Ensemble model inference with SHAP attribution and counterfactual reasoning',
    source: 'ThermoTrace GeoAI Core (XGBoost + Spatio-Temporal GNN)',
    status: 'INFERENCE & XAI LIVE',
    icon: '🤖',
    color: '#FFB547',
    techStack: ['XGBoost / LightGBM Ensemble', 'SHAP (TreeExplainer)', 'Calibrated Uncertainty'],
    summary: 'Classifies the exact nature of the thermal event with calibrated confidence and generates human-readable XAI feature importance breakdowns for regulatory scrutiny.',
    inputs: [
      '24 engineered features across thermal, temporal, landcover, and industrial dimensions',
      'Historical ground-truth verification dataset'
    ],
    processingSteps: [
      'Multimodal ensemble classification into 5 discrete taxonomy classes',
      'SHAP (SHapley Additive exPlanations) values computed for each feature',
      'Counterfactual engine computes boundary perturbation necessary to alter prediction',
      'Calibrated uncertainty estimation (Confirmed / Probable / Requires Verification)'
    ],
    outputs: [
      'Classification Label (e.g., Persistent Industrial Flaring Surge)',
      'Classification Confidence Score (e.g., 94.2%)',
      'SHAP Feature Importance Waterfall breakdown',
      'Plain-language analyst reason codes'
    ],
    xaiHook: 'Every prediction is backed by mathematical SHAP weights, counterfactual bounds, and evidence cards.'
  },
  {
    id: 5,
    level: 'LAYER 5',
    name: 'Sector Allocation & Blast Radius Hazard Zoning',
    tagline: 'Mapping risk directly into critical infrastructure sectors and safety perimeters',
    source: 'API 521 Radiant Heat Model & Sector Risk Matrix',
    status: 'SECTOR ZONES MAPPED',
    icon: '🏭',
    color: '#FF7A45',
    techStack: ['API Standard 521 Point Source Model', 'Multi-Sector Risk Engine', 'Hazard Contours'],
    summary: 'Maps the classified thermal event into its designated economic and safety sector, computing the 4.7 kW/m² radiant heat hazard zone and overall operational threat tier.',
    inputs: [
      'XAI Classified Event from Layer 4',
      'Facility sector type (Petroleum Refinery, Petrochemical, Steel, Power, Wildland)',
      'FRP (MW) and ambient atmospheric transmittance'
    ],
    processingSteps: [
      'Radiant heat flux modeling: $R = \\sqrt{(FRP \\cdot \\eta \\cdot \\tau) / (4\\pi \\cdot q)}$ for threshold $q = 4.7 \\text{ kW/m}^2$',
      'Composite Operational Risk Score ($0-100$) synthesis: $S = 0.40 \\cdot R_{FRP} + 0.35 \\cdot R_{Persist} + 0.25 \\cdot R_{Proximity}$',
      'Threat Tier assignment: CRITICAL (≥75), HIGH (50-74), MODERATE (25-49), LOW (<25)',
      'Sector-specific Standard Operating Procedure (SOP) mapping'
    ],
    outputs: [
      'Identified Sector (e.g., Petroleum & Hydrocarbon Refining)',
      'Hazard Radius Boundary (e.g., 240 m radius contour)',
      'Operational Risk Score (e.g., 84/100 · CRITICAL Tier)',
      'Targeted Emergency Directive (e.g., Divert Flare Gas Recovery System)'
    ],
    xaiHook: 'Explains exactly why a sector alert is elevated based on proximity to combustible infrastructure.'
  },
  {
    id: 6,
    level: 'LAYER 6',
    name: 'Automated Stakeholder Dispatch & Incident Escalation',
    tagline: 'Real-time multi-channel alerts pushed to verified emails and mobile phones',
    source: 'ThermoTrace Emergency Gateway (SMTP / SMS / WhatsApp / Webhook)',
    status: 'DISPATCH READY',
    icon: '📢',
    color: '#FF5C6C',
    techStack: ['Real SMTP Push to Phone (Gmail/Outlook)', 'Fast2SMS Indian Gateway', 'Twilio Carrier Handshake'],
    summary: 'Instantly alerts designated safety officers, plant managers, and regulatory officials (CPCB/ISRO) with structured incident briefings and emergency directives.',
    inputs: [
      'Sector Risk & Threat Tier from Layer 5',
      'Pre-configured stakeholder registry (Primary: rijja2310119@ssn.edu.in)',
      'Event telemetry snapshot and SOP protocol guide'
    ],
    processingSteps: [
      'Dynamic HTML incident brief synthesis with interactive telemetry links',
      'DLT-compliant high-priority SMS formatting (Sender ID: VM-THRMTR)',
      'Multi-channel dispatch execution (Email, SMS, and WhatsApp alerts)',
      'Immutable security audit logging of carrier delivery handshake receipts'
    ],
    outputs: [
      'Direct email notification sent to rijja2310119@ssn.edu.in',
      'SMS text delivered to emergency coordinator mobile phone',
      'Verified delivery receipt and audit trail record'
    ],
    xaiHook: 'Alert notifications contain the full XAI summary so operators understand why the alarm was triggered.'
  }
];

export const LayerByLayerPipeline: React.FC<{
  activeLayerId?: number;
  onSelectLayer?: (id: number) => void;
  compact?: boolean;
}> = ({ activeLayerId = 0, onSelectLayer, compact = false }) => {
  const [selectedId, setSelectedId] = useState<number>(activeLayerId);

  const currentLayer = PIPELINE_LAYERS.find(l => l.id === selectedId) || PIPELINE_LAYERS[0];

  const handleSelect = (id: number) => {
    setSelectedId(id);
    if (onSelectLayer) onSelectLayer(id);
  };

  return (
    <div className="layer-pipeline-container" style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: compact ? '16px' : '24px',
      overflow: 'hidden'
    }}>
      {/* Header Banner */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: '700',
              color: 'var(--accent-cyan)',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <span>🛰️</span> END-TO-END DATA ARCHITECTURE
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', margin: '4px 0' }}>
              How Raw NASA Satellite Telemetry Flows Layer-by-Layer Into Ground Sectors
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
              ThermoTrace does not jump directly to sectors — raw orbital infrared radiances undergo rigorous multi-tier cleaning, clustering, covariate fusion, and XAI inference.
            </p>
          </div>
          <div style={{
            padding: '6px 12px',
            borderRadius: 'var(--radius-xs)',
            background: 'rgba(67, 217, 232, 0.1)',
            border: '1px solid rgba(67, 217, 232, 0.3)',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--accent-cyan)'
          }}>
            7 PROCESSING LAYERS ACTIVE
          </div>
        </div>
      </div>

      {/* Interactive Layer Pipeline Stepper Tabs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '8px',
        marginBottom: '20px'
      }}>
        {PIPELINE_LAYERS.map(layer => {
          const isSelected = layer.id === selectedId;
          return (
            <button
              key={layer.id}
              onClick={() => handleSelect(layer.id)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                background: isSelected ? 'rgba(67, 217, 232, 0.12)' : 'var(--bg-primary)',
                border: isSelected ? `2px solid ${layer.color}` : '1px solid var(--border-subtle)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s ease',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', marginBottom: '4px' }}>
                <span style={{ fontSize: '16px' }}>{layer.icon}</span>
                <span style={{
                  fontSize: '9px',
                  fontWeight: '800',
                  color: layer.color,
                  letterSpacing: '0.5px'
                }}>
                  {layer.level}
                </span>
              </div>
              <div style={{
                fontSize: '11px',
                fontWeight: '700',
                color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                lineHeight: '1.3',
                marginBottom: '2px'
              }}>
                {layer.name.split(' ')[0]} {layer.name.split(' ')[1]}
              </div>
              <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                {layer.status}
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Layer Deep-Dive Card */}
      <div style={{
        background: 'var(--bg-primary)',
        border: `1px solid ${currentLayer.color}40`,
        borderLeft: `4px solid ${currentLayer.color}`,
        borderRadius: 'var(--radius-sm)',
        padding: '20px',
        position: 'relative'
      }}>
        {/* Layer Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{
                padding: '3px 8px',
                borderRadius: '4px',
                background: `${currentLayer.color}20`,
                color: currentLayer.color,
                fontSize: '10px',
                fontWeight: '800',
                letterSpacing: '0.5px'
              }}>
                {currentLayer.level}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Source: <strong>{currentLayer.source}</strong>
              </span>
            </div>
            <h4 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
              {currentLayer.icon} {currentLayer.name}
            </h4>
            <div style={{ fontSize: '12px', color: currentLayer.color, marginTop: '2px', fontWeight: '500' }}>
              {currentLayer.tagline}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {currentLayer.techStack.map((tech, i) => (
              <span key={i} style={{
                padding: '4px 8px',
                borderRadius: '4px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-secondary)'
              }}>
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Narrative Description */}
        <div style={{
          fontSize: '13px',
          color: 'var(--text-secondary)',
          lineHeight: '1.7',
          marginBottom: '16px',
          padding: '12px',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-xs)'
        }}>
          {currentLayer.summary}
        </div>

        {/* 3-Column Pipeline Grid: Inputs | Processing Transformations | Outputs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '14px',
          marginBottom: '16px'
        }}>
          {/* Inputs */}
          <div style={{
            padding: '12px',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-xs)',
            borderTop: '2px solid var(--accent-cyan)'
          }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--accent-cyan)', marginBottom: '8px', textTransform: 'uppercase' }}>
              📥 Layer Ingestion Inputs:
            </div>
            <ul style={{ paddingLeft: '16px', margin: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {currentLayer.inputs.map((inp, idx) => (
                <li key={idx} style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  {inp}
                </li>
              ))}
            </ul>
          </div>

          {/* Processing Transformations */}
          <div style={{
            padding: '12px',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-xs)',
            borderTop: `2px solid ${currentLayer.color}`
          }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: currentLayer.color, marginBottom: '8px', textTransform: 'uppercase' }}>
              ⚙️ Algorithmic Operations:
            </div>
            <ul style={{ paddingLeft: '16px', margin: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {currentLayer.processingSteps.map((step, idx) => (
                <li key={idx} style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  {step}
                </li>
              ))}
            </ul>
          </div>

          {/* Outputs */}
          <div style={{
            padding: '12px',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-xs)',
            borderTop: '2px solid var(--accent-green)'
          }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--accent-green)', marginBottom: '8px', textTransform: 'uppercase' }}>
              📤 Downstream Deliverables:
            </div>
            <ul style={{ paddingLeft: '16px', margin: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {currentLayer.outputs.map((out, idx) => (
                <li key={idx} style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  {out}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Explainable AI & Transparency Hook */}
        <div style={{
          padding: '10px 14px',
          background: 'rgba(67, 217, 232, 0.06)',
          border: '1px solid rgba(67, 217, 232, 0.2)',
          borderRadius: 'var(--radius-xs)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '16px' }}>💡</span>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>Explainable AI (XAI) Relevance:</strong> {currentLayer.xaiHook}
          </div>
        </div>

        {/* Navigation Step Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
          <button
            className="btn btn--outline btn--sm"
            disabled={selectedId === 0}
            onClick={() => handleSelect(selectedId - 1)}
          >
            ← Previous Layer
          </button>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', alignSelf: 'center' }}>
            Step {selectedId + 1} of {PIPELINE_LAYERS.length}
          </div>
          <button
            className="btn btn--cyan btn--sm"
            disabled={selectedId === PIPELINE_LAYERS.length - 1}
            onClick={() => handleSelect(selectedId + 1)}
          >
            Next Processing Layer →
          </button>
        </div>
      </div>
    </div>
  );
};

export default LayerByLayerPipeline;
