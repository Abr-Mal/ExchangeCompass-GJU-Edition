// frontend/src/MapComponent.jsx

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for Leaflet's default marker icon issue in React.
// This is necessary because Webpack (or Vite) may not correctly handle
// Leaflet's default icon paths, leading to broken marker images.
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Helper function: Converts a hexadecimal color string to an RGB object.
const hexToRgb = (hex) => {
    const h = hex.replace('#','');
    const bigint = parseInt(h, 16);
    return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
};

// Helper function: Converts RGB color components to a hexadecimal color string.
const rgbToHex = (r,g,b) => {
    const toHex = (n) => n.toString(16).padStart(2,'0');
    return `#${toHex(Math.round(r))}${toHex(Math.round(g))}${toHex(Math.round(b))}`;
};

// Helper function: Performs linear interpolation between two values.
const lerp = (a,b,t) => a + (b-a)*t;

/**
 * Generates a color based on a given score, creating a smooth 3-color gradient
 * from red (low score/expensive) to yellow (medium) to green (high score/cheap).
 * A gray color is returned for null, undefined, or non-finite scores.
 * The score is clamped between 0 and 5 for consistent color mapping.
 * @param {number | null | undefined} score - The score (e.g., cost score) to map to a color.
 * @returns {string} A hexadecimal color string.
 */
const getColorByCost = (score) => {
    if (score === null || score === undefined) return '#9aa0a6'; // Gray fallback for unknown scores.
    const s = Number(score);
    if (!Number.isFinite(s)) return '#9aa0a6';
    // Clamp the score to the assumed scale of 0 to 5.
    const clamped = Math.max(0, Math.min(5, s));
    // Normalize the clamped score to a 0-1 range.
    const t = clamped / 5; 

    // Define the gradient colors: red for low scores, yellow for mid, green for high.
    const red = '#d73027';   
    const yellow = '#fee08b';
    const green = '#1a9850'; 

    if (t <= 0.5) {
        // Blend from red to yellow for the lower half of the score range.
        const tt = t / 0.5;
        const c1 = hexToRgb(red), c2 = hexToRgb(yellow);
        const r = lerp(c1.r, c2.r, tt);
        const g = lerp(c1.g, c2.g, tt);
        const b = lerp(c1.b, c2.b, tt);
        return rgbToHex(r,g,b);
    } else {
        // Blend from yellow to green for the upper half of the score range.
        const tt = (t - 0.5) / 0.5;
        const c1 = hexToRgb(yellow), c2 = hexToRgb(green);
        const r = lerp(c1.r, c2.r, tt);
        const g = lerp(c1.g, c2.g, tt);
        const b = lerp(c1.b, c2.b, tt);
        return rgbToHex(r,g,b);
    }
};

/**
 * MapComponent displays an interactive Leaflet map with university markers.
 * Markers are colored based on the 'cost' score, creating a visual heatmap.
 * Clicking a marker triggers a callback to display detailed university information.
 * @param {Object} props - The component props.
 * @param {Array<Object>} props.unis - An array of university data objects.
 * @param {Object} props.coords - An object mapping city names to their [latitude, longitude] coordinates.
 * @param {Function} props.handleMarkerClick - Callback function executed when a map marker is clicked.
 */
const MapComponent = ({ unis, coords, handleMarkerClick }) => {
    // Set a central point of Germany to initially center the map view.
    const center = [51.1657, 10.4515]; 

    // Helper function to safely read a value from an object using multiple possible keys.
    const read = (obj, keys) => {
        for (const k of keys) if (obj && obj[k] !== undefined && obj[k] !== null) return obj[k];
        return null;
    };

    return (
        <MapContainer center={center} zoom={6} style={{ height: '100%', width: '100%' }}>
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
            />

            {/* Render a Marker for each university. */}
            {unis.map(uni => {
                const position = coords[uni.city];
                if (!position) return null; // Skip rendering a marker if coordinates are missing for the city.

                // Read cost and academics values from the university object, checking multiple possible field names.
                const costVal = read(uni, ['avg_cost', 'cost_score', 'costScore', 'cost']);
                const academicsVal = read(uni, ['avg_academics', 'academic_score', 'academics_score', 'academics']);

                // Create a custom colored marker icon based on the calculated cost score.
                const customIcon = new L.DivIcon({
                    className: 'custom-div-icon',
                    // The background color of the marker div is determined by the cost value.
                    html: `<div style="background-color: ${getColorByCost(costVal)}; width: 30px; height: 30px; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>`,
                    iconSize: [30, 42],
                    iconAnchor: [15, 42],
                    popupAnchor: [0, -35]
                });

                return (
                    <Marker 
                        key={uni.uni_name} 
                        position={position} 
                        icon={customIcon}
                        // Attach an event handler to trigger when the marker is clicked.
                        eventHandlers={{ click: () => handleMarkerClick(uni) }}
                    >
                        <Popup>
                            <strong>{uni.uni_name}</strong><br/>
                            {/* Display average scores if reviews exist, otherwise indicate no reviews. */}
                            {uni.review_count ? (
                                <>
                                    Avg. Cost: {costVal ?? '—'}/5<br/>
                                    Avg. Academics: {academicsVal ?? '—'}/5
                                </>
                            ) : (
                                <span>No reviews yet</span>
                            )}
                        </Popup>
                    </Marker>
                );
            })}
        </MapContainer>
    );
};

export default MapComponent;