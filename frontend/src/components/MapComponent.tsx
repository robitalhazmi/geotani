import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { CropId, getSuitabilityTier, PROVINCE_VIEWS, VillageDetail } from '../types'

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
      center: [118.0, -2.5], // Center over Indonesia
      zoom: 4.8,
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

      // 1. Fill Layer with multi-scale score color interpolation
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
            'fill-opacity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              3,
              0.85,
              6,
              0.85,
              8,
              0.80,
              12,
              0.75,
            ],
          },
          filter: [
            'all',
            ['has', `score_${activeCrop}`],
            ['>=', ['to-number', ['get', `score_${activeCrop}`], -1], minScore],
          ],
        },
        firstSymbolLayer
      )

      // 2. Village Boundaries Line Layer (fades in gracefully at zoom >= 7.5 to avoid washing out low-zoom heatmap)
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
              6,
              0.2,
              8,
              0.5,
              11,
              1.0,
              14,
              1.8,
            ],
            'line-opacity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              4,
              0.0,
              6.5,
              0.0,
              8,
              0.3,
              10,
              0.6,
              14,
              0.8,
            ],
          },
          filter: [
            'all',
            ['has', `score_${activeCrop}`],
            ['>=', ['to-number', ['get', `score_${activeCrop}`], -1], minScore],
          ],
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

      const feat = e.features[0]
      const rawScore = feat.properties?.[`score_${activeCrop}`]
      if (rawScore === null || rawScore === undefined || rawScore === '') {
        map.getCanvas().style.cursor = ''
        popupRef.current?.remove()
        return
      }

      map.getCanvas().style.cursor = 'pointer'

      const name = String(feat.properties?.name || 'Region')
      const kab = String(feat.properties?.kabupaten || '')
      const prov = String(feat.properties?.province || '')
      const scoreNum = Number(rawScore)
      const currentScore = scoreNum.toFixed(1)
      const tier = getSuitabilityTier(scoreNum)

      const container = document.createElement('div')
      container.className = 'p-2 font-sans text-xs min-w-[160px]'

      const titleEl = document.createElement('div')
      titleEl.className = 'font-bold text-gray-900 text-sm'
      titleEl.textContent = name
      container.appendChild(titleEl)

      if (kab || prov) {
        const subEl = document.createElement('div')
        subEl.className = 'text-[11px] text-gray-500 mb-1.5'
        subEl.textContent = [kab, prov].filter(Boolean).join(', ')
        container.appendChild(subEl)
      }

      const scoreRow = document.createElement('div')
      scoreRow.className = 'flex items-center justify-between gap-2 pt-1.5 border-t border-gray-100'

      const scoreValue = document.createElement('span')
      scoreValue.className = 'font-bold font-mono text-gray-900 text-sm'
      scoreValue.textContent = `${currentScore}%`

      const badge = document.createElement('span')
      badge.className = 'text-[10px] font-semibold px-2 py-0.5 rounded-full text-white'
      badge.style.backgroundColor = tier.color
      badge.textContent = tier.title

      scoreRow.appendChild(scoreValue)
      scoreRow.appendChild(badge)
      container.appendChild(scoreRow)

      popupRef.current?.setLngLat(e.lngLat).setDOMContent(container).addTo(map)
    })

    map.on('mouseleave', 'villages-fill', () => {
      map.getCanvas().style.cursor = ''
      popupRef.current?.remove()
    })

    // Click handler to select village and fetch details
    map.on('click', 'villages-fill', async (e) => {
      if (!e.features || !e.features[0]) return
      const feat = e.features[0]
      const rawScore = feat.properties?.[`score_${activeCrop}`]
      if (rawScore === null || rawScore === undefined || rawScore === '') return

      const villageId = feat.properties?.id
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

    map.setPaintProperty('villages-fill', 'fill-opacity', [
      'interpolate',
      ['linear'],
      ['zoom'],
      3,
      0.85,
      6,
      0.85,
      8,
      0.80,
      12,
      0.75,
    ])

    map.setFilter('villages-fill', [
      'all',
      ['has', `score_${activeCrop}`],
      ['>=', ['to-number', ['get', `score_${activeCrop}`], -1], minScore],
    ])

    if (map.getLayer('villages-line')) {
      map.setFilter('villages-line', [
        'all',
        ['has', `score_${activeCrop}`],
        ['>=', ['to-number', ['get', `score_${activeCrop}`], -1], minScore],
      ])
    }
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

    const target = PROVINCE_VIEWS[regionKey] || PROVINCE_VIEWS.all
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
