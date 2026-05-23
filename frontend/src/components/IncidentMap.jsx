import React from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import L from 'leaflet'

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Simple green circle for responders
const responderIcon = new L.DivIcon({
  className: 'responder-marker',
  html: '<div style="background: #10B981; border: 2px solid white; border-radius: 50%; width: 16px; height: 16px;"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

// Red alert triangle for incidents
const incidentIcon = new L.DivIcon({
  className: 'incident-marker',
  html: '<div style="background: #EF4444; border: 2px solid white; border-radius: 3px; width: 16px; height: 16px; transform: rotate(45deg);"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

const responders = [
  { id: 'fire-1', lat: 12.9716, lon: 77.5946, name: 'Fire Station 1' },
  { id: 'police-1', lat: 12.9616, lon: 77.6046, name: 'Police Station 1' },
  { id: 'medical-1', lat: 12.9816, lon: 77.5846, name: 'Medical Center 1' },
  { id: 'fire-2', lat: 12.9516, lon: 77.5746, name: 'Fire Station 2' },
  { id: 'police-2', lat: 12.9916, lon: 77.6146, name: 'Police Station 2' },
]

function IncidentMap({ incidents }) {
  return (
    <MapContainer
      center={[12.9716, 77.5946]}
      zoom={11}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
      />

      {/* Responder markers */}
      {responders.map(responder => (
        <Marker
          key={responder.id}
          position={[responder.lat, responder.lon]}
          icon={responderIcon}
        >
          <Popup>
            <div style={{ color: '#000' }}>
              <strong>{responder.name}</strong><br />
              Status: Active<br />
              Response Time: 3-5 min
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Recent incidents */}
      {incidents.slice(0, 20).map((incident, index) => (
        <Marker
          key={incident.report_id || index}
          position={[incident.location?.lat || 12.9716, incident.location?.lon || 77.5946]}
          icon={incidentIcon}
        >
          <Popup>
            <div style={{ color: '#000' }}>
              <strong>{incident.incident_type}</strong><br />
              Severity: {incident.severity}/5<br />
              Reporter: {incident.reporter_id}<br />
              Time: {new Date(incident.timestamp).toLocaleTimeString()}
              {incident.payload?.cascade_risk && (
                <><br />Risk: {(incident.payload.cascade_risk * 100).toFixed(1)}%</>
              )}
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Risk circles for recent high-severity incidents */}
      {incidents.slice(0, 5).filter(i => i.severity >= 4).map((incident, index) => (
        <Circle
          key={`circle-${incident.report_id || index}`}
          center={[incident.location?.lat || 12.9716, incident.location?.lon || 77.5946]}
          radius={incident.severity * 200}
          pathOptions={{
            color: '#EF4444',
            fillColor: '#EF4444',
            fillOpacity: 0.1,
            weight: 2,
          }}
        />
      ))}
    </MapContainer>
  )
}

export default IncidentMap