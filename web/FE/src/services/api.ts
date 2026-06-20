// API Service Layer for Surabaya School Capacity Audit REST API
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface HealthStatus {
  status: string;
  postgres_status: string;
  database: string;
}

export interface TableItem {
  table_name: string;
  description: string;
}

export interface TablesList {
  total_tables: number;
  tables: Record<string, string>;
}

export interface KecamatanSCGI {
  kecamatan_key: string;
  kecamatan_norm: string;
  demand_2025: number;
  demand_2030: number;
  kapasitas: number;
  jumlah_sekolah: number;
  deficit_rate: number;
  utilisasi_norm: number;
  growth_rate: number;
  scgi_raw: number;
  utilisasi_2030: number;
  deficit_2030: number;
  scgi_score: number;
  scgi_category: string;
  scgi_rank: number;
}

export interface ClusterSummary {
  priority_rank: number;
  priority_label: string;
  kecamatan: string[];
}

export interface KecamatanCluster {
  kecamatan_key: string;
  kecamatan_norm: string;
  scgi_score: number;
  scgi_category: string;
  scgi_rank: number;
  demand_2025: number;
  demand_2030: number;
  kapasitas: number;
  deficit_rate: number;
  utilisasi_norm: number;
  growth_rate: number;
  scgi_raw: number;
  utilisasi_2030: number;
  deficit_2030: number;
  cluster_id: number;
  priority_rank: number;
  priority_label: string;
}

export interface ClusterResponse {
  count: number;
  filter_priority: string | null;
  cluster_summary: ClusterSummary[];
  data: KecamatanCluster[];
}

export interface Rekomendasi {
  peringkat_prioritas: number;
  kecamatan_key: string;
  kecamatan_norm: string;
  tahun_target: number;
  demand_total: number;
  kapasitas: number;
  siswa_tak_tertampung: number;
  utilisasi_pct: number;
  jumlah_sekolah: number;
  ruang_kelas_baru: number;
  rekomendasi: string;
  skor_prioritas: number;
}

export interface GapAnalysis {
  kecamatan_key: string;
  kecamatan_norm: string;
  tahun_proyeksi: number;
  demand_total: number;
  kapasitas: number;
  gap: number;
  siswa_tak_tertampung: number;
  utilisasi_pct: number;
}

export interface Proyeksi {
  kecamatan_key: string;
  kecamatan_norm: string;
  tahun_proyeksi: number;
  demand_sd: number;
  demand_smp: number;
  demand_total: number;
}

export interface EvaluationMetric {
  model: string;
  metric: string;
  value: number;
  unit: string;
  status: string;
  interpretasi: string;
}

export interface DataQualityRow {
  table: string;
  layer: string;
  dimension: string;
  metric: string;
  value: string;
  status: string;
  note: string;
}

async function request<T>(path: string): Promise<T> {
  const url = `${BASE_URL}${path}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json() as T;
  } catch (error) {
    console.error(`API request failed for URL: ${url}`, error);
    throw error;
  }
}

export const api = {
  getHealth: () => request<HealthStatus>('/health'),
  
  getTables: () => request<TablesList>('/tables'),
  
  getSCGI: (top: number = 31, category?: string) => {
    let path = `/analysis/scgi?top=${top}`;
    if (category) path += `&category=${category}`;
    return request<{ count: number; filter_category: string | null; data: KecamatanSCGI[] }>(path);
  },
  
  getClusters: (priority?: string) => {
    let path = '/analysis/cluster';
    if (priority) path += `?priority=${priority}`;
    return request<ClusterResponse>(path);
  },
  
  getRekomendasi: (top: number = 31, filterRekom?: string) => {
    let path = `/analysis/rekomendasi?top=${top}`;
    if (filterRekom) path += `&filter_rekom=${filterRekom}`;
    return request<{ count: number; data: Rekomendasi[] }>(path);
  },
  
  getGap: (kecamatan: string) => 
    request<{ kecamatan: string; count: number; data: GapAnalysis[] }>(`/analysis/gap/${encodeURIComponent(kecamatan)}`),
  
  getProyeksi: (kecamatan: string) => 
    request<{ kecamatan: string; count: number; data: Proyeksi[] }>(`/analysis/proyeksi/${encodeURIComponent(kecamatan)}`),
  
  getEvaluation: () => 
    request<{ count: number; data: EvaluationMetric[] }>('/analysis/evaluation'),

  getDataQuality: () =>
    request<{ table_name: string; record_count: number; data: DataQualityRow[] }>('/tables/gold_data_quality_report?limit=100')
};
