import 'leaflet/dist/leaflet.css';
import './App.css';
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Map from './Pages/MapPage';
import MapPage from './Pages/MapPage';
import HomePage from './Pages/HomePage';

const apiKey = process.env.REACT_APP_API_KEY;

function App() {
  // Default coordinates (e.g., New York City)
 
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/map" element={<MapPage/>} />
      </Routes>
    </Router>
  );
}

export default App;
