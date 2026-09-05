\# M5 Dataset Schema



\## 1. industrial\_facilities.csv



This file contains the industrial facility master dataset used by M5.



Total facilities: 118,813



\### Facility fields



| Field | Description |

|---|---|

| facility\_id | Unique identifier of the industrial facility |

| name | Name of the facility |

| operator | Facility operator, when available |

| facility\_category | Category of the industrial facility |

| landuse | OSM land-use information |

| industrial | OSM industrial tag information |

| man\_made | OSM man-made tag information |

| power | OSM power-related information |

| building | OSM building information |

| source | Source of the facility record |

| longitude | Facility longitude |

| latitude | Facility latitude |



\### Facility categories



The initial M5 facility dataset contains:



\- POWER\_PLANT

\- FACTORY

\- INDUSTRIAL\_AREA

\- STORAGE\_FACILITY

\- QUARRY

\- WASTE\_PROCESSING

\- MINE

\- OIL\_GAS

\- REFINERY

\- CHEMICAL\_PLANT

\- CEMENT\_PLANT

\- STEEL\_PLANT



SUBSTATION and WAREHOUSE were excluded from the initial M5 facility set.



\---



\## 2. historical\_thermal\_events.csv



This file contains historical satellite thermal events associated with selected industrial facilities.



Total historical thermal events: 162,355



Associated facilities: 23,558



Association rule: nearest selected industrial facility within 5 km.



The 5 km rule is a project processing rule and does not prove that the facility caused the thermal event.



\### Event identity and timing



| Field | Description |

|---|---|

| event\_id | Unique identifier of the thermal event |

| start\_time | Start time of the clustered thermal event |

| end\_time | End time of the clustered thermal event |

| duration\_hours | Event duration in hours |

| year | Year of the event |

| month | Month of the event |

| day | Day of the event |

| day\_of\_week | Day of the week |

| hour | Hour associated with the event |

| season | Season associated with the event |



\### Event location



| Field | Description |

|---|---|

| centroid\_lat | Latitude of the event centroid |

| centroid\_lon | Longitude of the event centroid |

| spatial\_extent\_km | Spatial extent of the event |

| distance\_to\_facility\_km | Distance between event centroid and associated facility |



\### Thermal characteristics



| Field | Description |

|---|---|

| max\_frp\_mw | Maximum fire radiative power in MW |

| mean\_frp\_mw | Mean FRP in MW |

| median\_frp\_mw | Median FRP in MW |

| sum\_frp\_mw | Sum of FRP values |

| thermal\_intensity | Thermal intensity measure |

| thermal\_frp\_variability | Variability of FRP |

| thermal\_frp\_per\_detection | FRP normalized by detection count |

| thermal\_frp\_per\_hour | FRP normalized by event duration |

| thermal\_detection\_density | Detection density associated with the event |



\### Detection and satellite information



| Field | Description |

|---|---|

| detection\_count | Number of thermal detections contributing to the event |

| unique\_satellite\_count | Number of unique satellites contributing detections |

| satellites | Satellites associated with the event |

| event\_quality | Quality indicator for the event |



\### Temporal behavior



| Field | Description |

|---|---|

| is\_day | Indicates whether the event occurred during daytime |

| is\_night | Indicates whether the event occurred during nighttime |

| is\_weekend | Indicates whether the event occurred during a weekend |



\### Facility association



| Field | Description |

|---|---|

| nearest\_facility\_id | ID of the nearest associated facility |

| nearest\_facility\_type | Category of the associated facility |

| nearest\_facility\_name | Name of the associated facility |



\### Event behavior



| Field | Description |

|---|---|

| thermal\_persistence\_indicator | Indicator describing persistence of thermal activity |

| thermal\_concentration\_indicator | Indicator describing concentration of thermal activity |



\---



\## 3. historical\_industrial\_incidents.csv



This file contains documented historical industrial incidents obtained from external sources.



Documented incidents are maintained separately from satellite thermal events.



A satellite thermal event is not automatically considered an industrial fire or incident.



\### Incident fields



| Field | Description |

|---|---|

| incident\_id | Unique identifier for the documented incident |

| facility\_id | Associated facility ID when confidently matched |

| facility\_name | Facility name |

| incident\_date | Date of the documented incident |

| incident\_type | Type of industrial incident |

| description | Description of the documented incident |

| location | Location of the incident |

| state | State where the incident occurred |

| district | District where the incident occurred |

| source\_name | Name of the information source |

| source\_url | URL of the source |

| source\_date | Publication or source date |

| reference\_notes | Additional validation or reference information |



Documented incidents are reference and validation data. They are not automatically used as labels for satellite thermal events.



\---



\## 4. facility\_baselines.csv



This is the main M5 baseline output.



Total facilities with historical thermal observations: 23,558



Each row represents one industrial facility with historical thermal behavior summarized from the available observation period.



\### Facility identification



| Field | Description |

|---|---|

| facility\_id | Unique facility identifier |

| name | Facility name |

| operator | Facility operator |

| facility\_category | Industrial facility category |

| landuse | Land-use information |

| industrial | Industrial tag information |

| man\_made | Man-made tag information |

| power | Power-related information |

| building | Building information |

| source | Source of facility information |

| longitude | Facility longitude |

| latitude | Facility latitude |



\### Frequency baseline



| Field | Description |

|---|---|

| total\_events | Total historical thermal events associated with the facility |

| active\_days | Number of days on which thermal events were observed |

| avg\_events\_per\_month | Average event count across facility-months with observed events |

| median\_events\_per\_month | Median event count across facility-months with observed events |

| active\_months | Number of months containing observed thermal events |

| events\_per\_30\_days | Historical event count normalized to a 30-day period |



`events\_per\_30\_days` is calculated as:



events\_per\_30\_days = total\_events / 365 \* 30



\### Thermal intensity baseline



| Field | Description |

|---|---|

| mean\_frp\_mw | Mean historical FRP |

| median\_frp\_mw | Median historical FRP |

| max\_frp\_mw | Maximum historical FRP |

| min\_frp\_mw | Minimum historical FRP |

| mean\_thermal\_intensity | Mean historical thermal intensity |

| max\_thermal\_intensity | Maximum historical thermal intensity |



\### Temporal baseline



| Field | Description |

|---|---|

| most\_active\_hour | Hour with the highest historical activity |

| most\_active\_month | Month with the highest historical activity |

| day\_events | Number of daytime events |

| night\_events | Number of nighttime events |

| weekday\_events | Number of weekday events |

| weekend\_events | Number of weekend events |



\### Spatial baseline



| Field | Description |

|---|---|

| mean\_distance\_km | Mean event-to-facility distance |

| median\_distance\_km | Median event-to-facility distance |

| max\_distance\_km | Maximum event-to-facility distance |

| mean\_spatial\_extent\_km | Mean spatial extent of historical events |

| max\_spatial\_extent\_km | Maximum spatial extent of historical events |



Because the historical events were filtered using a 5 km association rule, distance values should not be interpreted as the natural operating radius of the facility.



\### Event characteristics



| Field | Description |

|---|---|

| mean\_duration\_hours | Mean historical event duration |

| median\_duration\_hours | Median historical event duration |

| max\_duration\_hours | Maximum historical event duration |

| mean\_detection\_count | Mean number of detections per event |

| median\_detection\_count | Median number of detections per event |

| max\_detection\_count | Maximum detections in an event |

| mean\_satellite\_count | Mean number of satellites contributing to events |

| max\_satellite\_count | Maximum number of satellites contributing to an event |



\### Historical evidence



| Field | Description |

|---|---|

| historical\_event\_observations | Number of historical thermal events available as evidence for the facility baseline |



This value represents the amount of historical event evidence available for the facility. It is not a confidence score.



\---



\## 5. Observation Coverage



The current historical thermal dataset covers a 365-day observation window:



\- Start: 2025-09-02 07:37

\- End: 2026-09-02 08:37



Therefore, the current facility baseline is an initial one-year historical baseline.



The dataset touches 13 calendar months, but these are not 13 complete months of observations.



\---



\## 6. M5 Output Relationship



The M5 module produces four main historical reference outputs:



1\. `industrial\_facilities.csv`

2\. `historical\_thermal\_events.csv`

3\. `historical\_industrial\_incidents.csv`

4\. `facility\_baselines.csv`



The `facility\_baselines.csv` file is the primary historical reference layer used by downstream anomaly detection.



M5 provides historical context and baseline statistics. It does not make the final anomaly decision.

