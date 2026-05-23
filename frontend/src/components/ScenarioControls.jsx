import React from 'react'

const scenarios = [
  {
    id: 'flood_grid',
    name: 'Flood + Grid Failure',
    description: 'Heavy rainfall causing power grid cascades'
  },
  {
    id: 'heat_hospital',
    name: 'Heat + Hospital Crisis',
    description: 'Extreme heat overwhelming medical infrastructure'
  },
  {
    id: 'cyclone_comms',
    name: 'Cyclone + Comms Down',
    description: 'High winds disrupting telecommunications'
  }
]

function ScenarioControls({ activeScenario, onStart, onStop }) {
  const handleScenarioClick = async (scenarioId) => {
    if (activeScenario === scenarioId) {
      // Stop the scenario
      await onStop(scenarioId)
    } else {
      // Stop current scenario if any, then start new one
      if (activeScenario) {
        await onStop(activeScenario)
      }
      await onStart(scenarioId)
    }
  }

  return (
    <div>
      <div className="panel-title">SCENARIO CONTROLS</div>

      {scenarios.map(scenario => (
        <button
          key={scenario.id}
          className={`scenario-btn ${activeScenario === scenario.id ? 'active' : ''}`}
          onClick={() => handleScenarioClick(scenario.id)}
        >
          <div style={{ fontWeight: '600' }}>
            {scenario.name}
          </div>
          <div style={{ fontSize: '10px', opacity: 0.8, marginTop: '2px' }}>
            {scenario.description}
          </div>
          {activeScenario === scenario.id && (
            <div style={{ fontSize: '10px', marginTop: '4px', color: '#FEE2E2' }}>
              ● ACTIVE - Click to stop
            </div>
          )}
        </button>
      ))}

      {!activeScenario && (
        <div style={{
          marginTop: '16px',
          fontSize: '11px',
          color: '#64748B',
          textAlign: 'center'
        }}>
          Select scenario to begin simulation
        </div>
      )}

      {activeScenario && (
        <div style={{
          marginTop: '16px',
          padding: '8px',
          background: '#1F2937',
          borderRadius: '4px',
          fontSize: '11px'
        }}>
          <div style={{ color: '#94A3B8', marginBottom: '4px' }}>STATUS</div>
          <div style={{ color: '#10B981' }}>
            ● Generating incidents every 3s
          </div>
          <div style={{ color: '#10B981' }}>
            ● Broadcasting alerts every 5s
          </div>
        </div>
      )}
    </div>
  )
}

export default ScenarioControls