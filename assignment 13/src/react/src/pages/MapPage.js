import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';
// Fix for default marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

export default function MapPage() {
  const defaultPosition = [11.54798, 107.80772];
  const zoomLevel = 5;
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchLocations() {
      try {
        setLoading(true);
        const { data, error } = await supabase
          .rpc('get_nutrition_with_coordinates'); // Call the function

        if (error) {
          setError(error);
          console.error('Error fetching locations:', error);
        } else {
          setLocations(data);
        }
      } catch (error) {
        setError(error);
        console.error('An unexpected error occurred:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchLocations();
  }, []);

  if (loading) {
    return <div>Loading locations...</div>;
  }

  if (error) {
    return <div>Error loading locations: {error.message}</div>;
  }

  return (
    <div>
      <h2>Nutrition Data with Coordinates from Supabase Function</h2>
      <div className="locations-list" style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', margin: '10px auto', width: '80%' }}>
        <ul>
          {locations.map((location) => (
            <li key={location.id}>
              Latitude: {location.latitude}, Longitude: {location.longitude},
              Nitrogen: {location.nitrogen}, Phosphorous: {location.phosphorous},
              Potassium: {location.potassium}, Moisture: {location.moisture},
              Altitude: {location.altitude},
              Created At: {new Date(location.created_at).toLocaleString()}
            </li>
          ))}
        </ul>
      </div>

      <div className="map-container" style={{ height: '400px', width: '80%', margin: '20px auto' }}>
        <MapContainer center={defaultPosition} zoom={zoomLevel} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {locations.map((location) => {
             // Check if latitude and longitude are valid numbers
            const isValidCoordinates = typeof location.latitude === 'number' && typeof location.longitude === 'number';

            return isValidCoordinates ? (
              <Marker key={location.id} position={[location.latitude, location.longitude]}>
                <Popup>
                  <div>
                    <p><strong>Nutrition Data</strong></p>
                    <p>Latitude: {location.latitude}, Longitude: {location.longitude}</p>
                    <p>Nitrogen: {location.Nitrogen}</p>
                    <p>Phosphorous: {location.Phosphorous}</p>
                    <p>Potassium: {location.Potassium}</p>
                    <p>Moisture: {location.Moisture}</p>
                    <p>Altitude: {location.altitude}</p>
                    <p>Created At: {new Date(location.created_at).toLocaleString()}</p>
                  </div>
                </Popup>
              </Marker>
            ) : null; // Return null for invalid coordinates to prevent Leaflet errors
          })}
        </MapContainer>
      </div>
      <Link to="/" className="App-link">
        Back to Home
      </Link>
    </div>
  );
}
