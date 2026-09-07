import React, { useState, useEffect, useMemo, useRef } from 'react';
import type {
  SimulationParams,
  SimulationResult,
  SimulationPreset,
} from '../services/api';
import {
  fetchSimulationPresets,
  runWhatIfSimulation,
  computeClientSimulation,
} from '../services/api';
import { useAuth } from '../services/AuthContext';
import { sendAlertEmail } from '../services/alertEmail';

interface WhatIfSimulatorProps {
  eventId?: string;
  onNavigate?: (page: string, params?: any) => void;
  onOpenNotificationModal?: (params?: any) => void;
}

export const WhatIfSimulator: React.FC<WhatIfSimulatorProps> = ({
  eventId,
  onNavigate,
  onOpenNotificationModal: _onOpenNotificationModal,
}) => {
  const { currentUser, addAuditLog } = useAuth();

  const [presets, setPresets] = useState<SimulationPreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('PRESET-JAMNAGAR-BLOWOUT');
  
  // Simulation Inputs
  const [facilityName, setFacilityName] = useState<string>('Jamnagar Mega Refinery Complex');
  const [baselineFRP, setBaselineFRP] = useState<number>(122.5);
  const [simulatedFRP, setSimulatedFRP] = useState<number>(340.0);
  const [durationHours, setDurationHours] = useState<number>(18.0);
  const [windSpeed, setWindSpeed] = useState<number>(18.0);
  const [windDirection, setWindDirection] = useState<number>(210.0);
  const [popDistance, setPopDistance] = useState<number>(2.2);
  const [atmosphericInversion, setAtmosphericInversion] = useState<boolean>(true);

  // Mitigation Handling Toggles ("How to handle it")
  const [mitigationFGRS, setMitigationFGRS] = useState<boolean>(false);
  const [mitigationDeluge, setMitigationDeluge] = useState<boolean>(false);
  const [mitigationESD, setMitigationESD] = useState<boolean>(false);
  const [mitigationEvac, setMitigationEvac] = useState<boolean>(false);
  const [mitigationUAV, setMitigationUAV] = useState<boolean>(false);

  // Results & Execution State
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [isExecutingSOP, setIsExecutingSOP] = useState<boolean>(false);
  const [sopExecutionStep, setSopExecutionStep] = useState<number>(0);
  const [sopCompleted, setSopCompleted] = useState<boolean>(false);
  const [exportedNotice, setExportedNotice] = useState<string | null>(null);
  const lastEmailedRiskRef = useRef<number>(0);

  // Load Presets
  useEffect(() => {
    async function loadPresets() {
      const p = await fetchSimulationPresets();
      setPresets(p);
    }
    loadPresets();
  }, []);

  // Preset switch handler
  const handleApplyPreset = (preset: SimulationPreset) => {
    setSelectedPresetId(preset.preset_id);
    setFacilityName(preset.facility_name);
    setBaselineFRP(preset.baseline_frp);
    setSimulatedFRP(preset.simulated_frp);
    setDurationHours(preset.duration_hours);
    setWindSpeed(preset.wind_speed_kmh);
    setWindDirection(preset.wind_direction_deg);
    setPopDistance(preset.population_distance_km);
    setAtmosphericInversion(preset.atmospheric_inversion);

    // Reset mitigations for fresh demonstration
    setMitigationFGRS(false);
    setMitigationDeluge(false);
    setMitigationESD(false);
    setMitigationEvac(false);
    setMitigationUAV(false);
    setSopCompleted(false);
    setSopExecutionStep(0);
  };

  // Run simulation whenever parameters or mitigations change
  useEffect(() => {
    const params: SimulationParams = {
      event_id: eventId || 'TT-CASE-SIM',
      facility_name: facilityName,
      baseline_frp: baselineFRP,
      simulated_frp: simulatedFRP,
      duration_hours: durationHours,
      wind_speed_kmh: windSpeed,
      wind_direction_deg: windDirection,
      population_distance_km: popDistance,
      atmospheric_inversion: atmosphericInversion,
      mitigation_fgrs: mitigationFGRS,
      mitigation_deluge: mitigationDeluge,
      mitigation_esd: mitigationESD,
      mitigation_evac: mitigationEvac,
      mitigation_uav: mitigationUAV,
    };

    // Calculate instantly on client for snappy 60fps UI feedback
    const res = computeClientSimulation(params);
    setResult(res);

    // Auto-email when simulated risk is high (and hasn't already been emailed at this tier)
    const simRisk = res.simulated_risk_score;
    if (simRisk >= 75 && simRisk > lastEmailedRiskRef.current + 5) {
      lastEmailedRiskRef.current = simRisk;
      sendAlertEmail({
        eventId: eventId || 'TT-SIM-' + Date.now(),
        facilityName: facilityName,
        frpMw: simulatedFRP,
        riskScore: simRisk,
        threatTier: simRisk >= 80 ? 'CRITICAL' : 'HIGH',
        hazardRadiusM: res.thermal_hazard_radius_m,
        customNotes: `Auto-dispatched from Incident Scenario Modeler. Simulated FRP: ${simulatedFRP} MW · Wind: ${windSpeed} km/h at ${windDirection}° · Duration: ${durationHours}h`,
      });
    }

    // Also dispatch to backend asynchronously
    runWhatIfSimulation(params).then(apiRes => {
      if (apiRes) setResult(apiRes);
    });
  }, [
    eventId,
    facilityName,
    baselineFRP,
    simulatedFRP,
    durationHours,
    windSpeed,
    windDirection,
    popDistance,
    atmosphericInversion,
    mitigationFGRS,
    mitigationDeluge,
    mitigationESD,
    mitigationEvac,
    mitigationUAV,
  ]);

  // Execute Automated SOP Sequence
  const handleExecuteSOP = () => {
    setIsExecutingSOP(true);
    setSopExecutionStep(1);
    setSopCompleted(false);

    // Step 1: Engage FGRS & Drone
    setTimeout(() => {
      setMitigationUAV(true);
      setMitigationFGRS(true);
      setSopExecutionStep(2);
      addAuditLog('SOP_EXECUTE_PHASE_1', 'Automated FGRS valve diversion and drone re-tasking initialized.');
    }, 900);

    // Step 2: Trigger Deluge
    setTimeout(() => {
      setMitigationDeluge(true);
      setSopExecutionStep(3);
      addAuditLog('SOP_EXECUTE_PHASE_2', 'Perimeter water deluge curtain engaged to limit radiant envelope.');
    }, 1800);

    // Step 3: Evacuation Advisory if risk > 50
    setTimeout(() => {
      if (simulatedFRP > 200 || popDistance < 2.0) {
        setMitigationEvac(true);
      }
      setSopExecutionStep(4);
      addAuditLog('SOP_EXECUTE_PHASE_3', 'Inter-agency CPCB and NDRF disaster advisory issued.');
    }, 2700);

    // Step 4: Finalize
    setTimeout(() => {
      setIsExecutingSOP(false);
      setSopCompleted(true);
      addAuditLog('SOP_EXECUTE_COMPLETE', 'Full emergency containment protocols successfully deployed.');
    }, 3400);
  };

  // Export Dossier
  const handleExportDossier = () => {
    if (!result) return;
    const dossier = {
      title: 'ThermoTrace What-If Counterfactual Simulation Dossier',
      generated_at: new Date().toISOString(),
      analyst: currentUser?.name || 'Authorized Lead Analyst',
      clearance: currentUser?.clearance_level || 'Level 4 Orbital',
      facility: facilityName,
      scenario: {
        baseline_frp_mw: baselineFRP,
        simulated_frp_mw: simulatedFRP,
        duration_hours: durationHours,
        wind_speed_kmh: windSpeed,
        wind_direction_deg: windDirection,
        population_distance_km: popDistance,
        atmospheric_inversion: atmosphericInversion,
      },
      mitigations_applied: {
        flare_gas_recovery_fgrs: mitigationFGRS,
        perimeter_deluge_injection: mitigationDeluge,
        emergency_plant_shutdown_esd: mitigationESD,
        downwind_evacuation_protocol: mitigationEvac,
        drone_uav_tasking: mitigationUAV,
      },
      outcomes: {
        baseline_risk: result.baseline_risk_score,
        unmitigated_simulated_risk: result.simulated_risk_score,
        mitigated_final_risk: result.mitigated_risk_score,
        risk_tier: result.risk_level,
        effective_frp_mw: result.effective_frp,
        thermal_hazard_radius_4_7kw_m: result.thermal_hazard_radius_m,
        public_safety_radius_1_6kw_m: result.public_safety_radius_m,
        plume_dispersion_length_km: result.plume_dispersion_length_km,
        mitigation_risk_reduction_pct: `${result.mitigation_impact_pct}%`,
      },
      recommended_sop: result.recommended_sop,
    };

    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ThermoTrace_Simulation_Dossier_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    setExportedNotice('Simulation dossier exported successfully as certified GeoAI incident briefing JSON.');
    setTimeout(() => setExportedNotice(null), 4000);
  };

  // Compass cardinal string
  const cardinalDirection = useMemo(() => {
    const val = Math.floor((windDirection / 45) + 0.5) % 8;
    const cardinals = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return cardinals[val];
  }, [windDirection]);

  return (
    <div className="what-if-page">
      {/* ─── Top Header & Controls ─── */}
      <div className="what-if-header">
        <div className="what-if-header__brand">
          <div className="what-if-header__icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div>
            <div className="what-if-header__title">
              INCIDENT SCENARIO MODELER
            </div>
            <div className="what-if-header__desc">
              Simulate industrial thermal flaring spikes, wind plume dispersion, and demonstrate emergency mitigation SOPs
            </div>
          </div>
        </div>

        <div className="what-if-header__actions">
          {eventId && (
            <div className="context-badge">
              <span>Origin Event:</span> <strong>{eventId}</strong>
            </div>
          )}
          <button className="btn btn--ghost btn--sm" onClick={handleExportDossier}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export Dossier
          </button>
          <button className="btn btn--outline btn--sm" onClick={() => onNavigate?.('dashboard')}>
            ← Command Center
          </button>
        </div>
      </div>

      {exportedNotice && (
        <div className="sim-export-banner">
          <span>✓</span> {exportedNotice}
        </div>
      )}

      {/* ─── Scenario Presets Toolbar ─── */}
      <div className="sim-presets-bar">
        <div className="sim-presets-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          1-Click Scenarios:
        </div>
        <div className="sim-presets-buttons">
          {presets.map(p => (
            <button
              key={p.preset_id}
              className={`preset-btn ${selectedPresetId === p.preset_id ? 'preset-btn--active' : ''}`}
              onClick={() => handleApplyPreset(p)}
              title={p.description}
            >
              {p.name.split('—')[0].trim()}
            </button>
          ))}
          <button
            className={`preset-btn ${selectedPresetId === 'CUSTOM' ? 'preset-btn--active' : ''}`}
            onClick={() => setSelectedPresetId('CUSTOM')}
          >
            Custom Sandbox
          </button>
        </div>
      </div>

      {/* ─── Main Grid: Left Controls (Inputs + Mitigations) | Right Radar & Outcomes ─── */}
      <div className="what-if-grid">

        {/* ─── LEFT COLUMN: Parameter Sliders & Active Mitigation Toggles ─── */}
        <div className="sim-panel sim-panel--controls">
          
          {/* Section 1: Target Anomaly Parameters */}
          <div className="sim-section">
            <div className="sim-section__header">
              <span className="sim-section__title">
                <span className="num-pill">1</span> Anomaly Telemetry & Meteorological Variables
              </span>
            </div>

            <div className="sim-control-group">
              <div className="sim-label-row">
                <span className="sim-label">Target Industrial Complex</span>
                <span className="sim-value-tag">{facilityName}</span>
              </div>
              <input
                type="text"
                className="sim-text-input"
                value={facilityName}
                onChange={e => setFacilityName(e.target.value)}
                placeholder="e.g. Jamnagar Refinery Complex"
              />
            </div>

            {/* Slider: Simulated FRP Spike */}
            <div className="sim-control-group">
              <div className="sim-label-row">
                <span className="sim-label">
                  Simulated Fire Radiative Power (FRP Spike)
                </span>
                <span className="sim-val text-amber">{simulatedFRP.toFixed(1)} MW</span>
              </div>
              <div className="sim-slider-container">
                <input
                  type="range"
                  min="20"
                  max="500"
                  step="5"
                  value={simulatedFRP}
                  onChange={e => setSimulatedFRP(parseFloat(e.target.value))}
                  className="sim-slider sim-slider--amber"
                />
                <div className="slider-ticks">
                  <span>20 MW (Nominal)</span>
                  <span className="baseline-marker">Baseline ({baselineFRP} MW)</span>
                  <span>500 MW (Blowout)</span>
                </div>
              </div>
            </div>

            {/* Slider: Duration */}
            <div className="sim-control-group">
              <div className="sim-label-row">
                <span className="sim-label">Persistence & Exposure Duration</span>
                <span className="sim-val">{durationHours.toFixed(0)} Hours</span>
              </div>
              <input
                type="range"
                min="1"
                max="48"
                step="1"
                value={durationHours}
                onChange={e => setDurationHours(parseFloat(e.target.value))}
                className="sim-slider"
              />
            </div>

            {/* Weather Split: Wind Speed & Direction */}
            <div className="sim-controls-row">
              <div className="sim-control-sub">
                <div className="sim-label-row">
                  <span className="sim-label">Wind Speed</span>
                  <span className="sim-val text-cyan">{windSpeed.toFixed(0)} km/h</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="80"
                  step="2"
                  value={windSpeed}
                  onChange={e => setWindSpeed(parseFloat(e.target.value))}
                  className="sim-slider sim-slider--cyan"
                />
              </div>

              <div className="sim-control-sub">
                <div className="sim-label-row">
                  <span className="sim-label">Wind Vector</span>
                  <span className="sim-val text-cyan">{windDirection.toFixed(0)}° ({cardinalDirection})</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="360"
                  step="10"
                  value={windDirection}
                  onChange={e => setWindDirection(parseFloat(e.target.value))}
                  className="sim-slider sim-slider--cyan"
                />
              </div>
            </div>

            {/* Settlement Distance */}
            <div className="sim-control-group">
              <div className="sim-label-row">
                <span className="sim-label">Proximity to Closest Residential Settlement</span>
                <span className="sim-val text-red">{popDistance.toFixed(1)} km</span>
              </div>
              <input
                type="range"
                min="0.3"
                max="12.0"
                step="0.1"
                value={popDistance}
                onChange={e => setPopDistance(parseFloat(e.target.value))}
                className="sim-slider sim-slider--red"
              />
            </div>

            {/* Thermal Inversion Toggle */}
            <div className="sim-toggle-row">
              <div>
                <div className="toggle-title">Atmospheric Night Inversion Layer</div>
                <div className="toggle-desc">Traps emissions close to ground surface, amplifying downwind hazard plume</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={atmosphericInversion}
                  onChange={e => setAtmosphericInversion(e.target.checked)}
                />
                <span className="slider-round" />
              </label>
            </div>

          </div>

          {/* Section 2: Active Mitigation Protocols ("How to handle it") */}
          <div className="sim-section sim-section--mitigations">
            <div className="sim-section__header">
              <span className="sim-section__title">
                <span className="num-pill num-pill--green">2</span> How to Handle It: Active Mitigation Protocols
              </span>
              <span className="sim-section__sub">Engage control measures to reduce threat envelope</span>
            </div>

            <div className="mitigation-options">
              
              {/* Mitigation 1: Flare Gas Recovery (FGRS) */}
              <div className={`mitigation-card ${mitigationFGRS ? 'mitigation-card--active' : ''}`}>
                <div className="mitigation-card__left">
                  <input
                    type="checkbox"
                    id="fgrs"
                    checked={mitigationFGRS}
                    onChange={e => setMitigationFGRS(e.target.checked)}
                  />
                  <label htmlFor="fgrs" className="mitigation-info">
                    <div className="mitigation-name">Flare Gas Recovery System (FGRS) Diversion</div>
                    <div className="mitigation-desc">Diverts surplus gas to compression units; suppresses flaring heat release by 45%.</div>
                  </label>
                </div>
                <div className="mitigation-impact text-green">-45% FRP</div>
              </div>

              {/* Mitigation 2: Deluge Injection */}
              <div className={`mitigation-card ${mitigationDeluge ? 'mitigation-card--active' : ''}`}>
                <div className="mitigation-card__left">
                  <input
                    type="checkbox"
                    id="deluge"
                    checked={mitigationDeluge}
                    onChange={e => setMitigationDeluge(e.target.checked)}
                  />
                  <label htmlFor="deluge" className="mitigation-info">
                    <div className="mitigation-name">High-Pressure Water Curtain & Nitrogen Deluge</div>
                    <div className="mitigation-desc">Deploys perimeter water atomizers to shield adjacent infrastructure and quench radiation.</div>
                  </label>
                </div>
                <div className="mitigation-impact text-green">-25% Rad</div>
              </div>

              {/* Mitigation 3: Emergency Plant Shutdown (ESD) */}
              <div className={`mitigation-card ${mitigationESD ? 'mitigation-card--active' : ''}`}>
                <div className="mitigation-card__left">
                  <input
                    type="checkbox"
                    id="esd"
                    checked={mitigationESD}
                    onChange={e => setMitigationESD(e.target.checked)}
                  />
                  <label htmlFor="esd" className="mitigation-info">
                    <div className="mitigation-name">Emergency Unit Depressurization (ESD-1)</div>
                    <div className="mitigation-desc">Immediate automated feed throttling to flare stack header for rapid cooldown.</div>
                  </label>
                </div>
                <div className="mitigation-impact text-green">-35% Feed</div>
              </div>

              {/* Mitigation 4: Evacuation Advisory */}
              <div className={`mitigation-card ${mitigationEvac ? 'mitigation-card--active' : ''}`}>
                <div className="mitigation-card__left">
                  <input
                    type="checkbox"
                    id="evac"
                    checked={mitigationEvac}
                    onChange={e => setMitigationEvac(e.target.checked)}
                  />
                  <label htmlFor="evac" className="mitigation-info">
                    <div className="mitigation-name">Public Shelter-in-Place & Downwind Evacuation</div>
                    <div className="mitigation-desc">Dispatches automated siren broadcast to local communities within the calculated plume zone.</div>
                  </label>
                </div>
                <div className="mitigation-impact text-green">-75% Pop Risk</div>
              </div>

              {/* Mitigation 5: UAV Drone Verification */}
              <div className={`mitigation-card ${mitigationUAV ? 'mitigation-card--active' : ''}`}>
                <div className="mitigation-card__left">
                  <input
                    type="checkbox"
                    id="uav"
                    checked={mitigationUAV}
                    onChange={e => setMitigationUAV(e.target.checked)}
                  />
                  <label htmlFor="uav" className="mitigation-info">
                    <div className="mitigation-name">Automated Thermal Drone (UAV) & Sentinel Tasking</div>
                    <div className="mitigation-desc">Ground-truth optical and FLIR verification for high-confidence situational telemetry.</div>
                  </label>
                </div>
                <div className="mitigation-impact text-cyan">99% Conf</div>
              </div>

            </div>

            {/* Quick Demonstration Action Button */}
            <div className="sim-action-banner">
              <button
                className={`btn btn--block ${sopCompleted ? 'btn--outline' : 'btn--cyan'}`}
                onClick={handleExecuteSOP}
                disabled={isExecutingSOP}
              >
                {isExecutingSOP ? (
                  <>
                    <span className="spinner-small" /> Executing SOP Step {sopExecutionStep} of 4...
                  </>
                ) : sopCompleted ? (
                  '✓ All Mitigations Deployed (Click to Re-run SOP)'
                ) : (
                  '⚡ Trigger Automated Response SOP (Execute All)'
                )}
              </button>
            </div>

          </div>

        </div>

        {/* ─── RIGHT COLUMN: Results Dashboard, Dynamic Radar Plume Canvas & SOP ─── */}
        <div className="sim-panel sim-panel--results">
          
          {/* Comparative Metrics Scorecard */}
          {result && (
            <div className="sim-scorecard-grid">
              
              {/* Card 1: Risk Delta */}
              <div className="sim-metric-card">
                <div className="sim-metric-label flex items-center justify-between">
                  <span>Operational Risk Score</span>
                  <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '1px 5px', borderRadius: '3px', background: 'rgba(167,139,250,0.15)', color: '#A78BFA' }}>
                    SIMULATED
                  </span>
                </div>
                <div className="sim-metric-split">
                  <div className="metric-col">
                    <span className="sub-title">Simulated</span>
                    <span className="metric-val text-red">{result.simulated_risk_score}</span>
                  </div>
                  <div className="metric-arrow">➔</div>
                  <div className="metric-col">
                    <span className="sub-title">Mitigated</span>
                    <span className="metric-val text-green">{result.mitigated_risk_score}</span>
                  </div>
                </div>
                <div className="sim-metric-sub">
                  Baseline was <strong>{result.baseline_risk_score}</strong> / 100
                </div>
              </div>

              {/* Card 2: Risk Tier & Incident Priority */}
              <div className="sim-metric-card">
                <div className="sim-metric-label">Threat Tier & Incident Priority</div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', margin: '4px 0' }}>
                  <div className={`threat-badge threat-badge--${result.risk_level.toLowerCase()}`}>
                    {result.risk_level}
                  </div>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 800, padding: '2px 8px', borderRadius: '4px', background: result.risk_level === 'CRITICAL' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)', color: result.risk_level === 'CRITICAL' ? '#FF5C6C' : '#F59E0B' }}>
                    PRIORITY: {result.risk_level}
                  </span>
                </div>
                <div className="sim-metric-sub">
                  Mitigation reduced risk by <strong>{result.mitigation_impact_pct}%</strong>
                </div>
              </div>

              {/* Card 3: Baseline Deviation & Escalation */}
              <div className="sim-metric-card">
                <div className="sim-metric-label">Baseline Deviation & Escalation</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <div className="metric-val text-amber">
                    +{((result.effective_frp - baselineFRP) / 18.5).toFixed(1)}σ
                  </div>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: result.effective_frp > baselineFRP * 2 ? '#FF5C6C' : '#F59E0B' }}>
                    {result.effective_frp > baselineFRP * 2 ? 'CRITICAL ESCALATION' : result.effective_frp > baselineFRP * 1.3 ? 'ESCALATING' : 'STABLE'}
                  </span>
                </div>
                <div className="sim-metric-sub">
                  Effective FRP: <strong>{result.effective_frp} MW</strong> (Base: {baselineFRP} MW)
                </div>
              </div>

              {/* Card 4: Plume Dispersion & Radiant Radius */}
              <div className="sim-metric-card">
                <div className="sim-metric-label">Hazard Radius & Plume</div>
                <div className="metric-val text-cyan">{result.thermal_hazard_radius_m}m / {result.plume_dispersion_length_km} km</div>
                <div className="sim-metric-sub">
                  Heading {windDirection}° ({cardinalDirection}) at {windSpeed} km/h
                </div>
              </div>

            </div>
          )}

          {/* Dynamic Radar Canvas / Plume Visualizer */}
          <div className="sim-radar-card">
            <div className="sim-radar-card__header">
              <span className="radar-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                Dynamic Thermal Radiation & Plume Dispersion Envelope
              </span>
              <span className="radar-legend">
                <span className="legend-dot legend-dot--red" /> 4.7 kW/m² Hazard
                <span className="legend-dot legend-dot--cyan" /> Smoke Plume Cone
                <span className="legend-dot legend-dot--yellow" /> Residential Settlement
              </span>
            </div>

            <div className="sim-radar-viewport">
              <svg
                viewBox="0 0 500 320"
                className="radar-svg"
                preserveAspectRatio="xMidYMid meet"
              >
                {/* Background Compass Rings */}
                <circle cx="250" cy="160" r="130" fill="none" stroke="#233B56" strokeWidth="1" strokeDasharray="3 3" />
                <circle cx="250" cy="160" r="90" fill="none" stroke="#233B56" strokeWidth="1" strokeDasharray="2 2" />
                <circle cx="250" cy="160" r="50" fill="none" stroke="#233B56" strokeWidth="1" />
                
                {/* Crosshairs */}
                <line x1="250" y1="20" x2="250" y2="300" stroke="#1A304A" strokeWidth="1" />
                <line x1="110" y1="160" x2="390" y2="160" stroke="#1A304A" strokeWidth="1" />

                {/* Compass Labels */}
                <text x="250" y="18" fill="#71869B" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">N</text>
                <text x="395" y="164" fill="#71869B" fontSize="10" textAnchor="start" fontFamily="var(--font-mono)">E</text>
                <text x="250" y="312" fill="#71869B" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">S</text>
                <text x="105" y="164" fill="#71869B" fontSize="10" textAnchor="end" fontFamily="var(--font-mono)">W</text>

                {/* Wind Driven Dispersion Plume Cone */}
                {result && (
                  <g
                    transform={`rotate(${windDirection - 90}, 250, 160)`}
                    opacity="0.45"
                  >
                    {/* Plume Triangle */}
                    <path
                      d={`M 250 160 L ${250 + Math.min(220, result.plume_dispersion_length_km * 35)} ${160 - Math.min(65, windSpeed * 0.9)} L ${250 + Math.min(220, result.plume_dispersion_length_km * 35)} ${160 + Math.min(65, windSpeed * 0.9)} Z`}
                      fill="url(#plumeGrad)"
                    />
                  </g>
                )}

                {/* 1.6 kW/m2 Public Safety Radius Circle */}
                {result && (
                  <circle
                    cx="250"
                    cy="160"
                    r={Math.max(25, Math.min(125, result.public_safety_radius_m * 0.18))}
                    fill="rgba(255, 181, 71, 0.08)"
                    stroke="#FFB547"
                    strokeWidth="1.2"
                    strokeDasharray="4 2"
                  />
                )}

                {/* 4.7 kW/m2 Hazard Radius Circle */}
                {result && (
                  <circle
                    cx="250"
                    cy="160"
                    r={Math.max(12, Math.min(90, result.thermal_hazard_radius_m * 0.18))}
                    fill="rgba(255, 92, 108, 0.22)"
                    stroke="#FF5C6C"
                    strokeWidth="1.8"
                  />
                )}

                {/* Center Facility Centroid Pulse */}
                <circle cx="250" cy="160" r="7" fill="#FF7A45" className="pulse-center" />
                <circle cx="250" cy="160" r="3" fill="#FFFFFF" />
                <text x="250" y="180" fill="#F4F8FC" fontSize="11" fontWeight="600" textAnchor="middle">
                  {facilityName.split('—')[0].trim().slice(0, 22)}
                </text>

                {/* Residential Settlement Marker */}
                {(() => {
                  // Place residential marker along azimuth
                  const rad = ((windDirection + 15) * Math.PI) / 180;
                  const distPx = Math.min(130, Math.max(50, popDistance * 20));
                  const popX = 250 + Math.sin(rad) * distPx;
                  const popY = 160 - Math.cos(rad) * distPx;
                  return (
                    <g transform={`translate(${popX}, ${popY})`}>
                      <rect x="-8" y="-8" width="16" height="16" rx="3" fill="#FFB547" opacity="0.9" />
                      <text x="0" y="3" fill="#07111F" fontSize="9" fontWeight="bold" textAnchor="middle">🏘</text>
                      <text x="0" y="18" fill="#FFB547" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">
                        {popDistance.toFixed(1)}km
                      </text>
                    </g>
                  );
                })()}

                {/* Gradients */}
                <defs>
                  <linearGradient id="plumeGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#43D9E8" stopOpacity="0.8" />
                    <stop offset="70%" stopColor="#4D8DFF" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#A78BFA" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>

          {/* Recommended SOP Playbook Steps */}
          {result && (
            <div className="sim-sop-card">
              <div className="sim-sop-header">
                <span className="sop-title">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 11 12 14 22 4" />
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                  </svg>
                  Operational Standard Operating Procedure (SOP) Checklist
                </span>
                <span className="sop-sub">Standard Incident Handling Protocol</span>
              </div>

              <div className="sop-steps-list">
                {result.recommended_sop.map(step => (
                  <div
                    key={step.step}
                    className={`sop-step-item sop-step-item--${step.status.toLowerCase()}`}
                  >
                    <div className="sop-step-number">{step.step}</div>
                    <div className="sop-step-content">
                      <div className="sop-step-top">
                        <span className="sop-step-title">{step.title}</span>
                        <span className={`sop-urgency-badge sop-urgency-badge--${step.urgency.toLowerCase()}`}>
                          {step.urgency}
                        </span>
                      </div>
                      <div className="sop-step-agency">Responsible Agency: {step.agency}</div>
                      <div className="sop-step-action">{step.action}</div>
                    </div>
                    <div className="sop-step-status">
                      <span className={`status-tag status-tag--${step.status.toLowerCase()}`}>
                        {step.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};

export default WhatIfSimulator;
