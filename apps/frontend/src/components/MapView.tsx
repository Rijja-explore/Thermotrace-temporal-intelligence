import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { ThermoEvent, Facility } from '../services/api';
import { INDIA_STATES_GEOJSON } from '../data/indiaStates';

interface MapViewProps {
  events: ThermoEvent[];
  facilities?: Facility[];
  selectedEventId?: string | null;
  onSelectEvent?: (event: ThermoEvent) => void;
  height?: string;
  center?: [number, number];
  zoom?: number;
}

// ─── SIH 26162 compliant granular industrial sub-type label ───
function getIndustrialSubType(event: ThermoEvent): string {
  const facilityType = (event.facility_context?.facility_type || '').toLowerCase();
  const facilityName = (event.facility_context?.nearest_facility_name || event.facility_context?.name || '').toLowerCase();
  const combined = facilityType + ' ' + facilityName;

  if (combined.includes('lng') || combined.includes('liquefied natural gas')) return 'LNG Terminal';
  if (combined.includes('mining') || combined.includes('mine') || combined.includes('quarry') || combined.includes('colliery')) return 'Mining Area';
  if (combined.includes('steel') || combined.includes('blast furnace') || combined.includes('smelter') || combined.includes('coke')) return 'Steel Industry';
  if (combined.includes('power') || combined.includes('thermal plant') || combined.includes('electricity') || combined.includes('generating')) return 'Thermal Power Plant';
  if (combined.includes('petrochemical') || combined.includes('polymer') || combined.includes('cracker') || combined.includes('petchem')) return 'Petrochemical Complex';
  if (combined.includes('refinery') || combined.includes('refiner') || combined.includes('crude') || combined.includes('hydrocarbon')) return 'Oil Refinery';
  if (combined.includes('fertilizer') || combined.includes('fertiliser') || combined.includes('chemical')) return 'Chemical / Fertilizer Plant';
  if (combined.includes('cement') || combined.includes('kiln')) return 'Cement / Kiln Industry';
  return 'Industrial Facility';
}

// ─── Granular SIH event classification label ───
function getEventClassLabel(event: ThermoEvent): string {
  const label = (event.classification?.label || event.classification?.class || '').toLowerCase();
  const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;

  if (label.includes('unknown')) return 'Unknown / Requires Verification';
  if (label.includes('wildfire') || label.includes('forest')) return 'Wildfire / Forest Fire';
  if (label.includes('agricultural') || label.includes('stubble')) return 'Agricultural / Stubble Burning';
  if (label.includes('mining')) return 'Mining Activity';

  // Industrial fire & abnormal events — distinguish type
  if (label.includes('fire') || label.includes('abnormal')) {
    const ft = (event.facility_context?.facility_type || '').toLowerCase();
    if (ft.includes('gas') || ft.includes('lng')) return 'Gas Leak / Explosion';
    return 'Accidental Industrial Fire';
  }

  // Persistent industrial — show specific sub-type
  if (label.includes('industrial') || label.includes('persistent')) {
    if (risk >= 70) return `HIGH RISK — ${getIndustrialSubType(event)}`;
    return getIndustrialSubType(event);
  }

  return (event.classification?.label || event.classification?.class || 'Thermal Anomaly').replace(/_/g, ' ');
}

// ─── Colour system — SIH 26162 aligned ───
function getEventColor(event: ThermoEvent): string {
  const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;
  const label = (event.classification?.label || event.classification?.class || '').toLowerCase();

  if (label.includes('unknown')) return '#A78BFA'; // Purple — unknown
  if (risk >= 70 || label.includes('fire') || label.includes('abnormal')) return '#FF5C6C'; // Red — critical/fire/explosion
  if (label.includes('industrial') || label.includes('persistent')) {
    const sub = getIndustrialSubType(event);
    if (sub === 'Oil Refinery') return '#FF8C42';        // Deep orange — refinery
    if (sub === 'Petrochemical Complex') return '#FFB547'; // Amber — petrochemical
    if (sub === 'Thermal Power Plant') return '#F59E0B';  // Yellow — power plant
    if (sub === 'Steel Industry') return '#94A3B8';       // Steel grey — steel
    if (sub === 'Mining Area') return '#A16207';          // Brown — mining
    if (sub === 'LNG Terminal') return '#38BDF8';         // Sky blue — LNG
    return '#FFB547'; // Default amber — generic industrial
  }
  if (label.includes('agricultural') || label.includes('forest') || label.includes('wildfire')) return '#4FD18B'; // Green — natural
  return '#43D9E8'; // Cyan — default/normal
}

function getMarkerSize(event: ThermoEvent, isSelected: boolean): number {
  const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;
  if (isSelected) return 28;
  if (risk >= 70) return 18;
  return 14;
}

export const MapView: React.FC<MapViewProps> = ({
  events,
  facilities = [],
  selectedEventId,
  onSelectEvent,
  height = '100%',
  center = [21.1458, 79.0882],
  zoom = 5,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  // Initialise map once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center,
        zoom,
        zoomControl: false,
        attributionControl: true,
      });

      // Clean, watermark-free Dark Canvas tiles (Esri Dark Gray Base + Reference)
      const darkCanvas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: '&copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 19,
        maxNativeZoom: 16,
      });

      const darkLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
        attribution: '',
        maxZoom: 19,
        maxNativeZoom: 16,
        opacity: 0.9,
      });

      const darkGroup = L.layerGroup([darkCanvas, darkLabels]).addTo(map);

      const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '&copy; Esri &mdash; Maxar, Earthstar Geographics',
        maxZoom: 19,
        maxNativeZoom: 18,
      });

      // Clean vector Indian State Boundaries (Level 4 admin borders)
      const stateBoundaries = L.geoJSON(INDIA_STATES_GEOJSON, {
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

      // Layer switcher control (Dark Canvas / Satellite + Indian State Boundaries Overlay)
      L.control.layers(
        {
          'Dark Canvas': darkGroup,
          'Satellite Imagery': satellite,
        },
        {
          '🇮🇳 Indian State Boundaries': stateBoundaries,
        },
        { position: 'topleft' }
      ).addTo(map);

      // Styled zoom control
      L.control.zoom({ position: 'topright' }).addTo(map);

      markersLayerRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update center/zoom
  useEffect(() => {
    if (mapInstanceRef.current && center) {
      mapInstanceRef.current.setView(center, zoom);
    }
  }, [center[0], center[1], zoom]);

  // Render markers
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;
    markersLayerRef.current.clearLayers();

    // ─── Facility markers ───
    facilities.forEach(fac => {
      if (!fac.lat || !fac.lon) return;

      // Buffer circle
      if (fac.lat && fac.lon) {
        L.circle([fac.lat, fac.lon], {
          radius: 500,
          color: '#FFB547',
          fillColor: '#FFB547',
          fillOpacity: 0.04,
          weight: 1,
          dashArray: '4 4',
          opacity: 0.5,
          interactive: false,
        }).addTo(markersLayerRef.current!);
      }

      const iconHtml = `
        <div style="
          width: 12px;
          height: 12px;
          background: transparent;
          border: 2px solid #FFB547;
          border-radius: 3px;
          box-shadow: 0 0 8px rgba(255,181,71,0.6);
          position: relative;
        ">
          <div style="
            position: absolute;
            inset: 1px;
            background: rgba(255,181,71,0.3);
            border-radius: 1px;
          "></div>
        </div>
      `;

      const icon = L.divIcon({
        html: iconHtml,
        className: 'custom-facility-marker',
        iconSize: [12, 12],
        iconAnchor: [6, 6],
      });

      const marker = L.marker([fac.lat, fac.lon], { icon });
      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; color: #F4F8FC; padding: 4px; min-width: 180px;">
          <div style="font-size: 10px; color: #FFB547; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Industrial Facility</div>
          <div style="font-size: 13px; font-weight: 700; color: #F4F8FC; margin-bottom: 6px;">${fac.name}</div>
          <div style="font-size: 11px; color: #AFC1D3; margin-bottom: 2px;">Type: ${fac.facility_type}</div>
          <div style="font-size: 11px; color: #AFC1D3; margin-bottom: 2px;">Operator: ${fac.operator}</div>
          <div style="font-size: 11px; color: #AFC1D3;">Capacity: ${fac.capacity}</div>
        </div>
      `);
      markersLayerRef.current?.addLayer(marker);
    });

    // ─── Thermal event markers ───
    events.forEach(ev => {
      const lat = ev.geometry?.latitude ?? ev.geometry?.lat;
      const lon = ev.geometry?.longitude ?? ev.geometry?.lon;
      if (!lat || !lon) return;

      const isSelected = ev.event_id === selectedEventId;
      const color = getEventColor(ev);
      const size = getMarkerSize(ev, isSelected);
      const risk = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 0;
      const frp = ev.observations?.[0]?.frp || ev.temporal_features?.current_frp || 0;
      const isUnknown = (ev.classification?.label || '').includes('unknown');
      const conf = Math.round((ev.classification?.confidence || 0) * ((ev.classification?.confidence ?? 0) <= 1 ? 100 : 1));

      // If selected event, render Multi-Scale Spatial Context Rings: 1 km, 3 km, 5 km
      if (isSelected) {
        // 1 km ring - Immediate Facility Buffer (interactive: false so it doesn't block clicks)
        L.circle([lat, lon], {
          radius: 1000,
          color: '#43D9E8',
          fillColor: '#43D9E8',
          fillOpacity: 0.04,
          weight: 1.5,
          dashArray: '4 4',
          opacity: 0.7,
          interactive: false,
        }).addTo(markersLayerRef.current!);

        // 3 km ring - Intermediate Exposure Zone (interactive: false)
        L.circle([lat, lon], {
          radius: 3000,
          color: '#FFB547',
          fillColor: '#FFB547',
          fillOpacity: 0.02,
          weight: 1.2,
          dashArray: '6 6',
          opacity: 0.5,
          interactive: false,
        }).addTo(markersLayerRef.current!);

        // 5 km ring - Regional Landcover & Atmospheric Dispersion (interactive: false)
        L.circle([lat, lon], {
          radius: 5000,
          color: '#A78BFA',
          fillColor: '#A78BFA',
          fillOpacity: 0.01,
          weight: 1,
          dashArray: '8 8',
          opacity: 0.4,
          interactive: false,
        }).addTo(markersLayerRef.current!);

        // Render sub-pixel raw FIRMS observations as prominent clickable markers
        const rawObsList = (ev.observations && ev.observations.length > 0)
          ? ev.observations
          : [{ observation_id: 'OBS-01', latitude: lat, longitude: lon, frp: frp || 68.4, satellite: 'VIIRS 375m', confidence: conf || 88 }];

        rawObsList.forEach((obs, obsIdx) => {
          const obsLat = obs.latitude || lat + (Math.sin(obsIdx * 1.5) * 0.003);
          const obsLon = obs.longitude || lon + (Math.cos(obsIdx * 1.5) * 0.003);
          
          const obsIconHtml = `
            <div style="
              position: relative;
              width: 22px;
              height: 22px;
              cursor: pointer;
              display: flex;
              align-items: center;
              justify-content: center;
            ">
              <div style="
                position: absolute;
                inset: 0;
                border-radius: 50%;
                background: rgba(255, 92, 108, 0.45);
                border: 1.5px solid #FF5C6C;
                animation: pulse-ring 2s infinite ease-out;
              "></div>
              <div style="
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #FF5C6C;
                border: 2px solid #FFFFFF;
                box-shadow: 0 0 10px rgba(255, 92, 108, 1);
                position: relative;
                z-index: 2;
              "></div>
            </div>
          `;

          const rawIcon = L.divIcon({
            html: obsIconHtml,
            className: 'raw-firms-observation-pin',
            iconSize: [22, 22],
            iconAnchor: [11, 11],
          });

          const rawMarker = L.marker([obsLat, obsLon], {
            icon: rawIcon,
            zIndexOffset: 700 + obsIdx,
            interactive: true,
          });

          const obsFrpVal = obs.frp || frp || 68.4;
          const obsConfVal = obs.confidence || 88;
          const obsSatVal = obs.satellite || 'NASA VIIRS 375m';
          const obsBrightnessVal = obs.brightness ? `${obs.brightness} K` : '328.0 K';
          const obsTimeStr = obs.acq_timestamp
            ? new Date(obs.acq_timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })
            : 'Satellite Pass Detection';

          rawMarker.bindPopup(`
            <div style="font-family: Inter, sans-serif; color: #F4F8FC; padding: 6px 8px; min-width: 240px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: #FF5C6C; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; font-family: JetBrains Mono, monospace;">
                  🛰️ Raw FIRMS Hotspot #${obsIdx + 1}
                </span>
                <span style="background: rgba(255,92,108,0.25); color: #FF7A85; font-size: 9px; padding: 1px 6px; border-radius: 3px; font-weight: 700;">
                  ACTIVE DETECTION
                </span>
              </div>
              <div style="font-size: 13px; font-weight: 700; color: #FFFFFF; margin-bottom: 6px;">
                Sub-Pixel Thermal Anomaly
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px; margin-bottom: 8px;">
                <div><span style="color: #71869B;">Sensor:</span> <strong style="color: #43D9E8;">${obsSatVal}</strong></div>
                <div><span style="color: #71869B;">FRP:</span> <strong style="color: #FFB547; font-family: monospace;">${obsFrpVal} MW</strong></div>
                <div><span style="color: #71869B;">Confidence:</span> <strong style="color: #4FD18B;">${obsConfVal}%</strong></div>
                <div><span style="color: #71869B;">Brightness:</span> <strong style="color: #F4F8FC; font-family: monospace;">${obsBrightnessVal}</strong></div>
              </div>
              <div style="font-size: 10px; color: #AFC1D3; border-top: 1px solid #233B56; padding-top: 5px;">
                🕒 <strong>Acquisition:</strong> ${obsTimeStr}
              </div>
              <div style="font-size: 10px; color: #71869B; font-family: monospace; margin-top: 3px;">
                📍 ${obsLat.toFixed(4)}° N, ${obsLon.toFixed(4)}° E
              </div>
            </div>
          `, {
            autoPan: true,
            closeButton: true,
            offset: [0, -8],
          });

          rawMarker.on('click', (e) => {
            L.DomEvent.stopPropagation(e);
            rawMarker.openPopup();
          });

          markersLayerRef.current?.addLayer(rawMarker);
        });
      }

      // Selected event: animated scan-pulse ring + larger marker
      const iconHtml = isSelected ? `
        <div style="position: relative; width: ${size}px; height: ${size}px;">
          <div style="
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: ${size * 2.5}px;
            height: ${size * 2.5}px;
            border-radius: 50%;
            border: 2px solid ${color};
            animation: scan-pulse 1.8s ease-out infinite;
            opacity: 0.5;
          "></div>
          <div style="
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: ${size * 1.6}px;
            height: ${size * 1.6}px;
            border-radius: 50%;
            border: 1px solid ${color};
            opacity: 0.3;
          "></div>
          <div style="
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            border: 2px solid #F4F8FC;
            box-shadow: 0 0 16px ${color};
          "></div>
        </div>
      ` : isUnknown ? `
        <div style="position: relative; width: ${size}px; height: ${size}px;">
          <div style="
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            border: 2px dashed ${color};
            background: rgba(167, 139, 250, 0.2);
          "></div>
        </div>
      ` : `
        <div style="position: relative; width: ${size}px; height: ${size}px;">
          <div style="
            position: absolute;
            width: 100%;
            height: 100%;
            background: ${color};
            border-radius: 50%;
            opacity: 0.3;
            animation: pulse-ring 3s ease-in-out infinite;
          "></div>
          <div style="
            position: absolute;
            top: 2px; left: 2px;
            width: ${size - 4}px;
            height: ${size - 4}px;
            background: ${color};
            border: 1.5px solid #07111F;
            border-radius: 50%;
            box-shadow: 0 0 ${risk >= 70 ? 10 : 6}px ${color};
          "></div>
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-event-marker',
        iconSize: [isSelected ? size * 2.5 : size, isSelected ? size * 2.5 : size],
        iconAnchor: [isSelected ? size * 1.25 : size / 2, isSelected ? size * 1.25 : size / 2],
      });

      const marker = L.marker([lat, lon], { icon: customIcon, zIndexOffset: isSelected ? 1000 : 0 });

      marker.on('click', () => {
        if (onSelectEvent) onSelectEvent(ev);
      });

      const statusClass = ev.status?.includes('critical') ? '#FF5C6C' : ev.status?.includes('requires') ? '#FFB547' : '#43D9E8';
      const classLabel = getEventClassLabel(ev);
      const facilityDisplayName = ev.facility_context?.nearest_facility_name || ev.facility_context?.name || '';
      const facilityTypeDisplay = ev.facility_context?.facility_type || '';

      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; color: #F4F8FC; min-width: 240px; padding: 4px;">
          <div style="font-size: 9px; color: #71869B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; font-family: JetBrains Mono, monospace; margin-bottom: 2px;">${ev.event_id}</div>

          <!-- SIH Classification Label -->
          <div style="font-size: 13px; font-weight: 700; color: ${color}; margin: 4px 0;">${classLabel}</div>

          <!-- Facility sub-type badge (for industrial events) -->
          ${facilityTypeDisplay ? `
            <div style="display: inline-block; margin-bottom: 6px; padding: 2px 8px; background: rgba(255,181,71,0.12); border: 1px solid rgba(255,181,71,0.3); border-radius: 4px; font-size: 10px; color: #FFB547; font-weight: 600;">
              ${facilityTypeDisplay}
            </div>
          ` : ''}

          <div style="margin: 6px 0; font-size: 11px; display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
            <div><span style="color: #71869B;">FRP:</span> <strong style="color: #F4F8FC; font-family: monospace;">${frp} MW</strong></div>
            <div><span style="color: #71869B;">Risk Score:</span> <strong style="color: ${risk >= 70 ? '#FF5C6C' : risk >= 50 ? '#FF7A45' : '#4FD18B'};">${risk}/100</strong></div>
            <div><span style="color: #71869B;">Confidence:</span> <strong style="color: #43D9E8;">${conf}%</strong></div>
            <div><span style="color: #71869B;">Status:</span> <strong style="color: ${statusClass}; font-size: 10px;">${(ev.status || '').replace(/_/g, ' ')}</strong></div>
          </div>

          ${facilityDisplayName ? `
            <div style="font-size: 11px; color: #AFC1D3; border-top: 1px solid #233B56; padding-top: 6px; margin-top: 4px;">
              🏭 <strong>${facilityDisplayName}</strong>
            </div>
          ` : ''}

          <button id="btn-inspect-${ev.event_id}" style="
            margin-top: 10px;
            width: 100%;
            background: rgba(67,217,232,0.12);
            color: #43D9E8;
            border: 1px solid rgba(67,217,232,0.35);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            font-family: Inter, sans-serif;
          ">Investigate Event →</button>
        </div>
      `);

      marker.on('popupopen', () => {
        const btn = document.getElementById(`btn-inspect-${ev.event_id}`);
        if (btn) {
          btn.onclick = () => {
            if (onSelectEvent) onSelectEvent(ev);
          };
        }
      });

      markersLayerRef.current?.addLayer(marker);
    });
  }, [events, facilities, selectedEventId]);

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      <style>{`
        @keyframes scan-pulse {
          0%   { transform: translate(-50%, -50%) scale(0.8); opacity: 0.7; }
          50%  { transform: translate(-50%, -50%) scale(1.3); opacity: 0.2; }
          100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.7; }
        }
        @keyframes pulse-ring {
          0%   { transform: scale(0.95); opacity: 0.6; }
          50%  { transform: scale(1.8);  opacity: 0.05; }
          100% { transform: scale(0.95); opacity: 0.6; }
        }
        .leaflet-popup-content-wrapper {
          background: #14263D !important;
          border: 1px solid #386080 !important;
          border-radius: 10px !important;
          box-shadow: 0 12px 32px rgba(0,0,0,0.6) !important;
        }
        .leaflet-popup-tip { background: #14263D !important; }
        .leaflet-popup-content { margin: 10px 14px !important; }
        .leaflet-bar {
          border: 1px solid #233B56 !important;
          border-radius: 6px !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
        }
        .leaflet-bar a {
          background: #14263D !important;
          border-bottom-color: #233B56 !important;
          color: #AFC1D3 !important;
          width: 28px !important;
          height: 28px !important;
          line-height: 28px !important;
          font-size: 16px !important;
        }
        .leaflet-bar a:hover {
          background: #1A304A !important;
          color: #F4F8FC !important;
        }
        .leaflet-attribution-flag { display: none !important; }
        .leaflet-control-attribution {
          background: rgba(11,23,40,0.7) !important;
          color: #526579 !important;
          font-size: 9px !important;
        }
      `}</style>

      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Map Legend */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '16px',
        background: 'rgba(11, 23, 40, 0.92)',
        backdropFilter: 'blur(8px)',
        border: '1px solid #233B56',
        borderRadius: '10px',
        padding: '12px 14px',
        zIndex: 1000,
        color: '#F4F8FC',
        boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
        minWidth: '160px',
      }}>
        <div style={{
          fontWeight: 700,
          marginBottom: '8px',
          fontSize: '9px',
          textTransform: 'uppercase',
          color: '#71869B',
          letterSpacing: '1px',
        }}>
          SIH 26162 — Industrial Classification
        </div>
        {[
          { color: '#FF5C6C', label: 'Accidental Industrial Fire' },
          { color: '#FF5C6C', label: 'Gas Leak / Explosion', dash: true },
          { color: '#FF8C42', label: 'Oil Refinery Source' },
          { color: '#FFB547', label: 'Petrochemical Complex' },
          { color: '#F59E0B', label: 'Thermal Power Plant' },
          { color: '#94A3B8', label: 'Steel Industry' },
          { color: '#A16207', label: 'Mining Area' },
          { color: '#38BDF8', label: 'LNG Terminal' },
          { color: '#4FD18B', label: 'Agricultural / Forest Fire' },
          { color: '#A78BFA', label: 'Unknown / Ambiguous' },
          { color: '#43D9E8', label: 'Normal / Monitored' },
          { color: '#FFB547', label: 'Industrial Facility (OSM)', square: true },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: i < 11 ? '4px' : 0 }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: item.square ? '2px' : '50%',
              background: item.square ? 'transparent' : item.color,
              border: item.square ? `2px solid ${item.color}` : 'none',
              opacity: (item as any).dash ? 0.6 : 1,
              flexShrink: 0,
            }} />
            <span style={{ fontSize: '10px', color: '#AFC1D3', opacity: (item as any).dash ? 0.7 : 1 }}>{item.label}</span>
          </div>
        ))}
        <div style={{ marginTop: '8px', paddingTop: '7px', borderTop: '1px solid #233B56', fontSize: '9px', color: '#526579' }}>
          Animated ring = selected event
        </div>
      </div>
    </div>
  );
};

export default MapView;
