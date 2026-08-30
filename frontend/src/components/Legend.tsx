import React, { useState } from 'react'
import { Info, ChevronDown, ChevronUp, Layers } from 'lucide-react'
import { CropId, CROPS } from '../types'

interface LegendProps {
  activeCrop: CropId
  minScore: number
  onChangeMinScore: (score: number) => void
}

export const Legend: React.FC<LegendProps> = ({
  activeCrop,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const crop = CROPS[activeCrop]

  const tiers = [
    { label: '85 - 100%', title: 'Highly Suitable (S1)', color: '#15803d' },
    { label: '70 - 85%', title: 'Suitable (S2)', color: '#4ade80' },
    { label: '50 - 70%', title: 'Moderately Suitable (S3)', color: '#facc15' },
    { label: '30 - 50%', title: 'Marginally Suitable (N1)', color: '#fb923c' },
    { label: '< 30%', title: 'Unsuitable / Restricted (N2)', color: '#f87171' },
  ]

  return (
    <div className="absolute bottom-6 left-6 z-20 w-72 sm:w-80 rounded-2xl bg-white/95 backdrop-blur-md shadow-lg border border-gray-200/90 text-gray-800 transition-all max-h-[calc(100vh-160px)] overflow-y-auto">
      {/* Header with Collapse toggle */}
      <div
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="flex items-center justify-between p-3.5 border-b border-gray-100 cursor-pointer hover:bg-gray-50/80 transition-colors select-none"
      >
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-emerald-700" />
          <div>
            <h3 className="text-xs font-bold text-gray-900">{crop.name} Legend</h3>
            <span className="text-[10px] text-gray-500 font-medium">FAO Suitability Scale</span>
          </div>
        </div>
        <button className="text-gray-400 hover:text-gray-600 p-1">
          {isCollapsed ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-3.5 space-y-3">
          {/* Quick Agronomic Parameters */}
          <div className="bg-gray-50 p-2 rounded-xl border border-gray-100/90 text-[11px] space-y-1">
            <div className="flex items-center justify-between text-gray-600">
              <span className="font-semibold text-gray-700">Optimal Temp:</span>
              <span className="font-mono text-gray-800">{crop.optimalTemp}</span>
            </div>
            <div className="flex items-center justify-between text-gray-600">
              <span className="font-semibold text-gray-700">Optimal Rain:</span>
              <span className="font-mono text-gray-800">{crop.optimalRainfall}</span>
            </div>
            <div className="flex items-center justify-between text-gray-600">
              <span className="font-semibold text-gray-700">Optimal Elevation:</span>
              <span className="font-mono text-gray-800">{crop.optimalElevation}</span>
            </div>
            <div className="flex items-center justify-between text-gray-600">
              <span className="font-semibold text-gray-700">Optimal Soil pH:</span>
              <span className="font-mono text-gray-800">{crop.optimalSoilPh}</span>
            </div>
          </div>

          {/* Color Gradient & Tiers */}
          <div className="space-y-1.5">
            <div className="h-2 w-full rounded-full bg-gradient-to-r from-red-400 via-yellow-400 via-green-400 to-green-800 shadow-inner" />

            <div className="grid grid-cols-1 gap-1 pt-1">
              {tiers.map((tier) => (
                <div key={tier.label} className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full ring-1 ring-black/10 shrink-0"
                      style={{ backgroundColor: tier.color }}
                    />
                    <span className="text-gray-700 font-medium">{tier.title}</span>
                  </div>
                  <span className="font-mono text-gray-400 text-[10px]">{tier.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Helper Note */}
          <div className="flex items-center gap-1.5 text-[10px] text-gray-500 bg-emerald-50/60 border border-emerald-100 px-2 py-1.5 rounded-lg">
            <Info className="h-3 w-3 shrink-0 text-emerald-700" />
            <span>Click any village to view soil, terrain & climate factor breakdown.</span>
          </div>
        </div>
      )}
    </div>
  )
}
