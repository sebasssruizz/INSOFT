export default function ProgressBar({ percentage }) {
  const value = Math.min(100, Math.max(0, percentage || 0))
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        <span>Progreso</span>
        <span className="font-semibold text-oft-700">{value}%</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-2.5">
        <div
          className="bg-ins-500 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
