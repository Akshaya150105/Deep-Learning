import React, { useState } from 'react';
import './styles.css'; // Optional: For basic styling
import axios from 'axios';

function App() {
  const [symptoms, setSymptoms] = useState('');
  const [response, setResponse] = useState('');
  const [conditions, setConditions] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setResponse('');
    setConditions([]);
  
    try {
      const res = await axios.get(`http://localhost:8000/query?symptoms=${symptoms}`);
      setResponse(res.data.response);
      setConditions(res.data.conditions);
    } catch (error) {
      setResponse('Error fetching response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>Medical Symptom Checker</h1>
      <div className="input-container">
        <input
          type="text"
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="Enter symptoms (e.g., itching,fatigue,yellowish skin)"
          disabled={loading}
          className="symptom-input"
        />
        <button onClick={handleSearch} disabled={loading} className="search-button">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      <div className="results">
        {response && <h3>Response:</h3>}
        <p>{response}</p>
        {conditions.length > 0 && <h3>Possible Conditions:</h3>}
        <ul>
          {conditions.map((cond, idx) => (
            <li key={idx}>
              {cond.condition}: {cond.text}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;