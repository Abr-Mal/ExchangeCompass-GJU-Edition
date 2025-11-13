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

  // State for major filtering
  const [selectedMajor, setSelectedMajor] = useState(''); // '' means no filter
  const [availableMajorsList, setAvailableMajorsList] = useState([]);

  // State for new review form
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReviewText, setNewReviewText] = useState('');
  const [newAcademicsScore, setNewAcademicsScore] = useState(3); // Default to 3
  const [newCostScore, setNewCostScore] = useState(3); // Default to 3
  const [newSocialScore, setNewSocialScore] = useState(3); // Default to 3
  const [newAccommodationScore, setNewAccommodationScore] = useState(3); // Default to 3
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewMessage, setReviewMessage] = useState(null); // For success/error messages

  // New state for comparison feature
  const [compareUni1, setCompareUni1] = useState(null);
  const [compareUni2, setCompareUni2] = useState(null);
  const [showComparison, setShowComparison] = useState(false); // Controls whether to show comparison view

  // When a marker is clicked, show its details in the right pane
  const handleMarkerClick = (uniData) => {
    setSelectedUniDetails(uniData);
    setHighlightedUni(uniData.uni_name);
    fetchAggregatedUniversityDetails(uniData.uni_name);
  };

  const fetchReviews = async (uniName) => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
    try {
      const res = await axios.get(`${BACKEND_URL}/api/reviews/${encodeURIComponent(uniName)}`);
      return res.data; // This endpoint now only returns raw reviews
    } catch (err) {
      console.error("Error fetching raw reviews:", err);
      return [];
    }
  };

  const fetchAggregatedUniversityDetails = async (uniName) => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
    setLoadingAISummary(true); // Re-using this for overall data loading indication
    try {
      const res = await axios.get(`${BACKEND_URL}/api/university/${encodeURIComponent(uniName)}`);
      const data = res.data; // This will be a single aggregated university object
      console.log("Fetched aggregated university details:", data); // DEBUG LOG
  
      if (data && !data.error) {
        // Update selectedUniDetails state with the aggregated data
        setSelectedUniDetails(data);
        setReviewsContent(data.theme_summary || 'No AI summary available.');
        // Fetch individual raw reviews separately for the list
        const rawReviews = await fetchReviews(uniName); 
        setReviewsRaw(rawReviews);
        setReviewsVisibleCount(5); // Reset visible count on new selection
        return data; // Return the full aggregated data
      } else {
        setReviewsContent(data?.error || `No details found for ${uniName}.`);
        setSelectedUniDetails(null); // Clear details if not found
        setReviewsRaw([]);
        return null; 
      }
    } catch (err) {
      console.error("Error fetching aggregated university details:", err);
      setError("Failed to fetch university details. Please check server or try again.");
      setSelectedUniDetails(null);
      setReviewsRaw([]);
      setReviewsContent('Failed to load details.');
      return null;
    } finally {
      setLoadingAISummary(false);
    }
  };

  const handleSelectForComparison = async (uniData) => {
    // Fetch full details for the university when it's selected for comparison
    const fullUniDetails = await fetchAggregatedUniversityDetails(uniData.uni_name);

    if (!fullUniDetails) {
      console.error("Could not fetch full details for comparison selection.", uniData);
      return;
    }

    const uniWithDetails = { ...uniData, ...fullUniDetails };

    if (!compareUni1) {
      setCompareUni1(uniWithDetails);
    } else if (compareUni1.uni_name === uniWithDetails.uni_name) {
      // Deselect Uni 1 if clicked again
      setCompareUni1(null);
    } else if (!compareUni2) {
      // Check if Uni 2 is different from Uni 1 before setting
      if (compareUni1 && uniWithDetails.uni_name === compareUni1.uni_name) {
        console.log("Attempted to select the same university for both comparison slots.");
        return; // Prevent selecting the same university twice
      }
      setCompareUni2(uniWithDetails);
    } else if (compareUni2.uni_name === uniWithDetails.uni_name) {
      // Deselect Uni 2 if clicked again
      setCompareUni2(null);
    } else {
      console.warn("Both comparison slots are full. To compare a new university, please deselect one first.");
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!selectedUniDetails || !newReviewText.trim()) {
      setReviewMessage({
        type: 'danger',
        text: 'Please select a university and provide a review text.'
      });
      return;
    }

    setSubmittingReview(true);
    setReviewMessage(null); // Clear previous messages
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";

    try {
      const reviewData = {
        uni_name: selectedUniDetails.uni_name,
        city: selectedUniDetails.city,
        raw_review_text: newReviewText,
        academics_score: parseInt(newAcademicsScore),
        cost_score: parseInt(newCostScore),
        social_score: parseInt(newSocialScore),
        accommodation_score: parseInt(newAccommodationScore),
      };

      const response = await axios.post(`${BACKEND_URL}/api/submit_review`, reviewData);

      if (response.status === 201) {
        setReviewMessage({
          type: 'success',
          text: 'Review submitted successfully! It will be visible shortly.'
        });
        // Optionally clear the form or hide it
        setNewReviewText('');
        setNewAcademicsScore(3);
        setNewCostScore(3);
        setNewSocialScore(3);
        setNewAccommodationScore(3);
        setShowReviewForm(false);
        // Re-fetch university details and reviews to reflect the new submission
        fetchAggregatedUniversityDetails(selectedUniDetails.uni_name);
      } else {
        setReviewMessage({
          type: 'danger',
          text: `Failed to submit review: ${response.data.error || 'Unknown error'}`
        });
      }
    } catch (error) {
      console.error("Error submitting review:", error);
      setReviewMessage({
        type: 'danger',
        text: `Failed to submit review: ${error.response?.data?.error || error.message}`
      });
    } finally {
      setSubmittingReview(false);
    }
  };

  // Initial Data Fetching (All Unis for Map)
  useEffect(() => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
  
    // Fetch available majors
    axios.get(`${BACKEND_URL}/api/majors`)
      .then(response => {
        setAvailableMajorsList(response.data);
      })
      .catch(err => {
        console.error("Error fetching majors:", err);
      });

    // Fetch universities, applying major filter if selected
    const unisUrl = selectedMajor 
      ? `${BACKEND_URL}/api/unis?major=${encodeURIComponent(selectedMajor)}`
      : `${BACKEND_URL}/api/unis`;

    axios.get(unisUrl)
      .then(response => {
        setUnis(response.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching data:", err);
        setError("Failed to fetch university data from backend. Please check if the server is running or reachable.");
        setLoading(false);
      });
  }, [selectedMajor]); // Add selectedMajor to dependency array to re-fetch when filter changes
  
  // Small helper to read a numeric score from multiple possible backend field names
  const readScore = (obj, keys) => {
    if (!obj) return null;
    for (const k of keys) {
      const v = obj[k];
      if (v !== undefined && v !== null) return v;
    }
    return null;
  };

  // The fetchAISummary is now just a helper to get the raw summary text
  const fetchAISummary = async (uniName) => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:5000";
    // setLoadingAISummary(true); // Removed as main fetch will handle it
  
    try {
      const r = await axios.get(`${BACKEND_URL}/api/summary/${encodeURIComponent(uniName)}`);
      if (r.data && r.data.summary) {
        return String(r.data.summary);
      } else if (r.data && r.data.error) {
        return `AI summary error: ${r.data.error}.`;
      } else {
        return 'No AI summary available.';
      }
    } catch (e) {
      console.error("Error fetching AI summary:", e);
      return 'Failed to fetch AI summary.';
    } finally {
      // setLoadingAISummary(false); // Removed as main fetch will handle it
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
    {(compareUni1 || compareUni2) && (
      <div className="comparison-bar d-flex justify-content-center mb-3">
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
    )}

    {showComparison ? (
      <div className="comparison-view-full-width container-fluid" style={{ top: `calc(var(--app-header-height) + var(--comparison-controls-height))` }}>
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
      <div className="split-screen" style={{ top: `calc(var(--app-header-height) ${compareUni1 || compareUni2 ? '+ var(--comparison-controls-height)' : ''})` }}>
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

                  {/* Add Review Button */}
                  <div className="mb-3">
                    <Button variant="outline-primary" onClick={() => setShowReviewForm(s => !s)}>
                      {showReviewForm ? 'Cancel Review' : 'Add Your Review'}
                    </Button>
                  </div>

                  {/* Review Submission Form */}
                  {showReviewForm && (
                    <div className="review-form-section mb-4 p-3 border rounded bg-light">
                      <h6>Submit Your Review for {selectedUniDetails.uni_name}</h6>
                      {reviewMessage && (
                        <div className={`alert alert-${reviewMessage.type}`} role="alert">
                          {reviewMessage.text}
                        </div>
                      )}
                      <form onSubmit={handleSubmitReview}>
                        <div className="mb-3">
                          <label htmlFor="reviewText" className="form-label small">Your Comments:</label>
                          <textarea
                            className="form-control"
                            id="reviewText"
                            rows="3"
                            value={newReviewText}
                            onChange={(e) => setNewReviewText(e.target.value)}
                            required
                            disabled={submittingReview}
                          ></textarea>
                        </div>
                        <div className="row mb-3">
                          <div className="col-md-6 mb-2">
                            <label htmlFor="academicsScore" className="form-label small">Academics (1-5):</label>
                            <input type="number" className="form-control" id="academicsScore" min="1" max="5" value={newAcademicsScore} onChange={(e) => setNewAcademicsScore(e.target.value)} disabled={submittingReview} />
                          </div>
                          <div className="col-md-6 mb-2">
                            <label htmlFor="costScore" className="form-label small">Cost (1-5, 5=cheap):</label>
                            <input type="number" className="form-control" id="costScore" min="1" max="5" value={newCostScore} onChange={(e) => setNewCostScore(e.target.value)} disabled={submittingReview} />
                          </div>
                          <div className="col-md-6 mb-2">
                            <label htmlFor="socialScore" className="form-label small">Social (1-5):</label>
                            <input type="number" className="form-control" id="socialScore" min="1" max="5" value={newSocialScore} onChange={(e) => setNewSocialScore(e.target.value)} disabled={submittingReview} />
                          </div>
                          <div className="col-md-6 mb-2">
                            <label htmlFor="accommodationScore" className="form-label small">Accommodation (1-5, 5=easy):</label>
                            <input type="number" className="form-control" id="accommodationScore" min="1" max="5" value={newAccommodationScore} onChange={(e) => setNewAccommodationScore(e.target.value)} disabled={submittingReview} />
                          </div>
                        </div>
                        <Button type="submit" variant="success" disabled={submittingReview}>
                          {submittingReview ? 'Submitting...' : 'Submit Review'}
                        </Button>
                      </form>
                    </div>
                  )}

                  {/* Student reviews list */}
                  <div className="reviews-section mt-3">
                    <h6>Student reviews</h6>
                    {reviewsRaw && reviewsRaw.length > 0 ? (
                      <div className="reviews-list">
                        {reviewsRaw.slice(0, reviewsVisibleCount).map((r, idx) => (
                          <div className="review-item" key={r.id || idx}>
                            <div className="review-meta small text-muted">
                              {r.reviewer_type === 'user_submitted' ? 'User Review' : (r.source_type === 'html_scrape' ? 'Web Scrape' : 'Survey')}
                              {r.academics_score && (
                                <span className="ms-2 badge bg-primary">A:{r.academics_score}</span>
                              )}
                              {r.cost_score && (
                                <span className="ms-1 badge bg-success">C:{r.cost_score}</span>
                              )}
                              {r.social_score && (
                                <span className="ms-1 badge bg-warning text-dark">S:{r.social_score}</span>
                              )}
                              {r.accommodation_score && (
                                <span className="ms-1 badge bg-info text-dark">H:{r.accommodation_score}</span>
                              )}
                            </div>
                            <div className="review-body">{r.raw_review_text || 'No text provided'}</div>
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
            <div className="card-header bg-dark text-white d-flex justify-content-between align-items-center">
              <span>Geospatial View (Cost of Living Heatmap)</span>
              {/* Major Filter Dropdown integrated into the map header */}
              <div className="major-filter-map-header">
                <label htmlFor="majorFilterMap" className="visually-hidden">Filter by Major:</label>
                <select 
                  id="majorFilterMap" 
                  className="form-select form-select-sm text-white border-secondary"
                  value={selectedMajor}
                  onChange={(e) => setSelectedMajor(e.target.value)}
                >
                  <option value="">All Majors</option>
                  {availableMajorsList.map(major => (
                    <option key={major} value={major}>{major}</option>
                  ))}
                </select>
              </div>
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
