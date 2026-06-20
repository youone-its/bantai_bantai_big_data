
const WILAYAH_MAP: Record<string, string> = {
  'PABEAN CANTIAN': 'Utara', 'SEMAMPIR': 'Utara', 'KENJERAN': 'Utara',
  'BULAK': 'Utara', 'KREMBANGAN': 'Utara', 'ASEMROWO': 'Utara',
  'TANDES': 'Barat', 'BENOWO': 'Barat', 'PAKAL': 'Barat',
  'LAKARSANTRI': 'Barat', 'SAMBIKEREP': 'Barat', 'SUKOMANUNGGAL': 'Barat',
  'DUKUH PAKIS': 'Barat', 'WIYUNG': 'Barat',
  'BUBUTAN': 'Pusat', 'SIMOKERTO': 'Pusat', 'GENTENG': 'Pusat',
  'TEGALSARI': 'Pusat', 'SAWAHAN': 'Pusat',
  'KARANGPILANG': 'Selatan', 'JAMBANGAN': 'Selatan',
  'GAYUNGAN': 'Selatan', 'WONOCOLO': 'Selatan', 'WONOKROMO': 'Selatan',
  'TAMBAKSARI': 'Timur', 'GUBENG': 'Timur', 'MULYOREJO': 'Timur',
  'SUKOLILO': 'Timur', 'TENGGILIS MEJOYO': 'Timur',
  'RUNGKUT': 'Timur', 'GUNUNG ANYAR': 'Timur',
};

const CLUSTER_COLORS: Record<string, { bg: string; text: string; border: string; fill: string }> = {
  'Sangat Kritis': { bg: 'rgba(239,68,68,0.1)', text: '#ef4444', border: 'rgba(239,68,68,0.3)', fill: '#ef4444' },
  'Kritis':        { bg: 'rgba(249,115,22,0.1)', text: '#f97316', border: 'rgba(249,115,22,0.3)', fill: '#f97316' },
  'Waspada':       { bg: 'rgba(234,179,8,0.1)',  text: '#eab308', border: 'rgba(234,179,8,0.3)',  fill: '#eab308' },
  'Aman':          { bg: 'rgba(16,185,129,0.1)', text: '#10b981', border: 'rgba(16,185,129,0.3)', fill: '#10b981' },
};

const normName = (s: string) => (s || '').trim().toUpperCase();

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

interface SCGIDashboardProps {
  simulatedData: KecData[];
}

export default function SCGIDashboard({ simulatedData }: SCGIDashboardProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>📊 School Capacity Gap Index (SCGI)</h2>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Metrik komposit skala 0.00–1.00 yang mengukur tingkat ketimpangan akses & infrastruktur pendidikan per kecamatan.</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        {[
          { label: '1. Densitas Demografi', weight: '50%', desc: 'Rasio anak usia 7-12 thn vs kapasitas terpasang. Bobot terbesar.' },
          { label: '2. Rasio Guru-Murid', weight: '20%', desc: 'Mengukur kecukupan tenaga pengajar untuk menjamin mutu.' },
          { label: '3. Sekolah Negeri', weight: '15%', desc: 'Ketersediaan sekolah negeri gratis untuk PPDB zonasi.' },
          { label: '4. Mutu Akreditasi', weight: '15%', desc: 'Rasio sekolah dengan akreditasi A di wilayah kecamatan.' },
        ].map((item, i) => (
          <div key={i} style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '16px', backdropFilter: 'blur(20px)' }}>
            <strong style={{ color: 'var(--accent-gold)', display: 'block', marginBottom: '4px', fontSize: '13px' }}>{item.label} <span style={{ color: '#10b981' }}>({item.weight})</span></strong>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{item.desc}</p>
          </div>
        ))}
      </div>
      <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', overflow: 'hidden', backdropFilter: 'blur(20px)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <h3 style={{ fontWeight: 600, fontSize: '14px' }}>Indeks SCGI per Kecamatan — Diurutkan dari Tertinggi</h3>
        </div>
        <div>
          {simulatedData.sort((a, b) => (b.scgi || 0) - (a.scgi || 0)).map(kec => {
            const c = CLUSTER_COLORS[kec.cluster || 'Aman'];
            return (
              <div key={kec.kecamatan_norm} style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px' }}>
                <div style={{ width: '180px', flexShrink: 0 }}>
                  <div style={{ fontWeight: 600 }}>{kec.kecamatan_norm}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Sby {WILAYAH_MAP[normName(kec.kecamatan_norm)] || '–'}</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#4b5563', marginBottom: '4px' }}>
                    <span>Aman (0.00)</span><span>Kritis (1.00)</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(0,0,0,0.4)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${(kec.scgi || 0) * 100}%`, height: '100%', background: `linear-gradient(to right, #10b981, ${c?.fill || '#ef4444'})`, transition: 'width 0.4s ease', borderRadius: '4px' }}></div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
                  <span style={{ fontFamily: 'monospace', fontWeight: 700, color: c?.text, fontSize: '16px' }}>{(kec.scgi || 0).toFixed(3)}</span>
                  <span style={{ padding: '3px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 700, background: c?.bg, color: c?.text, border: `1px solid ${c?.border}` }}>{kec.cluster}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
