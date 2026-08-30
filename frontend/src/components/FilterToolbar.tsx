import React, { useState, useEffect, useRef } from 'react'
import {
  Coffee,
  Sprout,
  Wheat,
  MapPin,
  SlidersHorizontal,
  Search,
  X,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import { CropId, CROPS, VillageDetail } from '../types'

interface FilterToolbarProps {
  activeCrop: CropId
  onSelectCrop: (crop: CropId) => void
  regionKey: string
  onSelectRegion: (regionKey: string) => void
  minScore: number
  onChangeMinScore: (score: number) => void
  onSelectVillage: (village: VillageDetail | null) => void
  apiUrl: string
}

export const FilterToolbar: React.FC<FilterToolbarProps> = ({
  activeCrop,
  onSelectCrop,
  regionKey,
  onSelectRegion,
  minScore,
  onChangeMinScore,
  onSelectVillage,
  apiUrl,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<VillageDetail[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  const getCropIcon = (id: CropId) => {
    switch (id) {
      case 'coffee':
        return <Coffee className="h-4 w-4 mr-1.5" />
      case 'cocoa':
        return <Sprout className="h-4 w-4 mr-1.5" />
      case 'sugarcane':
        return <Wheat className="h-4 w-4 mr-1.5" />
    }
  }

  // Handle Village Search debounce
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([])
      setShowDropdown(false)
      return
    }

    const timer = setTimeout(async () => {
      setIsSearching(true)
      try {
        const res = await fetch(`${apiUrl}/villages/search?q=${encodeURIComponent(searchQuery.trim())}&limit=6`)
        if (res.ok) {
          const data = await res.json()
          setSearchResults(data)
          setShowDropdown(true)
        }
      } catch (err) {
        console.error('Village search error:', err)
      } finally {
        setIsSearching(false)
      }
    }, 250)

    return () => clearTimeout(timer)
  }, [searchQuery, apiUrl])

  // Close search dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const scorePresets = [
    { label: 'All', value: 0 },
    { label: '≥ 50% (Moderate)', value: 50 },
    { label: '≥ 70% (Suitable)', value: 70 },
    { label: '≥ 85% (Prime)', value: 85 },
  ]

  const hasActiveFilters = minScore > 0 || regionKey !== 'all'

  return (
    <div className="border-b border-gray-200/90 bg-white/95 backdrop-blur-md px-6 py-2.5 shadow-xs z-15">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Crop Filters & Region Selector */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Crop Switcher */}
          <div className="flex items-center gap-1">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider mr-1 hidden sm:inline">
              Crop:
            </span>
            <div className="flex items-center gap-1 rounded-xl bg-gray-100/90 p-1 border border-gray-200/80">
              {(Object.keys(CROPS) as CropId[]).map((cropId) => {
                const crop = CROPS[cropId]
                const isActive = activeCrop === cropId
                return (
                  <button
                    key={cropId}
                    onClick={() => onSelectCrop(cropId)}
                    className={`flex items-center rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/70'
                    }`}
                  >
                    {getCropIcon(cropId)}
                    {crop.name}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="h-5 w-px bg-gray-200 hidden md:block" />

          {/* Region Filter */}
          <div className="flex items-center gap-1.5 text-xs bg-gray-50 border border-gray-200/90 rounded-xl px-3 py-1.5">
            <MapPin className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
            <span className="font-semibold text-gray-700 hidden lg:inline">Province:</span>
            <select
              value={regionKey}
              onChange={(e) => onSelectRegion(e.target.value)}
              className="bg-transparent text-xs font-semibold text-gray-800 outline-none cursor-pointer pr-1"
            >
              <option value="all">🇮🇩 All Pilot Regions</option>
              <option value="east_java">Jawa Timur (East Java)</option>
              <option value="lampung">Lampung</option>
              <option value="south_sulawesi">Sulawesi Selatan</option>
            </select>
          </div>
        </div>

        {/* Right: Min Score Filter Slider & Village Search */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Suitability Score Threshold Filter */}
          <div className="flex items-center gap-2 bg-emerald-50/70 border border-emerald-200/80 rounded-xl px-3 py-1.5">
            <SlidersHorizontal className="h-3.5 w-3.5 text-emerald-700 shrink-0" />
            <span className="text-xs font-semibold text-emerald-900 hidden sm:inline">Min Score:</span>
            
            {/* Quick Preset Buttons */}
            <div className="flex items-center gap-1">
              {scorePresets.map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => onChangeMinScore(preset.value)}
                  className={`rounded-md px-2 py-0.5 text-[11px] font-semibold transition-all cursor-pointer ${
                    minScore === preset.value
                      ? 'bg-emerald-600 text-white shadow-2xs'
                      : 'bg-white/80 text-emerald-800 border border-emerald-200/60 hover:bg-white'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {/* Range Slider for custom values */}
            <div className="flex items-center gap-2 pl-1 border-l border-emerald-200">
              <input
                type="range"
                min="0"
                max="95"
                step="5"
                value={minScore}
                onChange={(e) => onChangeMinScore(Number(e.target.value))}
                className="w-20 sm:w-24 h-1.5 bg-emerald-200 rounded-lg appearance-none cursor-pointer accent-emerald-700"
                title={`Filter villages with score ≥ ${minScore}%`}
              />
              <span className="font-mono text-xs font-bold text-emerald-800 w-9 text-right">
                {minScore}%
              </span>
            </div>
          </div>

          {/* Reset Filter Button if active */}
          {hasActiveFilters && (
            <button
              onClick={() => {
                onChangeMinScore(0)
                onSelectRegion('all')
              }}
              className="flex items-center gap-1 rounded-xl bg-gray-100 hover:bg-gray-200 px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 border border-gray-200 transition-all cursor-pointer"
              title="Reset all filters to default"
            >
              <RotateCcw className="h-3 w-3 text-gray-500" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          )}

          {/* Village Quick Search Input */}
          <div ref={searchRef} className="relative">
            <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-200/90 rounded-xl px-3 py-1.5 focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-emerald-500 focus-within:bg-white transition-all">
              {isSearching ? (
                <div className="h-3.5 w-3.5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin shrink-0" />
              ) : (
                <Search className="h-3.5 w-3.5 text-gray-400 shrink-0" />
              )}
              <input
                type="text"
                placeholder="Search village (e.g. Ardirejo)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => {
                  if (searchResults.length > 0) setShowDropdown(true)
                }}
                className="bg-transparent text-xs text-gray-800 placeholder-gray-400 outline-none w-36 sm:w-48"
              />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('')
                    setSearchResults([])
                    setShowDropdown(false)
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>

            {/* Search Dropdown Results */}
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute right-0 mt-1 w-72 rounded-xl bg-white p-1.5 shadow-xl border border-gray-200 z-50 max-h-64 overflow-y-auto">
                <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-gray-400">
                  Matching Villages ({searchResults.length})
                </div>
                {searchResults.map((village) => (
                  <button
                    key={village.id}
                    onClick={() => {
                      onSelectVillage(village)
                      setShowDropdown(false)
                      setSearchQuery('')
                    }}
                    className="w-full flex items-start gap-2 rounded-lg p-2 text-left hover:bg-emerald-50 transition-colors group cursor-pointer"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-emerald-600 mt-0.5 shrink-0 group-hover:scale-110 transition-transform" />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold text-gray-900 truncate">
                        {village.name}
                      </div>
                      <div className="text-[11px] text-gray-500 truncate">
                        {village.kecamatan ? `${village.kecamatan}, ` : ''}{village.kabupaten} ({village.province})
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
