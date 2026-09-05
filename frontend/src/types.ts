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
  all: { center: [118.0, -2.5], zoom: 4.8 },
  east_java: { center: [112.5, -7.7], zoom: 8.2 },
  lampung: { center: [105.2, -5.0], zoom: 8.5 },
  south_sulawesi: { center: [120.0, -3.8], zoom: 7.8 },
}

export interface SuitabilityTier {
  min: number
  max: number
  label: string
  title: string
  color: string
  textColor: string
  bgColor: string
  lightBg: string
  borderColor: string
}

export const SUITABILITY_TIERS: SuitabilityTier[] = [
  {
    min: 85,
    max: 100,
    label: '85 - 100%',
    title: 'Highly Suitable',
    color: '#16a34a',
    textColor: 'text-emerald-700',
    bgColor: 'bg-emerald-600',
    lightBg: 'bg-emerald-50',
    borderColor: 'border-emerald-300',
  },
  {
    min: 70,
    max: 85,
    label: '70 - 85%',
    title: 'Suitable',
    color: '#84cc16',
    textColor: 'text-lime-700',
    bgColor: 'bg-lime-500',
    lightBg: 'bg-lime-50',
    borderColor: 'border-lime-300',
  },
  {
    min: 50,
    max: 70,
    label: '50 - 70%',
    title: 'Moderately Suitable',
    color: '#eab308',
    textColor: 'text-amber-700',
    bgColor: 'bg-amber-500',
    lightBg: 'bg-amber-50',
    borderColor: 'border-amber-300',
  },
  {
    min: 30,
    max: 50,
    label: '30 - 50%',
    title: 'Marginally Suitable',
    color: '#f97316',
    textColor: 'text-orange-700',
    bgColor: 'bg-orange-500',
    lightBg: 'bg-orange-50',
    borderColor: 'border-orange-300',
  },
  {
    min: 0,
    max: 30,
    label: '< 30%',
    title: 'Unsuitable / Restricted',
    color: '#ef4444',
    textColor: 'text-red-700',
    bgColor: 'bg-red-500',
    lightBg: 'bg-red-50',
    borderColor: 'border-red-300',
  },
]

export function getSuitabilityTier(score: number): SuitabilityTier {
  if (score >= 85) return SUITABILITY_TIERS[0]
  if (score >= 70) return SUITABILITY_TIERS[1]
  if (score >= 50) return SUITABILITY_TIERS[2]
  if (score >= 30) return SUITABILITY_TIERS[3]
  return SUITABILITY_TIERS[4]
}
