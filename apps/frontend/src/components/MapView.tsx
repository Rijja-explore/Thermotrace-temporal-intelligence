import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { ThermoEvent, Facility } from '../services/api';

interface MapViewProps {
  events: ThermoEvent[];
  facilities?: Facility[];
  selectedEventId?: string | null;
  onSelectEvent?: (event: ThermoEvent) => void;
  height?: string;
  center?: [number, number];
  zoom?: number;
}

// ─── Token-aligned colour system ───
function getEventColor(event: ThermoEvent): string {
  const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;
  const label = (event.classification?.label || event.classification?.class || '').toLowerCase();

  if (label.includes('unknown')) return '#A78BFA'; // Purple — unknown
  if (risk >= 70 || label.includes('fire') || label.includes('abnormal')) return '#FF5C6C'; // Red — critical/fire
  if (label.includes('industrial') || label.includes('persistent') || label.includes('flaring')) return '#FFB547'; // Amber — industrial
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

      // Layer switcher control (Dark Canvas / Satellite)
      L.control.layers(
        {
          'Dark Canvas': darkGroup,
          'Satellite Imagery': satellite,
        },
        undefined,
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
      const label = (ev.classification?.label || ev.classification?.class || 'Thermal Anomaly').replace(/_/g, ' ');
      const risk = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 0;
      const frp = ev.observations?.[0]?.frp || ev.temporal_features?.current_frp || 0;
      const isUnknown = (ev.classification?.label || '').includes('unknown');

      // If selected event, render Multi-Scale Spatial Context Rings: 1 km, 3 km, 5 km
      if (isSelected) {
        // 1 km ring - Immediate Facility Buffer
        L.circle([lat, lon], {
          radius: 1000,
          color: '#43D9E8',
          fillColor: '#43D9E8',
          fillOpacity: 0.04,
          weight: 1.5,
          dashArray: '4 4',
          opacity: 0.7,
        }).bindTooltip('1 km Spatial Context (Immediate Industrial Perimeter)', { sticky: true }).addTo(markersLayerRef.current!);

        // 3 km ring - Intermediate Exposure Zone
        L.circle([lat, lon], {
          radius: 3000,
          color: '#FFB547',
          fillColor: '#FFB547',
          fillOpacity: 0.02,
          weight: 1.2,
          dashArray: '6 6',
          opacity: 0.5,
        }).bindTooltip('3 km Multi-Scale Buffer (Infrastructure & Population Context)', { sticky: true }).addTo(markersLayerRef.current!);

        // 5 km ring - Regional Landcover & Atmospheric Dispersion
        L.circle([lat, lon], {
          radius: 5000,
          color: '#A78BFA',
          fillColor: '#A78BFA',
          fillOpacity: 0.01,
          weight: 1,
          dashArray: '8 8',
          opacity: 0.4,
        }).bindTooltip('5 km Regional Buffer (Land Cover & Atmospheric Context)', { sticky: true }).addTo(markersLayerRef.current!);

        // Render sub-pixel raw FIRMS observations if available
        if (ev.observations && ev.observations.length > 1) {
          ev.observations.forEach((obs, obsIdx) => {
            const obsLat = obs.latitude || lat + (Math.sin(obsIdx * 1.5) * 0.002);
            const obsLon = obs.longitude || lon + (Math.cos(obsIdx * 1.5) * 0.002);
            
            const rawObsMarker = L.circleMarker([obsLat, obsLon], {
              radius: 4,
              fillColor: '#FF5C6C',
              color: '#F4F8FC',
              weight: 1,
              opacity: 0.9,
              fillOpacity: 0.8,
            });

            rawObsMarker.bindPopup(`
              <div style="font-family: Inter, sans-serif; color: #F4F8FC; padding: 4px; font-size: 11px;">
                <div style="color: #71869B; font-size: 9px; font-weight: 700; text-transform: uppercase;">Raw FIRMS Observation #${obsIdx + 1}</div>
                <div style="font-weight: 700; color: #FF5C6C; margin: 2px 0;">Thermal Anomaly Detection</div>
                <div>Sensor: <strong>${obs.satellite || 'NASA VIIRS 375m'}</strong></div>
                <div>FRP: <strong>${obs.frp || ev.observations?.[0]?.frp || 120} MW</strong></div>
                <div>Confidence: <strong>${obs.confidence || 85}%</strong></div>
                <div>Time: <strong>${obs.acq_timestamp ? new Date(obs.acq_timestamp).toLocaleTimeString() : 'NRT Pass'}</strong></div>
              </div>
            `);
            markersLayerRef.current?.addLayer(rawObsMarker);
          });
        }
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

      const conf = Math.round((ev.classification?.confidence || 0) * (ev.classification?.confidence <= 1 ? 100 : 1));
      const statusClass = ev.status?.includes('critical') ? '#FF5C6C' : ev.status?.includes('requires') ? '#FFB547' : '#43D9E8';

      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; color: #F4F8FC; min-width: 220px; padding: 4px;">
          <div style="font-size: 10px; color: #71869B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; font-family: JetBrains Mono, monospace;">${ev.event_id}</div>
          <div style="font-size: 13px; font-weight: 700; color: ${color}; margin: 4px 0; text-transform: capitalize;">${label}</div>
          <div style="margin: 8px 0; font-size: 11px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
            <div><span style="color: #71869B;">FRP:</span> <strong style="color: #F4F8FC; font-family: monospace;">${frp} MW</strong></div>
            <div><span style="color: #71869B;">Risk:</span> <strong style="color: ${risk >= 70 ? '#FF5C6C' : risk >= 50 ? '#FF7A45' : '#4FD18B'};">${risk}</strong></div>
            <div><span style="color: #71869B;">Conf:</span> <strong style="color: #43D9E8;">${conf}%</strong></div>
            <div><span style="color: #71869B;">Status:</span> <strong style="color: ${statusClass}; font-size: 10px;">${(ev.status || '').replace(/_/g, ' ')}</strong></div>
          </div>
          ${ev.facility_context?.nearest_facility_name || ev.facility_context?.name ? `
            <div style="font-size: 11px; color: #AFC1D3; border-top: 1px solid #233B56; padding-top: 6px; margin-top: 6px;">
              📍 ${ev.facility_context?.nearest_facility_name || ev.facility_context?.name || ''}
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
          Event Classification
        </div>
        {[
          { color: '#FF5C6C', label: 'High Risk / Fire' },
          { color: '#FFB547', label: 'Industrial Source' },
          { color: '#4FD18B', label: 'Agricultural / Forest' },
          { color: '#A78BFA', label: 'Unknown / Ambiguous' },
          { color: '#43D9E8', label: 'Normal / Monitored' },
          { color: '#FFB547', label: 'Industrial Facility', square: true },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: i < 5 ? '5px' : 0 }}>
            <div style={{
              width: item.square ? '8px' : '8px',
              height: '8px',
              borderRadius: item.square ? '2px' : '50%',
              background: item.square ? 'transparent' : item.color,
              border: item.square ? `2px solid ${item.color}` : 'none',
              flexShrink: 0,
            }} />
            <span style={{ fontSize: '10px', color: '#AFC1D3' }}>{item.label}</span>
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
