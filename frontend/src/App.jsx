import React, { useState, useEffect } from 'react';
import axios from 'axios'; 
import './App.css'; // Keep standard styling

function App() {
  const [unis, setUnis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // useEffect runs once after the component mounts
  useEffect(() => {
    // 1. Fetch data from the Flask backend's mock API route
    axios.get('http://127.0.0.1:5000/api/unis') 
      .then(response => {
        // 2. Data retrieved successfully
        setUnis(response.data);
        setLoading(false);
      })
      .catch(err => {
        // 3. Handle connection errors (e.g., if Flask isn't running)
        console.error("Error fetching data:", err);
        setError("Failed to fetch university data from backend. Is the Flask server running?");
        setLoading(false);
      });
  }, []); // The empty array [] ensures this runs only once

  if (loading) return <h1 style={{color: 'blue'}}>Loading ExchangeCompass Data...</h1>;
  if (error) return <h1 style={{color: 'red'}}>Error: {error}</h1>;

  return (
    <div className="App" style={{ padding: '20px' }}>
      <h1>ExchangeCompass: GJU Edition</h1>
      <h2>Mock Data Loaded Successfully ({unis.length} Universities)</h2>
      <ul style={{ listStyleType: 'none', padding: 0 }}>
        {unis.map(uni => (
          <li 
            key={uni.id} 
            style={{ 
              borderBottom: '1px solid #ccc', 
              padding: '10px 0', 
              marginBottom: '10px' 
            }}
          >
            <h3>{uni.uni_name} in {uni.city}</h3>
            <p>Overall Score: <strong>{uni.overall_score}/5.0</strong></p>
            <p>Academic Score: {uni.academic_score} | Cost Score: {uni.cost_score}</p>
            <p>Summary: {uni.summary}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;