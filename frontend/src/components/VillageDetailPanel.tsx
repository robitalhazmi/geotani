import React from 'react'
import { X, MapPin, CloudSun, Mountain, Layers, Navigation, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react'
import { CropId, CROPS, VillageDetail } from '../types'

interface VillageDetailPanelProps {
  village: VillageDetail
  activeCrop: CropId
  onSelectCrop: (crop: CropId) => void
  onClose: () => void
}

export const VillageDetailPanel: React.FC<VillageDetailPanelProps> = ({
  village,
  activeCrop,
  onSelectCrop,
  onClose,
}) => {
  const currentScoreObj = village.scores.find((s) => s.crop === activeCrop)
  const score = currentScoreObj ? currentScoreObj.score : 0
  const climateScore = currentScoreObj?.climate_score ?? 0
  const soilScore = currentScoreObj?.soil_score ?? 0
  const terrainScore = currentScoreObj?.terrain_score ?? 0
  const accessScore = currentScoreObj?.access_score ?? 0

  const getScoreColor = (val: number) => {
    if (val >= 85) return { bg: 'bg-emerald-700', text: 'text-emerald-700', border: 'border-emerald-200', lightBg: 'bg-emerald-50', label: 'Highly Suitable' }
    if (val >= 70) return { bg: 'bg-emerald-500', text: 'text-emerald-600', border: 'border-emerald-200', lightBg: 'bg-emerald-50', label: 'Suitable' }
    if (val >= 50) return { bg: 'bg-amber-500', text: 'text-amber-600', border: 'border-amber-200', lightBg: 'bg-amber-50', label: 'Moderately Suitable' }
    if (val >= 30) return { bg: 'bg-orange-500', text: 'text-orange-600', border: 'border-orange-200', lightBg: 'bg-orange-50', label: 'Marginally Suitable' }
    return { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-200', lightBg: 'bg-red-50', label: 'Unsuitable / Restricted' }
  }

  const scoreMeta = getScoreColor(score)

  // Explainability diagnosis
  const isClimateLimited = climateScore < 50 && (soilScore > 60 || terrainScore > 60)
  const isTerrainLimited = terrainScore < 40 && slopeScoreReason(terrainScore)

  function slopeScoreReason(val: number) {
    return val < 40
  }

  return (
    <div className="absolute top-20 right-6 z-10 w-96 max-h-[calc(100vh-6.5rem)] overflow-y-auto rounded-2xl bg-white/95 backdrop-blur-md p-5 shadow-2xl border border-gray-200/90 text-gray-800 transition-all animate-in fade-in slide-in-from-right-4 duration-200">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-gray-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-gray-900 leading-snug">{village.name}</h2>
            <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-600 uppercase tracking-wide">
              {village.resolution === 'village' ? 'Desa/Kelurahan' : 'Kabupaten'}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
            <MapPin className="h-3.5 w-3.5 shrink-0 text-gray-400" />
            <span className="truncate">
              {[village.kecamatan, village.kabupaten, village.province].filter(Boolean).join(', ')}
            </span>
          </div>
          <div className="text-[10px] font-mono text-gray-400 mt-0.5">
            P-Code: {village.adm_pcode}
          </div>
        </div>

        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition cursor-pointer"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Multi-Crop Switcher Tabs */}
      <div className="mt-3 grid grid-cols-3 gap-1.5 rounded-xl bg-gray-100 p-1">
        {(Object.keys(CROPS) as CropId[]).map((cropId) => {
          const s = village.scores.find((item) => item.crop === cropId)?.score ?? 0
          const isSelected = activeCrop === cropId
          return (
            <button
              key={cropId}
              onClick={() => onSelectCrop(cropId)}
              className={`flex flex-col items-center py-1.5 px-1 rounded-lg text-xs font-medium transition cursor-pointer ${
                isSelected
                  ? 'bg-white text-gray-900 shadow-xs font-bold'
                  : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              <span className="text-[11px] capitalize">{cropId}</span>
              <span className={`text-[11px] font-mono font-bold ${getScoreColor(s).text}`}>
                {s.toFixed(1)}%
              </span>
            </button>
          )
        })}
      </div>

      {/* Hero Overall Score Card */}
      <div className={`mt-4 rounded-xl border p-4 ${scoreMeta.lightBg} ${scoreMeta.border}`}>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
              {CROPS[activeCrop].name} Suitability
            </span>
            <div className="text-2xl font-black text-gray-900 font-mono mt-0.5">
              {score.toFixed(1)}%
            </div>
          </div>
          <span className={`text-xs font-bold px-3 py-1 rounded-full border bg-white ${scoreMeta.text} ${scoreMeta.border} shadow-xs`}>
            {scoreMeta.label}
          </span>
        </div>

        <div className="mt-3 w-full bg-gray-200/80 rounded-full h-2 overflow-hidden">
          <div
            className={`h-2 rounded-full ${scoreMeta.bg} transition-all duration-500`}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
      </div>

      {/* Sub-Score Factor Breakdown */}
      <div className="mt-5 space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">
          Factor Breakdown & Sub-Scores
        </h4>

        {/* 1. Climate Gate */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="flex items-center gap-1.5 font-medium text-gray-700">
              <CloudSun className="h-4 w-4 text-sky-500" />
              Climate Gate (Temp & Rain)
            </span>
            <span className="font-mono font-bold text-gray-900">{climateScore.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-1.5 rounded-full bg-sky-500"
              style={{ width: `${climateScore}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>Bio1 (Temp) & Bio12 (Rainfall)</span>
            <span>Limiting Gate</span>
          </div>
        </div>

        {/* 2. Soil Quality */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="flex items-center gap-1.5 font-medium text-gray-700">
              <Layers className="h-4 w-4 text-amber-700" />
              Soil Quality (pH, Texture, SOC)
            </span>
            <span className="font-mono font-bold text-gray-900">{soilScore.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-1.5 rounded-full bg-amber-600"
              style={{ width: `${soilScore}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>pH, Clay %, Sand %, Organic Carbon</span>
            <span>Weight: 40%</span>
          </div>
        </div>

        {/* 3. Terrain & Slope */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="flex items-center gap-1.5 font-medium text-gray-700">
              <Mountain className="h-4 w-4 text-emerald-600" />
              Terrain & Slope
            </span>
            <span className="font-mono font-bold text-gray-900">{terrainScore.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-1.5 rounded-full bg-emerald-600"
              style={{ width: `${terrainScore}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>Elevation & 30m Copernicus Slope</span>
            <span>Weight: 40%</span>
          </div>
        </div>

        {/* 4. Road Infrastructure */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="flex items-center gap-1.5 font-medium text-gray-700">
              <Navigation className="h-4 w-4 text-indigo-500" />
              Road Access & Logistics
            </span>
            <span className="font-mono font-bold text-gray-900">{accessScore.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-1.5 rounded-full bg-indigo-500"
              style={{ width: `${accessScore}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-gray-400 mt-1">
            <span>OSM Road Distance Decay</span>
            <span>Weight: 20%</span>
          </div>
        </div>
      </div>

      {/* Explainability Insight */}
      <div className="mt-4 rounded-xl bg-gray-50 border border-gray-200/80 p-3 text-xs">
        <div className="flex items-center gap-1.5 font-bold text-gray-800 mb-1">
          <Sparkles className="h-3.5 w-3.5 text-amber-500" />
          Agronomic Diagnosis
        </div>
        {score >= 75 ? (
          <div className="flex items-start gap-2 text-emerald-800">
            <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5 text-emerald-600" />
            <p className="text-[11px] leading-relaxed">
              Prime agroecological conditions. Both climate thresholds and topsoil/terrain parameters fall directly in the optimal FAO Ecocrop range.
            </p>
          </div>
        ) : isClimateLimited ? (
          <div className="flex items-start gap-2 text-amber-800">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
            <p className="text-[11px] leading-relaxed">
              Score is primarily constrained by the <strong>Climate Gate</strong> (temperature or annual rainfall deviates from optimal bounds).
            </p>
          </div>
        ) : isTerrainLimited ? (
          <div className="flex items-start gap-2 text-amber-800">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
            <p className="text-[11px] leading-relaxed">
              Steep slopes or elevation bounds reduce agricultural operability and yield potential.
            </p>
          </div>
        ) : (
          <p className="text-[11px] text-gray-600 leading-relaxed">
            Moderate suitability with balanced sub-scores across climate, soil nutrients, and logistics accessibility.
          </p>
        )}
      </div>
    </div>
  )
}
