import React, { useState, useEffect } from 'react'
import IncidentMap from './components/IncidentMap'
import CascadePanel from './components/CascadePanel'
import ScenarioControls from './components/ScenarioControls'

function App() {
  const [incidents, setIncidents] = useState([])
  const [alerts, setAlerts] = useState([])
  const [activeScenario, setActiveScenario] = useState(null)
  const [currentAlert, setCurrentAlert] = useState(null)

  useEffect(() => {
    // WebSocket connections
    const incidentWS = new WebSocket('ws://localhost:8000/ws/incidents')
    const alertWS = new WebSocket('ws://localhost:8000/ws/alerts')

    incidentWS.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'incident') {
        setIncidents(prev => [message.data, ...prev.slice(0, 49)]) // Keep last 50
      }
    }

    alertWS.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'alert') {
        setCurrentAlert(message.data)
        setAlerts(prev => [message.data, ...prev.slice(0, 19)]) // Keep last 20
      }
    }

    return () => {
      incidentWS.close()
      alertWS.close()
    }
  }, [])

  const startScenario = async (scenarioType) => {
    try {
      const response = await fetch(`http://localhost:8000/scenario/${scenarioType}`, {
        method: 'POST'
      })
      if (response.ok) {
        setActiveScenario(scenarioType)
      }
    } catch (error) {
      console.error('Failed to start scenario:', error)
    }
  }

  const stopScenario = async (scenarioType) => {
    try {
      await fetch(`http://localhost:8000/scenario/${scenarioType}`, {
        method: 'DELETE'
      })
      setActiveScenario(null)
    } catch (error) {
      console.error('Failed to stop scenario:', error)
    }
  }

  return (
    <div className="dashboard">
      <div className="map-section">
        <IncidentMap incidents={incidents} />
      </div>
      <div className="cascade-panel">
        <CascadePanel alert={currentAlert} />
      </div>
      <div className="controls-panel">
        <ScenarioControls
          activeScenario={activeScenario}
          onStart={startScenario}
          onStop={stopScenario}
        />
      </div>
    </div>
  )
}

export default App