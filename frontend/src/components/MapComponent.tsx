import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { CropId, VillageDetail } from '../types'

interface MapComponentProps {
  activeCrop: CropId
  minScore: number
  selectedVillage: VillageDetail | null
  onSelectVillage: (village: VillageDetail | null) => void
  regionKey: string
}

function getTilesUrl(): string {
  if (import.meta.env.VITE_TILES_URL) {
    return import.meta.env.VITE_TILES_URL
  }
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/tiles`
  }
  return 'http://localhost:3000'
}

function getApiUrl(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api`
  }
  return 'http://localhost:8000'
}

export function MapComponent({
  activeCrop,
  minScore,
  selectedVillage,
  onSelectVillage,
  regionKey,
}: MapComponentProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)

  useEffect(() => {
    if (!mapContainer.current) return

    const tilesBase = getTilesUrl()
    const apiBase = getApiUrl()

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [118.0, -3.5], // Center over Indonesia
      zoom: 5,
      minZoom: 3,
      maxZoom: 14,
    })

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-right')

    map.on('error', (e) => {
      console.warn('MapLibre event error:', e)
    })

    map.on('load', () => {
      const tileUrl = `${tilesBase}/village_suitability/{z}/{x}/{y}`
      console.log('Registering GeoTani vector tile source:', tileUrl)

      // Vector Tile Source from Martin Tile Server
      map.addSource('village_suitability', {
        type: 'vector',
        tiles: [tileUrl],
        minzoom: 3,
        maxzoom: 14,
      })

      // Find the first symbol/label layer in base style so labels stay on top
      const firstSymbolLayer = map.getStyle().layers?.find((l) => l.type === 'symbol')?.id

      // 1. Fill Layer with score color interpolation
      map.addLayer(
        {
          id: 'villages-fill',
          type: 'fill',
          source: 'village_suitability',
          'source-layer': 'village_suitability',
          paint: {
            'fill-color': [
              'interpolate',
              ['linear'],
              ['to-number', ['get', `score_${activeCrop}`], 0],
              0,
              '#ef4444',
              30,
              '#f97316',
              50,
              '#eab308',
              70,
              '#84cc16',
              85,
              '#16a34a',
              100,
              '#065f46',
            ],
            'fill-opacity': 0.75,
          },
          filter: ['>=', ['to-number', ['get', `score_${activeCrop}`], 0], minScore],
        },
        firstSymbolLayer
      )

      // 2. Village Boundaries Line Layer
      map.addLayer(
        {
          id: 'villages-line',
          type: 'line',
          source: 'village_suitability',
          'source-layer': 'village_suitability',
          paint: {
            'line-color': '#ffffff',
            'line-width': [
              'interpolate',
              ['linear'],
              ['zoom'],
              4,
              0.1,
              7,
              0.3,
              10,
              0.8,
              14,
              1.5,
            ],
            'line-opacity': 0.6,
          },
        },
        firstSymbolLayer
      )

      // 3. Selection Highlight Layer
      map.addLayer(
        {
          id: 'villages-highlight',
          type: 'line',
          source: 'village_suitability',
          'source-layer': 'village_suitability',
          paint: {
            'line-color': '#0284c7',
            'line-width': 3,
            'line-opacity': 0.95,
          },
          filter: ['==', ['get', 'id'], -1],
        },
        firstSymbolLayer
      )
    })

    // Hover tooltip popup
    popupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      className: 'geotani-popup',
    })

    map.on('mousemove', 'villages-fill', (e) => {
      if (!e.features || !e.features[0]) return
      map.getCanvas().style.cursor = 'pointer'

      const feat = e.features[0]
      const name = String(feat.properties?.name || 'Region')
      const kab = String(feat.properties?.kabupaten || '')
      const prov = String(feat.properties?.province || '')
      const currentScore = Number(feat.properties?.[`score_${activeCrop}`] ?? 0).toFixed(1)

      const container = document.createElement('div')
      container.className = 'p-1.5 font-sans text-xs'

      const titleEl = document.createElement('div')
      titleEl.className = 'font-bold text-gray-900'
      titleEl.textContent = name
      container.appendChild(titleEl)

      if (kab || prov) {
        const subEl = document.createElement('div')
        subEl.className = 'text-[11px] text-gray-500'
        subEl.textContent = [kab, prov].filter(Boolean).join(', ')
        container.appendChild(subEl)
      }

      const scoreEl = document.createElement('div')
      scoreEl.className = 'mt-1.5 font-semibold text-emerald-700'
      scoreEl.textContent = `Suitability Score: ${currentScore}%`
      container.appendChild(scoreEl)

      popupRef.current?.setLngLat(e.lngLat).setDOMContent(container).addTo(map)
    })

    map.on('mouseleave', 'villages-fill', () => {
      map.getCanvas().style.cursor = ''
      popupRef.current?.remove()
    })

    // Click handler to select village and fetch details
    map.on('click', 'villages-fill', async (e) => {
      if (!e.features || !e.features[0]) return
      const villageId = e.features[0].properties?.id

      if (villageId) {
        try {
          const res = await fetch(`${apiBase}/villages/${villageId}`)
          if (res.ok) {
            const data: VillageDetail = await res.json()
            onSelectVillage(data)
          }
        } catch (err) {
          console.error('Failed to load village details:', err)
        }
      }
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Update fill color and min score filter when activeCrop or minScore changes
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded() || !map.getLayer('villages-fill')) return

    map.setPaintProperty('villages-fill', 'fill-color', [
      'interpolate',
      ['linear'],
      ['to-number', ['get', `score_${activeCrop}`], 0],
      0,
      '#ef4444',
      30,
      '#f97316',
      50,
      '#eab308',
      70,
      '#84cc16',
      85,
      '#16a34a',
      100,
      '#065f46',
    ])

    map.setFilter('villages-fill', ['>=', ['to-number', ['get', `score_${activeCrop}`], 0], minScore])
  }, [activeCrop, minScore])

  // Update selection highlight filter
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded() || !map.getLayer('villages-highlight')) return

    if (selectedVillage) {
      map.setFilter('villages-highlight', ['==', ['get', 'id'], selectedVillage.id])
    } else {
      map.setFilter('villages-highlight', ['==', ['get', 'id'], -1])
    }
  }, [selectedVillage])

  // Handle region flyTo navigation
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const regions: Record<string, { center: [number, number]; zoom: number }> = {
      all: { center: [118.0, -3.0], zoom: 5 },
      east_java: { center: [112.5, -7.7], zoom: 8 },
      lampung: { center: [105.2, -5.0], zoom: 8 },
      south_sulawesi: { center: [120.0, -4.0], zoom: 7.5 },
    }

    const target = regions[regionKey] || regions.all
    map.flyTo({
      center: target.center,
      zoom: target.zoom,
      essential: true,
      duration: 1500,
    })
  }, [regionKey])

  return (
    <div className="relative h-full w-full">
      <div ref={mapContainer} className="h-full w-full" />
    </div>
  )
}
