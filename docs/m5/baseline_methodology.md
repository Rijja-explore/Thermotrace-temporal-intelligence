\# M5 Historical Baseline Methodology



\## 1. Purpose



The M5 Historical Intelligence and Baseline Module provides a historical reference layer for industrial facilities. It describes what thermal activity has normally been observed near a facility so that downstream anomaly detection can compare future activity against historical behavior.



M5 does not make the final anomaly decision.



\## 2. Historical Observation Window



The historical thermal dataset covers a 365-day observation window:



\- Start: 2025-09-02 07:37

\- End: 2026-09-02 08:37

\- Duration: 365 days



Although 13 calendar months are touched by the start and end dates, the dataset represents one year of observations rather than 13 complete months.



Therefore, this baseline should be described as an initial one-year historical baseline.



\## 3. Facility Data



Industrial facility information was derived from the project OSM facility dataset.



The M5 facility master contains 118,813 facilities across selected industrial categories:



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



\## 4. Historical Thermal Event Association



Historical thermal events were associated with industrial facilities using the nearest selected facility and a maximum distance of 5 km.



This produced 162,355 historical thermal events associated with 23,558 facilities.



The 5 km distance is a project processing rule used to construct the historical reference dataset. It does not establish that a thermal event was caused by the associated facility.



\## 5. Frequency Baseline



The frequency profile contains:



\- total\_events

\- active\_days

\- active\_months

\- avg\_events\_per\_month

\- median\_events\_per\_month

\- events\_per\_30\_days



`avg\_events\_per\_month` and `median\_events\_per\_month` describe event activity across facility-months in which events were observed.



`events\_per\_30\_days` normalizes the total number of historical events over the complete 365-day observation window:



events\_per\_30\_days = total\_events / 365 \* 30



\## 6. Thermal Intensity Baseline



Thermal intensity is represented using historical FRP and thermal-intensity statistics:



\- mean\_frp\_mw

\- median\_frp\_mw

\- max\_frp\_mw

\- min\_frp\_mw

\- mean\_thermal\_intensity

\- max\_thermal\_intensity



These values describe the historical thermal behavior observed near each facility.



\## 7. Temporal Baseline



Temporal behavior is represented using:



\- most\_active\_hour

\- most\_active\_month

\- day\_events

\- night\_events

\- weekday\_events

\- weekend\_events



These statistics describe when historical thermal activity was most frequently observed.



\## 8. Spatial Baseline



Spatial behavior is represented using:



\- mean\_distance\_km

\- median\_distance\_km

\- max\_distance\_km

\- mean\_spatial\_extent\_km

\- max\_spatial\_extent\_km



The distance statistics describe the relationship between detected event centroids and the associated facility.



Because events were filtered using a 5 km maximum association distance, the distance statistics should not be interpreted as the natural physical operating radius of a facility.



\## 9. Event Characteristics



Historical event characteristics include:



\- mean\_duration\_hours

\- median\_duration\_hours

\- max\_duration\_hours

\- mean\_detection\_count

\- median\_detection\_count

\- max\_detection\_count

\- mean\_satellite\_count

\- max\_satellite\_count



These statistics provide additional historical context about event persistence, detection density and satellite coverage.



\## 10. Historical Event Evidence



`historical\_event\_observations` represents the number of historical thermal events available as evidence for the facility baseline.



Facilities with different numbers of historical observations have different amounts of historical evidence. This value should therefore be considered when interpreting the reliability of a facility's baseline.



\## 11. Historical Industrial Incidents



Documented industrial incidents are maintained separately from satellite thermal events.



A satellite thermal detection is not automatically considered an industrial fire or incident.



Documented incidents contain source and reference information and are intended for historical validation and contextual analysis. They are not automatically used as labels for satellite events.



\## 12. Baseline Output



The main M5 baseline output is:



`data/processed/facility\_baselines.csv`



The current baseline contains 23,558 facility-level records and 44 fields covering facility identity, frequency, thermal intensity, temporal behavior, spatial behavior and event characteristics.



\## 13. Role in the Overall System



The M5 baseline is a historical reference layer.



Downstream anomaly detection can compare a new event's characteristics against the historical behavior of its associated facility.



M5 does not define arbitrary universal anomaly thresholds and does not make the final anomaly decision.



\## 14. Current Limitations



1\. The current historical baseline covers approximately one year of observations.

2\. The 5 km facility association rule is a project processing rule and does not prove causality.

3\. Facilities have different numbers of historical observations, so baseline evidence strength varies.

4\. Historical documented incidents are reference/validation data and are not automatic labels.

5\. Longer historical coverage can improve the stability of facility-specific baselines in future versions.



