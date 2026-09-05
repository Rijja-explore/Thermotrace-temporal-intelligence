/**
 * ThermoTrace API Client
 * Handles all communication with the FastAPI backend.
 * Falls back to local JSON when backend is unavailable.
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
    console.warn(`[API] ${path} failed, falling back to local data:`, err);
    throw err;
  }
}

// ─── Event Types ───
export interface ThermoEvent {
  event_id: string;
  geometry: { lat: number; lon: number };
  time_window: { start: string; end: string };
  observations: Array<{ frp: number; satellite: string; acq_date?: string }>;
  facility_context: {
    nearby_refinery_km?: number;
    name?: string;
    land_cover?: string;
    population_within_5km?: number;
  };
  landcover_context: Record<string, string>;
  temporal_features: {
    baseline_frp_mean?: number;
    baseline_frp_std?: number;
    current_frp?: number;
    deviation_sigma?: number;
    detection_count_30d?: number;
    persistence_ratio?: number;
  };
  classification: { class: string; confidence: number };
  scores: { industrial_likelihood: number; operational_risk: number };
  evidence: string[];
  status: string;
  data_version: string;
  model_version: string;
  satellite?: string;
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
  critical: number;
  high: number;
  industrial: number;
  persistent: number;
  abnormal: number;
  unknown: number;
  requires_verification: number;
  by_status: Record<string, number>;
}

export interface Alert {
  alert_id: string;
  event_id: string;
  severity: 'critical' | 'high' | 'medium';
  title: string;
  location: string;
  lat: number;
  lon: number;
  operational_risk: number;
  confidence: number;
  reasons: string[];
  status: string;
  timestamp: string;
}

export interface AlertsResponse {
  total: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  alerts: Alert[];
}

export interface Facility {
  facility_id: number;
  name: string;
  facility_type: string;
  lat: number;
  lon: number;
  capacity: string;
  operator: string;
  distance_km?: number;
}

// ─── API Functions ───

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
  query.set('region', params?.region || 'India');

  const qs = query.toString();
  return apiFetch<EventsResponse>(`/api/events/${qs ? '?' + qs : ''}`);
}

export async function fetchEventById(eventId: string): Promise<ThermoEvent> {
  return apiFetch<ThermoEvent>(`/api/events/${eventId}`);
}

export async function fetchSummary(region: string = 'India'): Promise<SummaryResponse> {
  const qs = region ? `?region=${encodeURIComponent(region)}` : '';
  return apiFetch<SummaryResponse>(`/api/events/summary${qs}`);
}

export async function fetchAlerts(severity?: string, region: string = 'India'): Promise<AlertsResponse> {
  const query = new URLSearchParams();
  if (severity) query.set('severity', severity);
  if (region) query.set('region', region);
  const qs = query.toString();
  return apiFetch<AlertsResponse>(`/api/alerts/${qs ? '?' + qs : ''}`);
}

export async function fetchFacilities(): Promise<{ total: number; facilities: Facility[] }> {
  return apiFetch('/api/facilities/');
}

export async function fetchNearbyFacilities(lat: number, lon: number, radiusKm = 10): Promise<{ total: number; facilities: Facility[] }> {
  return apiFetch(`/api/facilities/nearby?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`);
}

export async function submitAnalystAction(
  eventId: string,
  action: string,
  notes?: string,
  newClass?: string
): Promise<any> {
  return apiFetch(`/api/events/${eventId}/action`, {
    method: 'POST',
    body: {
      action,
      notes,
      new_class: newClass,
      analyst: 'demo-analyst',
    },
  });
}

export function getReportUrl(eventId: string): string {
  return `${API_BASE}/api/reports/${eventId}`;
}

/**
 * Fallback: Load events directly from the static JSON file
 * (used when the backend API is unavailable)
 */
export async function fetchEventsFromJson(region: string = 'India'): Promise<ThermoEvent[]> {
  try {
    const res = await fetch('/firms_data.json');
    if (!res.ok) throw new Error('No local data');
    const all: ThermoEvent[] = await res.json();

    if (!region || region.toLowerCase() === 'all') {
      return all;
    }

    const reg = region.trim().toLowerCase();
    return all.filter((e) => {
      const lat = e.geometry?.lat ?? 0;
      const lon = e.geometry?.lon ?? 0;
      const isIndiaCoords = lat >= 6.0 && lat <= 38.0 && lon >= 68.0 && lon <= 98.0;
      const eventRegion = (e.region || (isIndiaCoords || e.event_id?.startsWith('TT-IND-') ? 'India' : 'Global')).toLowerCase();

      if (reg === 'india') {
        return eventRegion === 'india';
      }
      if (reg === 'global') {
        return eventRegion !== 'india';
      }
      // Check state or facility name match
      const facName = (e.facility_context?.name || '').toLowerCase();
      const facState = ((e.facility_context as any)?.state || '').toLowerCase();
      return eventRegion === 'india' && (facState.includes(reg) || facName.includes(reg));
    });
  } catch {
    return [];
  }
}
