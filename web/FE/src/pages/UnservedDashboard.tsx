

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

interface UnservedDashboardProps {
  simulatedData: KecData[];
  totals: {
    totalCap: number;
    totalDemand: number;
    totalUnserved: number;
    totalUsb: number;
    totalRkb: number;
    criticalCount: number;
    avgScgi: number;
  };
}

export default function UnservedDashboard({ simulatedData, totals }: UnservedDashboardProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>⚠️ Estimasi Siswa Tidak Tertampung (Krisis PPDB)</h2>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Analisis kuantitatif potensi calon peserta didik baru yang berisiko tereliminasi sistem zonasi akibat ketiadaan bangku kosong.</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
          <h3 style={{ fontWeight: 600, fontSize: '14px', marginBottom: '14px' }}>Kecamatan dengan Risiko Defisit Tertinggi</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {simulatedData.filter(k => (k.unserved || 0) > 0).sort((a, b) => (b.unserved || 0) - (a.unserved || 0)).map(kec => (
              <div key={kec.kecamatan_norm} style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: '10px', padding: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                <div>
                  <strong style={{ display: 'block', marginBottom: '2px' }}>{kec.kecamatan_norm}</strong>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Defisit {Math.abs(kec.gapCapacity || 0)} bangku · SCGI {(kec.scgi || 0).toFixed(3)}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ color: '#ef4444', fontFamily: 'monospace', fontWeight: 900, fontSize: '22px', display: 'block' }}>{kec.unserved?.toLocaleString('id-ID')}</span>
                  <span style={{ fontSize: '10px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>Siswa Rentan</span>
                </div>
              </div>
            ))}
            {simulatedData.filter(k => (k.unserved || 0) > 0).length === 0 && (
              <div style={{ textAlign: 'center', padding: '30px', color: '#10b981', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px' }}>
                ✨ Semua kecamatan terpenuhi pada parameter simulasi ini.
              </div>
            )}
          </div>
        </div>
        <div style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
          <h3 style={{ fontWeight: 600, fontSize: '14px', color: '#ef4444', marginBottom: '12px' }}>Mengapa Hal Ini Terjadi?</h3>
          <p style={{ fontSize: '12px', color: '#d1d5db', lineHeight: '1.7' }}>
            Proses seleksi PPDB berbasis geospasial (Zonasi) mengharuskan ketersediaan kuota sekolah negeri sesuai radius domisili penduduk.
            <br /><br />
            Ketika kelurahan berpopulasi anak usia sekolah tinggi tidak didukung Unit Sekolah Baru (USB), sistem terpaksa menolak calon murid yang berjarak jauh.
          </p>
          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(239,68,68,0.15)', fontSize: '12px', color: '#ef4444', fontFamily: 'monospace', fontWeight: 700 }}>
            🚨 Potensi Beban Sosial Kota Tinggi
          </div>
          <div style={{ marginTop: '12px', fontSize: '11px', color: '#6b7280' }}>
            Total siswa berpotensi tidak tertampung: <strong style={{ color: '#ef4444', fontSize: '20px', fontFamily: 'monospace', display: 'block', marginTop: '4px' }}>{totals.totalUnserved.toLocaleString('id-ID')}</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
