import React from 'react'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

function CascadePanel({ alert }) {
  const analysis = alert?.analysis

  // Default values when no alert
  const defaultAnalysis = {
    overall_risk: 0.1,
    cascade_type: 'monitoring',
    domain_risks: {
      climate: 0.1,
      power_grid: 0.1,
      water: 0.1,
      medical: 0.1,
      telecom: 0.1
    },
    propagation_chain: [],
    confidence: 0.8
  }

  const currentAnalysis = analysis || defaultAnalysis

  // Prepare data for radial bar chart
  const riskData = [{
    name: 'Overall Risk',
    value: Math.round(currentAnalysis.overall_risk * 100),
    fill: currentAnalysis.overall_risk > 0.7 ? '#EF4444' :
          currentAnalysis.overall_risk > 0.4 ? '#F59E0B' : '#10B981'
  }]

  const getRiskClass = (risk) => {
    if (risk > 0.7) return 'risk-high'
    if (risk > 0.4) return 'risk-medium'
    return 'risk-low'
  }

  const getRiskLevel = (risk) => {
    if (risk > 0.7) return 'HIGH'
    if (risk > 0.4) return 'MED'
    return 'LOW'
  }

  const domains = [
    { name: 'Climate', key: 'climate' },
    { name: 'Power Grid', key: 'power_grid' },
    { name: 'Water', key: 'water' },
    { name: 'Medical', key: 'medical' },
    { name: 'Telecom', key: 'telecom' }
  ]

  return (
    <div>
      <div className="panel-title">CASCADE ANALYSIS</div>

      {/* Overall Risk Gauge */}
      <div className="risk-gauge">
        <div style={{ height: '120px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={riskData}>
              <RadialBar dataKey="value" cornerRadius={10} fill={riskData[0].fill} />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        <div style={{ textAlign: 'center', marginTop: '-60px' }}>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {riskData[0].value}%
          </div>
          <div style={{ fontSize: '12px', color: '#94A3B8' }}>
            {getRiskLevel(currentAnalysis.overall_risk)}
          </div>
        </div>
      </div>

      {/* Cascade Type */}
      <div style={{
        textAlign: 'center',
        marginBottom: '16px',
        padding: '4px 8px',
        background: '#1E293B',
        borderRadius: '12px',
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        {currentAnalysis.cascade_type.replace('_', ' ')}
      </div>

      {/* Domain Risks */}
      <div className="domain-flow">
        <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '8px', color: '#94A3B8' }}>
          DOMAIN RISKS
        </div>

        {domains.map(domain => {
          const risk = currentAnalysis.domain_risks[domain.key] || 0
          const isInChain = currentAnalysis.propagation_chain.includes(domain.key)

          return (
            <div
              key={domain.key}
              className="domain-node"
              style={{
                border: isInChain ? '1px solid #F59E0B' : '1px solid transparent',
                background: isInChain ? '#1F2937' : '#1E293B'
              }}
            >
              <div className={`status-indicator ${getRiskClass(risk)}`}></div>
              <div style={{ flex: 1 }}>{domain.name}</div>
              <div className="domain-risk">
                {Math.round(risk * 100)}%
              </div>
            </div>
          )
        })}
      </div>

      {/* Confidence */}
      <div style={{
        marginTop: '16px',
        fontSize: '11px',
        color: '#94A3B8',
        textAlign: 'center'
      }}>
        Confidence: {Math.round(currentAnalysis.confidence * 100)}%
      </div>

      {/* Last Update */}
      {alert && (
        <div style={{
          marginTop: '8px',
          fontSize: '10px',
          color: '#64748B',
          textAlign: 'center'
        }}>
          Updated: {new Date(alert.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}

export default CascadePanel