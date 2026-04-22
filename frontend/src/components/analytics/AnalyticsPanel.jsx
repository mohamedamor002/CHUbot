import { useEffect, useState } from 'react'
import { getKpis } from '../../api/client.js'

function KpiCard({ kpi }) {
  const hasValue = kpi.value !== null && kpi.value !== undefined
  const onTarget = !hasValue || kpi.target === null ? null
    : kpi.direction === 'higher' ? kpi.value >= kpi.target
    : kpi.value <= kpi.target

  const statusColor = !hasValue ? 'text-slate-400'
    : onTarget ? 'text-green-400' : 'text-red-400'

  const bgColor = !hasValue ? 'bg-white/5'
    : onTarget ? 'bg-green-500/10' : 'bg-red-500/10'

  return (
    <div className={`rounded-xl p-4 ${bgColor} border border-white/10`}>
      <p className="text-xs text-blue-200 mb-1 leading-tight">{kpi.label}</p>
      <div className="flex items-end gap-1">
        <span className={`text-2xl font-bold ${statusColor}`}>
          {hasValue ? `${kpi.value}` : '—'}
        </span>
        {hasValue && <span className="text-xs text-blue-300 mb-0.5">{kpi.unit}</span>}
      </div>
      {kpi.target !== null && kpi.target !== undefined && (
        <p className="text-xs text-blue-300 mt-1">
          Cible : {kpi.direction === 'higher' ? '≥' : '≤'} {kpi.target}{kpi.unit}
        </p>
      )}
      {kpi.note && <p className="text-xs text-slate-400 mt-1 italic">{kpi.note}</p>}
    </div>
  )
}

export default function AnalyticsPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getKpis().then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-xs text-blue-300 text-center py-8">Chargement...</p>
  if (!data) return <p className="text-xs text-red-400 text-center py-8">Erreur de chargement</p>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-xs text-blue-200">
          <span className="font-semibold text-white">{data.total_questions}</span> questions
        </p>
        <p className="text-xs text-blue-200">
          <span className="font-semibold text-white">{data.total_feedback}</span> évaluations
        </p>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {data.kpis.map((kpi) => (
          <KpiCard key={kpi.key} kpi={kpi} />
        ))}
      </div>
    </div>
  )
}
