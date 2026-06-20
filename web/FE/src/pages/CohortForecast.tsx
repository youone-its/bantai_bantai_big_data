
const CLUSTER_COLORS: Record<string, { bg: string; text: string; border: string; fill: string }> = {
  'Sangat Kritis': { bg: 'rgba(239,68,68,0.1)', text: '#ef4444', border: 'rgba(239,68,68,0.3)', fill: '#ef4444' },
  'Kritis':        { bg: 'rgba(249,115,22,0.1)', text: '#f97316', border: 'rgba(249,115,22,0.3)', fill: '#f97316' },
  'Waspada':       { bg: 'rgba(234,179,8,0.1)',  text: '#eab308', border: 'rgba(234,179,8,0.3)',  fill: '#eab308' },
  'Aman':          { bg: 'rgba(16,185,129,0.1)', text: '#10b981', border: 'rgba(16,185,129,0.3)', fill: '#10b981' },
};

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

interface CohortForecastProps {
  simulatedData: KecData[];
  forecastYears: number;
}

export default function CohortForecast({ simulatedData, forecastYears }: CohortForecastProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>📈 Age-Cohort Shift Forecasting — Proyeksi {forecastYears} Tahun</h2>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Visualisasi gap antara kapasitas terpasang vs kebutuhan proyeksi per kecamatan. Parameter disesuaikan lewat slider di sidebar.</p>
      </div>
      <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '24px', backdropFilter: 'blur(20px)' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '20px', color: 'var(--accent-gold)' }}>Grafik Kapasitas vs Kebutuhan Murid per Kecamatan</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {simulatedData.sort((a, b) => (b.projectedDemand || 0) - (a.projectedDemand || 0)).map(kec => {
            const maxVal = Math.max(...simulatedData.map(k => Math.max(k.kapasitas, k.projectedDemand || 0)));
            const capPct = (kec.kapasitas / maxVal) * 100;
            const demandPct = ((kec.projectedDemand || 0) / maxVal) * 100;
            const isDefisit = (kec.gapCapacity || 0) < 0;
            const c = CLUSTER_COLORS[kec.cluster || 'Aman'];
            return (
              <div key={kec.kecamatan_norm} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ fontWeight: 600, width: '160px', flexShrink: 0 }}>{kec.kecamatan_norm}</span>
                  <div style={{ display: 'flex', gap: '16px', fontFamily: 'monospace', fontSize: '11px' }}>
                    <span style={{ color: '#9ca3af' }}>Kapasitas: {kec.kapasitas.toLocaleString()}</span>
                    <span style={{ color: 'var(--accent-gold)' }}>Proyeksi: {(kec.projectedDemand || 0).toLocaleString()}</span>
                    <span style={{ color: isDefisit ? '#ef4444' : '#10b981', fontWeight: 700 }}>
                      {isDefisit ? `Defisit ${Math.abs(kec.gapCapacity || 0)}` : `Aman +${kec.gapCapacity}`}
                    </span>
                  </div>
                </div>
                <div style={{ height: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '4px', overflow: 'hidden', position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '2px', padding: '2px' }}>
                  <div style={{ width: `${capPct}%`, height: '4px', background: '#374151', borderRadius: '2px', transition: 'width 0.4s ease' }}></div>
                  <div style={{ width: `${demandPct}%`, height: '4px', background: isDefisit ? c?.fill || '#ef4444' : '#10b981', borderRadius: '2px', transition: 'width 0.4s ease' }}></div>
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ display: 'flex', gap: '20px', fontSize: '11px', color: '#6b7280', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.05)', fontFamily: 'monospace' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '12px', height: '4px', background: '#374151', borderRadius: '2px' }}></span>Kapasitas Terpasang</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '12px', height: '4px', background: '#10b981', borderRadius: '2px' }}></span>Proyeksi (Surplus/Cukup)</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '12px', height: '4px', background: '#ef4444', borderRadius: '2px' }}></span>Proyeksi (Defisit)</div>
        </div>
      </div>
    </div>
  );
}
