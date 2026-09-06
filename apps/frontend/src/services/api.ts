/**
 * ThermoTrace API Client — Connects React UI to FastAPI Backend.
 * Standardized to Canonical ThermoTrace Data Contract.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface FetchOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`);
    }

    return res.json();
  } catch (err) {
    console.warn(`[API] ${path} failed:`, err);
    throw err;
  }
}

// ─── CANONICAL EVENT TYPES ───
export interface ThermoEvent {
  event_id: string;
  title?: string;
  geometry: {
    latitude?: number;
    longitude?: number;
    lat?: number;
    lon?: number;
    elevation_m?: number;
    buffer_radius_m?: number;
  };
  time_window: { start: string; end: string; duration_hours?: number };
  observations: Array<{
    observation_id?: string;
    latitude?: number;
    longitude?: number;
    frp: number;
    brightness?: number;
    confidence?: number;
    acq_timestamp?: string;
    acq_date?: string;
    satellite: string;
  }>;
  facility_context: {
    nearest_facility_id?: string;
    nearest_facility_name?: string;
    name?: string;
    facility_type?: string;
    distance_to_facility_m?: number;
    nearby_refinery_km?: number;
    land_cover?: string;
    population_within_5km?: number;
  };
  landcover_context?: {
    primary_class?: string;
    urban_builtup_pct?: number;
    forest_pct?: number;
    cropland_pct?: number;
    water_pct?: number;
  };
  satellite_context?: {
    imagery_available?: boolean;
    source?: string;
    scene_id?: string;
    cloud_cover_pct?: number;
    thumbnail_url?: string;
  };
  temporal_features?: {
    window_7d?: { detection_count?: number; frp_mean?: number; persistence_ratio?: number };
    window_30d?: { detection_count?: number; frp_mean?: number; persistence_ratio?: number };
    window_90d?: { detection_count?: number; frp_mean?: number; persistence_ratio?: number };
    spatial_stability_m?: number;
    baseline_frp_mean?: number;
    baseline_frp_std?: number;
    current_frp?: number;
    deviation_sigma?: number;
    detection_count_30d?: number;
    persistence_ratio?: number;
  };
  classification: {
    label?: string;
    class?: string;
    confidence: number;
    probabilities?: Record<string, number>;
    top_evidence?: string[];
    evidence_against?: string[];
    model_version?: string;
  };
  baseline?: {
    facility_id?: string;
    normal_detection_frequency_per_month?: number;
    normal_intensity_mean?: number;
    normal_intensity_std?: number;
    normal_active_hours?: number[];
    normal_spatial_extent_m?: number;
    baseline_period_days?: number;
    history_quality?: string;
  };
  deviation?: {
    frp_deviation_pct?: number;
    frequency_deviation_pct?: number;
    is_statistically_significant?: boolean;
  };
  anomaly?: {
    anomaly_score: number;
    is_abnormal: boolean;
    frp_zscore?: number;
    frequency_zscore?: number;
    spatial_shift_m?: number;
    confidence?: string;
  };
  industrial_likelihood: {
    score: number;
    tier?: string;
    component_scores?: Record<string, number>;
  };
  operational_risk: {
    risk_score: number;
    risk_level?: string;
    component_scores?: Record<string, number>;
  };
  scores?: { industrial_likelihood: number; operational_risk: number };
  evidence?: {
    evidence_for?: string[];
    evidence_against?: string[];
    missing_evidence?: string[];
  } | string[];
  alert?: {
    should_alert?: boolean;
    alert_type?: string;
    priority?: string;
    reasons?: string[];
  };
  analyst_review?: {
    reviewed: boolean;
    decision?: string;
    reclassified_label?: string;
    notes?: string;
    timestamp?: string;
    analyst_id?: string;
  };
  status: string;
  data_version?: string;
  model_version?: string;
  engine_version?: string;
  region?: string;
}

export interface EventsResponse {
  total: number;
  offset: number;
  limit: number;
  events: ThermoEvent[];
}

export interface SummaryResponse {
  total: number;
  total_anomalies?: number;
  critical?: number;
  high?: number;
  industrial?: number;
  persistent?: number;
  abnormal?: number;
  unknown?: number;
  requires_verification?: number;
  industrial_events?: number;
  persistent_sources?: number;
  abnormal_events?: number;
  unknown_events?: number;
  high_risk_count?: number;
  by_status?: Record<string, number>;
}

export interface AlertItem {
  alert_id: string;
  event_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  location: string;
  latitude: number;
  longitude: number;
  operational_risk: number;
  anomaly_score: number;
  confidence: number;
  reasons: string[];
  status: string;
  timestamp: string;
}

export type Alert = AlertItem;

export interface AlertsResponse {
  total: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  alerts: AlertItem[];
}

export interface Facility {
  facility_id: number;
  name: string;
  facility_type: string;
  lat: number;
  lon: number;
  capacity: string;
  operator: string;
  state?: string;
  distance_km?: number;
}

// ─── API Client Functions ───

export async function fetchEvents(params?: {
  status?: string;
  risk_min?: number;
  event_class?: string;
  limit?: number;
  region?: string;
}): Promise<EventsResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.risk_min !== undefined) query.set('risk_min', String(params.risk_min));
  if (params?.event_class) query.set('event_class', params.event_class);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.region) query.set('region', params.region);

  const qs = query.toString();
  return apiFetch<EventsResponse>(`/api/events/${qs ? '?' + qs : ''}`);
}

export async function fetchEventById(eventId: string): Promise<ThermoEvent> {
  return apiFetch<ThermoEvent>(`/api/events/${eventId}`);
}

export async function fetchEventTimeline(eventId: string): Promise<any> {
  return apiFetch(`/api/events/${eventId}/timeline`);
}

export async function fetchEventEvidence(eventId: string): Promise<any> {
  return apiFetch(`/api/events/${eventId}/evidence`);
}

export async function fetchSummary(region?: string): Promise<SummaryResponse> {
  const query = new URLSearchParams();
  if (region) query.set('region', region);
  const qs = query.toString();
  const res = await apiFetch<any>(`/api/events/summary${qs ? '?' + qs : ''}`);
  
  return {
    total: res.total_anomalies || res.total || 0,
    critical: res.high_risk_count || res.critical || 0,
    high: res.high || 0,
    industrial: res.industrial_events || res.industrial || 0,
    persistent: res.persistent_sources || res.persistent || 0,
    abnormal: res.abnormal_events || res.abnormal || 0,
    unknown: res.unknown_events || res.unknown || 0,
    requires_verification: res.requires_verification || 0,
    by_status: res.by_status || {},
  };
}

export async function fetchAlerts(severity?: string, region?: string): Promise<AlertsResponse> {
  const query = new URLSearchParams();
  if (severity) query.set('severity', severity);
  if (region) query.set('region', region);
  const qs = query.toString();
  return apiFetch<AlertsResponse>(`/api/alerts/${qs ? '?' + qs : ''}`);
}

export async function fetchFacilities(): Promise<{ total: number; facilities: Facility[] }> {
  return apiFetch('/api/facilities/');
}

export async function fetchNearbyFacilities(lat: number, lon: number, radiusKm = 25): Promise<{ total: number; facilities: Facility[] }> {
  return apiFetch(`/api/facilities/nearby?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`);
}

export async function verifyEvent(
  eventId: string,
  decision: string,
  reclassifiedLabel?: string,
  notes?: string
): Promise<any> {
  return apiFetch(`/api/events/${eventId}/verify`, {
    method: 'POST',
    body: {
      decision,
      reclassified_label: reclassifiedLabel,
      notes,
      analyst_id: 'ANALYST_LEAD_01'
    },
  });
}

export async function submitAnalystAction(
  eventId: string,
  action: string,
  notes?: string,
  newClass?: string
): Promise<any> {
  return verifyEvent(eventId, action.toUpperCase(), newClass, notes);
}

export async function reclassifyEvent(
  eventId: string,
  newClass: string,
  notes?: string
): Promise<any> {
  return verifyEvent(eventId, 'RECLASSIFIED', newClass, notes);
}

export function getReportUrl(eventId: string): string {
  return `${API_BASE}/api/reports/${eventId}`;
}

export async function fetchEventsFromJson(_region?: string): Promise<ThermoEvent[]> {
  const res = await fetchEvents();
  return res.events;
}
