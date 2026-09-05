import { useEffect, useRef, useState } from 'react';
import { Viewer, Entity, PointGraphics } from 'resium';
import * as Cesium from 'cesium';

// Cesium ion Access Token
// TODO: Replace with your actual token or use import.meta.env.VITE_CESIUM_ION_TOKEN
const CESIUM_ION_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN || "YOUR_CESIUM_ION_TOKEN_HERE";

Cesium.Ion.defaultAccessToken = CESIUM_ION_TOKEN;

interface MapViewProps {
  events?: any[];
  selectedEvent?: any;
  onSelectEvent?: (event: any) => void;
  maxRenderLimit?: number;
  region?: string;
}

export default function MapView({
  events = [],
  selectedEvent = null,
  onSelectEvent,
  maxRenderLimit = 3000,
  region = 'India',
}: MapViewProps) {
  const viewerRef = useRef<any>(null);
  const [renderedEvents, setRenderedEvents] = useState<any[]>([]);

  // Throttle/slice if dataset is huge for seamless 60FPS 3D rendering
  useEffect(() => {
    if (events.length > maxRenderLimit) {
      // Sort by operational risk or FRP descending to prioritize high-risk thermal anomalies
      const prioritized = [...events]
        .sort((a, b) => (b.scores?.operational_risk || 0) - (a.scores?.operational_risk || 0))
        .slice(0, maxRenderLimit);
      setRenderedEvents(prioritized);
    } else {
      setRenderedEvents(events);
    }
  }, [events, maxRenderLimit]);

  useEffect(() => {
    const viewer = viewerRef.current?.cesiumElement;
    if (!viewer) return;

    const scene = viewer.scene;

    // ─── FULL RESOLUTION: respect device pixel ratio (HiDPI / Retina) ───
    viewer.useBrowserRecommendedResolution = false;
    viewer.resolutionScale = window.devicePixelRatio || 1.0;

    // ─── RENDERING QUALITY ───
    scene.highDynamicRange = true;
    scene.globe.enableLighting = true;

    // Key: lower = sharper tiles. 1.0 is photorealistic, 2.0 is high quality.
    scene.globe.maximumScreenSpaceError = 1.0;
    scene.globe.tileCacheSize = 1000;
    scene.globe.preloadSiblings = true;
    scene.globe.preloadAncestors = true;

    // MSAA x8 for anti-aliasing (removes jagged edges)
    scene.msaaSamples = 8;

    // FXAA on top for additional smoothing
    scene.postProcessStages.fxaa.enabled = true;

    // Atmosphere & shadows
    scene.skyAtmosphere.show = true;
    scene.globe.showGroundAtmosphere = true;
    scene.fog.enabled = true;
    scene.fog.density = 0.0001;
    viewer.shadows = true;
    scene.shadowMap.softShadows = true;
    scene.shadowMap.size = 4096;

    // Continuous rendering at 60fps (no stutter)
    scene.requestRenderMode = false;
    scene.maximumRenderTimeChange = Infinity;

    // ─── ZOOM RESTRICTIONS ───
    const MAX_HEIGHT = 7500000.0; // 7,500 km — globe always fills the viewport

    // DOM-LEVEL WHEEL INTERCEPTOR — fires before Cesium ever sees the event.
    const canvas = viewer.canvas;
    const blockZoomOut = (e: WheelEvent) => {
      const height = viewer.camera.positionCartographic?.height ?? 0;
      if (e.deltaY > 0 && height >= MAX_HEIGHT * 0.95) {
        e.stopImmediatePropagation();
        e.preventDefault();
      }
    };
    canvas.addEventListener('wheel', blockZoomOut, { capture: true, passive: false });

    // Cesium's built-in limiter (secondary safety net)
    scene.screenSpaceCameraController.minimumZoomDistance = 1.0;
    scene.screenSpaceCameraController.maximumZoomDistance = MAX_HEIGHT;

    // PostRender clamp — snap camera back if it somehow exceeds the limit
    const clampHeight = () => {
      const carto = viewer.camera.positionCartographic;
      if (carto && carto.height > MAX_HEIGHT) {
        viewer.camera.setView({
          destination: Cesium.Cartesian3.fromRadians(carto.longitude, carto.latitude, MAX_HEIGHT),
          orientation: {
            heading: viewer.camera.heading,
            pitch: viewer.camera.pitch,
            roll: viewer.camera.roll,
          },
        });
      }
    };
    scene.postRender.addEventListener(clampHeight);

    // ─── GOOGLE PHOTOREALISTIC 3D TILES ───
    viewer.imageryLayers.removeAll();
    scene.globe.show = false; // Hide the base globe to prevent conflicts with Google 3D Tiles
    
    async function loadGoogleTiles() {
      try {
        const googleTiles = await Cesium.createGooglePhotorealistic3DTileset();
        if (!viewer.isDestroyed()) {
          viewer.scene.primitives.add(googleTiles);
        }
      } catch (err) {
        console.warn('Failed to load Google Photorealistic 3D Tiles:', err);
        scene.globe.show = true; // Fallback
        window.alert("Google 3D Tiles failed to load. Please ensure it's added to your Cesium Ion account. Falling back to default satellite view.");
      }
    }
    
    loadGoogleTiles();

    // ─── INITIAL CAMERA POSITION: full globe view ───
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(78.9629, 20.5937, 7000000.0),
      orientation: {
        heading: Cesium.Math.toRadians(0.0),
        pitch: Cesium.Math.toRadians(-90.0),
        roll: 0.0,
      },
      duration: 1.5,
    });

    // Cleanup on unmount — MUST be at the end so everything above executes
    return () => {
      canvas.removeEventListener('wheel', blockZoomOut, { capture: true });
      scene.postRender.removeEventListener(clampHeight);
    };
  }, []);


  // ─── FLY CAMERA TO REGION ON REGION SWITCH ───
  useEffect(() => {
    const viewer = viewerRef.current?.cesiumElement;
    if (!viewer || selectedEvent) return;

    // Camera targets are the PRIMARY INDUSTRIAL FACILITY in each state,
    // matching exactly where FIRMS thermal detections are expected.
    const REGION_COORDS: Record<string, { lon: number; lat: number; height: number }> = {
      // ─── Broad views ──
      india:            { lon: 72.8777, lat: 19.0760, height: 5000.0 }, // Mumbai, 5km up (shows 3D instantly)
      global:           { lon: 15.0,    lat: 20.0,    height: 9000000.0 },
      all:              { lon: 78.9629, lat: 20.5937, height: 9000000.0  },

      // ── Indian states → focused on primary industrial facility ──
      // Gujarat: Jamnagar Refinery Complex (Reliance Industries) + Vadinar (Nayara Energy)
      gujarat:          { lon: 70.0577, lat: 22.4707, height: 200000.0 },
      // Maharashtra: BPCL/HPCL Mumbai Refinery Complex (Mahul/Chembur)
      maharashtra:      { lon: 72.8800, lat: 19.0100, height: 200000.0 },
      // Odisha: IOCL Paradip Refinery (coast) + SAIL Rourkela Steel Plant
      odisha:           { lon: 85.7660, lat: 20.5400, height: 500000.0 }, // midpoint between Paradip & Rourkela
      // West Bengal: IOCL Haldia Refinery Complex
      "west bengal":    { lon: 88.0640, lat: 22.0620, height: 200000.0 },
      // Tamil Nadu: CPCL Chennai Petrochemical Complex (Manali, North Chennai)
      "tamil nadu":     { lon: 80.3020, lat: 13.1650, height: 200000.0 },
      // Jharkhand: Tata Steel Jamshedpur + SAIL Bokaro Steel City
      jharkhand:        { lon: 86.2000, lat: 23.2200, height: 300000.0 }, // midpoint
      // Chhattisgarh: SAIL Bhilai Steel Plant
      chhattisgarh:     { lon: 81.3850, lat: 21.1890, height: 200000.0 },
      // Assam: Digboi + Numaligarh + Bongaigaon refineries
      assam:            { lon: 92.1550, lat: 26.5350, height: 400000.0 }, // midpoint across Assam corridor
      // Karnataka: MRPL Mangalore Refinery (Katipalla)
      karnataka:        { lon: 74.8385, lat: 12.9912, height: 200000.0 },
      // Kerala: BPCL Kochi Refinery (Ambalamugal)
      kerala:           { lon: 76.3530, lat:  9.9674, height: 200000.0 },
      // Haryana: IOCL Panipat Refinery & Petrochemical Complex
      haryana:          { lon: 76.9635, lat: 29.3909, height: 200000.0 },
      // Uttar Pradesh: IOCL Mathura Refinery
      "uttar pradesh":  { lon: 77.6737, lat: 27.4924, height: 200000.0 },
      // Bihar: IOCL Barauni Refinery
      bihar:            { lon: 85.9870, lat: 25.4670, height: 200000.0 },
      // Punjab: HMEL Guru Gobind Singh Bhatinda Refinery
      punjab:           { lon: 74.9350, lat: 30.1250, height: 200000.0 },
      // Madhya Pradesh: BPCL Bina Refinery
      "madhya pradesh": { lon: 78.1880, lat: 24.1750, height: 200000.0 },
      // Andhra Pradesh: HPCL Visakhapatnam Refinery
      "andhra pradesh": { lon: 83.2185, lat: 17.6868, height: 200000.0 },
    };

    const target = REGION_COORDS[region.toLowerCase()] || REGION_COORDS['india'];
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(target.lon, target.lat, target.height),
      orientation: {
        heading: Cesium.Math.toRadians(0.0),
        pitch: Cesium.Math.toRadians(-50.0),
        roll: 0.0,
      },
      duration: 1.2,
    });
  }, [region, selectedEvent]);

  // ─── FLY TO SELECTED EVENT ───
  useEffect(() => {
    const viewer = viewerRef.current?.cesiumElement;
    if (!viewer || !selectedEvent?.geometry) return;

    // Get approximate terrain height so the camera doesn't look underground at sea level
    const cartographic = Cesium.Cartographic.fromDegrees(
      selectedEvent.geometry.lon,
      selectedEvent.geometry.lat
    );
    const terrainHeight = viewer.scene.globe.getHeight(cartographic) || 0;

    const targetPosition = Cesium.Cartesian3.fromDegrees(
      selectedEvent.geometry.lon,
      selectedEvent.geometry.lat,
      terrainHeight
    );

    viewer.camera.flyToBoundingSphere(
      new Cesium.BoundingSphere(targetPosition, 0),
      {
        offset: new Cesium.HeadingPitchRange(
          Cesium.Math.toRadians(0.0),
          Cesium.Math.toRadians(-50.0),
          3000.0 // 3km distance from the point (close enough to see 3D buildings)
        ),
        duration: 1.2
      }
    );
  }, [selectedEvent]);

  // Color generator based on thermal characteristics
  const getHotspotColor = (event: any) => {
    const isIndustrial = (event.scores?.industrial_likelihood || 0) > 70;
    const isCritical = (event.scores?.operational_risk || 0) >= 75;
    const frp = event.observations?.[0]?.frp || 0;

    if (isIndustrial) {
      return Cesium.Color.fromCssColorString('#a855f7').withAlpha(0.9); // Neon Purple for Industrial Flare
    }
    if (isCritical || frp > 50) {
      return Cesium.Color.fromCssColorString('#ef4444').withAlpha(0.95); // Bright Crimson Red for Critical
    }
    if (frp > 15) {
      return Cesium.Color.fromCssColorString('#f97316').withAlpha(0.9); // Orange for High
    }
    return Cesium.Color.fromCssColorString('#eab308').withAlpha(0.85); // Yellow for Moderate
  };

  return (
    <Viewer
      ref={viewerRef}
      full
      animation={false}
      timeline={false}
      baseLayerPicker={false}     // We set imagery programmatically (Esri HD)
      shadows={true}
      infoBox={false}
      scene3DOnly={true}          // 3D-only mode: sharper rendering pipeline, no 2D overhead
      useBrowserRecommendedResolution={false} // Use full device pixel ratio
    >
      {renderedEvents.map((event) => {
        const isSelected = selectedEvent?.event_id === event.event_id;
        const color = getHotspotColor(event);
        const frp = event.observations?.[0]?.frp || 0;

        return (
          <Entity
            key={event.event_id}
            name={`🔥 ${event.classification?.class || "Thermal Anomaly"} (${event.event_id})`}
            position={Cesium.Cartesian3.fromDegrees(event.geometry.lon, event.geometry.lat)}
            onClick={() => onSelectEvent && onSelectEvent(event)}
          >
            <PointGraphics
              pixelSize={isSelected ? 16 : Math.min(14, Math.max(8, Math.round(frp * 0.4 + 7)))}
              color={color}
              outlineColor={isSelected ? Cesium.Color.CYAN : Cesium.Color.fromCssColorString('#ffffff')}
              outlineWidth={isSelected ? 3 : 1.5}
              scaleByDistance={new Cesium.NearFarScalar(1.0e3, 1.6, 6.0e6, 0.4)}
              heightReference={Cesium.HeightReference.CLAMP_TO_GROUND}
            />
          </Entity>
        );
      })}
    </Viewer>
  );
}
