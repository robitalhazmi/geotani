import React from 'react'
import { Coffee, Sprout, Wheat, MapPin, Database } from 'lucide-react'
import { CropId, CROPS, HealthStatus } from '../types'

interface NavbarProps {
  activeCrop: CropId
  onSelectCrop: (crop: CropId) => void
  onSelectRegion: (regionKey: string) => void
  health: HealthStatus | null
}

export const Navbar: React.FC<NavbarProps> = ({
  activeCrop,
  onSelectCrop,
  onSelectRegion,
  health,
}) => {
  const getCropIcon = (id: CropId) => {
    switch (id) {
      case 'coffee':
        return <Coffee className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
      case 'cocoa':
        return <Sprout className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
      case 'sugarcane':
        return <Wheat className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
    }
  }

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white/95 backdrop-blur px-3 py-2 sm:px-6 sm:py-2.5 shadow-xs z-20 gap-2">
      {/* Brand */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <div className="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-xs">
          <Sprout className="h-4 w-4 sm:h-4.5 sm:w-4.5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 sm:gap-2">
            <h1 className="text-sm sm:text-base font-bold text-gray-900 tracking-tight">GeoTani</h1>
            <span className="hidden sm:inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
              Open Source
            </span>
          </div>
          <p className="text-[10px] text-gray-500 hidden md:block">
            Agricultural Land Suitability & Geospatial Intelligence
          </p>
        </div>
      </div>

      {/* Crop Selector Tabs */}
      <div className="flex items-center gap-1 rounded-xl bg-gray-100 p-0.5 sm:p-1 border border-gray-200/80 shrink-0">
        {(Object.keys(CROPS) as CropId[]).map((cropId) => {
          const crop = CROPS[cropId]
          const isActive = activeCrop === cropId
          return (
            <button
              key={cropId}
              onClick={() => onSelectCrop(cropId)}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 sm:px-3 sm:py-1.5 text-[11px] sm:text-xs font-semibold transition-all cursor-pointer ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/60'
              }`}
            >
              {getCropIcon(cropId)}
              <span className="hidden xs:inline sm:inline">
                {cropId === 'coffee' ? 'Coffee' : crop.name.split(' ')[0]}
              </span>
            </button>
          )
        })}
      </div>

      {/* Region Quick Jump & Status */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Region selector dropdown */}
        <div className="flex items-center gap-1 text-[11px] sm:text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-lg px-2 py-1 sm:px-2.5 sm:py-1.5">
          <MapPin className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-gray-400 shrink-0" />
          <select
            onChange={(e) => onSelectRegion(e.target.value)}
            className="bg-transparent text-[11px] sm:text-xs font-medium text-gray-700 outline-none cursor-pointer max-w-[90px] xs:max-w-[120px] sm:max-w-none"
            defaultValue="all"
          >
            <option value="all">🇮🇩 All Regions</option>
            <option value="east_java">Jawa Timur</option>
            <option value="lampung">Lampung</option>
            <option value="south_sulawesi">Sulawesi Sel.</option>
          </select>
        </div>

        {/* Database Status indicator (Desktop only) */}
        <div
          className="hidden lg:flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border bg-gray-50 border-gray-200 text-gray-600"
          title={`Total scored villages: ${health?.total_scores.toLocaleString() || 0}`}
        >
          <Database className="h-3.5 w-3.5 text-emerald-600" />
          <span className="font-medium text-gray-700">
            {health?.total_villages ? `${health.total_villages.toLocaleString()} Villages` : 'Connecting...'}
          </span>
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>
      </div>
    </header>
  )
}
