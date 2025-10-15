// frontend/src/MapComponent.jsx

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for Leaflet's default marker icon issue in React
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Helper: convert hex color to rgb object
const hexToRgb = (hex) => {
    const h = hex.replace('#','');
    const bigint = parseInt(h, 16);
    return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
};

// Helper: convert rgb to hex string
const rgbToHex = (r,g,b) => {
    const toHex = (n) => n.toString(16).padStart(2,'0');
    return `#${toHex(Math.round(r))}${toHex(Math.round(g))}${toHex(Math.round(b))}`;
};

// Linear interpolation
const lerp = (a,b,t) => a + (b-a)*t;

// Smooth 3-color gradient: red -> yellow -> green
const getColorByCost = (score) => {
    if (score === null || score === undefined) return '#9aa0a6'; // gray fallback for unknown
    const s = Number(score);
    if (!Number.isFinite(s)) return '#9aa0a6';
    // clamp to 0..5 (assumed scale)
    const clamped = Math.max(0, Math.min(5, s));
    const t = clamped / 5; // 0..1

    const red = '#d73027';   // low (bad) -> red
    const yellow = '#fee08b';
    const green = '#1a9850'; // high (good) -> green

    if (t <= 0.5) {
        // blend red -> yellow
        const tt = t / 0.5;
        const c1 = hexToRgb(red), c2 = hexToRgb(yellow);
        const r = lerp(c1.r, c2.r, tt);
        const g = lerp(c1.g, c2.g, tt);
        const b = lerp(c1.b, c2.b, tt);
        return rgbToHex(r,g,b);
    } else {
        // blend yellow -> green
        const tt = (t - 0.5) / 0.5;
        const c1 = hexToRgb(yellow), c2 = hexToRgb(green);
        const r = lerp(c1.r, c2.r, tt);
        const g = lerp(c1.g, c2.g, tt);
        const b = lerp(c1.b, c2.b, tt);
        return rgbToHex(r,g,b);
    }
};

const MapComponent = ({ unis, coords, handleMarkerClick }) => {
    // Use a central point of Germany to center the map initially
    const center = [51.1657, 10.4515]; 

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

            {unis.map(uni => {
                const position = coords[uni.city];
                if (!position) return null; // Skip if coordinates are missing

                // Read cost/academics from multiple possible field names
                const costVal = read(uni, ['avg_cost', 'cost_score', 'costScore', 'cost']);
                const academicsVal = read(uni, ['avg_academics', 'academic_score', 'academics_score', 'academics']);

                // Create a custom colored marker icon based on the cost score
                const customIcon = new L.DivIcon({
                    className: 'custom-div-icon',
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
                        eventHandlers={{ click: () => handleMarkerClick(uni) }}
                    >
                                                <Popup>
                                                        <strong>{uni.uni_name}</strong><br/>
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