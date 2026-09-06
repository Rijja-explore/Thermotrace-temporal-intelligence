CREATE EXTENSION IF NOT EXISTS postgis;

-- ═══════════════════════════════════════════
-- THERMAL EVENTS
-- ═══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS events (
    event_id        VARCHAR(50) PRIMARY KEY,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION,
    geom            GEOMETRY(Point, 4326),
    time_start      TIMESTAMP WITH TIME ZONE,
    time_end        TIMESTAMP WITH TIME ZONE,
    status          VARCHAR(50) DEFAULT 'requires_verification',
    data_version    VARCHAR(50),
    model_version   VARCHAR(50),
    classification  JSONB DEFAULT '{}',
    scores          JSONB DEFAULT '{}',
    facility_context  JSONB DEFAULT '{}',
    landcover_context JSONB DEFAULT '{}',
    temporal_features JSONB DEFAULT '{}',
    observations    JSONB DEFAULT '[]',
    evidence        JSONB DEFAULT '[]',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS events_geom_idx  ON events USING GIST (geom);
CREATE INDEX IF NOT EXISTS events_status_idx ON events (status);

-- ═══════════════════════════════════════════
-- KNOWN INDUSTRIAL FACILITIES
-- ═══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS facilities (
    facility_id   SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    facility_type VARCHAR(100),
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    geom          GEOMETRY(Point, 4326),
    capacity      VARCHAR(100),
    operator      VARCHAR(200),
    metadata      JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS facilities_geom_idx ON facilities USING GIST (geom);

-- ═══════════════════════════════════════════
-- ANALYST AUDIT LOG
-- ═══════════════════════════════════════════
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id      SERIAL PRIMARY KEY,
    event_id    VARCHAR(50) REFERENCES events(event_id),
    analyst     VARCHAR(100) DEFAULT 'demo-analyst',
    action      VARCHAR(50) NOT NULL,        -- confirm, reject, reclassify, generate_report
    old_status  VARCHAR(50),
    new_status  VARCHAR(50),
    notes       TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════
-- SEED: Demo Events
-- ═══════════════════════════════════════════
INSERT INTO events (
    event_id, lat, lon, geom, time_start, time_end, status,
    classification, scores, facility_context, evidence, observations,
    temporal_features, data_version, model_version
) VALUES
(
    'TT-IND-00427', 19.0760, 72.8777,
    ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326),
    '2026-01-01T00:00:00Z', '2026-01-30T23:59:59Z', 'requires_verification',
    '{"class":"Persistent industrial source","confidence":87}',
    '{"industrial_likelihood":87,"operational_risk":72}',
    '{"nearby_refinery_km":0.43,"name":"Mumbai Refinery Complex","land_cover":"Industrial","population_within_5km":125000}',
    '["24 detections / 30 days","Stable centroid drift < 50m","Facility proximity 0.43 km","Night-time thermal persistence","FRP consistent with refinery flaring"]',
    '[{"frp":42.5,"satellite":"VIIRS_SNPP","acq_date":"2026-01-15"},{"frp":38.2,"satellite":"MODIS","acq_date":"2026-01-20"}]',
    '{"baseline_frp_mean":35.4,"baseline_frp_std":8.2,"current_frp":42.5,"deviation_sigma":0.87,"detection_count_30d":24,"persistence_ratio":0.8}',
    'demo-2026-01', 'hybrid-v1'
),
(
    'TT-IND-00512', 22.5726, 88.3639,
    ST_SetSRID(ST_MakePoint(88.3639, 22.5726), 4326),
    '2026-02-10T00:00:00Z', '2026-02-28T23:59:59Z', 'critical_alert',
    '{"class":"Anomalous Heat Signature","confidence":92}',
    '{"industrial_likelihood":45,"operational_risk":89}',
    '{"nearby_refinery_km":2.1,"name":"Kolkata Industrial Zone","land_cover":"Urban/Industrial","population_within_5km":340000}',
    '["Sudden temperature spike +180%","High contrast with surroundings","No scheduled maintenance","Population exposure high"]',
    '[{"frp":85.3,"satellite":"VIIRS_NOAA20","acq_date":"2026-02-15"}]',
    '{"baseline_frp_mean":12.1,"baseline_frp_std":4.5,"current_frp":85.3,"deviation_sigma":16.27,"detection_count_30d":8,"persistence_ratio":0.27}',
    'demo-2026-01', 'hybrid-v1'
),
(
    'TT-IND-00678', 13.0827, 80.2707,
    ST_SetSRID(ST_MakePoint(80.2707, 13.0827), 4326),
    '2026-03-01T00:00:00Z', '2026-03-15T23:59:59Z', 'monitored',
    '{"class":"Scheduled Flaring","confidence":95}',
    '{"industrial_likelihood":98,"operational_risk":20}',
    '{"nearby_refinery_km":0.08,"name":"Chennai Petrochemical Complex","land_cover":"Industrial Zone","population_within_5km":45000}',
    '["Matches flaring schedule","Expected thermal footprint","Facility operator confirmed","Regular maintenance cycle"]',
    '[{"frp":28.1,"satellite":"VIIRS_SNPP","acq_date":"2026-03-05"}]',
    '{"baseline_frp_mean":25.0,"baseline_frp_std":5.0,"current_frp":28.1,"deviation_sigma":0.62,"detection_count_30d":15,"persistence_ratio":0.5}',
    'demo-2026-01', 'hybrid-v1'
),
(
    'TT-IND-00901', 26.8467, 80.9462,
    ST_SetSRID(ST_MakePoint(80.9462, 26.8467), 4326),
    '2026-01-20T00:00:00Z', '2026-01-25T23:59:59Z', 'requires_verification',
    '{"class":"Agricultural Burning","confidence":78}',
    '{"industrial_likelihood":5,"operational_risk":55}',
    '{"nearby_refinery_km":12.5,"name":"N/A","land_cover":"Agricultural","population_within_5km":8000}',
    '["Seasonal pattern match","Agricultural land cover","Low industrial likelihood","Widespread spatial pattern"]',
    '[{"frp":15.2,"satellite":"MODIS","acq_date":"2026-01-22"}]',
    '{"baseline_frp_mean":8.0,"baseline_frp_std":6.0,"current_frp":15.2,"deviation_sigma":1.2,"detection_count_30d":5,"persistence_ratio":0.17}',
    'demo-2026-01', 'hybrid-v1'
),
(
    'TT-IND-01102', 28.6139, 77.2090,
    ST_SetSRID(ST_MakePoint(77.2090, 28.6139), 4326),
    '2026-04-10T00:00:00Z', '2026-04-14T23:59:59Z', 'investigating',
    '{"class":"Unknown Subsurface Heat","confidence":65}',
    '{"industrial_likelihood":30,"operational_risk":60}',
    '{"nearby_refinery_km":5.5,"name":"Delhi NCR Zone","land_cover":"Urban","population_within_5km":500000}',
    '["Diffused heat signature","No surface structure correlated","Subsurface investigation recommended","Moderate risk level"]',
    '[{"frp":22.0,"satellite":"VIIRS_NOAA21","acq_date":"2026-04-12"}]',
    '{"baseline_frp_mean":5.0,"baseline_frp_std":3.0,"current_frp":22.0,"deviation_sigma":5.67,"detection_count_30d":3,"persistence_ratio":0.1}',
    'demo-2026-01', 'hybrid-v1'
)
ON CONFLICT (event_id) DO NOTHING;

-- ═══════════════════════════════════════════
-- SEED: Demo Facilities
-- ═══════════════════════════════════════════
INSERT INTO facilities (name, facility_type, lat, lon, geom, capacity, operator) VALUES
('Mumbai Refinery Complex', 'Oil Refinery', 19.0780, 72.8800, ST_SetSRID(ST_MakePoint(72.8800, 19.0780), 4326), '300,000 bpd', 'BPCL'),
('Kolkata Industrial Zone', 'Chemical Plant', 22.5750, 88.3660, ST_SetSRID(ST_MakePoint(88.3660, 22.5750), 4326), 'N/A', 'Various'),
('Chennai Petrochemical Complex', 'Petrochemical', 13.0850, 80.2730, ST_SetSRID(ST_MakePoint(80.2730, 13.0850), 4326), '150,000 bpd', 'CPCL'),
('Jamnagar Refinery', 'Oil Refinery', 22.4707, 70.0577, ST_SetSRID(ST_MakePoint(70.0577, 22.4707), 4326), '1,240,000 bpd', 'Reliance Industries'),
('Mathura Refinery', 'Oil Refinery', 27.4924, 77.6737, ST_SetSRID(ST_MakePoint(77.6737, 27.4924), 4326), '160,000 bpd', 'IOCL')
ON CONFLICT DO NOTHING;
