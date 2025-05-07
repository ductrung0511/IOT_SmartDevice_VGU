import React from 'react'
import logo from '../logo.svg';
import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <h1>Welcome to Our App</h1>
        <Link to="/map" className="App-link">
          View Map
        </Link>
      </header>
    </div>
  )
}
