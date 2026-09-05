\# M5 Data Sources



\## 1. Industrial Facility Data



\### Source



OpenStreetMap (OSM) facility data provided as part of the ThermoTrace project dataset.



The project facility dataset was provided through the Member 1 data handoff and stored in:



`data/processed/osm/osm\_india.gpkg`



The GeoPackage contains an `osm\_facilities` layer containing facility-level point records.



\### Fields used by M5



M5 uses facility information including:



\- OSM facility ID

\- Facility name

\- Operator

\- Facility category

\- Land-use information

\- Industrial tags

\- Man-made tags

\- Power information

\- Building information

\- Source

\- Representative longitude

\- Representative latitude



\### M5 facility selection



The initial M5 facility master contains selected industrial categories:



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



The resulting M5 facility dataset contains 118,813 facilities.



SUBSTATION and WAREHOUSE were excluded from the initial M5 facility set.



\---



\## 2. Historical Satellite Thermal Data



\### Source



NASA FIRMS thermal anomaly data processed through the ThermoTrace project data pipeline.



The Member 1 handoff provides the canonicalized and eventized thermal data used by M5.



The project pipeline contains FIRMS VIIRS and MODIS observations and produces clustered thermal events.



\### M5 input



M5 uses the event-level feature dataset:



`data/processed/features/event\_features\_v2.parquet`



This dataset contains approximately 996,891 historical thermal events with event-level temporal, spatial and thermal features.



\### Fields used by M5



Important fields used to construct the historical reference layer include:



\- event\_id

\- start\_time

\- end\_time

\- duration\_hours

\- centroid\_lat

\- centroid\_lon

\- spatial\_extent\_km

\- detection\_count

\- unique\_satellite\_count

\- satellites

\- max\_frp\_mw

\- mean\_frp\_mw

\- median\_frp\_mw

\- event\_quality

\- year

\- month

\- day

\- day\_of\_week

\- hour

\- season

\- is\_day

\- is\_night

\- is\_weekend

\- nearest\_facility\_id

\- nearest\_facility\_type

\- nearest\_facility\_name

\- distance\_to\_facility\_km

\- thermal\_intensity

\- thermal\_frp\_variability

\- thermal\_frp\_per\_detection

\- thermal\_frp\_per\_hour

\- thermal\_detection\_density

\- thermal\_persistence\_indicator

\- thermal\_concentration\_indicator



\### Historical observation period



The M5 historical thermal dataset covers a 365-day observation window:



\- Start: 2025-09-02 07:37

\- End: 2026-09-02 08:37



This represents an initial one-year historical baseline.



\---



\## 3. Facility–Thermal Event Association



Historical thermal events are associated with the nearest selected industrial facility.



M5 applies a maximum association distance of 5 km.



This processing step produced:



\- 162,355 historical thermal events

\- 23,558 facilities with historical thermal observations



The 5 km distance is a project processing rule.



It does not prove that a thermal event was caused by the associated industrial facility.



\---



\## 4. Historical Industrial Incident Data



Documented industrial incidents are collected separately from satellite thermal observations.



Sources may include:



\- Government publications

\- Government investigation or regulatory records

\- Press Information Bureau (PIB)

\- National Human Rights Commission (NHRC)

\- Reputable news organizations

\- Other authoritative publicly available sources



Each documented incident should retain its source and reference information.



\### Incident information



The incident dataset contains:



\- incident\_id

\- facility\_id

\- facility\_name

\- incident\_date

\- incident\_type

\- description

\- location

\- state

\- district

\- source\_name

\- source\_url

\- source\_date

\- reference\_notes



\### Important distinction



Documented incidents are historical reference and validation data.



They are not automatically used as labels for satellite thermal events.



Similarly, a satellite thermal detection is not automatically considered an industrial fire or documented incident.



\---



\## 5. External Data and Source Traceability



M5 preserves source information wherever available.



Facility records retain the source field from the project facility dataset.



Documented industrial incidents retain:



\- Source name

\- Source URL

\- Source date

\- Reference notes



This allows historical information to be traced back to its originating dataset or documented source.



\---



\## 6. M5 Data Outputs



The M5 module produces four main historical reference datasets:



\### Industrial facilities



`data/processed/industrial\_facilities.csv`



Contains the selected industrial facility master records.



\### Historical thermal events



`data/processed/historical\_thermal\_events.csv`



Contains thermal events associated with selected industrial facilities using the 5 km processing rule.



\### Historical industrial incidents



`data/processed/historical\_industrial\_incidents.csv`



Contains documented historical industrial incidents with source references.



\### Facility baselines



`data/processed/facility\_baselines.csv`



Contains facility-level historical baseline statistics derived from the historical thermal events.



This is the primary M5 historical reference output for downstream anomaly analysis.



\---



\## 7. Data Processing Principle



M5 is a historical intelligence and baseline-processing module.



Its purpose is to summarize observed historical behavior rather than to determine whether a current event is anomalous.



M5 therefore:



1\. Uses actual historical observations.

2\. Preserves source information.

3\. Separates documented incidents from satellite observations.

4\. Builds facility-specific historical profiles.

5\. Avoids arbitrary universal thresholds.

6\. Provides baseline information to downstream anomaly detection.



M5 does not make the final anomaly decision.

