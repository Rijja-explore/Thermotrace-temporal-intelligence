/**
 * Shared utility to dispatch alert emails automatically
 * to rijja2310119@ssn.edu.in when a critical thermal event or demo is run.
 */

const ALERT_EMAIL = 'rijja2310119@ssn.edu.in';
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Track which events we've already emailed about (per session)
const emailedEventIds = new Set<string>();

export interface AlertEmailPayload {
  eventId: string;
  facilityName: string;
  frpMw: number;
  riskScore: number;
  threatTier: 'CRITICAL' | 'HIGH' | 'MODERATE';
  hazardRadiusM?: number;
  customNotes?: string;
  forceSend?: boolean;
}

/**
 * Direct web dispatch to FormSubmit bridge for guaranteed inbox delivery.
 */
async function dispatchDirectWebBridge(payload: AlertEmailPayload): Promise<boolean> {
  try {
    const res = await fetch(`https://formsubmit.co/ajax/${ALERT_EMAIL}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        _subject: `[THERMOTRACE ${payload.threatTier} ALERT] Thermal Spike at ${payload.facilityName} (${payload.frpMw.toFixed(0)} MW)`,
        Event_ID: payload.eventId,
        Facility_Name: payload.facilityName,
        Thermal_Radiative_Power: `${payload.frpMw.toFixed(1)} MW`,
        Operational_Risk_Score: `${payload.riskScore.toFixed(0)}/100`,
        Threat_Classification: payload.threatTier,
        Thermal_Hazard_Radius: `${payload.hazardRadiusM ?? 250} meters`,
        Directive_and_SOP: payload.customNotes || 'Immediate FGRS valve diversion and deluge curtain engagement advised.',
        Recipient_Email: ALERT_EMAIL,
        Dispatch_Source: 'ThermoTrace Satellite GeoAI Defense Engine (SIH26162)',
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
 * Sends an alert email for a critical event or demo run.
 */
export async function sendAlertEmail(payload: AlertEmailPayload): Promise<boolean> {
  if (!payload.forceSend && emailedEventIds.has(payload.eventId)) return false;
  emailedEventIds.add(payload.eventId);

  // 1. Dispatch to Backend API
  let backendOk = false;
  try {
    const res = await fetch(`${API_BASE}/api/notifications/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipient_email: ALERT_EMAIL,
        recipient_name: 'ThermoTrace Admin / Evaluation Team',
        event_id: payload.eventId,
        facility_name: payload.facilityName,
        frp_mw: payload.frpMw,
        risk_score: payload.riskScore,
        threat_tier: payload.threatTier,
        hazard_radius_m: payload.hazardRadiusM ?? 250,
        custom_notes: payload.customNotes ?? 'Auto-dispatched by ThermoTrace real-time monitoring engine.',
      }),
    });
    backendOk = res.ok;
  } catch {
    backendOk = false;
  }

  // 2. Dispatch to Direct Web Mail Bridge for guaranteed inbox arrival
  const webOk = await dispatchDirectWebBridge(payload);

  return backendOk || webOk;
}

/**
 * Dispatches an automated email whenever the 3-minute Guided Demo is started.
 */
export async function dispatchDemoRunEmail(): Promise<boolean> {
  return sendAlertEmail({
    eventId: `TT-DEMO-RUN-${Date.now().toString().slice(-4)}`,
    facilityName: 'Jamnagar Mega Refinery Complex (Stack #4)',
    frpMw: 340.0,
    riskScore: 88.0,
    threatTier: 'CRITICAL',
    hazardRadiusM: 280,
    customNotes: 'Guided Demo Triggered: 340 MW thermal surge detected via NASA VIIRS pass. Automated inter-agency notification test dispatched.',
    forceSend: true,
  });
}

/**
 * Automatically sends emails for all critical events in a list.
 * Called from Dashboard on data load.
 */
export async function autoDispatchCriticalAlerts(
  events: Array<{ event_id: string; facility_context?: any; scores?: any; frp?: number; operational_risk?: any }>
): Promise<number> {
  const criticals = events.filter(e => {
    const risk = e.operational_risk?.risk_score ?? e.scores?.operational_risk ?? 0;
    return risk >= 75;
  });

  let sent = 0;
  for (const ev of criticals.slice(0, 2)) {
    const risk = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 0;
    const sent_ = await sendAlertEmail({
      eventId: ev.event_id,
      facilityName: ev.facility_context?.nearest_facility_name ?? ev.facility_context?.name ?? 'Jamnagar Refinery Complex',
      frpMw: ev.frp ?? 340.0,
      riskScore: risk,
      threatTier: risk >= 80 ? 'CRITICAL' : 'HIGH',
      hazardRadiusM: 240,
      customNotes: `Auto-detected by ThermoTrace pipeline. Operational risk: ${risk}/100. Requires immediate review.`,
    });
    if (sent_) sent++;
  }
  return sent;
}
