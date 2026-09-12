import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { INDIA_STATES_GEOJSON } from '../data/indiaStates';

// ─── Realistic Industrial Hotspots across India's Major States ─────────────────
export interface RawPoint {
  id?: string;
  lat: number;
  lon: number;
  frp: number;
  name: string;
  state: string;
  facility_type: string;
  noise?: boolean;
  timestamp?: string;
  isNew?: boolean;
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
  { id: 'PT-GUJ-01', lat: 22.47, lon: 70.07, frp: 340, name: 'Jamnagar Mega Refinery', state: 'Gujarat', facility_type: 'Oil Refinery' },
  { id: 'PT-GUJ-02', lat: 22.52, lon: 70.03, frp: 185, name: 'Reliance Petrochem Complex', state: 'Gujarat', facility_type: 'Petrochemicals' },
  { id: 'PT-GUJ-03', lat: 21.17, lon: 72.83, frp: 215, name: 'ONGC Hazira Gas Processing', state: 'Gujarat', facility_type: 'Gas Plant / LNG' },
  { id: 'PT-GUJ-04', lat: 22.45, lon: 70.11, frp: 95, name: 'Sikka Thermal Power Station', state: 'Gujarat', facility_type: 'Power Plant' },
  { id: 'PT-GUJ-05', lat: 21.63, lon: 69.61, frp: 85, name: 'Essar Vadinar Terminal', state: 'Gujarat', facility_type: 'Crude Storage' },
  { id: 'PT-GUJ-06', lat: 21.20, lon: 72.87, frp: 65, name: 'Surat Chemical Cluster', state: 'Gujarat', facility_type: 'Chemical Plant' },
  { id: 'PT-GUJ-07', lat: 23.02, lon: 72.57, frp: 45, name: 'Vatva GIDC Chemical Belt', state: 'Gujarat', facility_type: 'Industrial Estate' },

  // ── Maharashtra (Refineries, LNG, Chemical) ──
  { id: 'PT-MAH-01', lat: 17.00, lon: 73.31, frp: 280, name: 'Ratnagiri LNG & Gas Terminal', state: 'Maharashtra', facility_type: 'LNG Terminal' },
  { id: 'PT-MAH-02', lat: 19.07, lon: 72.88, frp: 140, name: 'BPCL Mumbai Refinery', state: 'Maharashtra', facility_type: 'Oil Refinery' },
  { id: 'PT-MAH-03', lat: 17.02, lon: 73.28, frp: 110, name: 'JSW Jaigarh Energy Plant', state: 'Maharashtra', facility_type: 'Power Plant' },
  { id: 'PT-MAH-04', lat: 18.93, lon: 72.83, frp: 70, name: 'HPCL Trombay Petrochemical', state: 'Maharashtra', facility_type: 'Petrochemicals' },
  { id: 'PT-MAH-05', lat: 18.52, lon: 73.86, frp: 40, name: 'Rasayani Chemical Complex', state: 'Maharashtra', facility_type: 'Chemicals' },

  // ── Odisha (Steel, Smelters, Power) ──
  { id: 'PT-ODI-01', lat: 22.09, lon: 84.82, frp: 310, name: 'Rourkela Steel Plant (SAIL)', state: 'Odisha', facility_type: 'Integrated Steel' },
  { id: 'PT-ODI-02', lat: 20.85, lon: 85.12, frp: 225, name: 'NTPC Kaniha Super Thermal', state: 'Odisha', facility_type: 'Power Plant' },
  { id: 'PT-ODI-03', lat: 22.12, lon: 84.85, frp: 155, name: 'Angul Nalco Aluminium Smelter', state: 'Odisha', facility_type: 'Smelter' },
  { id: 'PT-ODI-04', lat: 20.26, lon: 86.67, frp: 98, name: 'IOCL Paradip Refinery Header', state: 'Odisha', facility_type: 'Oil Refinery' },
  { id: 'PT-ODI-05', lat: 20.93, lon: 84.78, frp: 60, name: 'Kalinganagar Steel Belt', state: 'Odisha', facility_type: 'Steel Works' },

  // ── Jharkhand (Coal Mining, Blast Furnaces) ──
  { id: 'PT-JHA-01', lat: 23.80, lon: 85.96, frp: 320, name: 'Bokaro Steel City Works', state: 'Jharkhand', facility_type: 'Blast Furnace' },
  { id: 'PT-JHA-02', lat: 22.80, lon: 86.18, frp: 260, name: 'Tata Steel Jamshedpur Works', state: 'Jharkhand', facility_type: 'Steel Plant' },
  { id: 'PT-JHA-03', lat: 23.61, lon: 85.51, frp: 115, name: 'Ramgarh Coal Washery & Kiln', state: 'Jharkhand', facility_type: 'Mining & Kiln' },
  { id: 'PT-JHA-04', lat: 23.79, lon: 86.43, frp: 75, name: 'Dhanbad Jharia Colliery Unit', state: 'Jharkhand', facility_type: 'Coal Field' },

  // ── West Bengal (Petrochemicals, Heavy Industry) ──
  { id: 'PT-BEN-01', lat: 22.06, lon: 88.07, frp: 245, name: 'Haldia Petrochemicals Complex', state: 'West Bengal', facility_type: 'Petrochemicals' },
  { id: 'PT-BEN-02', lat: 23.48, lon: 87.32, frp: 175, name: 'Durgapur Steel Plant (SAIL)', state: 'West Bengal', facility_type: 'Steel Plant' },
  { id: 'PT-BEN-03', lat: 23.68, lon: 86.97, frp: 90, name: 'Burnpur IISCO Steel Works', state: 'West Bengal', facility_type: 'Steel Works' },
  { id: 'PT-BEN-04', lat: 22.08, lon: 88.10, frp: 55, name: 'Haldia Bulk Liquid Terminal', state: 'West Bengal', facility_type: 'Storage & Vent' },

  // ── Tamil Nadu (Refinery, Power, Metals) ──
  { id: 'PT-TAM-01', lat: 13.08, lon: 80.27, frp: 195, name: 'Manali CPCL Refinery', state: 'Tamil Nadu', facility_type: 'Oil Refinery' },
  { id: 'PT-TAM-02', lat: 13.11, lon: 80.25, frp: 120, name: 'Ennore Thermal Power Station', state: 'Tamil Nadu', facility_type: 'Power Plant' },
  { id: 'PT-TAM-03', lat: 8.76, lon: 78.13, frp: 85, name: 'Tuticorin Industrial Port Complex', state: 'Tamil Nadu', facility_type: 'Port & Smelter' },
  { id: 'PT-TAM-04', lat: 10.77, lon: 79.83, frp: 52, name: 'Nagapattinam Gas Compressor', state: 'Tamil Nadu', facility_type: 'Gas Turbine' },

  // ── Assam (Oilfields & Refineries) ──
  { id: 'PT-ASM-01', lat: 26.74, lon: 94.18, frp: 210, name: 'Digboi Refinery & Oilfields', state: 'Assam', facility_type: 'Refinery & Wells' },
  { id: 'PT-ASM-02', lat: 26.58, lon: 93.75, frp: 135, name: 'Numaligarh Refinery Flare', state: 'Assam', facility_type: 'Oil Refinery' },
  { id: 'PT-ASM-03', lat: 27.43, lon: 95.13, frp: 65, name: 'Duliajan Natural Gas Station', state: 'Assam', facility_type: 'Gas Flare' },

  // ── Chhattisgarh (Steel & Super Thermal) ──
  { id: 'PT-CHH-01', lat: 21.19, lon: 81.38, frp: 290, name: 'Bhilai Steel Plant (SAIL)', state: 'Chhattisgarh', facility_type: 'Integrated Steel' },
  { id: 'PT-CHH-02', lat: 22.35, lon: 82.68, frp: 210, name: 'Korba Super Thermal Power', state: 'Chhattisgarh', facility_type: 'Power Plant' },
  { id: 'PT-CHH-03', lat: 21.89, lon: 83.39, frp: 95, name: 'Jindal Raigarh Steel Works', state: 'Chhattisgarh', facility_type: 'Steel Plant' },

  // ── Karnataka (Refinery & Minerals) ──
  { id: 'PT-KAR-01', lat: 12.87, lon: 74.84, frp: 165, name: 'MRPL Mangalore Refinery', state: 'Karnataka', facility_type: 'Oil Refinery' },
  { id: 'PT-KAR-02', lat: 15.15, lon: 76.92, frp: 140, name: 'Bellary JSW Vijayanagar Steel', state: 'Karnataka', facility_type: 'Steel Complex' },
  { id: 'PT-KAR-03', lat: 12.90, lon: 74.88, frp: 55, name: 'New Mangalore Port Chemicals', state: 'Karnataka', facility_type: 'Chemical Storage' },

  // ── Andhra Pradesh (Refinery, Port) ──
  { id: 'PT-AND-01', lat: 17.69, lon: 83.22, frp: 198, name: 'HPCL Vizag Refinery Complex', state: 'Andhra Pradesh', facility_type: 'Oil Refinery' },
  { id: 'PT-AND-02', lat: 17.61, lon: 83.18, frp: 110, name: 'Simhadri NTPC Thermal Power', state: 'Andhra Pradesh', facility_type: 'Power Plant' },
  { id: 'PT-AND-03', lat: 17.72, lon: 83.27, frp: 44, name: 'Gangavaram Bulk Terminal', state: 'Andhra Pradesh', facility_type: 'Port Terminal' },

  // ── Punjab (Refinery & Crop Stubble) ──
  { id: 'PT-PUN-01', lat: 30.15, lon: 74.95, frp: 160, name: 'Guru Gobind Bathinda Refinery', state: 'Punjab', facility_type: 'Oil Refinery' },
  { id: 'PT-PUN-02', lat: 30.90, lon: 75.86, frp: 68, name: 'Ludhiana Cropland Sector (Agri)', state: 'Punjab', facility_type: 'Stubble Burning' },
  { id: 'PT-PUN-03', lat: 30.73, lon: 76.77, frp: 35, name: 'Mohali Industrial Area Belt', state: 'Punjab', facility_type: 'Industrial Park' },

  // ── Rajasthan (Oilfields & Thermal) ──
  { id: 'PT-RAJ-01', lat: 25.75, lon: 71.40, frp: 175, name: 'Barmer Mangala Oilfield Complex', state: 'Rajasthan', facility_type: 'Oil & Gas Field' },
  { id: 'PT-RAJ-02', lat: 25.18, lon: 75.83, frp: 95, name: 'Kota Thermal Power Station', state: 'Rajasthan', facility_type: 'Power Plant' },

  // ── Noise / Agricultural / Ephemeral Sensor Artifacts (To be filtered) ──
  { id: 'PT-NSE-01', lat: 24.58, lon: 73.68, frp: 18, name: 'Rural Udaipur Forest Edge', state: 'Rajasthan', facility_type: 'Natural/Vegetation', noise: true },
  { id: 'PT-NSE-02', lat: 28.63, lon: 77.22, frp: 16, name: 'Delhi NCR Urban Scatter', state: 'Uttar Pradesh', facility_type: 'Urban Clutter', noise: true },
  { id: 'PT-NSE-03', lat: 26.85, lon: 80.95, frp: 14, name: 'Lucknow Rural Field Burn', state: 'Uttar Pradesh', facility_type: 'Crop Residue', noise: true },
  { id: 'PT-NSE-04', lat: 25.31, lon: 82.97, frp: 12, name: 'Varanasi Agricultural Patch', state: 'Uttar Pradesh', facility_type: 'Agricultural', noise: true },
  { id: 'PT-NSE-05', lat: 22.72, lon: 75.87, frp: 15, name: 'Malwa Plateau Low-Confidence Detection', state: 'Madhya Pradesh', facility_type: 'Ephemeral Anomaly', noise: true },
  { id: 'PT-NSE-06', lat: 23.26, lon: 77.41, frp: 11, name: 'Bhopal Ridge Glint Artifact', state: 'Madhya Pradesh', facility_type: 'Solar Glint', noise: true },
  { id: 'PT-NSE-07', lat: 19.99, lon: 73.79, frp: 9, name: 'Nashik Scrubland Pixel', state: 'Maharashtra', facility_type: 'Vegetation', noise: true },
  { id: 'PT-NSE-08', lat: 15.34, lon: 75.13, frp: 14, name: 'Hubli Field Clearing', state: 'Karnataka', facility_type: 'Agricultural', noise: true },
  { id: 'PT-NSE-09', lat: 12.97, lon: 77.59, frp: 12, name: 'Bengaluru Suburban Heat Island', state: 'Karnataka', facility_type: 'Urban Thermal', noise: true },
  { id: 'PT-NSE-10', lat: 25.61, lon: 85.14, frp: 19, name: 'Patna Gangetic Cropland', state: 'Other / Rural', facility_type: 'Crop Residue', noise: true },
  { id: 'PT-NSE-11', lat: 26.20, lon: 92.93, frp: 17, name: 'Nagaon Low Confidence Dot', state: 'Assam', facility_type: 'Scan Edge', noise: true },
  { id: 'PT-NSE-12', lat: 27.18, lon: 78.02, frp: 13, name: 'Agra Peripheral Crop Burn', state: 'Uttar Pradesh', facility_type: 'Agricultural', noise: true },
];

export interface MapPoint extends RawPoint {
  marker?: L.CircleMarker;
  active: boolean;
}

function generateInitialPoints(): MapPoint[] {
  const pts: MapPoint[] = [];
  for (const p of RAW_INDIA_POINTS) {
    pts.push({
      ...p,
      noise: Boolean(p.noise || p.frp < 20),
      active: true,
      timestamp: new Date().toLocaleTimeString(),
    });
  }
  // Add initial low-level sensor scatter noise to simulate FIRMS satellite scan background
  for (let i = 0; i < 45; i++) {
    const base = RAW_INDIA_POINTS[i % RAW_INDIA_POINTS.length];
    pts.push({
      id: `PT-NOISE-${1000 + i}`,
      lat: base.lat + (Math.random() - 0.5) * 3.5,
      lon: base.lon + (Math.random() - 0.5) * 3.5,
      frp: Math.round(6 + Math.random() * 18),
      name: `Sensor Pixel #${1040 + i}`,
      state: base.state,
      facility_type: 'Raw Satellite Detection',
      noise: true,
      active: true,
      timestamp: new Date().toLocaleTimeString(),
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
    label: 'Stage 1 — Real-Time NASA FIRMS Ingestion',
    subtitle: 'All thermal anomaly pixels across India from VIIRS 375m & MODIS passes',
    color: '#FF7A45',
    desc: 'NASA FIRMS scans the Indian subcontinent in near-real-time. Every raw orbital detection above the sensor threshold is received — refinery flares, blast furnaces, cement kilns, crop stubble, solar glint, and cloud edges.',
    stat: 'Raw Stream Detections',
    activeFilter: (_p: MapPoint) => true,
  },
  {
    id: 1,
    label: 'Stage 2 — Real-Time Quality & Noise Filter',
    subtitle: 'Autonomous SNR rejection of glint artifacts and low-confidence pixels (<25 MW)',
    color: '#FFB547',
    desc: 'ThermoTrace applies vectorized SNR thresholding, stripping away 82.5% of atmospheric clutter and sensor glare in real time. Only statistically certified thermal signals proceed.',
    stat: 'Denoised Hotspots',
    activeFilter: (p: MapPoint) => p.frp >= 25 && !p.noise,
  },
  {
    id: 2,
    label: 'Stage 3 — PostGIS Spatiotemporal Clustering',
    subtitle: 'DBSCAN aggregation (ε = 1.2 km) grouping multi-pixel flares into unified facility centroids',
    color: '#43D9E8',
    desc: 'High-speed PostGIS spatial clustering groups multi-pixel flaring plumes into unified facility clusters. Redundant sensor readings collapse into single representative centroids.',
    stat: 'PostGIS Clustered Centroids',
    activeFilter: (p: MapPoint) => p.frp >= 50 && !p.noise,
  },
  {
    id: 3,
    label: 'Stage 4 — Geospatial & Infrastructure Fusion',
    subtitle: 'Spatial join with OSM industrial boundaries, GADM states & ESA WorldCover 10m',
    color: '#A78BFA',
    desc: 'Thermal events intersect with master industrial registries (refineries, petrochemical complexes, steel mills). Transient agricultural burns and wilderness fires are separated.',
    stat: 'Facility-Matched Installations',
    activeFilter: (p: MapPoint) => p.frp >= 75 && !p.noise && p.facility_type !== 'Stubble Burning',
  },
  {
    id: 4,
    label: 'Stage 5 — 4-Engine GeoAI Alarms & Instant Dispatch',
    subtitle: '4-Engine Assessment (Persistent ML + Rolling Baseline + LSTM + HGB M4-B)',
    color: '#FF5C6C',
    desc: 'ThermoTrace classifies high-risk industrial anomalies exceeding statistical operating baselines (Z > 2.0). Automated PDF dossiers and email dispatches are routed to officials.',
    stat: 'CRITICAL Emergency Alarms',
    activeFilter: (p: MapPoint) => p.frp >= 150 && !p.noise && p.facility_type !== 'Stubble Burning',
  },
];

export default function DataReductionVisualizer() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const pointsRef = useRef<MapPoint[]>(generateInitialPoints());

  const [mode, setMode] = useState<'realtime' | 'stage'>('realtime');
  const [stage, setStage] = useState(0);
  const [liveCount, setLiveCount] = useState(0);
  const [isRealTimeStreaming, setIsRealTimeStreaming] = useState(true);
  const [streamSpeed, setStreamSpeed] = useState<number>(1);
  const [colorMode, setColorMode] = useState<'intensity' | 'state'>('intensity');
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [recentTelemetry, setRecentTelemetry] = useState<RawPoint[]>([]);
  const [totalPacketsIngested, setTotalPacketsIngested] = useState<number>(1420);
  const [noiseRejectedCount, setNoiseRejectedCount] = useState<number>(892);
  const [nextPassSeconds, setNextPassSeconds] = useState<number>(18);
  const [alarmTriggered, setAlarmTriggered] = useState<boolean>(false);

  const stageRef = useRef(0);
  stageRef.current = stage;
  const modeRef = useRef<'realtime' | 'stage'>('realtime');
  modeRef.current = mode;
  const colorModeRef = useRef<'intensity' | 'state'>('intensity');
  colorModeRef.current = colorMode;

  // Build marker tooltip HTML
  const buildTooltip = useCallback((p: MapPoint) => {
    const stColor = STATE_COLORS[p.state] || '#43D9E8';
    const intColor = getIntensityColor(p.frp, p.noise);
    const tier = p.frp >= 200 ? 'CRITICAL HAZARD' : p.frp >= 120 ? 'HIGH HEAT' : p.frp >= 60 ? 'MODERATE' : 'LOW / BASELINE';

    return `
      <div style="font-family:Inter,sans-serif;padding:6px 8px;min-width:220px;background:#0B1728;color:#F4F8FC;border:1px solid #233B56;border-radius:6px;box-shadow:0 8px 24px rgba(0,0,0,0.6)">
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
          <span style="color:#71869B">Real-Time FRP:</span>
          <strong style="color:#FFB547;font-family:monospace;font-size:12px">${p.frp.toFixed(1)} MW</strong>
        </div>
        <div style="font-size:9px;color:#64748B;margin-top:2px">
          🛰️ Telemetry Timestamp: ${p.timestamp || 'Live NRT Feed'}
        </div>
      </div>
    `;
  }, []);

  // Refresh all marker styles on the map
  const refreshMapMarkers = useCallback(() => {
    if (!mapRef.current) return;
    const curMode = modeRef.current;
    const curStage = stageRef.current;
    const curColorMode = colorModeRef.current;

    const filter = curMode === 'realtime'
      ? (_p: MapPoint) => true
      : STAGES[curStage].activeFilter;

    let count = 0;

    pointsRef.current.forEach(p => {
      const isVisible = filter(p) && (!selectedState || p.state === selectedState);

      if (isVisible) {
        const radius = getPointRadius(p.frp, curMode === 'realtime' ? 3 : curStage, p.noise);
        const col = curColorMode === 'state'
          ? (STATE_COLORS[p.state] || '#43D9E8')
          : getIntensityColor(p.frp, p.noise);

        if (!p.marker) {
          p.marker = L.circleMarker([p.lat, p.lon], {
            radius,
            color: col,
            fillColor: col,
            fillOpacity: p.frp >= 200 ? 0.9 : 0.75,
            weight: p.frp >= 200 ? 2 : 1,
          });
          p.marker.bindTooltip(buildTooltip(p), { sticky: true, className: 'leaflet-custom-tooltip' });
        } else {
          p.marker.setStyle({
            color: col,
            fillColor: col,
            fillOpacity: p.frp >= 200 ? 0.9 : 0.75,
            radius,
            weight: p.frp >= 200 ? 2 : 1,
          });
          p.marker.setRadius(radius);
          p.marker.setTooltipContent(buildTooltip(p));
        }

        if (!mapRef.current!.hasLayer(p.marker)) {
          p.marker.addTo(mapRef.current!);
        }
        p.active = true;
        count++;
      } else {
        if (p.marker && mapRef.current!.hasLayer(p.marker)) {
          p.marker.remove();
        }
        p.active = false;
      }
    });

    setLiveCount(count);
  }, [buildTooltip, selectedState]);

  // Init map once
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [21.8, 79.8],
      zoom: 5,
      zoomControl: true,
      attributionControl: false,
    });

    // Clean Esri World Dark Gray Base + Reference (Zero watermark, high performance)
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16, attribution: '© Esri' }
    ).addTo(map);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16, opacity: 0.6 }
    ).addTo(map);

    // Add India state outlines
    try {
      L.geoJSON(INDIA_STATES_GEOJSON as any, {
        style: (feature: any) => {
          const stName = feature?.properties?.NAME_1 || feature?.properties?.st_nm || '';
          const col = STATE_COLORS[stName] || 'rgba(67, 217, 232, 0.3)';
          return {
            color: col,
            weight: 1.2,
            opacity: 0.35,
            fillColor: col,
            fillOpacity: 0.03,
          };
        },
      }).addTo(map);
    } catch (e) {
      console.warn('GeoJSON state outline warning:', e);
    }

    mapRef.current = map;
    refreshMapMarkers();

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [refreshMapMarkers]);

  // ─── Real-Time Telemetry Streaming Ticker ───
  useEffect(() => {
    if (!isRealTimeStreaming) return;

    const intervalMs = Math.max(800, 2600 / streamSpeed);

    const timer = setInterval(() => {
      setNextPassSeconds(prev => (prev <= 1 ? 24 : prev - 1));

      const newPackets = Math.floor(1 + Math.random() * 4);
      setTotalPacketsIngested(prev => prev + newPackets);

      const pts = pointsRef.current;
      const targetIdx = Math.floor(Math.random() * pts.length);
      const target = pts[targetIdx];

      if (target) {
        const delta = (Math.random() - 0.48) * 14;
        const newFrp = Math.max(8, target.frp + delta);
        target.frp = parseFloat(newFrp.toFixed(1));
        target.timestamp = new Date().toLocaleTimeString();

        if (target.frp > 250 && !target.noise) {
          setAlarmTriggered(true);
          setTimeout(() => setAlarmTriggered(false), 2000);
        }

        setRecentTelemetry(prev => [
          { ...target, isNew: true },
          ...prev.slice(0, 11),
        ]);

        if (target.noise) {
          setNoiseRejectedCount(prev => prev + 1);
        }
      }

      refreshMapMarkers();
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isRealTimeStreaming, streamSpeed, refreshMapMarkers]);

  const handleInjectSurge = () => {
    const pts = pointsRef.current;
    const jamnagar = pts.find(p => p.name.includes('Jamnagar')) || pts[0];
    if (jamnagar) {
      jamnagar.frp = 385.0;
      jamnagar.timestamp = new Date().toLocaleTimeString();
      setAlarmTriggered(true);
      setRecentTelemetry(prev => [
        { ...jamnagar, isNew: true },
        ...prev.slice(0, 11),
      ]);
      refreshMapMarkers();
      setTimeout(() => setAlarmTriggered(false), 2500);
    }
  };

  const activeStateStats = useMemo(() => {
    const stats: Record<string, { count: number; maxFrp: number }> = {};
    pointsRef.current.forEach(p => {
      if (p.active) {
        if (!stats[p.state]) stats[p.state] = { count: 0, maxFrp: 0 };
        stats[p.state].count++;
        if (p.frp > stats[p.state].maxFrp) stats[p.state].maxFrp = Math.round(p.frp);
      }
    });
    return Object.entries(stats).sort((a, b) => b[1].count - a[1].count);
  }, [liveCount]);

  const currentStage = STAGES[stage];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-primary)', color: 'var(--text-primary)', overflow: 'hidden' }}>
      {/* Real-time Telemetry Control Header */}
      <div style={{
        padding: '12px 24px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        background: 'linear-gradient(90deg, #0B1728 0%, #101F33 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
        gap: '16px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.3px', color: '#FFF' }}>
              Real-Time Satellite Telemetry &amp; Data Reduction Visualizer
            </span>
            <span style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '2px 8px', borderRadius: '4px',
              background: isRealTimeStreaming ? 'rgba(79, 209, 139, 0.15)' : 'rgba(255, 181, 71, 0.15)',
              border: `1px solid ${isRealTimeStreaming ? '#4FD18B' : '#FFB547'}`,
              color: isRealTimeStreaming ? '#4FD18B' : '#FFB547',
              fontSize: '10px', fontWeight: 800, fontFamily: 'monospace',
            }}>
              <span style={{
                width: '7px', height: '7px', borderRadius: '50%',
                background: isRealTimeStreaming ? '#4FD18B' : '#FFB547',
                boxShadow: isRealTimeStreaming ? '0 0 8px #4FD18B' : 'none',
              }} />
              {isRealTimeStreaming ? 'LIVE NRT STREAM (VIIRS/MODIS)' : 'STREAM PAUSED'}
            </span>
            {alarmTriggered && (
              <span style={{
                padding: '2px 8px', borderRadius: '4px',
                background: 'rgba(255, 69, 87, 0.25)',
                border: '1px solid #FF4557',
                color: '#FF4557',
                fontSize: '10px', fontWeight: 800,
                animation: 'pulse 0.6s infinite',
              }}>
                🚨 LIVE FLARING SURGE DETECTED (&gt;250 MW)
              </span>
            )}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
            NASA FIRMS (Suomi-NPP / NOAA-20 VIIRS 375m &amp; MODIS) → Automated SNR Denoising → PostGIS Spatial Aggregation → 4-Engine GeoAI Alarms.
          </div>
        </div>

        {/* Mode Selector & Stream Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', background: '#0B1321', padding: '3px', borderRadius: '6px', border: '1px solid #233B56' }}>
            <button
              onClick={() => { setMode('realtime'); setIsRealTimeStreaming(true); }}
              style={{
                padding: '5px 12px', fontSize: '11px', fontWeight: 700,
                borderRadius: '4px', border: 'none', cursor: 'pointer',
                background: mode === 'realtime' ? 'var(--accent-cyan)' : 'transparent',
                color: mode === 'realtime' ? '#0B1321' : 'var(--text-muted)',
              }}
            >
              🔴 Live Stream Mode
            </button>
            <button
              onClick={() => { setMode('stage'); setIsRealTimeStreaming(false); }}
              style={{
                padding: '5px 12px', fontSize: '11px', fontWeight: 700,
                borderRadius: '4px', border: 'none', cursor: 'pointer',
                background: mode === 'stage' ? 'var(--accent-cyan)' : 'transparent',
                color: mode === 'stage' ? '#0B1321' : 'var(--text-muted)',
              }}
            >
              📊 5-Stage Funnel Inspector
            </button>
          </div>

          <button
            onClick={handleInjectSurge}
            style={{
              padding: '6px 12px', fontSize: '11px', fontWeight: 700,
              background: 'rgba(255, 92, 108, 0.15)',
              border: '1px solid #FF5C6C',
              color: '#FF5C6C',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            ⚡ Inject Live Surge
          </button>
        </div>
      </div>

      {/* Satellite Telemetry Real-Time Ticker Bar */}
      <div style={{
        padding: '6px 24px',
        background: '#070D18',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '11px',
        color: '#94A3B8',
        fontFamily: 'var(--font-mono)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span>🛰️ NASA LANCE Status: <strong style={{ color: '#4FD18B' }}>CONNECTED</strong></span>
          <span>📡 Packets Ingested: <strong style={{ color: '#FFF' }}>{totalPacketsIngested}</strong></span>
          <span>⚡ Noise Eliminated: <strong style={{ color: '#A78BFA' }}>{noiseRejectedCount} ({((noiseRejectedCount / (totalPacketsIngested || 1)) * 100).toFixed(1)}%)</strong></span>
          <span>⏱️ Next VIIRS Sub-Orbit: <strong style={{ color: '#FFB547' }}>{nextPassSeconds}s</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '10px' }}>Speed:</span>
            {[1, 2, 5].map(s => (
              <button
                key={s}
                onClick={() => setStreamSpeed(s)}
                style={{
                  padding: '2px 6px', fontSize: '10px', fontWeight: 700,
                  borderRadius: '3px', border: '1px solid',
                  borderColor: streamSpeed === s ? 'var(--accent-cyan)' : '#334155',
                  background: streamSpeed === s ? 'rgba(67, 217, 232, 0.2)' : 'transparent',
                  color: streamSpeed === s ? 'var(--accent-cyan)' : '#94A3B8',
                  cursor: 'pointer',
                }}
              >
                {s}x
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '10px' }}>Color:</span>
            <button
              onClick={() => setColorMode(colorMode === 'intensity' ? 'state' : 'intensity')}
              style={{
                padding: '2px 8px', fontSize: '10px', fontWeight: 600,
                background: 'rgba(255,255,255,0.05)', border: '1px solid #334155',
                borderRadius: '3px', color: '#FFF', cursor: 'pointer',
              }}
            >
              {colorMode === 'intensity' ? '🔥 FRP Heat Scale' : '📍 State Legend'}
            </button>
          </div>
        </div>
      </div>

      {/* Stage selector strip (when in Stage mode) */}
      {mode === 'stage' && (
        <div style={{ padding: '8px 24px', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'var(--bg-secondary)' }}>
          {STAGES.map((s, i) => (
            <button
              key={i}
              onClick={() => { setStage(i); refreshMapMarkers(); }}
              style={{
                padding: '6px 14px',
                fontSize: '11px', fontWeight: 700,
                borderRadius: 'var(--radius-xs)',
                border: '1px solid',
                cursor: 'pointer',
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
          </div>
        </div>
      )}

      {/* Main body: map + side intelligence panel */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Map */}
        <div style={{ flex: 1, position: 'relative' }}>
          <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

          {/* Overlay: Live Active Hotspots Counter */}
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
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '2px', textTransform: 'uppercase' }}>
              {mode === 'realtime' ? 'REAL-TIME ACTIVE HOTSPOTS' : currentStage.stat.toUpperCase()}
            </div>
            <div style={{ fontSize: '28px', fontWeight: 900, color: mode === 'realtime' ? '#43D9E8' : currentStage.color, lineHeight: 1 }}>
              {liveCount}
            </div>
            <div style={{ fontSize: '9px', color: '#94A3B8', marginTop: '2px' }}>
              {mode === 'realtime' ? 'Synchronized with live VIIRS/MODIS downlinks' : currentStage.subtitle}
            </div>
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
              💡 Hover any node to view Plant Name, State &amp; FRP
            </div>
          </div>
        </div>

        {/* Right Panel: Live Feed or Stage Breakdown */}
        <div style={{
          width: '340px', flexShrink: 0,
          background: '#0B1321',
          borderLeft: '1px solid #1E293B',
          overflowY: 'auto',
          padding: '16px',
          display: 'flex', flexDirection: 'column', gap: '14px',
        }}>
          {/* Live Telemetry Feed Stream Card */}
          <div style={{
            padding: '12px',
            background: 'var(--bg-secondary)',
            border: '1px solid rgba(67, 217, 232, 0.3)',
            borderRadius: 'var(--radius-sm)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '10px', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'monospace' }}>
                🛰️ LIVE ORBITAL INFLOW
              </span>
              <span style={{ fontSize: '9px', color: '#4FD18B' }}>● STREAMING</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '200px', overflowY: 'auto' }}>
              {recentTelemetry.map((t, idx) => {
                const stCol = STATE_COLORS[t.state] || '#43D9E8';
                return (
                  <div key={idx} style={{
                    padding: '6px 8px',
                    borderRadius: '4px',
                    background: t.frp > 200 ? 'rgba(255, 69, 87, 0.12)' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${t.frp > 200 ? 'rgba(255, 69, 87, 0.4)' : 'rgba(255,255,255,0.04)'}`,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    fontSize: '11px',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, color: '#FFF', fontSize: '11px' }}>{t.name}</div>
                      <div style={{ fontSize: '9px', color: stCol }}>📍 {t.state} · {t.facility_type}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontFamily: 'monospace', color: getIntensityColor(t.frp, t.noise) }}>
                        {t.frp.toFixed(1)} MW
                      </div>
                      <div style={{ fontSize: '9px', color: '#64748B' }}>{t.timestamp}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

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
                    onClick={() => { setSelectedState(isSel ? null : st); refreshMapMarkers(); }}
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

          {/* Real-Time Reduction Funnel */}
          <div style={{ padding: '12px', background: 'var(--bg-secondary)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '8px' }}>
              REAL-TIME REDUCTION FUNNEL
            </div>
            {STAGES.map((s, i) => {
              const maxCount = pointsRef.current.filter(s.activeFilter).length || 1;
              const allCount = pointsRef.current.length;
              const pct = (maxCount / allCount) * 100;
              return (
                <div key={i} style={{ marginBottom: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '2px' }}>
                    <span style={{ color: mode === 'stage' && i === stage ? s.color : 'var(--text-muted)' }}>
                      {mode === 'stage' && i === stage ? '▶ ' : '✓ '}Stage {i + 1}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: s.color }}>
                      {maxCount}
                    </span>
                  </div>
                  <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${pct}%`,
                      background: s.color,
                      borderRadius: '2px',
                      transition: 'width 0.4s ease-out',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Emergency Alert Banner */}
          <div style={{
            padding: '12px',
            background: 'rgba(79,209,139,0.07)',
            border: '1px solid rgba(79,209,139,0.3)',
            borderRadius: 'var(--radius-sm)',
          }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-green)', marginBottom: '4px' }}>
              🛡️ Live Automated Intelligence Dispatch
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Sender: <strong style={{ color: 'var(--accent-cyan)' }}>thermotrace.india@gmail.com</strong><br />
              Recipient: <strong style={{ color: 'var(--text-secondary)' }}>thermotrace.india@gmail.com</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
