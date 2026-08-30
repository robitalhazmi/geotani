import React, { useState } from 'react'
import { SlidersHorizontal, Info, ChevronUp, Sparkles, X } from 'lucide-react'
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
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false)
  const crop = CROPS[activeCrop]

  const tiers = [
    { label: '85 - 100%', title: 'Highly Suitable', color: '#16a34a' },
    { label: '70 - 85%', title: 'Suitable', color: '#84cc16' },
    { label: '50 - 70%', title: 'Moderately Suitable', color: '#eab308' },
    { label: '30 - 50%', title: 'Marginally Suitable', color: '#f97316' },
    { label: '< 30%', title: 'Unsuitable / Restricted', color: '#ef4444' },
  ]

  const renderLegendBody = () => (
    <>
      {/* Crop Overview */}
      <div className="mb-3 border-b border-gray-100 pb-2.5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-900">{crop.name}</h3>
          <span className="text-[10px] sm:text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
            {crop.category}
          </span>
        </div>
        <p className="mt-1 text-xs text-gray-500 line-clamp-2">{crop.description}</p>

        {/* Quick parameters */}
        <div className="mt-2 grid grid-cols-2 gap-1.5 text-[10px] sm:text-[11px] bg-gray-50 p-2 rounded-lg border border-gray-100 text-gray-600">
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
          <span className="text-gray-400 font-normal text-[11px]">FAO Ecocrop</span>
        </div>

        {/* Gradient Preview Bar */}
        <div className="h-2.5 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 via-lime-500 to-green-800 shadow-inner" />

        {/* Color Tiers */}
        <div className="grid grid-cols-1 gap-1 pt-1">
          {tiers.map((tier) => (
            <div key={tier.label} className="flex items-center justify-between text-[11px]">
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full ring-1 ring-black/10 shrink-0"
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
      <div className="mt-3.5 border-t border-gray-100 pt-3">
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
        <span>Click any village polygon on the map to inspect breakdown.</span>
      </div>
    </>
  )

  return (
    <>
      {/* 1. Desktop Floating Card (Fixed to Bottom-Left) */}
      <div className="hidden md:block absolute bottom-6 left-6 z-10 w-80 rounded-2xl bg-white/95 backdrop-blur-md p-4 shadow-lg border border-gray-200/80 text-gray-800">
        {renderLegendBody()}
      </div>

      {/* 2. Mobile Floating Pill Trigger (Bottom-Center) */}
      <div className="md:hidden absolute bottom-4 inset-x-4 z-10 flex justify-center pointer-events-auto">
        <button
          onClick={() => setIsMobileOpen(true)}
          className="flex items-center gap-2 bg-white/95 backdrop-blur-md px-4 py-2.5 rounded-full shadow-lg border border-gray-200/90 text-xs font-semibold text-gray-800 transition-transform active:scale-95 cursor-pointer"
        >
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-600 animate-pulse" />
          <span>{crop.name}</span>
          <span className="text-gray-300">|</span>
          <span className="text-emerald-700 font-mono">≥ {minScore}%</span>
          <span className="text-gray-300">|</span>
          <span className="flex items-center text-gray-500 gap-0.5 text-[11px]">
            <SlidersHorizontal className="h-3 w-3" />
            Legend
            <ChevronUp className="h-3.5 w-3.5" />
          </span>
        </button>
      </div>

      {/* 3. Mobile Bottom Sheet Drawer */}
      {isMobileOpen && (
        <div className="md:hidden fixed inset-x-0 bottom-0 z-30 max-h-[80vh] overflow-y-auto rounded-t-3xl bg-white/98 backdrop-blur-md p-5 shadow-2xl border-t border-gray-200 text-gray-800 animate-in fade-in slide-in-from-bottom duration-200">
          <div className="flex flex-col items-center mb-3">
            <div
              className="h-1.5 w-12 rounded-full bg-gray-300 mb-2 cursor-pointer"
              onClick={() => setIsMobileOpen(false)}
            />
            <div className="flex w-full items-center justify-between">
              <span className="text-xs font-bold text-gray-800 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                Suitability Legend & Controls
              </span>
              <button
                onClick={() => setIsMobileOpen(false)}
                className="p-1 rounded-full text-gray-400 hover:text-gray-700 bg-gray-100 cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          {renderLegendBody()}
        </div>
      )}
    </>
  )
}
