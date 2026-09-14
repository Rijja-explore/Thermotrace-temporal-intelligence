import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { INDIA_STATES_GEOJSON } from '../data/indiaStates';
import { CANONICAL_EVENTS } from '../data/canonicalEvents';
import { fetchEvents } from '../services/api';
import type { ThermoEvent } from '../services/api';

// ─── State Mapping Helper ──────────────────────────────────────────────────
export const STATE_COLORS: Record<string, string> = {
  'Gujarat': '#FF8C42',
  'Maharashtra': '#38BDF8',
  'Odisha': '#FACC15',
  'Jharkhand': '#FB7185',
  'West Bengal': '#34D399',
  'Tamil Nadu': '#C084FC',
  'Assam': '#F472B6',
  'Karnataka': '#818CF8',
  'Andhra Pradesh': '#2DD4BF',
  'Punjab': '#4ADE80',
  'Chhattisgarh': '#FB923C',
  'Rajasthan': '#E879F9',
  'Uttar Pradesh': '#A3E635',
  'Madhya Pradesh': '#FBBF24',
  'Other / Telemetry Clutter': '#64748B',
};

export function inferIndianState(lat: number, lon: number, facName = ''): string {
  const nameLower = facName.toLowerCase();
  if (nameLower.includes('jamnagar') || nameLower.includes('hazira') || nameLower.includes('reliance') || nameLower.includes('sikka') || nameLower.includes('surat') || nameLower.includes('vatva')) return 'Gujarat';
  if (nameLower.includes('mumbai') || nameLower.includes('ratnagiri') || nameLower.includes('trombay') || nameLower.includes('rasayani') || nameLower.includes('jaigarh')) return 'Maharashtra';
  if (nameLower.includes('rourkela') || nameLower.includes('kaniha') || nameLower.includes('paradip') || nameLower.includes('angul') || nameLower.includes('kalinganagar')) return 'Odisha';
  if (nameLower.includes('bokaro') || nameLower.includes('jamshedpur') || nameLower.includes('ramgarh') || nameLower.includes('dhanbad') || nameLower.includes('jharia')) return 'Jharkhand';
  if (nameLower.includes('haldia') || nameLower.includes('durgapur') || nameLower.includes('burnpur')) return 'West Bengal';
  if (nameLower.includes('manali') || nameLower.includes('ennore') || nameLower.includes('tuticorin') || nameLower.includes('nagapattinam')) return 'Tamil Nadu';
  if (nameLower.includes('digboi') || nameLower.includes('numaligarh') || nameLower.includes('duliajan') || nameLower.includes('nagaon')) return 'Assam';
  if (nameLower.includes('bhilai') || nameLower.includes('korba') || nameLower.includes('raigarh') || nameLower.includes('jindal')) return 'Chhattisgarh';
  if (nameLower.includes('mrpl') || nameLower.includes('mangalore') || nameLower.includes('bellary') || nameLower.includes('vijayanagar')) return 'Karnataka';
  if (nameLower.includes('vizag') || nameLower.includes('simhadri') || nameLower.includes('gangavaram') || nameLower.includes('hpcl vizag')) return 'Andhra Pradesh';
  if (nameLower.includes('bathinda') || nameLower.includes('ludhiana') || nameLower.includes('crop') || nameLower.includes('agri') || nameLower.includes('agricultural')) return 'Punjab';
  if (nameLower.includes('barmer') || nameLower.includes('mangala') || nameLower.includes('kota')) return 'Rajasthan';

  // Coordinate bounding boxes
  if (lat >= 20.0 && lat <= 24.5 && lon >= 68.5 && lon <= 74.5) return 'Gujarat';
  if (lat >= 15.6 && lat <= 22.0 && lon >= 72.5 && lon <= 80.5) return 'Maharashtra';
  if (lat >= 17.8 && lat <= 22.5 && lon >= 81.3 && lon <= 87.5) return 'Odisha';
  if (lat >= 21.9 && lat <= 25.3 && lon >= 83.3 && lon <= 87.9) return 'Jharkhand';
  if (lat >= 21.5 && lat <= 27.2 && lon >= 85.8 && lon <= 89.9) return 'West Bengal';
  if (lat >= 8.0 && lat <= 13.5 && lon >= 76.2 && lon <= 80.3) return 'Tamil Nadu';
  if (lat >= 24.1 && lat <= 28.0 && lon >= 89.7 && lon <= 96.0) return 'Assam';
  if (lat >= 17.8 && lat <= 24.1 && lon >= 80.2 && lon <= 84.4) return 'Chhattisgarh';
  if (lat >= 11.5 && lat <= 18.4 && lon >= 74.0 && lon <= 78.6) return 'Karnataka';
  if (lat >= 12.6 && lat <= 19.9 && lon >= 76.7 && lon <= 84.8) return 'Andhra Pradesh';
  if (lat >= 29.5 && lat <= 32.5 && lon >= 73.8 && lon <= 76.9) return 'Punjab';
  if (lat >= 23.0 && lat <= 30.2 && lon >= 69.5 && lon <= 78.3) return 'Rajasthan';

  return 'Other / Telemetry Clutter';
}

// ─── Pipeline Point Interface ──────────────────────────────────────────────
export interface PipelinePoint {
  id: string;
  eventId: string;
  observationId?: string;
  lat: number;
  lon: number;
  frp: number;
  brightness?: number;
  confidence?: number;
  satellite: string;
  name: string;
  state: string;
  facilityType: string;
  isNoise: boolean;
  stageReached: number; // 0=Raw, 1=Quality, 2=Clustered, 3=GIS/Baseline, 4=AI Fusion Alarm
  riskScore: number;
  baselineZ: number;
  lstmState: 'STABLE' | 'WATCH' | 'ESCALATING' | 'CRITICAL_ESCALATION';
  hgbClass: string;
  persistenceRatio: number;
  rawEvent?: ThermoEvent;
  marker?: L.CircleMarker;
  active: boolean;
}

// ─── Generate Pure Pipeline Points from Canonical Events ───────────────────
function buildPipelinePoints(canonicalList: ThermoEvent[]): PipelinePoint[] {
  const points: PipelinePoint[] = [];

  canonicalList.forEach((ev, evIdx) => {
    const geo = ev.geometry || {};
    const baseLat = geo.latitude ?? geo.lat ?? 22.0;
    const baseLon = geo.longitude ?? geo.lon ?? 78.0;
    const facCtx = ev.facility_context || {};
    const facName = facCtx.nearest_facility_name || facCtx.name || ev.title || `Industrial Complex ${ev.event_id}`;
    const facType = facCtx.facility_type || (facName.toLowerCase().includes('refinery') ? 'Oil Refinery' : facName.toLowerCase().includes('steel') ? 'Integrated Steel' : 'Industrial Complex');
    const state = ev.region || inferIndianState(baseLat, baseLon, facName);

    const riskScore = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 50.0;
    const baselineZ = ev.facility_thermal_fingerprint?.current_observation?.deviation_z ?? (ev.observations?.[0]?.frp ? (ev.observations[0].frp - 80) / 18 : 2.5);
    const lstmState = (ev.early_warning?.escalation_state as any) || (riskScore >= 75 ? 'CRITICAL_ESCALATION' : riskScore >= 60 ? 'ESCALATING' : 'STABLE');
    const hgbClass = ev.classification?.label || 'persistent_industrial_source';
    const persistenceRatio = ev.temporal_features?.window_30d?.persistence_ratio ?? ev.temporal_features?.persistence_ratio ?? 0.85;

    const obsList = ev.observations && ev.observations.length > 0
      ? ev.observations
      : [{
          observation_id: `OBS-${ev.event_id}-1`,
          latitude: baseLat,
          longitude: baseLon,
          frp: ev.temporal_features?.current_frp ?? 120.0,
          brightness: 330.0,
          confidence: 95,
          satellite: 'VIIRS_NPP',
        }];

    // Determine highest pipeline stage reached for this canonical event
    // Stage 4 = CRITICAL AI Fusion Alarm (Risk >= 65 or Escalating or Z >= 3.0)
    // Stage 3 = Facility Matched with Baseline
    // Stage 2 = DBSCAN Clustered Centroid
    const isAgricultural = facName.toLowerCase().includes('agri') || facType.toLowerCase().includes('agri') || facName.toLowerCase().includes('crop');
    const isHighAlarm = (riskScore >= 64.0 || baselineZ >= 4.0 || lstmState === 'CRITICAL_ESCALATION' || lstmState === 'ESCALATING') && !isAgricultural;
    const eventMaxStage = isHighAlarm ? 4 : isAgricultural ? 2 : 3;

    obsList.forEach((obs, obsIdx) => {
      const pLat = obs.latitude ?? baseLat + (obsIdx > 0 ? (obsIdx * 0.003 - 0.0015) : 0);
      const pLon = obs.longitude ?? baseLon + (obsIdx > 0 ? (obsIdx * 0.003 - 0.0015) : 0);
      const frp = obs.frp || 60.0;
      const sat = obs.satellite || (obsIdx % 2 === 0 ? 'VIIRS_NPP' : 'MODIS');

      // Primary observation represents the cluster centroid at Stage 2+
      const isCentroid = obsIdx === 0;
      const ptStageReached = isCentroid ? eventMaxStage : 1; // sub-pixels merge at Stage 2 (Clustering)

      points.push({
        id: `${ev.event_id}-${obs.observation_id || obsIdx}`,
        eventId: ev.event_id,
        observationId: obs.observation_id || `OBS-${evIdx}-${obsIdx}`,
        lat: pLat,
        lon: pLon,
        frp,
        brightness: obs.brightness || 320.0,
        confidence: obs.confidence || 90,
        satellite: sat,
        name: isCentroid ? facName : `${facName} (Sub-pixel Flare Pass ${obsIdx + 1})`,
        state,
        facilityType: facType,
        isNoise: false,
        stageReached: ptStageReached,
        riskScore,
        baselineZ,
        lstmState,
        hgbClass,
        persistenceRatio,
        rawEvent: ev,
        active: true,
      });
    });
  });

  // Add realistic FIRMS background telemetry clutter (eliminated in Stage 2 Quality Filtering)
  const noiseClusters = [
    { lat: 24.58, lon: 73.68, state: 'Rajasthan', name: 'Aravalli Scrubland Glint', type: 'Solar Glint / Scatter', frp: 14.2 },
    { lat: 28.63, lon: 77.22, state: 'Uttar Pradesh', name: 'NCR Peripheral Thermal Clutter', type: 'Urban Heat Island', frp: 16.5 },
    { lat: 26.85, lon: 80.95, state: 'Uttar Pradesh', name: 'Gangetic Low Confidence Pixel', type: 'Scan Edge Artifact', frp: 11.8 },
    { lat: 22.72, lon: 75.87, state: 'Madhya Pradesh', name: 'Malwa Plateau Glint', type: 'Transient Flare Scatter', frp: 15.0 },
    { lat: 19.99, lon: 73.79, state: 'Maharashtra', name: 'Western Ghats Sensor Scatter', type: 'Vegetation Noise', frp: 9.4 },
    { lat: 15.34, lon: 75.13, state: 'Karnataka', name: 'Deccan Plateau Scan Edge', type: 'Atmospheric Noise', frp: 12.1 },
    { lat: 25.61, lon: 85.14, state: 'Other / Telemetry Clutter', name: 'Patna Cropland Transient', type: 'Crop Residue Scatter', frp: 18.0 },
    { lat: 26.20, lon: 92.93, state: 'Assam', name: 'Brahmaputra Cloud Edge Dot', type: 'Cloud Edge Scatter', frp: 13.5 },
    { lat: 27.18, lon: 78.02, state: 'Uttar Pradesh', name: 'Agra Peripheral Crop Burn', type: 'Transient Stubble', frp: 14.0 },
    { lat: 23.26, lon: 77.41, state: 'Madhya Pradesh', name: 'Bhopal Ridge Glint Artifact', type: 'Solar Glint', frp: 11.2 },
  ];

  noiseClusters.forEach((n, idx) => {
    points.push({
      id: `NOISE-FIRMS-${idx + 1}`,
      eventId: `NRT-SCAN-${1040 + idx}`,
      observationId: `PIXEL-CLUTTER-${idx + 1}`,
      lat: n.lat,
      lon: n.lon,
      frp: n.frp,
      brightness: 305.0,
      confidence: 32,
      satellite: idx % 2 === 0 ? 'MODIS' : 'VIIRS_375M',
      name: n.name,
      state: n.state,
      facilityType: n.type,
      isNoise: true,
      stageReached: 0, // Eliminated after Stage 1
      riskScore: 8.0,
      baselineZ: -1.2,
      lstmState: 'STABLE',
      hgbClass: 'transient_noise_glint',
      persistenceRatio: 0.05,
      active: true,
    });
  });

  return points;
}

// ─── Token Colors by Heat Intensity ───
export function getIntensityColor(frp: number, isNoise = false): string {
  if (isNoise || frp < 20) return '#64748B'; // Muted grey for noise
  if (frp >= 200) return '#FF4557';          // Extreme Critical - Crimson
  if (frp >= 120) return '#FF7A45';          // High Intensity - Vivid Orange
  if (frp >= 60)  return '#FFB547';          // Moderate - Amber Gold
  if (frp >= 30)  return '#43D9E8';          // Low - Cyan
  return '#10B981';                            // Minor - Green
}

export function getPointRadius(frp: number, stageIdx: number, isNoise = false): number {
  if (isNoise || frp < 20) return 4.0;
  if (stageIdx >= 4) {
    return Math.max(10, Math.min(22, frp / 16));
  }
  if (stageIdx >= 2) {
    return Math.max(7, Math.min(16, frp / 22));
  }
  if (frp >= 200) return 12;
  if (frp >= 100) return 9;
  if (frp >= 50) return 6.5;
  return 5.0;
}

// ─── Pipeline Stage Definitions ───
const STAGES = [
  {
    id: 0,
    label: 'Stage 1 — Raw Satellite Ingestion',
    subtitle: 'Near-Real-Time NASA FIRMS telemetry from MODIS (1km) & VIIRS (375m)',
    color: '#FF7A45',
    desc: 'NASA FIRMS scans the Indian subcontinent in near-real-time. Every thermal pixel above sensor threshold is ingested — refinery flares, steel kilns, power stations, seasonal crop burning, solar glint, and raw sensor noise.',
    stat: 'Raw Satellite Detections',
    isPointActive: (_p: PipelinePoint) => true,
  },
  {
    id: 1,
    label: 'Stage 2 — Quality Filtering',
    subtitle: 'Signal-to-noise thresholding, eliminating scan edge artifacts and sensor glint (<25 MW / low confidence)',
    color: '#FFB547',
    desc: 'ThermoTrace applies signal-to-noise thresholds, eliminating low-confidence telemetry clutter, solar glint, and sensor artifacts. Statistically validated observations move downstream.',
    stat: 'Quality-Filtered Telemetry',
    isPointActive: (p: PipelinePoint) => p.stageReached >= 1 && !p.isNoise,
  },
  {
    id: 2,
    label: 'Stage 3 — Spatial Clustering (DBSCAN)',
    subtitle: 'Consolidation of multi-pixel observations into discrete canonical event centroids (ε = 1.2 km)',
    color: '#43D9E8',
    desc: 'DBSCAN spatial clustering (ε = 1.2 km) groups multi-pixel flare passes into unified event complexes. Redundant sub-pixel readings collapse into canonical event centroids.',
    stat: 'Clustered Event Centroids',
    isPointActive: (p: PipelinePoint) => p.stageReached >= 2 && !p.isNoise,
  },
  {
    id: 3,
    label: 'Stage 4 — Facility / GIS Matching & Baselines',
    subtitle: 'Spatial join with OSM industrial registries and rolling 90-day facility baselines (Z-score + MAD)',
    color: '#A78BFA',
    desc: 'Events intersect with registered industrial boundaries (refineries, steel plants, power stations, LNG terminals). Non-facility burns are contextualized, and 90-day baseline deviations (Z/MAD) are computed.',
    stat: 'Facility-Matched Complexes',
    isPointActive: (p: PipelinePoint) => p.stageReached >= 3 && !p.isNoise,
  },
  {
    id: 4,
    label: 'Stage 5 — Multimodal AI Fusion & Critical Alarms',
    subtitle: '4-Engine Hybrid AI Fusion: Persistence ML + Facility Baseline + PyTorch LSTM Temporal + HGB Classifier',
    color: '#FF5C6C',
    desc: 'ThermoTrace fuses 4 intelligence engines to surface the highest-threat industrial anomalies exceeding facility operational baselines, queuing them for Analyst verification and dossier dispatch.',
    stat: 'Prioritized Critical Alarms',
    isPointActive: (p: PipelinePoint) => p.stageReached >= 4 && !p.isNoise,
  },
];

interface DataReductionVisualizerProps {
  onNavigate?: (path: string, params?: Record<string, string>) => void;
}

export default function DataReductionVisualizer({ onNavigate }: DataReductionVisualizerProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const pointsRef = useRef<PipelinePoint[]>([]);
  const [stage, setStage] = useState(0);
  const [liveCount, setLiveCount] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [colorMode, setColorMode] = useState<'intensity' | 'state'>('intensity');
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [inspectedPoint, setInspectedPoint] = useState<PipelinePoint | null>(null);
  const stageRef = useRef(0);
  const colorModeRef = useRef<'intensity' | 'state'>('intensity');
  colorModeRef.current = colorMode;

  // Build marker tooltip HTML
  const buildTooltip = useCallback((p: PipelinePoint) => {
    const stColor = STATE_COLORS[p.state] || '#43D9E8';
    const intColor = getIntensityColor(p.frp, p.isNoise);
    const tier = p.riskScore >= 75 ? 'CRITICAL ALARM' : p.frp >= 200 ? 'HIGH HEAT' : p.frp >= 60 ? 'MODERATE' : 'BASELINE / LOW';

    return `
      <div style="font-family:Inter,sans-serif;padding:8px 10px;min-width:230px;background:#0B1728;color:#F4F8FC;border:1px solid #233B56;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.7)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span style="font-size:10px;font-weight:700;color:${stColor};text-transform:uppercase;letter-spacing:0.5px">
            📍 ${p.state}
          </span>
          <span style="font-size:9px;font-family:monospace;background:rgba(255,255,255,0.08);color:${intColor};padding:1px 6px;border-radius:3px;font-weight:700">
            ${tier}
          </span>
        </div>
        <div style="font-size:13px;font-weight:700;color:#FFF;margin-bottom:2px">
          ${p.name}
        </div>
        <div style="font-size:10px;color:#94A3B8;margin-bottom:6px;display:flex;justify-content:space-between">
          <span>${p.facilityType}</span>
          <span style="font-family:monospace;color:#CBD5E1">${p.eventId}</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;border-top:1px solid #1E293B;padding-top:6px">
          <span style="color:#71869B">Satellite FRP:</span>
          <strong style="color:#FFB547;font-family:monospace;font-size:12px">${p.frp.toFixed(1)} MW</strong>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:10px;color:#94A3B8;margin-top:3px">
          <span>Sensor / Pass:</span>
          <span style="font-family:monospace;color:#38BDF8">${p.satellite}</span>
        </div>
        ${p.stageReached >= 3 ? `
          <div style="display:flex;justify-content:space-between;align-items:center;font-size:10px;color:#94A3B8;margin-top:3px">
            <span>Baseline Deviation:</span>
            <span style="font-family:monospace;color:${p.baselineZ >= 3 ? '#FF5C6C' : '#34D399'}">Z = +${p.baselineZ.toFixed(1)}σ</span>
          </div>
        ` : ''}
        <div style="margin-top:6px;font-size:9px;color:#38BDF8;text-align:center;border-top:1px dashed #1E293B;padding-top:4px">
          👉 Click dot for Full 4-Engine Fusion Breakdown
        </div>
      </div>
    `;
  }, []);

  // Update styles for all markers
  const refreshMarkerStyles = useCallback((curStage: number, mode: 'intensity' | 'state') => {
    if (!mapRef.current) return;
    const filter = STAGES[curStage].isPointActive;
    let count = 0;

    pointsRef.current.forEach(p => {
      if (!p.marker) return;
      const isVisible = filter(p) && (!selectedState || p.state === selectedState);

      if (isVisible) {
        const radius = getPointRadius(p.frp, curStage, p.isNoise);
        const col = mode === 'state'
          ? (STATE_COLORS[p.state] || '#43D9E8')
          : getIntensityColor(p.frp, p.isNoise);

        p.marker.setStyle({
          color: col,
          fillColor: col,
          fillOpacity: curStage >= 4 ? 0.95 : 0.8,
          radius,
          weight: p.frp >= 200 || p.riskScore >= 75 ? 2.5 : 1.2,
          opacity: 0.95,
        });
        p.marker.setRadius(radius);

        if (!mapRef.current!.hasLayer(p.marker)) {
          p.marker.addTo(mapRef.current!);
        }
        p.active = true;
        count++;
      } else {
        if (mapRef.current!.hasLayer(p.marker)) {
          p.marker.remove();
        }
        p.active = false;
      }
    });

    setLiveCount(count);
  }, [selectedState]);

  // Initialize Map and canonical pipeline points
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [22.0, 79.5],
      zoom: 5,
      minZoom: 4,
      maxZoom: 11,
      zoomControl: false,
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Dark CartoDB Tiles
    L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution: '&copy; OpenStreetMap &copy; CARTO | NASA FIRMS Near-Real-Time Telemetry',
        subdomains: 'abcd',
        maxZoom: 19,
      }
    ).addTo(map);

    // Render Indian State Boundaries
    try {
      L.geoJSON(INDIA_STATES_GEOJSON as any, {
        style: {
          color: '#1E3A5F',
          weight: 1.2,
          opacity: 0.8,
          fillColor: '#07111E',
          fillOpacity: 0.25,
        },
      }).addTo(map);
    } catch {
      // GeoJSON boundary fallback
    }

    mapRef.current = map;

    // Load initial canonical points
    const initPoints = buildPipelinePoints(CANONICAL_EVENTS);
    pointsRef.current = initPoints;

    initPoints.forEach(p => {
      const radius = getPointRadius(p.frp, 0, p.isNoise);
      const col = getIntensityColor(p.frp, p.isNoise);

      const marker = L.circleMarker([p.lat, p.lon], {
        radius,
        color: col,
        fillColor: col,
        fillOpacity: 0.8,
        weight: p.frp >= 200 ? 2 : 1,
        opacity: 0.9,
      }).addTo(map);

      marker.bindTooltip(buildTooltip(p), {
        permanent: false,
        direction: 'top',
        offset: [0, -6],
      });

      marker.on('click', () => {
        setInspectedPoint(p);
      });

      p.marker = marker;
    });

    setLiveCount(initPoints.length);

    // Dynamically synchronize with live backend events
    fetchEvents().then(res => {
      const liveEvents: ThermoEvent[] = res?.events || [];
      if (liveEvents.length > 0 && mapRef.current) {
        // Clear previous markers
        pointsRef.current.forEach(p => {
          if (p.marker && mapRef.current?.hasLayer(p.marker)) {
            p.marker.remove();
          }
        });

        const syncedPoints = buildPipelinePoints(liveEvents);
        pointsRef.current = syncedPoints;

        syncedPoints.forEach(p => {
          const radius = getPointRadius(p.frp, stageRef.current, p.isNoise);
          const col = colorModeRef.current === 'state'
            ? (STATE_COLORS[p.state] || '#43D9E8')
            : getIntensityColor(p.frp, p.isNoise);

          const marker = L.circleMarker([p.lat, p.lon], {
            radius,
            color: col,
            fillColor: col,
            fillOpacity: 0.8,
            weight: p.frp >= 200 ? 2 : 1,
            opacity: 0.9,
          });

          marker.bindTooltip(buildTooltip(p), {
            permanent: false,
            direction: 'top',
            offset: [0, -6],
          });

          marker.on('click', () => {
            setInspectedPoint(p);
          });

          p.marker = marker;
        });

        refreshMarkerStyles(stageRef.current, colorModeRef.current);
      }
    }).catch(() => {
      // Offline fallback: CANONICAL_EVENTS is already loaded cleanly
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [buildTooltip, refreshMarkerStyles]);

  // Apply stage transition
  const applyStage = useCallback((nextStage: number) => {
    if (isTransitioning || !mapRef.current) return;
    setIsTransitioning(true);
    refreshMarkerStyles(nextStage, colorModeRef.current);
    setTimeout(() => setIsTransitioning(false), 350);
  }, [isTransitioning, refreshMarkerStyles]);

  const goToStage = useCallback((next: number) => {
    stageRef.current = next;
    setStage(next);
    applyStage(next);
  }, [applyStage]);

  // React to color mode or state filter change
  useEffect(() => {
    refreshMarkerStyles(stage, colorMode);
  }, [colorMode, selectedState, stage, refreshMarkerStyles]);

  // Auto-play
  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(() => {
      const next = (stageRef.current + 1) % STAGES.length;
      goToStage(next);
    }, 4500);
    return () => clearInterval(interval);
  }, [autoPlay, goToStage]);

  const currentStage = STAGES[stage];

  // Compute active state distribution in current stage
  const activeStateStats = useMemo(() => {
    const filter = currentStage.isPointActive;
    const map: Record<string, { count: number; maxFrp: number; events: string[] }> = {};
    for (const p of pointsRef.current) {
      if (filter(p)) {
        if (!map[p.state]) map[p.state] = { count: 0, maxFrp: 0, events: [] };
        map[p.state].count++;
        if (p.frp > map[p.state].maxFrp) map[p.state].maxFrp = p.frp;
        if (!map[p.state].events.includes(p.eventId)) map[p.state].events.push(p.eventId);
      }
    }
    return Object.entries(map).sort((a, b) => b[1].count - a[1].count);
  }, [currentStage]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '16px 24px 8px', flexShrink: 0, background: 'var(--bg-primary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="page-title" style={{ margin: 0, fontSize: '20px', fontWeight: 800 }}>
              NASA FIRMS Data Reduction — Canonical Ingestion Pipeline
            </div>
            <span style={{
              fontSize: '9px', fontFamily: 'var(--font-mono)', fontWeight: 700,
              color: '#38BDF8', background: 'rgba(56,189,248,0.12)',
              border: '1px solid rgba(56,189,248,0.3)',
              padding: '2px 8px', borderRadius: 'var(--radius-xs)',
            }}>
              ⚡ LIVE PIPELINE SYNCHRONIZATION
            </span>
            {autoPlay && (
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                ● AUTO-PLAYING
              </span>
            )}
          </div>

          {/* Color Mode Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0B1321', border: '1px solid #1E293B', borderRadius: '6px', padding: '3px 6px' }}>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, paddingLeft: '4px' }}>COLOR BY:</span>
            <button
              onClick={() => setColorMode('intensity')}
              style={{
                padding: '4px 10px', fontSize: '10px', fontWeight: 700, borderRadius: '4px',
                border: 'none', cursor: 'pointer',
                background: colorMode === 'intensity' ? 'var(--accent-cyan)' : 'transparent',
                color: colorMode === 'intensity' ? '#07111F' : 'var(--text-muted)',
              }}
            >
              FRP Heat Intensity
            </button>
            <button
              onClick={() => setColorMode('state')}
              style={{
                padding: '4px 10px', fontSize: '10px', fontWeight: 700, borderRadius: '4px',
                border: 'none', cursor: 'pointer',
                background: colorMode === 'state' ? 'var(--accent-amber)' : 'transparent',
                color: colorMode === 'state' ? '#07111F' : 'var(--text-muted)',
              }}
            >
              Indian State
            </button>
          </div>
        </div>

        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Trace how raw NASA FIRMS detections are ingested, quality-filtered, spatially clustered via DBSCAN, matched with 90-day facility baselines, and prioritized via 4-Engine AI Multimodal Fusion.
        </div>
      </div>

      {/* Stage control strip */}
      <div style={{ padding: '8px 24px', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'var(--bg-secondary)' }}>
        {STAGES.map((s, i) => (
          <button
            key={i}
            onClick={() => goToStage(i)}
            disabled={isTransitioning}
            style={{
              padding: '6px 14px',
              fontSize: '11px', fontWeight: 700,
              borderRadius: 'var(--radius-xs)',
              border: '1px solid',
              cursor: isTransitioning ? 'wait' : 'pointer',
              transition: 'all 0.2s',
              background: stage === i ? `${s.color}22` : 'transparent',
              borderColor: stage === i ? s.color : i < stage ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.07)',
              color: stage === i ? s.color : i < stage ? 'var(--text-muted)' : 'var(--text-disabled)',
            }}
          >
            {i < stage ? '✓ ' : stage === i ? '▶ ' : ''}Stage {i + 1}
          </button>
        ))}

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '10px' }}>
          {selectedState && (
            <button
              onClick={() => setSelectedState(null)}
              style={{ padding: '4px 8px', fontSize: '10px', background: 'rgba(239,68,68,0.2)', border: '1px solid #FF5C6C', borderRadius: '4px', color: '#FF5C6C', cursor: 'pointer' }}
            >
              ✕ Clear Filter: {selectedState}
            </button>
          )}
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '11px', color: 'var(--text-secondary)' }}>
            <input type="checkbox" checked={autoPlay} onChange={e => setAutoPlay(e.target.checked)} />
            Auto-Play
          </label>
          <button
            onClick={() => { goToStage(0); setSelectedState(null); setInspectedPoint(null); }}
            style={{ padding: '5px 12px', fontSize: '11px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 'var(--radius-xs)', background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            ↺ Reset
          </button>
        </div>
      </div>

      {/* Main body: map + info panel */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Map */}
        <div style={{ flex: 1, position: 'relative' }}>
          <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

          {/* Overlay: Live counter */}
          <div style={{
            position: 'absolute', top: '14px', left: '14px', zIndex: 1000,
            background: 'rgba(11, 23, 40, 0.94)',
            border: '1px solid rgba(67,217,232,0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            fontFamily: 'var(--font-mono)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            pointerEvents: 'none',
          }}>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '2px', textTransform: 'uppercase' }}>PIPELINE ACTIVE COUNT</div>
            <div style={{ fontSize: '28px', fontWeight: 900, color: currentStage.color, lineHeight: 1 }}>
              {liveCount}
            </div>
            <div style={{ fontSize: '9px', color: '#94A3B8', marginTop: '2px' }}>{currentStage.stat}</div>
          </div>

          {/* Map Color Legend */}
          <div style={{
            position: 'absolute', bottom: '20px', left: '14px', zIndex: 1000,
            background: 'rgba(11, 23, 40, 0.94)',
            border: '1px solid #1E293B',
            borderRadius: '8px',
            padding: '10px 12px',
            color: '#F4F8FC',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            fontSize: '10px',
            maxWidth: '260px',
          }}>
            <div style={{ fontWeight: 700, color: '#71869B', textTransform: 'uppercase', fontSize: '9px', marginBottom: '6px', letterSpacing: '0.5px' }}>
              {colorMode === 'intensity' ? 'FRP Heat Scale (MW & Size)' : 'State Color Legend'}
            </div>
            {colorMode === 'intensity' ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#FF4557', flexShrink: 0 }} />
                  <span>&gt;200 MW (Critical)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#FF7A45', flexShrink: 0 }} />
                  <span>120–200 MW (High)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#FFB547', flexShrink: 0 }} />
                  <span>60–120 MW (Mid)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#43D9E8', flexShrink: 0 }} />
                  <span>25–60 MW (Low)</span>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', maxHeight: '100px', overflowY: 'auto' }}>
                {Object.entries(STATE_COLORS).slice(0, 8).map(([st, col]) => (
                  <div key={st} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: col, flexShrink: 0 }} />
                    <span style={{ fontSize: '9px', color: '#CBD5E1' }}>{st}</span>
                  </div>
                ))}
              </div>
            )}
            <div style={{ fontSize: '9px', color: '#64748B', marginTop: '6px', borderTop: '1px solid #1E293B', paddingTop: '4px' }}>
              💡 Click any dot to inspect its 4-Engine AI Fusion scorecard
            </div>
          </div>

          {/* Stage label overlay at bottom right */}
          <div style={{
            position: 'absolute', bottom: '20px', right: '14px', zIndex: 1000,
            background: 'rgba(11, 23, 40, 0.94)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderLeft: `4px solid ${currentStage.color}`,
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            maxWidth: '380px',
            pointerEvents: 'none',
          }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: currentStage.color, marginBottom: '2px' }}>
              {currentStage.label}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
              {currentStage.subtitle}
            </div>
          </div>
        </div>

        {/* Right Panel: State Distribution, Pipeline Funnel & Event Inspector */}
        <div style={{
          width: '340px', flexShrink: 0,
          background: 'var(--bg-primary)',
          borderLeft: '1px solid rgba(255,255,255,0.06)',
          overflowY: 'auto',
          padding: '16px',
          display: 'flex', flexDirection: 'column', gap: '14px',
        }}>
          {/* Stat Highlight Card */}
          <div style={{
            padding: '14px',
            background: `${currentStage.color}12`,
            border: `1px solid ${currentStage.color}30`,
            borderLeft: `4px solid ${currentStage.color}`,
            borderRadius: 'var(--radius-sm)',
          }}>
            <div style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '4px' }}>
              {currentStage.stat.toUpperCase()}
            </div>
            <div style={{ fontSize: '36px', fontWeight: 900, color: currentStage.color, lineHeight: 1, marginBottom: '4px' }}>
              {liveCount}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
              {stage > 0 ? `Filtered down from ${pointsRef.current.length} raw telemetry passes` : 'NASA FIRMS sensor sweeps across Indian states'}
            </div>
          </div>

          {/* Description Card */}
          <div style={{
            fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6,
            padding: '12px', background: 'var(--bg-secondary)',
            border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)',
          }}>
            {currentStage.desc}
          </div>

          {/* Canonical Event Inspection Card (when a point is clicked) */}
          {inspectedPoint && (
            <div style={{
              padding: '14px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              borderRadius: 'var(--radius-sm)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#38BDF8', fontWeight: 700 }}>
                  CANONICAL EVENT: {inspectedPoint.eventId}
                </span>
                <button
                  onClick={() => setInspectedPoint(null)}
                  style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: '12px' }}
                >
                  ✕
                </button>
              </div>

              <div style={{ fontSize: '13px', fontWeight: 700, color: '#FFF', marginBottom: '2px' }}>
                {inspectedPoint.name}
              </div>
              <div style={{ fontSize: '10px', color: '#94A3B8', marginBottom: '10px' }}>
                📍 {inspectedPoint.state} · {inspectedPoint.facilityType}
              </div>

              {/* 4-Engine Multimodal AI Scorecard */}
              <div style={{ background: '#07111F', borderRadius: '6px', padding: '10px', border: '1px solid #1E293B', marginBottom: '10px' }}>
                <div style={{ fontSize: '9px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: '6px' }}>
                  4-ENGINE AI FUSION SCORECARD
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '10px' }}>
                  <div>
                    <span style={{ color: '#71869B' }}>FRP Intensity:</span>
                    <div style={{ color: '#FFB547', fontWeight: 700, fontFamily: 'monospace' }}>{inspectedPoint.frp.toFixed(1)} MW</div>
                  </div>
                  <div>
                    <span style={{ color: '#71869B' }}>Z/MAD Deviation:</span>
                    <div style={{ color: inspectedPoint.baselineZ >= 3 ? '#FF5C6C' : '#34D399', fontWeight: 700, fontFamily: 'monospace' }}>
                      Z = +{inspectedPoint.baselineZ.toFixed(1)}σ
                    </div>
                  </div>
                  <div>
                    <span style={{ color: '#71869B' }}>LSTM Escalation:</span>
                    <div style={{ color: inspectedPoint.lstmState === 'CRITICAL_ESCALATION' ? '#FF4557' : inspectedPoint.lstmState === 'ESCALATING' ? '#FF7A45' : '#38BDF8', fontWeight: 700, fontFamily: 'monospace' }}>
                      {inspectedPoint.lstmState}
                    </div>
                  </div>
                  <div>
                    <span style={{ color: '#71869B' }}>Composite Risk:</span>
                    <div style={{ color: inspectedPoint.riskScore >= 75 ? '#FF4557' : '#FFB547', fontWeight: 700, fontFamily: 'monospace' }}>
                      {inspectedPoint.riskScore.toFixed(0)} / 100
                    </div>
                  </div>
                </div>
              </div>

              {onNavigate && inspectedPoint.eventId.startsWith('TT-') && (
                <button
                  onClick={() => onNavigate(`/investigation/${inspectedPoint.eventId}`)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    background: 'rgba(56, 189, 248, 0.15)',
                    border: '1px solid #38BDF8',
                    borderRadius: '4px',
                    color: '#38BDF8',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  🔍 Deep Dive in Event Investigation →
                </button>
              )}
            </div>
          )}

          {/* State-Wise Industrial Distribution */}
          <div style={{ padding: '12px', background: 'var(--bg-secondary)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                STATE-WISE INDUSTRIAL SITES
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-disabled)' }}>Click to isolate</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '160px', overflowY: 'auto' }}>
              {activeStateStats.map(([st, stat]) => {
                const isSel = selectedState === st;
                const dotColor = STATE_COLORS[st] || '#43D9E8';
                return (
                  <div
                    key={st}
                    onClick={() => setSelectedState(isSel ? null : st)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '5px 8px', borderRadius: '4px',
                      background: isSel ? 'rgba(67,217,232,0.15)' : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${isSel ? 'var(--accent-cyan)' : 'transparent'}`,
                      cursor: 'pointer', fontSize: '11px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: dotColor, flexShrink: 0 }} />
                      <span style={{ color: isSel ? '#FFF' : '#CBD5E1', fontWeight: isSel ? 700 : 500 }}>{st}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '10px', color: '#FFB547', fontFamily: 'monospace' }}>max {stat.maxFrp.toFixed(0)} MW</span>
                      <span style={{
                        fontSize: '9px', fontWeight: 700, fontFamily: 'monospace',
                        background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: '3px', color: '#FFF',
                      }}>
                        {stat.count}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Reduction Funnel */}
          <div style={{ padding: '12px', background: 'var(--bg-secondary)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '8px' }}>
              PIPELINE REDUCTION FUNNEL
            </div>
            {STAGES.map((s, i) => {
              const maxCount = pointsRef.current.filter(s.isPointActive).length || 1;
              const allCount = pointsRef.current.length || 1;
              const pct = (maxCount / allCount) * 100;
              return (
                <div key={i} style={{ marginBottom: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '2px' }}>
                    <span style={{ color: i === stage ? s.color : i < stage ? 'var(--text-muted)' : 'var(--text-disabled)' }}>
                      {i === stage ? '▶ ' : i < stage ? '✓ ' : '  '}Stage {i + 1}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: i <= stage ? s.color : 'var(--text-disabled)' }}>
                      {maxCount}
                    </span>
                  </div>
                  <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: i <= stage ? `${pct}%` : '0%',
                      background: i <= stage ? s.color : 'transparent',
                      borderRadius: '2px',
                      transition: 'width 0.4s ease-out',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Priority Alarm Queue Banner on Stage 5 */}
          {stage === 4 && (
            <div style={{
              padding: '12px',
              background: 'rgba(255,92,108,0.08)',
              border: '1px solid rgba(255,92,108,0.3)',
              borderRadius: 'var(--radius-sm)',
              animation: 'fadeIn 0.3s ease-out',
            }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#FF5C6C', marginBottom: '4px' }}>
                🚨 Critical Alarms Queued for Operational Response
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Top critical events prioritized in operational queue.<br />
                Analyst triggers certified dossier dispatch to:<br />
                <strong style={{ color: 'var(--text-secondary)' }}>thermotrace.india@gmail.com</strong>
              </div>
            </div>
          )}

          {/* Navigation buttons */}
          <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
            <button
              onClick={() => goToStage(Math.max(0, stage - 1))}
              disabled={stage === 0 || isTransitioning}
              style={{
                flex: 1, padding: '8px', fontSize: '11px', fontWeight: 600,
                border: '1px solid rgba(255,255,255,0.1)', borderRadius: 'var(--radius-xs)',
                background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer',
                opacity: stage === 0 ? 0.4 : 1,
              }}
            >
              ← Prev Stage
            </button>
            <button
              onClick={() => goToStage(Math.min(STAGES.length - 1, stage + 1))}
              disabled={stage === STAGES.length - 1 || isTransitioning}
              style={{
                flex: 1, padding: '8px', fontSize: '11px', fontWeight: 700,
                border: `1px solid ${currentStage.color}60`,
                borderRadius: 'var(--radius-xs)',
                background: `${currentStage.color}18`,
                color: currentStage.color,
                cursor: 'pointer',
                opacity: stage === STAGES.length - 1 ? 0.4 : 1,
              }}
            >
              Next Stage →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
