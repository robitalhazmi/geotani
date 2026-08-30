import React, { useEffect, useRef } from 'react'
import maplibregl, { Map, Popup } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { CropId, VillageDetail } from '../types'

interface MapComponentProps {
  activeCrop: CropId
  minScore: number
  selectedVillage: VillageDetail | null
  onSelectVillage: (village: VillageDetail | null) => void
  regionKey: string
}

export const MapComponent: React.FC<MapComponentProps> = ({
  activeCrop,
  minScore,
  selectedVillage,
  onSelectVillage,
  regionKey,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const popupRef = useRef<Popup | null>(null)

  // Initialize Map
  useEffect(() => {
    if (mapRef.current || !mapContainer.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [115.0, -7.5], // Center near East Java & Bali initially
      zoom: 6,
      minZoom: 4,
      maxZoom: 14,
    })

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-right')

    map.on('load', () => {
      const tilesUrl = import.meta.env.VITE_TILES_URL || 'http://localhost:3000'

      // Vector Tile Source from Martin Tile Server
      map.addSource('village_suitability', {
        type: 'vector',
        tiles: [`${tilesUrl}/village_suitability/{z}/{x}/{y}`],
        minzoom: 4,
        maxzoom: 14,
      })

      // Fill Layer with score interpolation
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
              ['coalesce', ['get', `score_${activeCrop}`], 0],
              0,
              '#fca5a5',
              30,
              '#fb923c',
              50,
              '#facc15',
              70,
              '#4ade80',
              85,
              '#15803d',
              100,
              '#052e16',
            ],
            'fill-opacity': 0.72,
          },
          filter: ['>=', ['coalesce', ['get', `score_${activeCrop}`], 0], minScore],
        },
        'building' // Place beneath building layer if present
      )

      // Village Boundaries Line Layer
      map.addLayer({
        id: 'villages-line',
        type: 'line',
        source: 'village_suitability',
        'source-layer': 'village_suitability',
        paint: {
          'line-color': '#ffffff',
          'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.2, 10, 0.8, 14, 1.5],
          'line-opacity': 0.5,
        },
      })

      // Selection Highlight Layer
      map.addLayer({
        id: 'villages-highlight',
        type: 'line',
        source: 'village_suitability',
        'source-layer': 'village_suitability',
        paint: {
          'line-color': '#0284c7',
          'line-width': 3,
          'line-opacity': 0.9,
        },
        filter: ['==', ['get', 'id'], -1],
      })
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
      const name = String(feat.properties?.name || 'Village')
      const kab = String(feat.properties?.kabupaten || '')
      const currentScore = Number(feat.properties?.[`score_${activeCrop}`] ?? 0).toFixed(1)

      const container = document.createElement('div')
      container.className = 'p-1 font-sans text-xs'

      const titleEl = document.createElement('div')
      titleEl.className = 'font-bold text-gray-900'
      titleEl.textContent = name
      container.appendChild(titleEl)

      if (kab) {
        const subEl = document.createElement('div')
        subEl.className = 'text-[11px] text-gray-500'
        subEl.textContent = kab
        container.appendChild(subEl)
      }

      const scoreEl = document.createElement('div')
      scoreEl.className = 'mt-1 font-semibold text-emerald-700'
      scoreEl.textContent = `Suitability: ${currentScore}%`
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
          const res = await fetch(`http://localhost:8000/villages/${villageId}`)
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
      ['coalesce', ['get', `score_${activeCrop}`], 0],
      0,
      '#fca5a5',
      30,
      '#fb923c',
      50,
      '#facc15',
      70,
      '#4ade80',
      85,
      '#15803d',
      100,
      '#052e16',
    ])

    map.setFilter('villages-fill', ['>=', ['coalesce', ['get', `score_${activeCrop}`], 0], minScore])
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

  return <div ref={mapContainer} className="relative h-full w-full" />
}
