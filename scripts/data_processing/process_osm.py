import os
import glob
import json
import osmium

class ChennaiHandler(osmium.SimpleHandler):
    def __init__(self, minx, miny, maxx, maxy):
        super(ChennaiHandler, self).__init__()
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        
        self.buildings = []
        self.waterways = []
        self.highways = []
        
    def _in_bbox(self, loc):
        return self.minx <= loc.lon <= self.maxx and self.miny <= loc.lat <= self.maxy
        
    def node(self, n):
        pass # Nodes alone usually don't have building/highway ways
        
    def way(self, w):
        try:
            # Check bounding box (roughly check first node)
            if len(w.nodes) > 0 and self._in_bbox(w.nodes[0].location):
                tags = dict(w.tags)
                coords = [[n.location.lon, n.location.lat] for n in w.nodes]
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coords
                    },
                    "properties": tags
                }
                
                if 'building' in tags:
                    if coords[0] == coords[-1]:
                        feature['geometry']['type'] = "Polygon"
                        feature['geometry']['coordinates'] = [coords]
                    self.buildings.append(feature)
                elif 'highway' in tags:
                    self.highways.append(feature)
                elif 'waterway' in tags or 'water' in tags or 'natural' in tags:
                    # Very simple categorization
                    if tags.get('natural') == 'water' or tags.get('water') or 'waterway' in tags:
                        if coords[0] == coords[-1]:
                            feature['geometry']['type'] = "Polygon"
                            feature['geometry']['coordinates'] = [coords]
                        self.waterways.append(feature)
        except osmium.InvalidLocationError:
            pass # Ignore unresolved locations

def process_osm():
    print("Processing OpenStreetMap...")
    base_dir = "data/raw/geospatial/osm"
    out_dir = "data/processed/geospatial"
    os.makedirs(out_dir, exist_ok=True)
    
    files = glob.glob(os.path.join(base_dir, "*.pbf"))
    if not files:
        print("No OSM PBF files found.")
        return
        
    pbf_file = files[0]
    print(f"Parsing {pbf_file}...")
    
    # Bbox: 79.5, 12.5, 80.5, 13.5
    handler = ChennaiHandler(79.5, 12.5, 80.5, 13.5)
    handler.apply_file(pbf_file, locations=True, idx='flex_mem')
    
    print(f"Extracted {len(handler.buildings)} buildings, {len(handler.highways)} highways, {len(handler.waterways)} waterways.")
    
    # Save to GeoJSON
    def save_geojson(features, filename):
        out_path = os.path.join(out_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({
                "type": "FeatureCollection",
                "features": features
            }, f)
        print(f"Saved {filename}")

    save_geojson(handler.buildings, "chennai_buildings.geojson")
    save_geojson(handler.highways, "chennai_highways.geojson")
    save_geojson(handler.waterways, "chennai_waterways.geojson")

if __name__ == "__main__":
    process_osm()
