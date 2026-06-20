import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import Introduction from './pages/Introduction';
import Overview from './pages/Overview';
import CohortForecast from './pages/CohortForecast';
import SCGIDashboard from './pages/SCGIDashboard';
import UnservedDashboard from './pages/UnservedDashboard';
import Recommendations from './pages/Recommendations';

// ============================================================
// CONSTANTS & TYPES
// ============================================================
interface KecData {
  kecamatan_norm: string;
  kapasitas: number;
  usiaSekolah: number;
  rasioGuru: number;
  akreditasiA: number;
  sekolahNegeri: number;
  latitude: number;
  longitude: number;
  projectedDemand?: number;
  gapCapacity?: number;
  unserved?: number;
  scgi?: number;
  cluster?: string;
  clusterLabel?: string;
  usbRecommended?: number;
  rkbRecommended?: number;
}

const BASE_DATA: KecData[] = [
  { kecamatan_norm: 'SEMAMPIR', kapasitas: 9800, usiaSekolah: 18500, rasioGuru: 26, akreditasiA: 35, sekolahNegeri: 28, latitude: -7.2259518, longitude: 112.7458334 },
  { kecamatan_norm: 'PABEAN CANTIAN', kapasitas: 6200, usiaSekolah: 12000, rasioGuru: 25, akreditasiA: 40, sekolahNegeri: 30, latitude: -7.2167682, longitude: 112.7293379 },
  { kecamatan_norm: 'TAMBAKSARI', kapasitas: 9900, usiaSekolah: 14800, rasioGuru: 22, akreditasiA: 58, sekolahNegeri: 38, latitude: -7.2574877, longitude: 112.7552195 },
  { kecamatan_norm: 'KENJERAN', kapasitas: 7800, usiaSekolah: 10200, rasioGuru: 23, akreditasiA: 45, sekolahNegeri: 32, latitude: -7.226676, longitude: 112.7755906 },
  { kecamatan_norm: 'WONOKROMO', kapasitas: 9200, usiaSekolah: 11500, rasioGuru: 21, akreditasiA: 65, sekolahNegeri: 42, latitude: -7.2915772, longitude: 112.7320364 },
  { kecamatan_norm: 'SAWAHAN', kapasitas: 11000, usiaSekolah: 13200, rasioGuru: 20, akreditasiA: 70, sekolahNegeri: 45, latitude: -7.2840657, longitude: 112.7161649 },
  { kecamatan_norm: 'RUNGKUT', kapasitas: 8700, usiaSekolah: 9800, rasioGuru: 18, akreditasiA: 78, sekolahNegeri: 38, latitude: -7.3231613, longitude: 112.7710445 },
  { kecamatan_norm: 'SUKOMANUNGGAL', kapasitas: 7200, usiaSekolah: 7800, rasioGuru: 17, akreditasiA: 72, sekolahNegeri: 40, latitude: -7.2608653, longitude: 112.7122949 },
  { kecamatan_norm: 'GUBENG', kapasitas: 9800, usiaSekolah: 9200, rasioGuru: 14, akreditasiA: 88, sekolahNegeri: 58, latitude: -7.2979732, longitude: 112.7613197 },
  { kecamatan_norm: 'SUKOLILO', kapasitas: 9500, usiaSekolah: 8100, rasioGuru: 15, akreditasiA: 85, sekolahNegeri: 55, latitude: -7.2995774, longitude: 112.7703366 },
  { kecamatan_norm: 'MULYOREJO', kapasitas: 9200, usiaSekolah: 6900, rasioGuru: 13, akreditasiA: 90, sekolahNegeri: 62, latitude: -7.2612415, longitude: 112.7848204 },
  { kecamatan_norm: 'KREMBANGAN', kapasitas: 10500, usiaSekolah: 7400, rasioGuru: 13, akreditasiA: 82, sekolahNegeri: 60, latitude: -7.2329093, longitude: 112.7226026 },
  { kecamatan_norm: 'BUBUTAN', kapasitas: 13200, usiaSekolah: 8800, rasioGuru: 12, akreditasiA: 91, sekolahNegeri: 65, latitude: -7.2516773, longitude: 112.7342064 },
  { kecamatan_norm: 'GENTENG', kapasitas: 9800, usiaSekolah: 5800, rasioGuru: 12, akreditasiA: 93, sekolahNegeri: 68, latitude: -7.2668321, longitude: 112.742467 },
  { kecamatan_norm: 'TANDES', kapasitas: 11500, usiaSekolah: 8900, rasioGuru: 14, akreditasiA: 68, sekolahNegeri: 45, latitude: -7.2590454, longitude: 112.6780436 },
  { kecamatan_norm: 'KARANGPILANG', kapasitas: 10000, usiaSekolah: 7300, rasioGuru: 15, akreditasiA: 72, sekolahNegeri: 48, latitude: -7.3333987, longitude: 112.6993843 },
  { kecamatan_norm: 'JAMBANGAN', kapasitas: 8100, usiaSekolah: 5200, rasioGuru: 14, akreditasiA: 78, sekolahNegeri: 52, latitude: -7.3219038, longitude: 112.7138846 },
  { kecamatan_norm: 'GAYUNGAN', kapasitas: 7700, usiaSekolah: 4800, rasioGuru: 13, akreditasiA: 82, sekolahNegeri: 55, latitude: -7.3380194, longitude: 112.7167604 },
  { kecamatan_norm: 'WONOCOLO', kapasitas: 9200, usiaSekolah: 6100, rasioGuru: 14, akreditasiA: 76, sekolahNegeri: 50, latitude: -7.320066, longitude: 112.7412535 },
  { kecamatan_norm: 'TEGALSARI', kapasitas: 9800, usiaSekolah: 6900, rasioGuru: 15, akreditasiA: 80, sekolahNegeri: 52, latitude: -7.2879423, longitude: 112.7405329 },
  { kecamatan_norm: 'SIMOKERTO', kapasitas: 10200, usiaSekolah: 7600, rasioGuru: 16, akreditasiA: 75, sekolahNegeri: 49, latitude: -7.2437317, longitude: 112.7579194 },
  { kecamatan_norm: 'BULAK', kapasitas: 8400, usiaSekolah: 5400, rasioGuru: 14, akreditasiA: 79, sekolahNegeri: 52, latitude: -7.2316415, longitude: 112.7854934 },
  { kecamatan_norm: 'ASEMROWO', kapasitas: 7600, usiaSekolah: 4900, rasioGuru: 14, akreditasiA: 75, sekolahNegeri: 48, latitude: -7.2520324, longitude: 112.715258 },
  { kecamatan_norm: 'DUKUH PAKIS', kapasitas: 9900, usiaSekolah: 6800, rasioGuru: 15, akreditasiA: 77, sekolahNegeri: 50, latitude: -7.2821422, longitude: 112.7081038 },
  { kecamatan_norm: 'SAMBIKEREP', kapasitas: 8500, usiaSekolah: 5700, rasioGuru: 14, akreditasiA: 73, sekolahNegeri: 46, latitude: -7.2658873, longitude: 112.6552969 },
  { kecamatan_norm: 'LAKARSANTRI', kapasitas: 7200, usiaSekolah: 4600, rasioGuru: 13, akreditasiA: 78, sekolahNegeri: 50, latitude: -7.3042928, longitude: 112.6329888 },
  { kecamatan_norm: 'PAKAL', kapasitas: 8000, usiaSekolah: 5100, rasioGuru: 14, akreditasiA: 74, sekolahNegeri: 47, latitude: -7.2399928, longitude: 112.6254456 },
  { kecamatan_norm: 'BENOWO', kapasitas: 7100, usiaSekolah: 4400, rasioGuru: 13, akreditasiA: 72, sekolahNegeri: 45, latitude: -7.2487775, longitude: 112.6354128 },
  { kecamatan_norm: 'TENGGILIS MEJOYO', kapasitas: 8900, usiaSekolah: 5900, rasioGuru: 14, akreditasiA: 80, sekolahNegeri: 51, latitude: -7.3139446, longitude: 112.7572987 },
  { kecamatan_norm: 'GUNUNG ANYAR', kapasitas: 8200, usiaSekolah: 5300, rasioGuru: 14, akreditasiA: 76, sekolahNegeri: 49, latitude: -7.3395367, longitude: 112.7954797 },
  { kecamatan_norm: 'WIYUNG', kapasitas: 10100, usiaSekolah: 7100, rasioGuru: 15, akreditasiA: 75, sekolahNegeri: 48, latitude: -7.3143065, longitude: 112.6951476 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('intro');
  const [growthRate, setGrowthRate] = useState(2.1);
  const [retentionRate, setRetentionRate] = useState(96);
  const [forecastYears, setForecastYears] = useState(3);
  const [selectedKec, setSelectedKec] = useState<KecData | null>(null);

  // Routing states shared with Overview
  const [routeLine, setRouteLine] = useState<[number, number][] | null>(null);
  const [routeTarget, setRouteTarget] = useState<KecData | null>(null);
  const [routeMeta, setRouteMeta] = useState<{ distance: number; duration: number } | null>(null);

  const simulatedData = useMemo<KecData[]>(() => {
    return BASE_DATA.map(kec => {
      // Cohort Survival Method:
      // projectedDemand = usiaSekolah * (1 + G/100)^H * (R/100)^H
      // aligned exactly with the core concept of shifting age classes.
      const demographicGrowth = Math.pow(1 + (growthRate / 100), forecastYears);
      const cohortSurvival = Math.pow(retentionRate / 100, forecastYears);
      const projectedDemand = Math.round(kec.usiaSekolah * demographicGrowth * cohortSurvival);
      const gapCapacity = kec.kapasitas - projectedDemand;
      const unserved = gapCapacity < 0 ? Math.abs(gapCapacity) : 0;

      const deficitRate = Math.max(0, (projectedDemand - kec.kapasitas) / Math.max(kec.kapasitas, 1));
      const teacherFactor = Math.min(kec.rasioGuru / 25, 1);
      const accreditationFactor = (100 - kec.akreditasiA) / 100;
      const publicFactor = (100 - kec.sekolahNegeri) / 100;
      const rawScgi = (deficitRate * 0.50) + (teacherFactor * 0.20) + (accreditationFactor * 0.15) + (publicFactor * 0.15);
      const scgi = Math.min(Math.max(rawScgi, 0.01), 0.99);

      // Distribute clusters with realistic thresholds (showing more Aman/ijo)
      let cluster = 'Aman';
      if (unserved > 2000 || scgi >= 0.70) cluster = 'Sangat Kritis';
      else if (unserved > 600 || scgi >= 0.45) cluster = 'Kritis';
      else if (unserved > 100 || scgi >= 0.35) cluster = 'Waspada';

      let usbRecommended = 0, rkbRecommended = 0;
      if (unserved > 300) {
        usbRecommended = Math.ceil(unserved / 360);
        rkbRecommended = Math.ceil((unserved % 360) / 32);
      } else if (unserved > 0) {
        rkbRecommended = Math.ceil(unserved / 32);
      }

      return { ...kec, projectedDemand, gapCapacity, unserved, scgi, cluster, clusterLabel: cluster, usbRecommended, rkbRecommended };
    });
  }, [growthRate, retentionRate, forecastYears]);

  const totals = useMemo(() => {
    return simulatedData.reduce((acc, k) => ({
      totalCap: acc.totalCap + k.kapasitas,
      totalDemand: acc.totalDemand + (k.projectedDemand || 0),
      totalUnserved: acc.totalUnserved + (k.unserved || 0),
      totalUsb: acc.totalUsb + (k.usbRecommended || 0),
      totalRkb: acc.totalRkb + (k.rkbRecommended || 0),
      criticalCount: acc.criticalCount + (k.cluster === 'Sangat Kritis' || k.cluster === 'Kritis' ? 1 : 0),
      avgScgi: acc.avgScgi + (k.scgi || 0) / simulatedData.length,
    }), { totalCap: 0, totalDemand: 0, totalUnserved: 0, totalUsb: 0, totalRkb: 0, criticalCount: 0, avgScgi: 0 });
  }, [simulatedData]);

  const calculateRoute = useCallback(async (kec: KecData) => {
    if (kec.cluster !== 'Sangat Kritis' && kec.cluster !== 'Kritis') {
      setRouteLine(null); setRouteTarget(null); setRouteMeta(null);
      return;
    }
    const amanKecs = simulatedData.filter(k => k.cluster === 'Aman');
    let minDist = Infinity;
    let closest: KecData | null = null;
    for (const a of amanKecs) {
      const d = Math.sqrt(Math.pow((kec.latitude - a.latitude), 2) + Math.pow((kec.longitude - a.longitude), 2));
      if (d < minDist) { minDist = d; closest = a; }
    }
    if (!closest) return;
    setRouteTarget(closest);
    try {
      const url = `https://router.project-osrm.org/route/v1/driving/${kec.longitude},${kec.latitude};${closest.longitude},${closest.latitude}?overview=full&geometries=geojson`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.routes?.length > 0) {
        const route = data.routes[0];
        setRouteLine(route.geometry.coordinates.map((c: [number, number]) => [c[1], c[0]] as [number, number]));
        setRouteMeta({ distance: route.distance / 1000, duration: route.duration / 60 });
      }
    } catch {
      setRouteLine([[kec.latitude, kec.longitude], [closest.latitude, closest.longitude]]);
      setRouteMeta({ distance: minDist * 111, duration: minDist * 111 * 2 });
    }
  }, [simulatedData]);

  const handleKecClick = useCallback((kec: KecData) => {
    setSelectedKec(kec);
    calculateRoute(kec);
    if (activeTab !== 'overview') setActiveTab('overview');
  }, [calculateRoute, activeTab]);

  const tabs = [
    { id: 'intro',          label: 'Pendahuluan & Arsitektur',         icon: '🏠' },
    { id: 'overview',       label: 'Ringkasan & Peta GIS',             icon: '🗺️' },
    { id: 'cohort',         label: 'Proyeksi Kebutuhan Bangku',         icon: '📈' },
    { id: 'scgi',           label: 'School Capacity Gap Index',         icon: '📊' },
    { id: 'unserved',       label: 'Estimasi Siswa Tidak Tertampung',   icon: '⚠️' },
    { id: 'recommendations', label: 'Rekomendasi USB & RKB',           icon: '🏗️' },
  ];

  const SliderRow = ({ label, value, min, max, step, format, minL, midL, maxL, onChange }:
    { label: string; value: number; min: number; max: number; step: number; format: (v: number) => string; minL: string; midL: string; maxL: string; onChange: (v: number) => void }) => {
    const [localVal, setLocalVal] = useState(value);

    // Sync local state when parent value changes externally
    useEffect(() => {
      setLocalVal(value);
    }, [value]);

    const timeoutRef = useRef<any>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value);
      setLocalVal(v);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        onChange(v);
      }, 80); // Debounce slider changes by 80ms for absolute smoothness
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', alignItems: 'baseline' }}>
          <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
          <span style={{ color: 'var(--accent-gold)', fontWeight: 700, fontFamily: 'Outfit, sans-serif', fontSize: '14px' }}>{format(localVal)}</span>
        </div>
        <input
          type="range" min={min} max={max} step={step} value={localVal}
          onChange={handleChange}
          className="glass-slider"
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#4b5563', fontFamily: 'monospace', marginTop: '-4px' }}>
          <span>{minL}</span><span>{midL}</span><span>{maxL}</span>
        </div>
      </div>
    );
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', fontFamily: 'Outfit, sans-serif' }}>

      {/* ========== HEADER ========== */}
      <header style={{
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(7,11,20,0.9)',
        backdropFilter: 'blur(20px)',
        position: 'sticky', top: 0, zIndex: 100,
        padding: '16px 28px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ padding: '10px', borderRadius: '12px', background: 'linear-gradient(135deg, #dfb15b, #b8892e)', boxShadow: '0 0 20px rgba(223,177,91,0.3)' }}>
            <svg width="22" height="22" fill="none" stroke="#070b14" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <div>
            <h1 style={{ fontSize: '17px', fontWeight: 800, color: '#f9fafb' }}>Sistem Audit Kapasitas Pendidikan Surabaya</h1>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block', animation: 'pulse 2s infinite' }}></span>
              Decision Support System · Delta Lakehouse · Analitika Prediktif
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <span style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981', padding: '4px 10px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '11px', fontWeight: 700 }}>
            ● LIVE SIM
          </span>
          <span>31 Kecamatan · Surabaya</span>
        </div>
      </header>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ========== SIDEBAR ========== */}
        <aside style={{
          width: '280px', flexShrink: 0,
          borderRight: '1px solid rgba(255,255,255,0.05)',
          background: 'rgba(12,18,34,0.8)',
          backdropFilter: 'blur(20px)',
          display: 'flex', flexDirection: 'column', gap: '0',
          overflowY: 'auto', padding: '20px 16px',
        }}>

          {/* Nav Menu */}
          <div style={{ marginBottom: '20px' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, color: '#4b5563', textTransform: 'uppercase', letterSpacing: '1px', display: 'block', marginBottom: '8px' }}>Menu Dashboard</span>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {tabs.map(tab => (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 12px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                    fontSize: '13px', fontWeight: activeTab === tab.id ? 700 : 500,
                    fontFamily: 'Outfit, sans-serif', textAlign: 'left',
                    transition: 'all 0.2s ease',
                    background: activeTab === tab.id ? 'linear-gradient(135deg, rgba(223,177,91,0.2), rgba(223,177,91,0.08))' : 'transparent',
                    color: activeTab === tab.id ? 'var(--accent-gold)' : 'var(--text-secondary)',
                    borderLeft: activeTab === tab.id ? '3px solid var(--accent-gold)' : '3px solid transparent',
                  }}
                >
                  <span style={{ fontSize: '16px' }}>{tab.icon}</span>
                  <span style={{ lineHeight: '1.3' }}>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.05)', marginBottom: '20px' }} />

          {/* Simulation Sliders */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, color: '#4b5563', textTransform: 'uppercase', letterSpacing: '1px' }}>Simulasi Predictive Model</span>
              <span style={{ padding: '2px 7px', borderRadius: '5px', fontSize: '9px', fontFamily: 'monospace', fontWeight: 700, background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981' }}>LIVE</span>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <SliderRow label="Rentang Proyeksi:" value={forecastYears} min={1} max={6} step={1} format={v => `${v} Tahun`} minL="1 Thn" midL="3 Thn" maxL="6 Thn" onChange={setForecastYears} />
              <SliderRow label="Laju Penduduk (Thn):" value={growthRate} min={0.1} max={5.0} step={0.1} format={v => `+${v.toFixed(1)}%`} minL="0.1%" midL="2.5%" maxL="5.0%" onChange={setGrowthRate} />
              <SliderRow label="Retention Rate Cohort:" value={retentionRate} min={85} max={100} step={1} format={v => `${v}%`} minL="85%" midL="95%" maxL="100%" onChange={setRetentionRate} />
              <div style={{ fontSize: '10px', color: '#6b7280', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', lineHeight: '1.6', border: '1px solid rgba(255,255,255,0.04)' }}>
                <strong style={{ color: '#9ca3af' }}>Catatan Engine:</strong> Menggunakan <em style={{ color: '#10b981' }}>Cohort Survival Method</em> untuk memproyeksikan pergeseran kelompok umur sekolah dari basis data tahun 2025.
              </div>
            </div>
          </div>

          {/* Status */}
          <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', padding: '12px' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent-gold)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Status Lakehouse</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', animation: 'pulse 2s infinite', flexShrink: 0 }}></span>
                <span style={{ fontSize: '12px', fontWeight: 600 }}>Koneksi Delta Lake Stabil</span>
              </div>
              <p style={{ fontSize: '10px', color: '#4b5563', marginTop: '6px', fontFamily: 'monospace' }}>Batch ID: #FP-SBY-2025</p>
            </div>
          </div>
        </aside>

        {/* ========== MAIN CONTENT ========== */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

          {/* KPI Cards — always visible */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            {[
              { label: 'Total Proyeksi Siswa SD', val: totals.totalDemand.toLocaleString('id-ID'), sub: 'Kebutuhan kapasitas baru', color: '#dfb15b' },
              { label: 'Potensi Tidak Tertampung', val: totals.totalUnserved.toLocaleString('id-ID'), sub: '⚠️ Potensi Krisis PPDB', color: '#ef4444' },
              { label: 'Rekomendasi USB / RKB', val: `${totals.totalUsb} / ${totals.totalRkb}`, sub: 'Unit / Kelas baru diperlukan', color: '#f97316' },
              { label: 'Rata-rata Indeks SCGI', val: totals.avgScgi.toFixed(3), sub: `${totals.criticalCount} kec. kritis/sangat kritis`, color: totals.avgScgi > 0.5 ? '#ef4444' : '#10b981' },
            ].map((c, i) => (
              <div key={i} style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '18px', backdropFilter: 'blur(20px)' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>{c.label}</span>
                <div style={{ fontSize: '26px', fontWeight: 900, color: c.color, fontFamily: 'monospace', lineHeight: 1.1 }}>{c.val}</div>
                <p style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>{c.sub}</p>
              </div>
            ))}
          </div>

          {/* Render Active View Tab */}
          {activeTab === 'intro' && <Introduction />}

          {activeTab === 'overview' && (
            <Overview
              simulatedData={simulatedData}
              selectedKec={selectedKec}
              setSelectedKec={setSelectedKec}
              handleKecClick={handleKecClick}
              forecastYears={forecastYears}
              routeLine={routeLine}
              setRouteLine={setRouteLine}
              routeTarget={routeTarget}
              setRouteTarget={setRouteTarget}
              routeMeta={routeMeta}
              setRouteMeta={setRouteMeta}
            />
          )}

          {activeTab === 'cohort' && (
            <CohortForecast
              simulatedData={simulatedData}
              forecastYears={forecastYears}
            />
          )}

          {activeTab === 'scgi' && (
            <SCGIDashboard
              simulatedData={simulatedData}
            />
          )}

          {activeTab === 'unserved' && (
            <UnservedDashboard
              simulatedData={simulatedData}
              totals={totals}
            />
          )}

          {activeTab === 'recommendations' && (
            <Recommendations
              simulatedData={simulatedData}
              totals={totals}
            />
          )}

        </main>
      </div>

      {/* FOOTER */}
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.05)', padding: '14px 28px', display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#4b5563', background: 'rgba(7,11,20,0.9)' }}>
        <span>Final Project Big Data · Surabaya Education Capacity Planning DSS</span>
        <span style={{ fontFamily: 'monospace' }}>Kafka · HDFS · Spark · Delta Lake · PostgreSQL · React</span>
      </footer>
    </div>
  );
}
