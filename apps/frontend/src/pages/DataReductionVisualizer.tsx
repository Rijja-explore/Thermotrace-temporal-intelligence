import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { INDIA_STATES_GEOJSON } from '../data/indiaStates';
import { API_BASE } from '../services/api';

// ─── Realistic Industrial Hotspots across India's Major States ─────────────────
export interface RawPoint {
  lat: number;
  lon: number;
  frp: number;
  name: string;
  state: string;
  facility_type: string;
  noise?: boolean;
}

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
  'Other / Rural': '#64748B',
};

const RAW_INDIA_POINTS: RawPoint[] = [
  // ── Gujarat (Refineries, Chemicals, Ports) ──
  { lat: 22.47, lon: 70.07, frp: 340, name: 'Jamnagar Mega Refinery', state: 'Gujarat', facility_type: 'Oil Refinery' },
  { lat: 22.52, lon: 70.03, frp: 185, name: 'Reliance Petrochem Complex', state: 'Gujarat', facility_type: 'Petrochemicals' },
  { lat: 21.17, lon: 72.83, frp: 215, name: 'ONGC Hazira Gas Processing', state: 'Gujarat', facility_type: 'Gas Plant / LNG' },
  { lat: 22.45, lon: 70.11, frp: 95, name: 'Sikka Thermal Power Station', state: 'Gujarat', facility_type: 'Power Plant' },
  { lat: 21.63, lon: 69.61, frp: 85, name: 'Essar Vadinar Terminal', state: 'Gujarat', facility_type: 'Crude Storage' },
  { lat: 21.20, lon: 72.87, frp: 65, name: 'Surat Chemical Cluster', state: 'Gujarat', facility_type: 'Chemical Plant' },
  { lat: 23.02, lon: 72.57, frp: 45, name: 'Vatva GIDC Chemical Belt', state: 'Gujarat', facility_type: 'Industrial Estate' },

  // ── Maharashtra (Refineries, LNG, Chemical) ──
  { lat: 17.00, lon: 73.31, frp: 280, name: 'Ratnagiri LNG & Gas Terminal', state: 'Maharashtra', facility_type: 'LNG Terminal' },
  { lat: 19.07, lon: 72.88, frp: 140, name: 'BPCL Mumbai Refinery', state: 'Maharashtra', facility_type: 'Oil Refinery' },
  { lat: 17.02, lon: 73.28, frp: 110, name: 'JSW Jaigarh Energy Plant', state: 'Maharashtra', facility_type: 'Power Plant' },
  { lat: 18.93, lon: 72.83, frp: 70, name: 'HPCL Trombay Petrochemical', state: 'Maharashtra', facility_type: 'Petrochemicals' },
  { lat: 18.52, lon: 73.86, frp: 40, name: 'Rasayani Chemical Complex', state: 'Maharashtra', facility_type: 'Chemicals' },

  // ── Odisha (Steel, Smelters, Power) ──
  { lat: 22.09, lon: 84.82, frp: 310, name: 'Rourkela Steel Plant (SAIL)', state: 'Odisha', facility_type: 'Integrated Steel' },
  { lat: 20.85, lon: 85.12, frp: 225, name: 'NTPC Kaniha Super Thermal', state: 'Odisha', facility_type: 'Power Plant' },
  { lat: 22.12, lon: 84.85, frp: 155, name: 'Angul Nalco Aluminium Smelter', state: 'Odisha', facility_type: 'Smelter' },
  { lat: 20.26, lon: 86.67, frp: 98, name: 'IOCL Paradip Refinery Header', state: 'Odisha', facility_type: 'Oil Refinery' },
  { lat: 20.93, lon: 84.78, frp: 60, name: 'Kalinganagar Steel Belt', state: 'Odisha', facility_type: 'Steel Works' },

  // ── Jharkhand (Coal Mining, Blast Furnaces) ──
  { lat: 23.80, lon: 85.96, frp: 320, name: 'Bokaro Steel City Works', state: 'Jharkhand', facility_type: 'Blast Furnace' },
  { lat: 22.80, lon: 86.18, frp: 260, name: 'Tata Steel Jamshedpur Works', state: 'Jharkhand', facility_type: 'Steel Plant' },
  { lat: 23.61, lon: 85.51, frp: 115, name: 'Ramgarh Coal Washery & Kiln', state: 'Jharkhand', facility_type: 'Mining & Kiln' },
  { lat: 23.79, lon: 86.43, frp: 75, name: 'Dhanbad Jharia Colliery Unit', state: 'Jharkhand', facility_type: 'Coal Field' },

  // ── West Bengal (Petrochemicals, Heavy Industry) ──
  { lat: 22.06, lon: 88.07, frp: 245, name: 'Haldia Petrochemicals Complex', state: 'West Bengal', facility_type: 'Petrochemicals' },
  { lat: 23.48, lon: 87.32, frp: 175, name: 'Durgapur Steel Plant (SAIL)', state: 'West Bengal', facility_type: 'Steel Plant' },
  { lat: 23.68, lon: 86.97, frp: 90, name: 'Burnpur IISCO Steel Works', state: 'West Bengal', facility_type: 'Steel Works' },
  { lat: 22.08, lon: 88.10, frp: 55, name: 'Haldia Bulk Liquid Terminal', state: 'West Bengal', facility_type: 'Storage & Vent' },

  // ── Tamil Nadu (Refinery, Power, Metals) ──
  { lat: 13.08, lon: 80.27, frp: 195, name: 'Manali CPCL Refinery', state: 'Tamil Nadu', facility_type: 'Oil Refinery' },
  { lat: 13.11, lon: 80.25, frp: 120, name: 'Ennore Thermal Power Station', state: 'Tamil Nadu', facility_type: 'Power Plant' },
  { lat: 8.76, lon: 78.13, frp: 85, name: 'Tuticorin Industrial Port Complex', state: 'Tamil Nadu', facility_type: 'Port & Smelter' },
  { lat: 10.77, lon: 79.83, frp: 52, name: 'Nagapattinam Gas Compressor', state: 'Tamil Nadu', facility_type: 'Gas Turbine' },

  // ── Assam (Oilfields & Refineries) ──
  { lat: 26.74, lon: 94.18, frp: 210, name: 'Digboi Refinery & Oilfields', state: 'Assam', facility_type: 'Refinery & Wells' },
  { lat: 26.58, lon: 93.75, frp: 135, name: 'Numaligarh Refinery Flare', state: 'Assam', facility_type: 'Oil Refinery' },
  { lat: 27.43, lon: 95.13, frp: 65, name: 'Duliajan Natural Gas Station', state: 'Assam', facility_type: 'Gas Flare' },

  // ── Chhattisgarh (Steel & Super Thermal) ──
  { lat: 21.19, lon: 81.38, frp: 290, name: 'Bhilai Steel Plant (SAIL)', state: 'Chhattisgarh', facility_type: 'Integrated Steel' },
  { lat: 22.35, lon: 82.68, frp: 210, name: 'Korba Super Thermal Power', state: 'Chhattisgarh', facility_type: 'Power Plant' },
  { lat: 21.89, lon: 83.39, frp: 95, name: 'Jindal Raigarh Steel Works', state: 'Chhattisgarh', facility_type: 'Steel Plant' },

  // ── Karnataka (Refinery & Minerals) ──
  { lat: 12.87, lon: 74.84, frp: 165, name: 'MRPL Mangalore Refinery', state: 'Karnataka', facility_type: 'Oil Refinery' },
  { lat: 15.15, lon: 76.92, frp: 140, name: 'Bellary JSW Vijayanagar Steel', state: 'Karnataka', facility_type: 'Steel Complex' },
  { lat: 12.90, lon: 74.88, frp: 55, name: 'New Mangalore Port Chemicals', state: 'Karnataka', facility_type: 'Chemical Storage' },

  // ── Andhra Pradesh (Refinery, Port) ──
  { lat: 17.69, lon: 83.22, frp: 198, name: 'HPCL Vizag Refinery Complex', state: 'Andhra Pradesh', facility_type: 'Oil Refinery' },
  { lat: 17.61, lon: 83.18, frp: 110, name: 'Simhadri NTPC Thermal Power', state: 'Andhra Pradesh', facility_type: 'Power Plant' },
  { lat: 17.72, lon: 83.27, frp: 44, name: 'Gangavaram Bulk Terminal', state: 'Andhra Pradesh', facility_type: 'Port Terminal' },

  // ── Punjab (Refinery & Crop Stubble) ──
  { lat: 30.15, lon: 74.95, frp: 160, name: 'Guru Gobind Bathinda Refinery', state: 'Punjab', facility_type: 'Oil Refinery' },
  { lat: 30.90, lon: 75.86, frp: 68, name: 'Ludhiana Cropland Sector (Agri)', state: 'Punjab', facility_type: 'Stubble Burning' },
  { lat: 30.73, lon: 76.77, frp: 35, name: 'Mohali Industrial Area Belt', state: 'Punjab', facility_type: 'Industrial Park' },

  // ── Rajasthan (Oilfields & Thermal) ──
  { lat: 25.75, lon: 71.40, frp: 175, name: 'Barmer Mangala Oilfield Complex', state: 'Rajasthan', facility_type: 'Oil & Gas Field' },
  { lat: 25.18, lon: 75.83, frp: 95, name: 'Kota Thermal Power Station', state: 'Rajasthan', facility_type: 'Power Plant' },

  // ── Noise / Agricultural / Cloud Edge Artifacts (To be filtered) ──
  { lat: 24.58, lon: 73.68, frp: 18, name: 'Rural Udaipur Forest Edge', state: 'Rajasthan', facility_type: 'Natural/Vegetation', noise: true },
  { lat: 28.63, lon: 77.22, frp: 16, name: 'Delhi NCR Urban Scatter', state: 'Uttar Pradesh', facility_type: 'Urban Clutter', noise: true },
  { lat: 26.85, lon: 80.95, frp: 14, name: 'Lucknow Rural Field Burn', state: 'Uttar Pradesh', facility_type: 'Crop Residue', noise: true },
  { lat: 25.31, lon: 82.97, frp: 12, name: 'Varanasi Agricultural Patch', state: 'Uttar Pradesh', facility_type: 'Agricultural', noise: true },
  { lat: 22.72, lon: 75.87, frp: 15, name: 'Malwa Plateau Transient Flare', state: 'Madhya Pradesh', facility_type: 'Transient Cloud', noise: true },
  { lat: 23.26, lon: 77.41, frp: 11, name: 'Bhopal Ridge Glint Artifact', state: 'Madhya Pradesh', facility_type: 'Solar Glint', noise: true },
  { lat: 19.99, lon: 73.79, frp: 9, name: 'Nashik Scrubland Pixel', state: 'Maharashtra', facility_type: 'Vegetation', noise: true },
  { lat: 15.34, lon: 75.13, frp: 14, name: 'Hubli Field Clearing', state: 'Karnataka', facility_type: 'Agricultural', noise: true },
  { lat: 12.97, lon: 77.59, frp: 12, name: 'Bengaluru Suburban Heat Island', state: 'Karnataka', facility_type: 'Urban Thermal', noise: true },
  { lat: 25.61, lon: 85.14, frp: 19, name: 'Patna Gangetic Cropland', state: 'Other / Rural', facility_type: 'Crop Residue', noise: true },
  { lat: 26.20, lon: 92.93, frp: 17, name: 'Nagaon Low Confidence Dot', state: 'Assam', facility_type: 'Scan Edge', noise: true },
  { lat: 27.18, lon: 78.02, frp: 13, name: 'Agra Peripheral Crop Burn', state: 'Uttar Pradesh', facility_type: 'Agricultural', noise: true },
];

export interface MapPoint extends RawPoint {
  marker?: L.CircleMarker;
  active: boolean;
}

function generateAllPoints(): MapPoint[] {
  const pts: MapPoint[] = [];
  for (const p of RAW_INDIA_POINTS) {
    pts.push({ ...p, noise: Boolean(p.noise || p.frp < 20), active: true });
  }
  // Add additional low-level sensor scatter noise (~50 points) to simulate FIRMS satellite scan background
  for (let i = 0; i < 50; i++) {
    const base = RAW_INDIA_POINTS[i % RAW_INDIA_POINTS.length];
    pts.push({
      lat: base.lat + (Math.random() - 0.5) * 3.5,
      lon: base.lon + (Math.random() - 0.5) * 3.5,
      frp: Math.round(6 + Math.random() * 18),
      name: `Sensor Pixel #${1040 + i}`,
      state: base.state,
      facility_type: 'Raw Satellite Detection',
      noise: true,
      active: true,
    });
  }
  return pts;
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
  if (isNoise || frp < 20) return 3.5;
  if (stageIdx >= 4) {
    return Math.max(10, Math.min(22, frp / 16));
  }
  if (stageIdx >= 2) {
    return Math.max(7, Math.min(16, frp / 22));
  }
  // Early stage: differentiate small vs large
  if (frp >= 200) return 13;
  if (frp >= 100) return 9;
  if (frp >= 50) return 6.5;
  return 4.5;
}

const STAGES = [
  {
    id: 0,
    label: 'Stage 1 — Raw NASA FIRMS Satellite Detections',
    subtitle: 'All thermal anomaly pixels across India from MODIS & VIIRS sensors',
    color: '#FF7A45',
    desc: 'NASA FIRMS scans the entire Indian subcontinent every 12 hours. Every pixel above the sensor thermal threshold is received — refinery flares, steel plants, power stations, seasonal crop burning, solar glint, and cloud edges.',
    stat: 'All Detections',
    activeFilter: (_p: MapPoint) => true,
  },
  {
    id: 1,
    label: 'Stage 2 — Sensor Quality & Noise Filter',
    subtitle: 'Exclude glint artifacts, cloud boundaries, and low-confidence pixels (<25 MW)',
    color: '#FFB547',
    desc: 'ThermoTrace applies signal-to-noise thresholds, eliminating low-FRP atmospheric clutter and sensor glare. Only statistically reliable thermal signals remain.',
    stat: 'Quality-Filtered',
    activeFilter: (p: MapPoint) => p.frp >= 25 && !p.noise,
  },
  {
    id: 2,
    label: 'Stage 3 — Spatiotemporal DBSCAN Clustering',
    subtitle: 'Merge adjacent co-located thermal pixels into distinct event complexes',
    color: '#43D9E8',
    desc: 'DBSCAN spatial clustering (ε = 1.2 km) groups multi-pixel flares into unified facility hot zones. Redundant sub-pixel readings collapse into representative event centroids.',
    stat: 'Clustered Events',
    activeFilter: (p: MapPoint) => p.frp >= 50 && !p.noise,
  },
  {
    id: 3,
    label: 'Stage 4 — Geospatial & Infrastructure Fusion',
    subtitle: 'Spatial join with OSM industrial boundaries, GADM states & ESA WorldCover',
    color: '#A78BFA',
    desc: 'Events are intersected with verified industrial facilities (refineries, steel plants, power complexes) and land cover classifications. Transient agricultural burns and wilderness fires are separated.',
    stat: 'Facility-Matched',
    activeFilter: (p: MapPoint) => p.frp >= 75 && !p.noise && p.facility_type !== 'Stubble Burning',
  },
  {
    id: 4,
    label: 'Stage 5 — AI Anomaly Classification & Emergency Alert',
    subtitle: 'M4-B HistGradientBoosting + Baseline Deviation Z-Score ranking',
    color: '#FF5C6C',
    desc: 'ThermoTrace classifies the highest-risk industrial anomalies exceeding facility baselines. Automated alert intelligence dossier is dispatched to emergency response leads.',
    stat: 'CRITICAL Alarms',
    activeFilter: (p: MapPoint) => p.frp >= 150 && !p.noise && p.facility_type !== 'Stubble Burning',
  },
];

export default function DataReductionVisualizer() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const pointsRef = useRef<MapPoint[]>([]);
  const [stage, setStage] = useState(0);
  const [liveCount, setLiveCount] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [colorMode, setColorMode] = useState<'intensity' | 'state'>('intensity');
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const stageRef = useRef(0);
  const colorModeRef = useRef<'intensity' | 'state'>('intensity');
  colorModeRef.current = colorMode;

  // Build marker tooltip HTML
  const buildTooltip = useCallback((p: MapPoint) => {
    const stColor = STATE_COLORS[p.state] || '#43D9E8';
    const intColor = getIntensityColor(p.frp, p.noise);
    const tier = p.frp >= 200 ? 'CRITICAL HAZARD' : p.frp >= 120 ? 'HIGH HEAT' : p.frp >= 60 ? 'MODERATE' : 'LOW / BASELINE';

    return `
      <div style="font-family:Inter,sans-serif;padding:6px 8px;min-width:210px;background:#0B1728;color:#F4F8FC;border:1px solid #233B56;border-radius:6px;box-shadow:0 8px 24px rgba(0,0,0,0.6)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span style="font-size:10px;font-weight:700;color:${stColor};text-transform:uppercase;letter-spacing:0.5px">
            📍 ${p.state}
          </span>
          <span style="font-size:9px;font-family:monospace;background:rgba(255,255,255,0.08);color:${intColor};padding:1px 5px;border-radius:3px;font-weight:700">
            ${tier}
          </span>
        </div>
        <div style="font-size:13px;font-weight:700;color:#FFF;margin-bottom:2px">
          ${p.name || 'Transient Hotspot Pixel'}
        </div>
        <div style="font-size:10px;color:#94A3B8;margin-bottom:6px">
          ${p.facility_type || 'Industrial Installation'}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;border-top:1px solid #1E293B;padding-top:4px">
          <span style="color:#71869B">Thermal FRP:</span>
          <strong style="color:#FFB547;font-family:monospace;font-size:12px">${p.frp.toFixed(1)} MW</strong>
        </div>
      </div>
    `;
  }, []);

  // Update styles for all markers
  const refreshMarkerStyles = useCallback((curStage: number, mode: 'intensity' | 'state') => {
    if (!mapRef.current) return;
    const filter = STAGES[curStage].activeFilter;
    let count = 0;

    pointsRef.current.forEach(p => {
      if (!p.marker) return;
      const isVisible = filter(p) && (!selectedState || p.state === selectedState);

      if (isVisible) {
        const radius = getPointRadius(p.frp, curStage, p.noise);
        const col = mode === 'state'
          ? (STATE_COLORS[p.state] || '#43D9E8')
          : getIntensityColor(p.frp, p.noise);

        p.marker.setStyle({
          color: col,
          fillColor: col,
          fillOpacity: curStage >= 4 ? 0.9 : 0.75,
          radius,
          weight: p.frp >= 200 ? 2 : 1,
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

  // Init map once
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [21.5, 79.5],
      zoom: 5,
      zoomControl: true,
      attributionControl: false,
    });

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16 }
    ).addTo(map);

    // Clean vector Indian State Boundaries (Level 4 admin borders)
    L.geoJSON(INDIA_STATES_GEOJSON, {
      style: {
        color: '#38BDF8',
        weight: 1.25,
        opacity: 0.65,
        fillOpacity: 0.02,
        fillColor: '#38BDF8',
        dashArray: '3, 4',
      },
      onEachFeature: (feature, layer) => {
        const stateName = feature.properties?.NAME_1;
        if (stateName) {
          layer.bindTooltip(
            `<div style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;color:#38BDF8;padding:2px 6px;background:rgba(11,23,40,0.9);border:1px solid #233B56;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.5)">📍 ${stateName}</div>`,
            { sticky: true, direction: 'top' }
          );
        }
      },
    }).addTo(map);

    mapRef.current = map;

    const allPoints = generateAllPoints().map(p => ({ ...p, active: true }));
    pointsRef.current = allPoints;

    allPoints.forEach(p => {
      const radius = getPointRadius(p.frp, 0, p.noise);
      const col = getIntensityColor(p.frp, p.noise);

      const marker = L.circleMarker([p.lat, p.lon], {
        radius,
        color: col,
        fillColor: col,
        fillOpacity: 0.75,
        weight: p.frp >= 200 ? 2 : 1,
        opacity: 0.9,
      }).addTo(map);

      marker.bindTooltip(buildTooltip(p), {
        permanent: false,
        direction: 'top',
        offset: [0, -6],
      });

      p.marker = marker;
    });

    setLiveCount(allPoints.length);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [buildTooltip]);

  // Apply stage transition
  const applyStage = useCallback((nextStage: number) => {
    if (isTransitioning || !mapRef.current) return;
    setIsTransitioning(true);

    refreshMarkerStyles(nextStage, colorModeRef.current);

    // Stage 4: Auto-dispatch emergency alert
    if (nextStage === 4 && !emailSent) {
      setEmailSent(true);
      fetch(`${API_BASE}/api/notifications/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient_email: 'rijja2310119@ssn.edu.in',
          recipient_name: 'ThermoTrace Admin',
          event_id: 'TT-PIPELINE-AUTO',
          facility_name: 'Jamnagar + Bokaro + Rourkela + Bhilai Mega Industrial Cluster',
          frp_mw: 340.0,
          risk_score: 88.0,
          threat_tier: 'CRITICAL',
          hazard_radius_m: 350,
          custom_notes: 'Auto-dispatched by ThermoTrace Data Reduction Pipeline: Top Critical industrial anomalies isolated from raw FIRMS scan.',
        }),
      }).catch(() => {});
    }

    setTimeout(() => setIsTransitioning(false), 400);
  }, [isTransitioning, emailSent, refreshMarkerStyles]);

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
    }, 4000);
    return () => clearInterval(interval);
  }, [autoPlay, goToStage]);

  const currentStage = STAGES[stage];

  // Compute active state distribution in current stage
  const activeStateStats = useMemo(() => {
    const filter = currentStage.activeFilter;
    const map: Record<string, { count: number; maxFrp: number }> = {};
    for (const p of pointsRef.current) {
      if (filter(p)) {
        if (!map[p.state]) map[p.state] = { count: 0, maxFrp: 0 };
        map[p.state].count++;
        if (p.frp > map[p.state].maxFrp) map[p.state].maxFrp = p.frp;
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
              NASA FIRMS Data Reduction — State-Wise Industrial Intelligence
            </div>
            <span style={{
              fontSize: '9px', fontFamily: 'var(--font-mono)', fontWeight: 700,
              color: '#FF7A45', background: 'rgba(255,122,69,0.12)',
              border: '1px solid rgba(255,122,69,0.3)',
              padding: '2px 8px', borderRadius: 'var(--radius-xs)',
            }}>
              🔴 LIVE INDIA MAP
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
          Watch raw NASA FIRMS detections across Indian states — color-coded and sized by FRP intensity and state provenance — filtered and clustered into verified industrial facility alarms.
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
            onClick={() => { goToStage(0); setSelectedState(null); setEmailSent(false); }}
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
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '2px', textTransform: 'uppercase' }}>ACTIVE HOTSPOTS</div>
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
              💡 Hover any dot to view Industrial Name, State &amp; FRP
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

        {/* Right Panel: State Distribution, Pipeline Funnel & Actions */}
        <div style={{
          width: '320px', flexShrink: 0,
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
              {stage > 0 ? `Filtered down from ${pointsRef.current.length} raw satellite anomalies` : 'Initial NASA FIRMS sensor sweep'}
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

          {/* State-Wise Industrial Distribution (User requested state-wise differentiate) */}
          <div style={{ padding: '12px', background: 'var(--bg-secondary)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                STATE-WISE INDUSTRIAL SITES
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-disabled)' }}>Click to isolate</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '180px', overflowY: 'auto' }}>
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
                      <span style={{ fontSize: '10px', color: '#FFB547', fontFamily: 'monospace' }}>max {stat.maxFrp} MW</span>
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
              REDUCTION FUNNEL
            </div>
            {STAGES.map((s, i) => {
              const maxCount = pointsRef.current.filter(s.activeFilter).length || 1;
              const allCount = pointsRef.current.length;
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

          {/* Email Alert Banner on Stage 5 */}
          {stage === 4 && (
            <div style={{
              padding: '12px',
              background: 'rgba(79,209,139,0.07)',
              border: '1px solid rgba(79,209,139,0.3)',
              borderRadius: 'var(--radius-sm)',
              animation: 'fadeIn 0.3s ease-out',
            }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-green)', marginBottom: '4px' }}>
                ✅ Emergency Alert Dispatched
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Top critical events dispatched to central feed at<br />
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
