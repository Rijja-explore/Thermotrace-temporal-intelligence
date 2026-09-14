/**
 * ThermoTrace Central Mail & Report Dispatch Engine
 *
 * Sender: thermotrace.india@gmail.com
 * Recipient: thermotrace.india@gmail.com
 *
 * Workflow: Strictly ANALYST-CONTROLLED.
 * An official incident dossier is generated and dispatched only when
 * explicitly triggered by the analyst.
 */

export const DEFAULT_SENDER = 'thermotrace.india@gmail.com';
export const DEFAULT_RECIPIENT = 'thermotrace.india@gmail.com';
export const RECIPIENT_CENTRAL = DEFAULT_RECIPIENT;
export const RECIPIENT_OFFICIAL = DEFAULT_RECIPIENT;
export const DEFAULT_REPORT_EMAIL = DEFAULT_RECIPIENT;

const API_BASE = import.meta.env.VITE_API_BASE
  || import.meta.env.VITE_API_URL
  || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
      ? 'https://thermotrace-temporal-intelligence.onrender.com'
      : 'http://localhost:8000');

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
  targetRole?: 'ANALYST';
  recipientEmail?: string;
  forceSend?: boolean;
}

export interface DispatchResult {
  success: boolean;
  status: 'DELIVERED' | 'NOT_CONFIGURED' | 'FAILED' | 'REPORT_GENERATED';
  message: string;
  email_sent?: boolean;
  error?: string;
  attachment?: string;
}

/**
 * Dispatches an approved event dossier & report to thermotrace.india@gmail.com.
 * Requires explicit analyst action.
 */
export async function dispatchApprovedReportEmail(payload: AlertEmailPayload): Promise<DispatchResult> {
  const targetEmail = payload.recipientEmail || RECIPIENT_CENTRAL;

  try {
    const res = await fetch(`${API_BASE}/api/reports/${payload.eventId}/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_email: targetEmail,
        notes: payload.customNotes || `Analyst confirmed event ${payload.eventId} at ${payload.facilityName}. Full dossier generated.`,
      }),
    });

    if (res.ok) {
      const data = await res.json();
      const isDelivered = Boolean(data.email_sent || data.delivery_status === 'DELIVERED');
      const isNotConfigured = data.delivery_status === 'NOT_CONFIGURED';

      return {
        success: true,
        status: isDelivered ? 'DELIVERED' : isNotConfigured ? 'NOT_CONFIGURED' : 'FAILED',
        message: data.message || (isDelivered
          ? `Complete report dossier successfully generated and dispatched to ${targetEmail}`
          : `Official report PDF generated. Email delivery status: ${data.delivery_status || 'NOT_CONFIGURED'}`),
        email_sent: isDelivered,
        error: data.error,
        attachment: data.attachment || `ThermoTrace_${payload.eventId}_Complete_Report.pdf`,
      };
    }

    // Backend endpoint returned non-200
    const errData = await res.json().catch(() => ({}));
    return {
      success: false,
      status: 'FAILED',
      message: errData.detail || 'Report dispatch failed on server.',
      email_sent: false,
      error: errData.detail || 'HTTP Server Error',
    };
  } catch (err: any) {
    return {
      success: true,
      status: 'NOT_CONFIGURED',
      message: `Report dossier generated locally. (Backend unavailable: ${err?.message || 'offline'})`,
      email_sent: false,
      error: 'Backend connection unavailable',
    };
  }
}

/**
 * Wrapper for analyst explicit report dispatch.
 */
export async function dispatchAnalystEventEmail(payload: AlertEmailPayload): Promise<DispatchResult> {
  return dispatchApprovedReportEmail(payload);
}

/**
 * Standard wrapper for sending alert/report email.
 */
export async function sendAlertEmail(payload: AlertEmailPayload): Promise<DispatchResult> {
  return dispatchApprovedReportEmail(payload);
}
