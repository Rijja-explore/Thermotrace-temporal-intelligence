/**
 * ThermoTrace Dual-Tier Alert Email Engine
 *
 * Routing Policy:
 * 1. When an event occurs (new anomaly / surge / auto-ingestion):
 *    -> Dispatches technical investigation dossier to ANALYST (anagesh2410198@ssn.edu.in / anagesh842005@gmail.com)
 * 2. When the analyst confirms / validates the event or triggers SOP:
 *    -> Dispatches emergency directive notice to INCIDENT COMMAND OFFICIAL (rijja2310119@ssn.edu.in)
 */

export const RECIPIENT_ANALYST = 'anagesh842005@gmail.com'; // Primary verified inbox for analyst alerts
export const RECIPIENT_ANALYST_INSTITUTIONAL = 'anagesh2410198@ssn.edu.in';
export const RECIPIENT_OFFICIAL = 'rijja2310119@ssn.edu.in'; // Official Incident Commander

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Track dispatched event IDs to prevent duplicate spamming within the same session
const emailedEventIds = new Set<string>();

export interface AlertEmailPayload {
  eventId: string;
  facilityName: string;
  frpMw: number;
  riskScore: number;
  threatTier: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'CONFIRMED';
  hazardRadiusM?: number;
  plumeCorridor?: string;
  populationExposure?: number;
  customNotes?: string;
  targetRole?: 'ANALYST' | 'OFFICIAL' | 'AUTO';
  recipientEmail?: string;
  forceSend?: boolean;
}

/**
 * Direct web dispatch to FormSubmit bridge for guaranteed real inbox arrival.
 */
async function dispatchDirectWebBridge(targetEmail: string, subject: string, data: Record<string, any>): Promise<boolean> {
  try {
    const res = await fetch(`https://formsubmit.co/ajax/${targetEmail}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        _subject: subject,
        ...data,
        Recipient: targetEmail,
        System_Source: 'ThermoTrace Spaceborne Thermal Intelligence Platform (SIH26162)',
        Timestamp: new Date().toISOString(),
        _captcha: 'false',
        _template: 'table',
      }),
    });
    return res.ok;
  } catch (err) {
    console.warn('[Direct Web Mail Bridge] Note:', err);
    return false;
  }
}

/**
 * Dispatches an investigation dossier to the ANALYST when an event occurs.
 */
export async function dispatchAnalystEventEmail(payload: AlertEmailPayload): Promise<boolean> {
  const cacheKey = `analyst-${payload.eventId}`;
  if (!payload.forceSend && emailedEventIds.has(cacheKey)) return false;
  emailedEventIds.add(cacheKey);

  const targetEmail = payload.recipientEmail || RECIPIENT_ANALYST;
  const subject = `[THERMOTRACE ANALYST ALERT] New Anomaly Detected at ${payload.facilityName} (${payload.frpMw.toFixed(0)} MW)`;

  // 1. Dispatch to Backend API
  let backendOk = false;
  try {
    const res = await fetch(`${API_BASE}/api/notifications/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_id: payload.eventId,
        facility_name: payload.facilityName,
        frp_mw: payload.frpMw,
        risk_score: payload.riskScore,
        threat_tier: payload.threatTier === 'CONFIRMED' ? 'HIGH' : payload.threatTier,
        hazard_radius_m: payload.hazardRadiusM ?? 240,
        target_override_email: targetEmail,
        custom_notes: payload.customNotes || 'New high-risk thermal anomaly isolated by HistGradientBoosting + LSTM pipeline. Analyst verification requested.',
      }),
    });
    backendOk = res.ok;
  } catch {
    backendOk = false;
  }

  // 2. Dispatch via direct web mail bridge for guaranteed real inbox delivery
  const webOk = await dispatchDirectWebBridge(targetEmail, subject, {
    Notification_Type: 'ANALYST INVESTIGATION BRIEF',
    Event_ID: payload.eventId,
    Target_Facility: payload.facilityName,
    Observed_FRP: `${payload.frpMw.toFixed(1)} MW`,
    Operational_Risk_Score: `${payload.riskScore.toFixed(0)}/100`,
    Action_Required: 'Verify satellite observations, review SHAP feature attribution & LSTM projection, and execute confirmation in ThermoTrace.',
    Investigation_Portal: 'https://thermotrace.vercel.app',
  });

  return backendOk || webOk;
}

/**
 * Dispatches an emergency response directive to the OFFICIAL when the Analyst CONFIRMS an event.
 */
export async function dispatchOfficialConfirmedEmail(payload: AlertEmailPayload): Promise<boolean> {
  const cacheKey = `official-${payload.eventId}`;
  if (!payload.forceSend && emailedEventIds.has(cacheKey)) return false;
  emailedEventIds.add(cacheKey);

  const targetEmail = payload.recipientEmail || RECIPIENT_OFFICIAL;
  const subject = `[THERMOTRACE OFFICIAL DIRECTIVE] Confirmed Incident at ${payload.facilityName} (${payload.eventId})`;

  // 1. Dispatch to Backend API
  let backendOk = false;
  try {
    const res = await fetch(`${API_BASE}/api/notifications/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_id: payload.eventId,
        facility_name: payload.facilityName,
        frp_mw: payload.frpMw,
        risk_score: payload.riskScore,
        threat_tier: 'CONFIRMED',
        hazard_radius_m: payload.hazardRadiusM ?? 350,
        plume_corridor: payload.plumeCorridor || '8.6 km NE',
        population_exposure: payload.populationExposure || 123,
        target_override_email: targetEmail,
        custom_notes: payload.customNotes || 'Analyst has verified and confirmed high-severity industrial thermal excursion. Immediate emergency response directive issued.',
      }),
    });
    backendOk = res.ok;
  } catch {
    backendOk = false;
  }

  // 2. Dispatch via direct web mail bridge for real inbox delivery
  const webOk = await dispatchDirectWebBridge(targetEmail, subject, {
    Notification_Type: '🚨 OFFICIAL EMERGENCY RESPONSE DIRECTIVE',
    Incident_Reference: payload.eventId,
    Confirmed_Facility: payload.facilityName,
    Peak_Thermal_Power: `${payload.frpMw.toFixed(1)} MW`,
    Calculated_Hazard_Perimeter: `${payload.hazardRadiusM ?? 350} meters (API 521)`,
    Atmospheric_Plume_Corridor: payload.plumeCorridor || '8.6 km NE corridor',
    Estimated_Population_Exposure: `${payload.populationExposure ?? 123} residents`,
    Recommended_SOP: payload.customNotes || '1. Alert facility safety officer. 2. Activate Flare Gas Recovery (FGRS) diversion. 3. Establish 350m safety cordon. 4. Stand by CPCB & NDRF response units.',
    Incident_Command_Console: 'https://thermotrace.vercel.app',
  });

  return backendOk || webOk;
}

/**
 * Legacy wrapper: sends appropriate email based on threat tier & role
 */
export async function sendAlertEmail(payload: AlertEmailPayload): Promise<boolean> {
  if (payload.threatTier === 'CONFIRMED' || payload.targetRole === 'OFFICIAL') {
    return dispatchOfficialConfirmedEmail(payload);
  } else {
    return dispatchAnalystEventEmail(payload);
  }
}

/**
 * Dispatches an automated email whenever the 3-minute Guided Demo is started.
 */
export async function dispatchDemoRunEmail(): Promise<boolean> {
  // Dispatches investigation brief to Analyst and operational test directive to Official
  const p1 = dispatchAnalystEventEmail({
    eventId: `TT-DEMO-RUN-${Date.now().toString().slice(-4)}`,
    facilityName: 'Jamnagar Mega Refinery Complex (Stack #4)',
    frpMw: 340.0,
    riskScore: 88.0,
    threatTier: 'CRITICAL',
    hazardRadiusM: 280,
    customNotes: 'Guided Demo Triggered: 340 MW thermal surge detected via NASA VIIRS pass. Automated inter-agency notification test dispatched.',
    forceSend: true,
  });

  const p2 = dispatchOfficialConfirmedEmail({
    eventId: `TT-DEMO-RUN-${Date.now().toString().slice(-4)}`,
    facilityName: 'Jamnagar Mega Refinery Complex (Stack #4)',
    frpMw: 340.0,
    riskScore: 88.0,
    threatTier: 'CONFIRMED',
    hazardRadiusM: 350,
    customNotes: 'Demonstration Emergency Protocol: Incident verified. Deluge curtains & FGRS diversion directives issued.',
    forceSend: true,
  });

  const [res1, res2] = await Promise.all([p1, p2]);
  return res1 || res2;
}

/**
 * Automatically sends analyst emails for all critical events in a list on initial load.
 */
export async function autoDispatchCriticalAlerts(
  events: Array<{ event_id: string; facility_context?: any; scores?: any; frp?: number; operational_risk?: any }>
): Promise<number> {
  const criticals = events.filter(e => {
    const risk = e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0;
    return risk >= 80;
  });

  let sent = 0;
  for (const ev of criticals.slice(0, 2)) {
    const risk = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 0;
    const ok = await dispatchAnalystEventEmail({
      eventId: ev.event_id,
      facilityName: ev.facility_context?.nearest_facility_name ?? ev.facility_context?.name ?? 'Jamnagar Refinery Complex',
      frpMw: ev.frp ?? 340.0,
      riskScore: risk,
      threatTier: 'CRITICAL',
      hazardRadiusM: 240,
      customNotes: `Auto-detected by ThermoTrace real-time pipeline. Risk: ${risk}/100. Verification required.`,
    });
    if (ok) sent++;
  }
  return sent;
}

