# GIS Data Audit

| Dataset | Source | Spatial Coverage | Resolution / Format | Asset Types | Completeness | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| chennai_dem_30m.tif | Copernicus DEM | Chennai Region | 30m / GeoTIFF | Elevation | Complete | REAL |
| southern-zone-latest.osm.pbf | Geofabrik (OSM) | South India | Vector / PBF | All | Open-source subset | REAL |
| chennai_highways.geojson | OSM Extraction | Chennai Region | Vector / GeoJSON | Roads/Bridges | Good | REAL |
| chennai_waterways.geojson | OSM Extraction | Chennai Region | Vector / GeoJSON | Rivers/Drains | Good | REAL |
| chennai_buildings.geojson | OSM Extraction | Chennai Region | Vector / GeoJSON | Structures | Variable | REAL |
| Substations | N/A | N/A | N/A | Power Grid | MISSING | MISSING |
| Pumping Stations | N/A | N/A | N/A | Water Ops | MISSING | MISSING |

**Conclusion:** We possess verified physical topologies for roads and natural/constructed waterways. Critical active infrastructure (power grids, pumping stations) are completely missing from the public extracts. We will proceed strictly with available real assets and will **not** fabricate coordinates for the missing layers.
