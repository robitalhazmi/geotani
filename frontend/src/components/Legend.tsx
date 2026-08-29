import React from 'react'
import { SlidersHorizontal, Info } from 'lucide-react'
import { CropId, CROPS } from '../types'

interface LegendProps {
  activeCrop: CropId
  minScore: number
  onChangeMinScore: (score: number) => void
}

export const Legend: React.FC<LegendProps> = ({
  activeCrop,
  minScore,
  onChangeMinScore,
}) => {
  const crop = CROPS[activeCrop]

  const tiers = [
    { label: '85 - 100%', title: 'Highly Suitable', color: '#15803d' },
    { label: '70 - 85%', title: 'Suitable', color: '#4ade80' },
    { label: '50 - 70%', title: 'Moderately Suitable', color: '#facc15' },
    { label: '30 - 50%', title: 'Marginally Suitable', color: '#fb923c' },
    { label: '< 30%', title: 'Unsuitable / Restricted', color: '#f87171' },
  ]

  return (
    <div className="absolute bottom-6 left-6 z-10 w-80 rounded-2xl bg-white/95 backdrop-blur-md p-4 shadow-lg border border-gray-200/80 text-gray-800 transition-all">
      {/* Crop Overview */}
      <div className="mb-3 border-b border-gray-100 pb-2.5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-900">{crop.name}</h3>
          <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
            {crop.category}
          </span>
        </div>
        <p className="mt-1 text-xs text-gray-500 line-clamp-2">{crop.description}</p>
        
        {/* Quick parameters */}
        <div className="mt-2 grid grid-cols-2 gap-1.5 text-[11px] bg-gray-50 p-2 rounded-lg border border-gray-100 text-gray-600">
          <div><span className="font-semibold text-gray-700">Temp:</span> {crop.optimalTemp}</div>
          <div><span className="font-semibold text-gray-700">Rain:</span> {crop.optimalRainfall}</div>
          <div><span className="font-semibold text-gray-700">Elev:</span> {crop.optimalElevation}</div>
          <div><span className="font-semibold text-gray-700">pH:</span> {crop.optimalSoilPh}</div>
        </div>
      </div>

      {/* Suitability Color Scale */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-semibold text-gray-700 mb-1">
          <span>Suitability Score</span>
          <span className="text-gray-400 font-normal">FAO Ecocrop</span>
        </div>

        {/* Gradient Preview Bar */}
        <div className="h-2.5 w-full rounded-full bg-gradient-to-r from-red-400 via-yellow-400 via-green-400 to-green-800 shadow-inner" />

        {/* Color Tiers */}
        <div className="grid grid-cols-1 gap-1 pt-1">
          {tiers.map((tier) => (
            <div key={tier.label} className="flex items-center justify-between text-[11px]">
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full ring-1 ring-black/10"
                  style={{ backgroundColor: tier.color }}
                />
                <span className="text-gray-600">{tier.title}</span>
              </div>
              <span className="font-mono text-gray-400 text-[10px]">{tier.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Filter Threshold Slider */}
      <div className="mt-4 border-t border-gray-100 pt-3">
        <div className="flex items-center justify-between text-xs font-medium text-gray-700">
          <span className="flex items-center gap-1">
            <SlidersHorizontal className="h-3.5 w-3.5 text-gray-500" />
            Min Score Filter
          </span>
          <span className="font-bold text-emerald-700 font-mono">≥ {minScore}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="95"
          step="5"
          value={minScore}
          onChange={(e) => onChangeMinScore(Number(e.target.value))}
          className="mt-2 w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
        />
        <div className="flex justify-between text-[10px] text-gray-400 mt-1">
          <span>Show all</span>
          <span>Only high suitability</span>
        </div>
      </div>

      {/* Hint footer */}
      <div className="mt-3 flex items-center gap-1.5 text-[10px] text-gray-400 bg-gray-50 px-2 py-1 rounded">
        <Info className="h-3 w-3 shrink-0 text-gray-400" />
        <span>Click any village polygon to inspect full score factors.</span>
      </div>
    </div>
  )
}
