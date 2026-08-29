export type CropId = 'coffee' | 'cocoa' | 'sugarcane'

export interface CropMeta {
  id: CropId
  name: string
  scientificName: string
  category: 'Perennial' | 'Annual'
  optimalTemp: string
  optimalRainfall: string
  optimalElevation: string
  optimalSoilPh: string
  description: string
}

export interface CropScoreDetail {
  crop: string
  score: number
  climate_score?: number
  soil_score?: number
  terrain_score?: number
  access_score?: number
  computed_at?: string
}

export interface VillageDetail {
  id: number
  adm_pcode: string
  name: string
  kecamatan?: string
  kabupaten?: string
  province?: string
  resolution: string
  center_lat?: number
  center_lon?: number
  bbox?: [number, number, number, number]
  scores: CropScoreDetail[]
}

export interface HealthStatus {
  status: string
  version: string
  database: string
  total_villages: number
  total_scores: number
}

export const CROPS: Record<CropId, CropMeta> = {
  coffee: {
    id: 'coffee',
    name: 'Coffee (Robusta)',
    scientificName: 'Coffea canephora',
    category: 'Perennial',
    optimalTemp: '22 - 26 °C',
    optimalRainfall: '1,500 - 2,500 mm',
    optimalElevation: '200 - 800 m',
    optimalSoilPh: '5.5 - 6.5',
    description: 'Thrives in warm, humid climates with well-drained volcanic soils and moderate slopes.',
  },
  cocoa: {
    id: 'cocoa',
    name: 'Cocoa',
    scientificName: 'Theobroma cacao',
    category: 'Perennial',
    optimalTemp: '22 - 30 °C',
    optimalRainfall: '1,500 - 2,500 mm',
    optimalElevation: '50 - 500 m',
    optimalSoilPh: '6.0 - 7.2',
    description: 'Lowland tropical tree crop demanding high rainfall consistency and deep organic soil.',
  },
  sugarcane: {
    id: 'sugarcane',
    name: 'Sugarcane',
    scientificName: 'Saccharum officinarum',
    category: 'Annual',
    optimalTemp: '24 - 30 °C',
    optimalRainfall: '1,500 - 2,500 mm',
    optimalElevation: '0 - 400 m',
    optimalSoilPh: '6.0 - 7.5',
    description: 'Annual grass requiring flat alluvial terrain, strong sunshine, and dry harvest period.',
  },
}

export const PROVINCE_VIEWS: Record<string, { center: [number, number]; zoom: number }> = {
  all: { center: [118.0, -3.0], zoom: 5 },
  east_java: { center: [112.5, -7.7], zoom: 8 },
  lampung: { center: [105.2, -5.0], zoom: 8 },
  south_sulawesi: { center: [120.0, -4.0], zoom: 7.5 },
}
