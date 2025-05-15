import json
import math

class GeofenceChecker:
    def __init__(self, geojson_file):
        # Load geofence from GeoJSON file
        with open(geojson_file, 'r') as f:
            self.geofence_data = json.load(f)
        
        # Extract the polygon coordinates
        self.polygons = []
        for feature in self.geofence_data['features']:
            if feature['geometry']['type'] == 'Polygon':
                geometry_id = feature['properties'].get('geometryId', 'unknown')
                self.polygons.append({
                    'coordinates': feature['geometry']['coordinates'][0],
                    'geometryId': geometry_id
                })
    
    def haversine_distance(self, lon1, lat1, lon2, lat2):
        """Calculate the great circle distance between two points in kilometers"""
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r * 1000  # Convert to meters
    
    def point_in_polygon(self, point, polygon):
        """Ray casting algorithm to determine if a point is inside a polygon"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def distance_to_polygon_edge(self, lat, lon, polygon_coords):
        """Calculate the minimum distance from a point to the polygon edge"""
        min_distance = float('inf')
        nearest_lat, nearest_lon = None, None
        
        # Check each edge of the polygon
        for i in range(len(polygon_coords) - 1):
            p1_lon, p1_lat = polygon_coords[i]
            p2_lon, p2_lat = polygon_coords[i + 1]
            
            # Calculate the distance to this edge
            # For simplicity, we'll calculate distance to each vertex and the projection on the edge
            d1 = self.haversine_distance(lon, lat, p1_lon, p1_lat)
            d2 = self.haversine_distance(lon, lat, p2_lon, p2_lat)
            
            # Simple approximation for distance to line segment
            if d1 < min_distance:
                min_distance = d1
                nearest_lat, nearest_lon = p1_lat, p1_lon
            
            if d2 < min_distance:
                min_distance = d2
                nearest_lat, nearest_lon = p2_lat, p2_lon
        
        return min_distance, nearest_lat, nearest_lon
    
    def check_point(self, lat, lon, search_buffer=50):
        """Check if a point is inside any of the geofences and return distance info"""
        results = []
        
        for polygon in self.polygons:
            coords = polygon['coordinates']
            is_inside = self.point_in_polygon((lon, lat), coords)
            
            distance, nearest_lat, nearest_lon = self.distance_to_polygon_edge(lat, lon, coords)
            
            # Apply the same logic as Azure Maps for distance values
            if is_inside:
                if distance > search_buffer:
                    distance = -999  # Well inside
                else:
                    distance = -distance  # Just inside
            else:
                if distance > search_buffer:
                    distance = 999  # Well outside
                # else distance is positive and less than search_buffer (just outside)
            
            results.append({
                "geometryId": polygon['geometryId'],
                "distance": distance,
                "nearestLat": nearest_lat,
                "nearestLon": nearest_lon,
                "isInside": is_inside
            })
        
        return {
            "geometries": results,
            "expiredGeofenceGeometryId": [],
            "invalidPeriodGeofenceGeometryId": []
        }