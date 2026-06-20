
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

interface RecommendationsProps {
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

export default function Recommendations({ simulatedData, totals }: RecommendationsProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>🏗️ Rekomendasi Pembangunan Fisik (USB & RKB)</h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Saran aksi pembangunan sarana pendidikan baru berbasis analisis kapasitas prediktif model.</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block' }}>Estimasi Total Anggaran</span>
          <strong style={{ color: '#10b981', fontFamily: 'monospace', fontSize: '18px' }}>Rp {((totals.totalUsb * 12) + (totals.totalRkb * 0.35)).toFixed(1)} Milyar</strong>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', overflow: 'hidden', backdropFilter: 'blur(20px)' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontWeight: 600, fontSize: '14px' }}>Tabel Prioritas Intervensi</h3>
            <span style={{ fontSize: '11px', color: '#6b7280', fontFamily: 'monospace' }}>1 USB ≈ 360 Kursi · 1 RKB = 32 Kursi</span>
          </div>
          {simulatedData.filter(k => (k.unserved || 0) > 0).sort((a, b) => (b.unserved || 0) - (a.unserved || 0)).map(kec => (
            <div key={kec.kecamatan_norm} style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px', gap: '12px' }}>
              <div style={{ width: '160px', flexShrink: 0 }}>
                <strong style={{ display: 'block' }}>{kec.kecamatan_norm}</strong>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{kec.unserved} siswa tidak tertampung</span>
              </div>
              <div style={{ display: 'flex', gap: '8px', flex: 1 }}>
                {(kec.usbRecommended || 0) > 0 && (
                  <span style={{ padding: '5px 10px', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontWeight: 700, fontSize: '12px' }}>
                    🏗️ {kec.usbRecommended} USB
                  </span>
                )}
                {(kec.rkbRecommended || 0) > 0 && (
                  <span style={{ padding: '5px 10px', borderRadius: '8px', background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.3)', color: '#eab308', fontWeight: 700, fontSize: '12px' }}>
                    🧱 {kec.rkbRecommended} RKB
                  </span>
                )}
              </div>
              <div style={{ textAlign: 'right', fontFamily: 'monospace', fontSize: '12px', flexShrink: 0 }}>
                <span style={{ color: '#6b7280', display: 'block', fontSize: '10px' }}>Estimasi Biaya</span>
                <strong style={{ color: '#f9fafb' }}>Rp {(((kec.usbRecommended || 0) * 12) + ((kec.rkbRecommended || 0) * 0.35)).toFixed(2)} M</strong>
              </div>
            </div>
          ))}
          {simulatedData.filter(k => (k.unserved || 0) > 0).length === 0 && (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
              Tidak ada pembangunan fisik baru yang mendesak pada skenario simulasi ini.
            </div>
          )}
        </div>
        <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
          <h3 style={{ fontWeight: 600, fontSize: '14px', marginBottom: '14px' }}>Asumsi Parameter Pembiayaan</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '12px' }}>
            {[
              { tag: 'USB', label: 'Unit Sekolah Baru (SD)', desc: 'Rp 12.0 Milyar/unit — Lahan + Konstruksi 3 Lantai + Fasilitas Lengkap.' },
              { tag: 'RKB', label: 'Ruang Kelas Baru', desc: 'Rp 350 Juta/lokal — Penambahan tingkat vertikal gedung yang sudah ada.' },
            ].map(item => (
              <div key={item.tag} style={{ display: 'flex', gap: '12px' }}>
                <span style={{ padding: '4px 8px', borderRadius: '6px', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--accent-gold)', fontFamily: 'monospace', fontWeight: 700, fontSize: '11px', flexShrink: 0, alignSelf: 'flex-start' }}>{item.tag}</span>
                <div>
                  <strong style={{ display: 'block', color: '#f3f4f6', marginBottom: '3px' }}>{item.label}</strong>
                  <p style={{ color: '#6b7280', lineHeight: '1.5', fontSize: '11px' }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '11px', color: '#6b7280', lineHeight: '1.5' }}>
            💡 Rekomendasi dihitung otomatis untuk wilayah yang memiliki gap minus pada neraca kapasitas terproyeksi. Sesuaikan slider untuk eksplorasi skenario anggaran.
          </div>
        </div>
      </div>
    </div>
  );
}
