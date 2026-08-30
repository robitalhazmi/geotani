import { useEffect, useState } from 'react'
import { CropId, HealthStatus, VillageDetail } from './types'
import { Navbar } from './components/Navbar'
import { MapComponent } from './components/MapComponent'
import { Legend } from './components/Legend'
import { VillageDetailPanel } from './components/VillageDetailPanel'

function App() {
  const [activeCrop, setActiveCrop] = useState<CropId>('coffee')
  const [minScore, setMinScore] = useState<number>(0)
  const [selectedVillage, setSelectedVillage] = useState<VillageDetail | null>(null)
  const [regionKey, setRegionKey] = useState<string>('all')
  const [health, setHealth] = useState<HealthStatus | null>(null)

  const apiUrl = import.meta.env.VITE_API_URL || '/api'

  // Fetch API / database health status
  useEffect(() => {
    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then((data: HealthStatus) => setHealth(data))
      .catch((err) => console.error('API health check error:', err))
  }, [apiUrl])

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-gray-100 font-sans antialiased">
      {/* Top Navigation */}
      <Navbar
        activeCrop={activeCrop}
        onSelectCrop={setActiveCrop}
        onSelectRegion={setRegionKey}
        health={health}
      />

      {/* Main Map Container */}
      <main className="relative flex-1">
        <MapComponent
          activeCrop={activeCrop}
          minScore={minScore}
          selectedVillage={selectedVillage}
          onSelectVillage={setSelectedVillage}
          regionKey={regionKey}
        />

        {/* Legend and Filter Slider */}
        <Legend
          activeCrop={activeCrop}
          minScore={minScore}
          onChangeMinScore={setMinScore}
        />

        {/* Village Details Slide-in Panel */}
        {selectedVillage && (
          <VillageDetailPanel
            village={selectedVillage}
            activeCrop={activeCrop}
            onSelectCrop={setActiveCrop}
            onClose={() => setSelectedVillage(null)}
          />
        )}
      </main>

      {/* Footer Status Bar */}
      <footer className="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-2 text-[11px] text-gray-500 z-20">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-emerald-800">GeoTani v0.1.0</span>
          <span>•</span>
          <span>Pilot Provinces: Lampung, Jawa Timur, Sulawesi Selatan</span>
        </div>
        <div>
          Data Sources: HDX (BPS ADM4), Copernicus GLO-30 DEM, WorldClim v2.1, SoilGrids v2.0, OpenStreetMap
        </div>
      </footer>
    </div>
  )
}

export default App
