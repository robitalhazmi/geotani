import React from 'react'
import { Sprout, Database, ExternalLink } from 'lucide-react'
import { HealthStatus } from '../types'

interface NavbarProps {
  health: HealthStatus | null
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
}) => {
  return (
    <header className="flex flex-wrap items-center justify-between border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-2.5 shadow-2xs z-20">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-xs">
          <Sprout className="h-4.5 w-4.5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold text-gray-900 tracking-tight">GeoTani</h1>
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200 uppercase tracking-wider">
              Open Source
            </span>
          </div>
          <p className="text-[11px] text-gray-500 hidden sm:block">
            Agricultural Land Suitability & Geospatial Intelligence
          </p>
        </div>
      </div>

      {/* Database Status indicator & GitHub Link */}
      <div className="flex items-center gap-3">
        {/* Database Record Badge */}
        <div
          className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border bg-gray-50 border-gray-200/80 text-gray-600"
          title={`Total scored villages: ${health?.total_scores.toLocaleString() || 0}`}
        >
          <Database className="h-3.5 w-3.5 text-emerald-600" />
          <span className="font-medium text-gray-700">
            {health?.total_villages ? `${health.total_villages.toLocaleString()} Villages` : 'Connecting...'}
          </span>
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>

        {/* GitHub link */}
        <a
          href="https://github.com/robitalhazmi/geotani"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-xs font-semibold text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200/80 px-2.5 py-1 rounded-lg border border-gray-200 transition-colors"
        >
          <span>GitHub</span>
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </header>
  )
}
