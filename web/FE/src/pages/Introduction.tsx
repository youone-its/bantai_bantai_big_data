import { useEffect, useState } from 'react';

export default function Introduction() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      opacity: mounted ? 1 : 0,
      transform: mounted ? 'translateY(0)' : 'translateY(-20px)',
      transition: 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)'
    }}>
      
      {/* Styles for custom scrollbars or animations if needed */}
      <style>{`
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
      `}</style>

      {/* Hero Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(12,20,38,0.85) 0%, rgba(7,11,20,0.95) 100%)',
        border: '1px solid rgba(223,177,91,0.15)',
        borderRadius: '16px',
        padding: '36px',
        position: 'relative',
        overflow: 'hidden',
        backdropFilter: 'blur(20px)',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}>
        {/* Abstract Glow Elements */}
        <div style={{
          position: 'absolute', top: '-120px', right: '-120px',
          width: '320px', height: '320px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(223,177,91,0.1) 0%, transparent 70%)',
          pointerEvents: 'none'
        }}></div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
          <span style={{
            background: 'rgba(223,177,91,0.08)',
            border: '1px solid rgba(223,177,91,0.25)',
            color: 'var(--accent-gold)',
            padding: '6px 14px',
            borderRadius: '30px',
            fontSize: '11px',
            fontWeight: 800,
            letterSpacing: '1px',
            textTransform: 'uppercase'
          }}>
            🏛️ DECISION SUPPORT SYSTEM
          </span>
          <span style={{ fontSize: '12px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
            <span style={{
              width: '6px', height: '6px', borderRadius: '50%', background: '#10b981',
              display: 'inline-block', animation: 'pulseGlow 2s infinite'
            }}></span>
            Koneksi database sinkron & aktif
          </span>
        </div>

        <h1 style={{
          fontSize: '28px',
          fontWeight: 900,
          lineHeight: '1.3',
          color: '#f9fafb',
          maxWidth: '850px',
          marginBottom: '18px',
          background: 'linear-gradient(to right, #ffffff 50%, #dfb15b 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.5px'
        }}>
          Sistem Audit Ketimpangan Kapasitas Pendidikan Dasar Kota Surabaya Berbasis Arsitektur Data Lakehouse dan Predictive Analytics
        </h1>

        <p style={{
          fontSize: '14.5px',
          color: 'var(--text-secondary)',
          lineHeight: '1.7',
          maxWidth: '850px',
          marginBottom: '24px'
        }}>
          Platform analitik eksekutif yang dirancang khusus untuk memetakan, memprediksi, dan memberikan solusi terhadap problematika daya tampung sekolah dasar pada proses PPDB zonasi tahunan di Kota Surabaya. Melalui integrasi data demografi dan kapasitas sekolah, sistem ini memproyeksikan kebutuhan bangku sekolah jangka panjang hingga tahun 2030 guna memandu kebijakan strategis pemerataan pendidikan.
        </p>

        <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '10px',
            padding: '10px 18px',
            fontSize: '12.5px',
            color: '#d1d5db',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{ color: 'var(--accent-gold)' }}>📈</span>
            <strong>Modul Prediksi</strong>: Proyeksi Jangka Panjang
          </div>
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '10px',
            padding: '10px 18px',
            fontSize: '12.5px',
            color: '#d1d5db',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{ color: 'var(--accent-gold)' }}>⚙️</span>
            <strong>Pipeline Data</strong>: Integrasi Otomatis
          </div>
        </div>
      </div>

      {/* Core Highlights Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        
        {/* Core Analysis Modules */}
        <div style={{
          background: 'rgba(12,20,38,0.65)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: '14px',
          padding: '24px',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
        }}>
          <h2 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--accent-gold)', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📊 Tekno-Analitik Unggulan
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ fontSize: '20px', background: 'rgba(223,177,91,0.06)', border: '1px solid rgba(223,177,91,0.15)', borderRadius: '10px', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>📈</div>
              <div>
                <h3 style={{ fontSize: '13.5px', fontWeight: 700, color: '#f3f4f6', marginBottom: '3px' }}>Cohort Survival Forecasting</h3>
                <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  Memproyeksikan demand kelompok umur sekolah dasar (7–12 tahun) per kecamatan untuk jangka waktu 3–5 tahun mendatang berdasarkan pergeseran struktur usia penduduk dan laju kelulusan kelas.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ fontSize: '20px', background: 'rgba(223,177,91,0.06)', border: '1px solid rgba(223,177,91,0.15)', borderRadius: '10px', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>📊</div>
              <div>
                <h3 style={{ fontSize: '13.5px', fontWeight: 700, color: '#f3f4f6', marginBottom: '3px' }}>School Capacity Gap Index (SCGI)</h3>
                <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  Formulasi indeks komposit dinamis berskala 0-100 untuk mengukur tingkat kerentanan kapasitas sekolah dengan mengintegrasikan defisit daya tampung, rasio utilisasi pagu, dan akselerasi pertumbuhan siswa.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ fontSize: '20px', background: 'rgba(223,177,91,0.06)', border: '1px solid rgba(223,177,91,0.15)', borderRadius: '10px', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>🤖</div>
              <div>
                <h3 style={{ fontSize: '13.5px', fontWeight: 700, color: '#f3f4f6', marginBottom: '3px' }}>Clustering Prioritas Kebijakan</h3>
                <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  Pengelompokkan otomatis kecamatan berdasarkan tingkat urgensi intervensi menggunakan Machine Learning (K-Means) untuk memetakan prioritas bantuan pembangunan sekolah secara objektif.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ fontSize: '20px', background: 'rgba(223,177,91,0.06)', border: '1px solid rgba(223,177,91,0.15)', borderRadius: '10px', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>🗺️</div>
              <div>
                <h3 style={{ fontSize: '13.5px', fontWeight: 700, color: '#f3f4f6', marginBottom: '3px' }}>Spasial Routing Aksesibilitas</h3>
                <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  Integrasi modul perutean jalan raya menggunakan OSRM API untuk menghitung estimasi jarak dan waktu tempuh berkendara secara *real-time* dari daerah berstatus defisit menuju sekolah terdekat yang memadai.
                </p>
              </div>
            </div>

          </div>
        </div>

        {/* Pipeline & Integration Technology Stack */}
        <div style={{
          background: 'rgba(12,20,38,0.65)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: '14px',
          padding: '24px',
          backdropFilter: 'blur(20px)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
        }}>
          <h2 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--accent-gold)', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            ⚙️ Aliran Data & Integrasi Sistem
          </h2>

          <div style={{
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.04)',
            borderRadius: '12px',
            padding: '18px',
            marginBottom: '16px',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            gap: '14px'
          }}>
            <div style={{ display: 'flex', gap: '8px', fontSize: '11px', alignItems: 'center' }}>
              <span style={{ padding: '3px 8px', background: 'rgba(239,110,68,0.1)', color: '#ef6e44', borderRadius: '4px', fontWeight: 700, fontSize: '10px', letterSpacing: '0.5px' }}>RAW INGESTION</span>
              <span style={{ color: '#4b5563' }}>➔</span>
              <span style={{ padding: '3px 8px', background: 'rgba(156,163,175,0.1)', color: '#9ca3af', borderRadius: '4px', fontWeight: 700, fontSize: '10px', letterSpacing: '0.5px' }}>CLEANED & DEDUP</span>
              <span style={{ color: '#4b5563' }}>➔</span>
              <span style={{ padding: '3px 8px', background: 'rgba(223,177,91,0.1)', color: 'var(--accent-gold)', borderRadius: '4px', fontWeight: 700, fontSize: '10px', letterSpacing: '0.5px' }}>ANALYTICS MART</span>
            </div>
            
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Pemrosesan terbagi ke dalam arsitektur penyimpanan terdistribusi berkeamanan tinggi. Data mentah dibersihkan, disatukan berdasarkan kunci geospasial kecamatan, dan diformulasikan ke dalam tabel analitik. Hasil kalkulasi berat disinkronisasi ke database relasional berkinerja tinggi sebagai serving layer demi menyajikan kecepatan respons optimal saat visualisasi dashboard.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '6px' }}>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ display: 'block', fontSize: '9px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '2px' }}>Ingestion</span>
                <span style={{ fontSize: '11.5px', color: '#f3f4f6', fontWeight: 600 }}>Message Broker</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ display: 'block', fontSize: '9px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '2px' }}>Data Warehouse</span>
                <span style={{ fontSize: '11.5px', color: '#f3f4f6', fontWeight: 600 }}>Distributed Lakehouse</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ display: 'block', fontSize: '9px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '2px' }}>Database Serving</span>
                <span style={{ fontSize: '11.5px', color: '#f3f4f6', fontWeight: 600 }}>PostgreSQL DB</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ display: 'block', fontSize: '9px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '2px' }}>API Gateway</span>
                <span style={{ fontSize: '11.5px', color: '#f3f4f6', fontWeight: 600 }}>FastAPI REST Service</span>
              </div>
            </div>
          </div>

          <div style={{ background: 'rgba(223,177,91,0.04)', border: '1px solid rgba(223,177,91,0.15)', borderRadius: '10px', padding: '12px', fontSize: '11px', color: '#dfb15b', lineHeight: '1.5' }}>
            💡 <strong>Pemisahan Komputasi</strong>: Beban komputasi analitik terpisah sepenuhnya dengan database serving, menjamin performa antarmuka pengguna yang sangat responsif saat me-render visualisasi grafis dan peta spasial.
          </div>
        </div>

      </div>

      {/* Sektor Data Terpadu Section */}
      <div style={{
        background: 'rgba(12,20,38,0.65)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: '14px',
        padding: '24px',
        backdropFilter: 'blur(20px)',
        boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
      }}>
        <h2 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--accent-gold)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🌐 Penyelarasan Sektoral Sumber Data
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          {[
            { title: 'Struktur Demografi Usia', desc: 'Rincian jumlah anak usia pra-sekolah dan sekolah dasar tingkat kelurahan.' },
            { title: 'Standardisasi Akreditasi', desc: 'Nilai dan tingkat kelayakan kualitas penunjang pendidikan sekolah dasar.' },
            { title: 'Daya Tampung Sekolah', desc: 'Kuota daya tampung (pagu) dibanding dengan jumlah murid yang terdaftar.' },
            { title: 'Rasio Sumber Daya Guru', desc: 'Keseimbangan jumlah guru dan siswa di masing-masing wilayah kecamatan.' }
          ].map((d, idx) => (
            <div key={idx} style={{
              background: 'rgba(0,0,0,0.25)',
              border: '1px solid rgba(255,255,255,0.03)',
              borderRadius: '10px',
              padding: '16px',
              transition: 'border-color 0.3s ease',
            }}>
              <strong style={{ display: 'block', fontSize: '13px', color: '#f3f4f6', marginBottom: '6px' }}>{d.title}</strong>
              <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: '1.5', display: 'block' }}>{d.desc}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
