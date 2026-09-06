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

export const MapView: React.FC<MapViewProps> = ({
  events,
  facilities = [],
  selectedEventId,
  onSelectEvent,
  height = '100%',
  center = [21.1458, 79.0882], // Default India centroid
  zoom = 5,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  // Helper to color-code thermal events based on classification and risk
  const getEventColor = (event: ThermoEvent): string => {
    const risk = event.operational_risk?.risk_score ?? event.scores?.operational_risk ?? 0;
    const label = (event.classification?.label || event.classification?.class || '').toLowerCase();

    if (label.includes('unknown')) return '#a855f7'; // Purple for Unknown
    if (risk >= 70 || label.includes('fire') || label.includes('abnormal')) return '#ef4444'; // Red for High Risk / Fire
    if (label.includes('industrial') || label.includes('persistent')) return '#f97316'; // Amber for Industrial
    if (label.includes('agricultural') || label.includes('forest')) return '#22c55e'; // Green for Natural/Agri
    return '#3b82f6'; // Blue default
  };

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center,
        zoom,
        zoomControl: false,
      });

      // Dark Matter Map Tiles for GIS Mission Control aesthetics
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

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

  // Update map center/zoom if center prop changes
  useEffect(() => {
    if (mapInstanceRef.current && center) {
      mapInstanceRef.current.setView(center, zoom);
    }
  }, [center[0], center[1], zoom]);

  // Render Markers
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;

    markersLayerRef.current.clearLayers();

    // Render Industrial Facilities
    facilities.forEach((fac) => {
      const facLat = fac.lat;
      const facLon = fac.lon;
      if (!facLat || !facLon) return;

      const iconHtml = `
        <div style="
          width: 14px;
          height: 14px;
          background: #3b82f6;
          border: 2px solid #60a5fa;
          border-radius: 3px;
          box-shadow: 0 0 8px rgba(59, 130, 246, 0.8);
        "></div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-facility-marker',
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const marker = L.marker([facLat, facLon], { icon: customIcon });
      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; color: #f8fafc; padding: 4px;">
          <strong style="color: #60a5fa; font-size: 14px;">🏭 ${fac.name}</strong><br/>
          <span style="font-size: 12px; color: #94a3b8;">Type: ${fac.facility_type}</span><br/>
          <span style="font-size: 12px; color: #94a3b8;">Operator: ${fac.operator}</span><br/>
          <span style="font-size: 12px; color: #94a3b8;">Capacity: ${fac.capacity}</span>
        </div>
      `);
      markersLayerRef.current?.addLayer(marker);
    });

    // Render Thermal Events
    events.forEach((ev) => {
      const lat = ev.geometry?.latitude ?? ev.geometry?.lat;
      const lon = ev.geometry?.longitude ?? ev.geometry?.lon;
      if (!lat || !lon) return;

      const isSelected = ev.event_id === selectedEventId;
      const color = getEventColor(ev);
      const label = (ev.classification?.label || ev.classification?.class || 'Thermal Anomaly').replace(/_/g, ' ');
      const risk = ev.operational_risk?.risk_score ?? ev.scores?.operational_risk ?? 0;
      const frp = ev.observations?.[0]?.frp || ev.temporal_features?.current_frp || 0;

      const pulseSize = isSelected ? 24 : 16;
      const iconHtml = `
        <div style="
          position: relative;
          width: ${pulseSize}px;
          height: ${pulseSize}px;
        ">
          <div style="
            position: absolute;
            width: 100%;
            height: 100%;
            background: ${color};
            border-radius: 50%;
            opacity: 0.6;
            animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
          "></div>
          <div style="
            position: absolute;
            top: 2px;
            left: 2px;
            width: ${pulseSize - 4}px;
            height: ${pulseSize - 4}px;
            background: ${color};
            border: 2px solid ${isSelected ? '#ffffff' : '#0f172a'};
            border-radius: 50%;
            box-shadow: 0 0 12px ${color};
          "></div>
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-event-marker',
        iconSize: [pulseSize, pulseSize],
        iconAnchor: [pulseSize / 2, pulseSize / 2],
      });

      const marker = L.marker([lat, lon], { icon: customIcon });

      marker.on('click', () => {
        if (onSelectEvent) {
          onSelectEvent(ev);
        }
      });

      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; color: #f8fafc; min-width: 220px; padding: 4px;">
          <div style="font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">${ev.event_id}</div>
          <div style="font-size: 14px; font-weight: 700; color: ${color}; margin-top: 2px;">${label}</div>
          <div style="margin-top: 8px; font-size: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
            <div><span style="color: #64748b;">FRP:</span> <strong>${frp} MW</strong></div>
            <div><span style="color: #64748b;">Risk:</span> <strong style="color: ${risk > 60 ? '#ef4444' : '#22c55e'};">${risk}</strong></div>
          </div>
          <div style="margin-top: 6px; font-size: 12px; color: #cbd5e1;">
            <strong>Location:</strong> ${ev.facility_context?.nearest_facility_name || ev.facility_context?.name || 'Open Area'}
          </div>
          <button id="btn-inspect-${ev.event_id}" style="
            margin-top: 10px;
            width: 100%;
            background: #2563eb;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
          ">Investigate Event &rarr;</button>
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
        @keyframes pulse-ring {
          0% { transform: scale(0.95); opacity: 0.8; }
          50% { transform: scale(1.6); opacity: 0.2; }
          100% { transform: scale(0.95); opacity: 0.8; }
        }
        .leaflet-popup-content-wrapper {
          background: #1e293b !important;
          border: 1px solid #334155 !important;
          border-radius: 12px !important;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5) !important;
        }
        .leaflet-popup-tip {
          background: #1e293b !important;
        }
      `}</style>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: '12px' }} />

      {/* Map Floating Legend */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        background: 'rgba(15, 23, 42, 0.90)',
        backdropFilter: 'blur(8px)',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '12px 16px',
        zIndex: 1000,
        color: '#f8fafc',
        fontSize: '12px',
        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)'
      }}>
        <div style={{ fontWeight: 700, marginBottom: '8px', fontSize: '11px', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.5px' }}>
          Geospatial Layers Legend
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }}></span>
            <span>High Risk / Fire</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f97316', display: 'inline-block' }}></span>
            <span>Industrial Flare</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
            <span>Agricultural / Forest</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#a855f7', display: 'inline-block' }}></span>
            <span>Unknown / Ambiguous</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', gridColumn: 'span 2' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#3b82f6', border: '1px solid #60a5fa', display: 'inline-block' }}></span>
            <span>Industrial Facility Boundary</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;
