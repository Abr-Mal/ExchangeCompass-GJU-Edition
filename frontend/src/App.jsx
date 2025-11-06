import React, { useState, useEffect } from 'react';
import axios from 'axios'; 
import MapComponent from './MapComponent';
import './App.css';
import { Button } from 'react-bootstrap';
import RadarChartComponent from './RadarChartComponent';

const CITY_COORDINATES = {
    "Aalen": [48.84, 10.10],
    "Fulda": [50.56, 9.68],
    "Giessen": [50.58, 8.68], // For Technische Hochschule Mittelhessen (THM)
    "Kaiserslautern": [49.44, 7.75],
    "Bayreuth": [49.95, 11.57],
    "Brandenburg an der Havel": [52.41, 12.53],
    "Deggendorf": [48.84, 12.96],
    "Wolfsburg": [52.42, 10.79], // For Ostfalia HS
    "Rosenheim": [47.86, 12.12],
    "Siegen": [50.88, 8.02],
    "Köthen": [51.75, 11.98], // For Anhalt HS (Campus Köthen)
    "Sankt Augustin": [50.77, 7.19], // For Bonn-Rhein-Sieg HS
    "Gummersbach": [51.03, 7.56], // For Köln TH (Campus Gummersbach)
    "Krefeld": [51.33, 6.57], // For Niederrhein / Krefeld HS
    "Osnabrück": [52.28, 8.05],
    "Saarbrücken": [49.24, 7.00], // For Saarland HTW
    "Schmalkalden": [50.72, 10.45],
    "Zwickau": [50.72, 12.50],
    "Bremen": [53.08, 8.80],
    "Regensburg": [49.01, 12.10], // For Regensburg OTH
    "Trier": [49.75, 6.64],
    "Nordhausen": [51.50, 10.79], // For Hochschule Nordhausen
    "Stralsund": [54.31, 13.08], // For Hochschule Stralsund
    "Ilmenau": [50.68, 10.93], // For Technische Universität Ilmenau
    "Wernigerode": [51.84, 10.78], // For Hochschule Harz
};

function App() {
  const [unis, setUnis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Selected university (single) for detail view
  const [selectedUniDetails, setSelectedUniDetails] = useState(null);
  const [highlightedUni, setHighlightedUni] = useState(null);
  const [reviewsContent, setReviewsContent] = useState(null);
  const [reviewsRaw, setReviewsRaw] = useState([]);
  const [reviewsVisibleCount, setReviewsVisibleCount] = useState(5);
  const [showAIReview, setShowAIReview] = useState(false);
  const [loadingAISummary, setLoadingAISummary] = useState(false);

  // New state for comparison feature
  const [compareUni1, setCompareUni1] = useState(null);
  const [compareUni2, setCompareUni2] = useState(null);
  const [showComparison, setShowComparison] = useState(false); // Controls whether to show comparison view

  // When a marker is clicked, show its details in the right pane
  const handleMarkerClick = (uniData) => {
    setSelectedUniDetails(uniData);
    setHighlightedUni(uniData.uni_name);
    fetchReviews(uniData.uni_name);
  };

  const fetchReviews = async (uniName) => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
    // Removed setReviewsContent('Loading...') here, as AI summary loading is handled by loadingAISummary
  
    try {
      const res = await axios.get(`${BACKEND_URL}/api/reviews/${encodeURIComponent(uniName)}`);
      const data = res.data;
  
      const read = (obj, keys) => {
        if (!obj) return null;
        for (const k of keys) {
          if (obj[k] !== undefined && obj[k] !== null) return obj[k];
        }
        return null;
      };
  
      const asNumber = (v) => {
        if (v === null || v === undefined) return null;
        const n = Number(v);
        return Number.isFinite(n) ? n : null;
      };
  
      if (Array.isArray(data) && data.length > 0) {
        const keysCost = ['avg_cost', 'cost_score', 'costScore', 'cost'];
        const keysAcad = ['avg_academics', 'academic_score', 'academics_score', 'academics'];
        const keysSocial = ['avg_social', 'social_score', 'student_life', 'social'];
        const keysAcc = ['avg_accommodation', 'accommodation_score', 'housing', 'accommodation'];
  
        const sums = { cost: 0, acad: 0, social: 0, acc: 0 };
        const counts = { cost: 0, acad: 0, social: 0, acc: 0 };
  
        data.forEach((r) => {
          const c = asNumber(read(r, keysCost)); if (c !== null) { sums.cost += c; counts.cost += 1; }
          const a = asNumber(read(r, keysAcad)); if (a !== null) { sums.acad += a; counts.acad += 1; }
          const s = asNumber(read(r, keysSocial)); if (s !== null) { sums.social += s; counts.social += 1; }
          const ac = asNumber(read(r, keysAcc)); if (ac !== null) { sums.acc += ac; counts.acc += 1; }
        });
  
        const avgCost = counts.cost ? +(sums.cost / counts.cost).toFixed(2) : null;
        const avgAcad = counts.acad ? +(sums.acad / counts.acad).toFixed(2) : null;
        const avgSocial = counts.social ? +(sums.social / counts.social).toFixed(2) : null;
        const avgAcc = counts.acc ? +(sums.acc / counts.acc).toFixed(2) : null;
  
        const overallParts = [avgCost, avgAcad, avgSocial, avgAcc].filter(v => v !== null);
        const overall = overallParts.length ? +(overallParts.reduce((x, y) => x + y, 0) / overallParts.length).toFixed(2) : null;
  
        setSelectedUniDetails(prev => ({
          ...(prev || {}),
          avg_cost: avgCost,
          avg_academics: avgAcad,
          avg_social: avgSocial,
          avg_accommodation: avgAcc,
          overall_score: overall,
          review_count: data.length
        }));
  
        setReviewsRaw(data);
        setReviewsVisibleCount(5);
  
        await fetchAISummary(uniName);
        return { avgCost, avgAcad, avgSocial, avgAcc, overall, review_count: data.length, theme_summary: null }; // Return aggregated data
      } else if (data && typeof data === 'object') {
        const read = (obj, keys) => {
          if (!obj) return null;
          for (const k of keys) {
            if (obj[k] !== undefined && obj[k] !== null) return obj[k];
          }
          return null;
        };
  
        setSelectedUniDetails(prev => ({
          ...(prev || {}),
          avg_cost: read(data, ['avg_cost', 'cost_score', 'costScore', 'cost']) ?? prev?.avg_cost,
          avg_academics: read(data, ['avg_academics', 'academic_score', 'academics_score', 'academics']) ?? prev?.avg_academics,
          avg_social: read(data, ['avg_social', 'social_score', 'student_life', 'social']) ?? prev?.avg_social,
          avg_accommodation: read(data, ['avg_accommodation', 'accommodation_score', 'housing', 'accommodation']) ?? prev?.avg_accommodation,
          overall_score: read(data, ['overall_score', 'avg_overall', 'score', 'rating']) ?? prev?.overall_score,
          review_count: data.review_count ?? prev?.review_count
        }));
        setReviewsRaw([data]);
        setReviewsVisibleCount(5);
        await fetchAISummary(uniName);
        return { 
          avg_cost: read(data, ['avg_cost', 'cost_score', 'costScore', 'cost']) ?? null,
          avg_academics: read(data, ['avg_academics', 'academic_score', 'academics_score', 'academics']) ?? null,
          avg_social: read(data, ['avg_social', 'social_score', 'student_life', 'social']) ?? null,
          avg_accommodation: read(data, ['avg_accommodation', 'accommodation_score', 'housing', 'accommodation']) ?? null,
          overall_score: read(data, ['overall_score', 'avg_overall', 'score', 'rating']) ?? null,
          review_count: data.review_count ?? 0,
          theme_summary: null
        }; // Return aggregated data
      } else if (typeof data === 'string') {
        setReviewsContent(data);
        return { theme_summary: data }; // Return summary string
      } else {
        setReviewsContent('No AI summary available.');
        return { theme_summary: 'No AI summary available.' };
      }
    } catch (err) {
      console.error("Error fetching reviews:", err);
      setReviewsContent('Failed to fetch individual reviews from backend. Please try again later.');
      return { theme_summary: 'Failed to fetch reviews.' };
    }
  };
  
  const handleSelectForComparison = async (uniData) => {
    // Fetch full details for the university when it's selected for comparison
    const fullUniDetails = await fetchReviews(uniData.uni_name);

    if (!fullUniDetails) {
      console.error("Could not fetch full details for comparison selection.", uniData);
      return;
    }

    const uniWithDetails = { ...uniData, ...fullUniDetails };

    if (!compareUni1) {
      setCompareUni1(uniWithDetails);
    } else if (compareUni1 && uniWithDetails.uni_name === compareUni1.uni_name) {
      // Deselect Uni 1 if clicked again
      setCompareUni1(null);
    } else if (!compareUni2) {
      setCompareUni2(uniWithDetails);
    } else if (compareUni2 && uniWithDetails.uni_name === compareUni2.uni_name) {
      // Deselect Uni 2 if clicked again
      setCompareUni2(null);
    } else {
      // If both are selected and a new one is clicked, maybe replace one or do nothing
      console.warn("Both comparison slots are full. Cannot add more for now.");
    }
  };

  // (filters and list removed; reviews handled via fetchReviews)

  // Fetching Aggregated Data
  useEffect(() => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
  
    axios.get(`${BACKEND_URL}/api/unis`)
      .then(response => {
        setUnis(response.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching data:", err);
        setError("Failed to fetch university data from backend. Please check if the server is running or reachable.");
        setLoading(false);
      });
  }, []);
  
  // Small helper to read a numeric score from multiple possible backend field names
  const readScore = (obj, keys) => {
    if (!obj) return null;
    for (const k of keys) {
      const v = obj[k];
      if (v !== undefined && v !== null) return v;
    }
    return null;
  };

  // Call the backend synthesis endpoint to get a single AI summary for the university
  const fetchAISummary = async (uniName) => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
    setLoadingAISummary(true);
  
    try {
      const r = await axios.get(`${BACKEND_URL}/api/summary/${encodeURIComponent(uniName)}`);
      
      if (r.data && r.data.summary) {
        setReviewsContent(String(r.data.summary));
        return String(r.data.summary);
      } else if (r.data && r.data.error) {
        setReviewsContent(`AI synthesis error: ${r.data.error}.`);
        return `AI synthesis error: ${r.data.error}.`;
      } else {
        setReviewsContent('No AI summary available for this university.');
        return 'No AI summary available.';
      }
    } catch (e) {
      console.error("Error fetching AI summary:", e);
      setReviewsContent('Failed to fetch AI summary from backend. Please ensure the backend is running or try again later.');
      return 'Failed to fetch AI summary.';
    } finally {
        setLoadingAISummary(false);
    }
  };
  

  if (loading) return (
    <div className="d-flex justify-content-center align-items-center w-100 h-100" style={{ height: '100vh' }}>
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading universities...</span>
        </div>
        <p className="mt-3">Loading university data...</p>
      </div>
    </div>
  );
  if (error) return (
    <div className="d-flex justify-content-center align-items-center w-100 h-100" style={{ height: '100vh' }}>
      <div className="alert alert-danger text-center" role="alert">
        <h4 className="alert-heading">Connection Error!</h4>
        <p>Failed to fetch university data from the backend. Please ensure the server is running and reachable.</p>
        <p className="mb-0 small text-break">Details: {error}</p>
      </div>
    </div>
  );

  // No list filters in the new layout — the map drives selection.

  // Ensure map shows markers for all known cities even if there are no reviews
  const mergedUnis = (() => {
    const out = [...unis];
    const citiesWithUnis = new Set(unis.map(u => u.city));
    Object.keys(CITY_COORDINATES).forEach(city => {
      if (!citiesWithUnis.has(city)) {
        out.push({
          uni_name: `${city} (no reviews)`,
          city: city,
          overall_score: null,
          avg_cost: null,
          avg_academics: null,
          avg_social: null,
          avg_accommodation: null,
          review_count: 0,
        });
      }
    });
    return out;
  })();

  return (
  <div className="container-fluid py-4"> {/* Use container-fluid for max width */}
    <header className="app-header text-center mb-4">
      <h1 className="display-5">ExchangeCompass: GJU Edition 🧭</h1>
      <p className="lead text-muted">Data-Driven Insights for Your German Exchange</p>
    </header>

    {/* Comparison Controls (visible above the split view) */}
    <div className="d-flex justify-content-center mb-3">
      <Button 
        variant="primary" 
        onClick={() => setShowComparison(true)} 
        disabled={!compareUni1 || !compareUni2} // Enable only when both are selected
        className="me-2"
      >
        Compare Selected Universities ({[compareUni1, compareUni2].filter(Boolean).length}/2)
      </Button>
      <Button 
        variant="secondary" 
        onClick={() => { setCompareUni1(null); setCompareUni2(null); setShowComparison(false); setReviewsContent(null); }}
        disabled={!compareUni1 && !compareUni2} // Enable if any uni is selected for comparison
      >
        Clear Comparison
      </Button>
    </div>

    {showComparison ? (
      <div className="comparison-view-full-width container-fluid">
        {/* Back to Map button */}
        <div className="text-center mb-3">
          <Button variant="outline-secondary" onClick={() => setShowComparison(false)}>
            Back to Map
          </Button>
        </div>
        <div className="row">
          {/* University 1 Column */}
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h3 className="card-title">{compareUni1?.uni_name || 'Select University 1'}</h3>
                <p className="card-subtitle mb-2 text-muted">{compareUni1?.city}</p>
                <RadarChartComponent uniData={compareUni1} />
                {/* Add other details for Uni 1 as needed */}
                <div className="mb-3">
                  <span className="badge bg-primary me-2">Academics: {readScore(compareUni1, ['avg_academics','academic_score','academics_score','academics']) ?? '—'}</span>
                  <span className="badge bg-success me-2">Cost: {readScore(compareUni1, ['avg_cost','cost_score','costScore','cost']) ?? '—'}</span>
                  <span className="badge bg-warning text-dark me-2">Social: {readScore(compareUni1, ['avg_social','social_score','student_life','social']) ?? '—'}</span>
                  <span className="badge bg-info text-dark">Accommodation: {readScore(compareUni1, ['avg_accommodation','accommodation_score','housing','accommodation']) ?? '—'}</span>
                </div>
                 <h6>AI Summary</h6>
                <p className="small">{compareUni1?.theme_summary || 'No AI summary available.'}</p>
              </div>
            </div>
          </div>

          {/* University 2 Column */}
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h3 className="card-title">{compareUni2?.uni_name || 'Select University 2'}</h3>
                <p className="card-subtitle mb-2 text-muted">{compareUni2?.city}</p>
                <RadarChartComponent uniData={compareUni2} />
                {/* Add other details for Uni 2 as needed */}
                <div className="mb-3">
                  <span className="badge bg-primary me-2">Academics: {readScore(compareUni2, ['avg_academics','academic_score','academics_score','academics']) ?? '—'}</span>
                  <span className="badge bg-success me-2">Cost: {readScore(compareUni2, ['avg_cost','cost_score','costScore','cost']) ?? '—'}</span>
                  <span className="badge bg-warning text-dark me-2">Social: {readScore(compareUni2, ['avg_social','social_score','student_life','social']) ?? '—'}</span>
                  <span className="badge bg-info text-dark">Accommodation: {readScore(compareUni2, ['avg_accommodation','accommodation_score','housing','accommodation']) ?? '—'}</span>
                </div>
                <h6>AI Summary</h6>
                <p className="small">{compareUni2?.theme_summary || 'No AI summary available.'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    ) : (
      <div className="split-screen">
        {/* LEFT: Detail pane (fixed half) */}
        <div className="left-pane">
          <div className="p-3 d-flex flex-column" style={{height: '100%'}}>
            {!selectedUniDetails ? (
              <div className="d-flex align-items-center justify-content-center h-100 text-muted">
                <div style={{textAlign: 'center'}}>
                  <h5>Select a university from the map</h5>
                  <p className="small">Click any marker on the right to view full details and AI review here.</p>
                </div>
              </div>
            ) : (
              <div className="card h-100 overflow-auto">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <div>
                      <h3 className="mb-1">{selectedUniDetails.uni_name}</h3>
                      <div className="text-muted small">{selectedUniDetails.city}</div>
                    </div>
                  </div>

                  {/* Star rating + numeric */}
                  <div className="mb-3 d-flex align-items-center gap-2">
                    <div>
                      {(() => {
                        const raw = Number(selectedUniDetails?.overall_score) || 0;
                        const rounded = Math.round(raw); // 0..5
                        return Array.from({ length: 5 }).map((_, i) => (
                          <span key={i} className="star">{i < rounded ? '★' : '☆'}</span>
                        ));
                      })()}
                    </div>
                    <div className="small text-muted">{selectedUniDetails?.overall_score?.toFixed ? selectedUniDetails.overall_score.toFixed(2) : selectedUniDetails?.overall_score} • {selectedUniDetails?.review_count ?? 0} reviews</div>
                  </div>

                  {/* Key metric badges */}
                  <div className="mb-3">
                    <span className="badge bg-primary me-2">Academics: {readScore(selectedUniDetails, ['avg_academics','academic_score','academics_score','academics']) ?? '—'}</span>
                    <span className="badge bg-success me-2">Cost: {readScore(selectedUniDetails, ['avg_cost','cost_score','costScore','cost']) ?? '—'}</span>
                    <span className="badge bg-warning text-dark me-2">Social: {readScore(selectedUniDetails, ['avg_social','social_score','student_life','social']) ?? '—'}</span>
                    <span className="badge bg-info text-dark">Accommodation: {readScore(selectedUniDetails, ['avg_accommodation','accommodation_score','housing','accommodation']) ?? '—'}</span>
                  </div>

                  {/* Radar Chart */}
                  <div className="mb-3">
                    <RadarChartComponent uniData={selectedUniDetails} />
                  </div>

                  {/* AI review toggle */}
                  <div className="mb-2">
                    <Button variant="link" onClick={() => setShowAIReview(s => !s)}>{showAIReview ? 'Hide AI review' : 'Show AI review'}</Button>
                  </div>

                  {showAIReview && (
                    <div className="ai-review mb-3" style={{ minHeight: '100px' }}> {/* Added minHeight to prevent twitching */}
                      {loadingAISummary ? (
                        <div className="d-flex align-items-center justify-content-center h-100 text-muted">
                          <div className="spinner-border spinner-border-sm text-primary me-2" role="status">
                            <span className="visually-hidden">Loading AI summary...</span>
                          </div>
                          <div className="small text-muted">Generating AI summary...</div>
                        </div>
                      ) : reviewsContent ? (
                        <div className="small">{reviewsContent}</div>
                      ) : (
                        <div className="small text-muted">No AI summary available for this university.</div>
                      )}
                    </div>
                  )}

                  {/* Student reviews list */}
                  <div className="reviews-section mt-3">
                    <h6>Student reviews</h6>
                    {reviewsRaw && reviewsRaw.length > 0 ? (
                      <div className="reviews-list">
                        {reviewsRaw.slice(0, reviewsVisibleCount).map((r, idx) => (
                          <div className="review-item" key={idx}>
                            <div className="review-meta small text-muted">{r.author || r.student || 'Student'} • {r.created_at || r.date || ''}</div>
                            <div className="review-body">{r.raw_review_text || r.raw_review || r.review_text || r.comment || r.summary || r.theme_summary || 'No text provided'}</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="small text-muted">No student reviews available.</div>
                    )}
                    {reviewsRaw && reviewsRaw.length > reviewsVisibleCount && (
                      <div className="mt-2 text-center">
                        <Button variant="outline-primary" size="sm" onClick={() => setReviewsVisibleCount(c => c + 5)}>Load more</Button>
                      </div>
                    )}
                  </div>

                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: MAP */}
        <div className="right-pane">
          <div className="card h-100 shadow-lg">
            <div className="card-header bg-dark text-white">
              Geospatial View (Cost of Living Heatmap)
            </div>
            <div className="card-body p-0 d-flex flex-column" style={{minHeight: 0}}>
              <MapComponent 
                unis={mergedUnis} 
                coords={CITY_COORDINATES} 
                handleMarkerClick={handleMarkerClick}
                handleSelectForComparison={handleSelectForComparison}
                compareUni1={compareUni1}
                compareUni2={compareUni2}
              />
            </div>
          </div>
        </div>
      </div>
    )}

  </div>
  );

}

export default App;
