import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, GeoJSON, Polyline, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

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

const getMarkerIcon = (color: string, label: string) => L.divIcon({
  html: `<div style="background:${color};width:28px;height:28px;border-radius:50%;border:2px solid white;display:flex;align-items:center;justify-content:center;color:#070b14;font-size:9px;font-weight:bold;box-shadow:0 0 12px ${color}88;">${label}</div>`,
  className: '',
  iconSize: [28, 28],
  iconAnchor: [14, 14]
});

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

interface OverviewProps {
  simulatedData: KecData[];
  selectedKec: KecData | null;
  setSelectedKec: (k: KecData | null) => void;
  handleKecClick: (k: KecData) => void;
  forecastYears: number;
  routeLine: [number, number][] | null;
  setRouteLine: (line: [number, number][] | null) => void;
  routeTarget: KecData | null;
  setRouteTarget: (target: KecData | null) => void;
  routeMeta: { distance: number; duration: number } | null;
  setRouteMeta: (meta: { distance: number; duration: number } | null) => void;
}

export default function Overview({
  simulatedData,
  selectedKec,
  setSelectedKec,
  handleKecClick,
  forecastYears,
  routeLine,
  setRouteLine,
  routeTarget,
  setRouteTarget,
  routeMeta,
  setRouteMeta,
}: OverviewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeWilayah, setActiveWilayah] = useState('Semua');
  const [mapLayer, setMapLayer] = useState<'kmeans' | 'scgi' | 'deficit'>('kmeans');
  const [geoJsonData, setGeoJsonData] = useState<any>(null);
  const [hoveredKec, setHoveredKec] = useState<KecData | null>(null);
  const geoJsonRef = useRef<L.GeoJSON | null>(null);

  // Load GeoJSON once
  useEffect(() => {
    fetch('/surabaya_kecamatan_voronoi.geojson')
      .then(r => r.json())
      .then(d => setGeoJsonData(d))
      .catch(console.error);
  }, []);

  // Filter geoJsonData features to strictly contain only the selected region
  const filteredGeoJson = useMemo(() => {
    if (!geoJsonData) return null;
    if (activeWilayah === 'Semua') return geoJsonData;
    return {
      ...geoJsonData,
      features: geoJsonData.features.filter((f: any) => {
        const name = normName(f.properties?.kecamatan_norm || '');
        const wilayah = WILAYAH_MAP[name] || '';
        return wilayah === activeWilayah;
      })
    };
  }, [geoJsonData, activeWilayah]);

  const filteredData = useMemo(() =>
    simulatedData.filter(kec => {
      const matchSearch = kec.kecamatan_norm.toLowerCase().includes(searchQuery.toLowerCase());
      const matchRegion = activeWilayah === 'Semua' || WILAYAH_MAP[normName(kec.kecamatan_norm)] === activeWilayah;
      return matchSearch && matchRegion;
    }),
    [simulatedData, searchQuery, activeWilayah]);

  const getKecStyle = useCallback((feature: any) => {
    const name = normName(feature.properties?.kecamatan_norm || '');
    const match = simulatedData.find(k => normName(k.kecamatan_norm) === name);
    const cluster = match?.cluster || 'Aman';
    const scgi = match?.scgi || 0;
    const gap = match?.gapCapacity || 0;

    let fillColor = CLUSTER_COLORS[cluster]?.fill || '#10b981';
    let fillOpacity = 0.55;

    if (mapLayer === 'scgi') {
      // Heatmap SCGI: beautiful continuous smooth HSL gradient (Green to Yellow to Red)
      fillColor = `hsl(${(1 - scgi) * 120}, 75%, 45%)`;
      fillOpacity = 0.65;
    } else if (mapLayer === 'deficit') {
      // Defisit Kapasitas: stark contrast Blue (surplus) vs Red (shortage)
      if (gap < 0) {
        // Red scale based on deficit intensity
        const intensity = Math.min(Math.abs(gap) / 2500, 1);
        fillColor = `rgba(239, 68, 68, ${0.45 + intensity * 0.45})`;
      } else {
        // Blue scale based on surplus intensity
        const intensity = Math.min(gap / 2500, 1);
        fillColor = `rgba(59, 130, 246, ${0.35 + intensity * 0.45})`;
      }
      fillOpacity = 0.70;
    } else {
      // Klaster K-Means: high opacity cluster blocks
      fillOpacity = 0.65;
    }

    return {
      fillColor,
      weight: 1.5,
      opacity: 1,
      color: 'rgba(223,177,91,0.25)',
      fillOpacity,
    };
  }, [simulatedData, mapLayer]);

  const onEachKec = useCallback((feature: any, layer: L.Layer) => {
    const name = normName(feature.properties?.kecamatan_norm || '');
    const match = simulatedData.find(k => normName(k.kecamatan_norm) === name);

    layer.on({
      mouseover: (e) => {
        e.target.setStyle({ fillOpacity: 0.85, weight: 2.5, color: '#dfb15b' });
        if (match) setHoveredKec(match);
      },
      mouseout: (e) => {
        if (geoJsonRef.current) geoJsonRef.current.resetStyle(e.target);
        setHoveredKec(null);
      },
      click: () => {
        if (match) handleKecClick(match);
      }
    });
  }, [simulatedData, handleKecClick]);

  const deficitKecs = simulatedData.filter(k => (k.unserved || 0) > 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Map Layer Selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '14px', padding: '16px 20px', backdropFilter: 'blur(20px)' }}>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700 }}>🗺️ Peta GIS & Analisis Spasial Interaktif</h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '3px' }}>Kota Surabaya — Klik kecamatan untuk detail & routing OSRM ke kecamatan aman terdekat</p>
        </div>
        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)', gap: '2px' }}>
          {(['kmeans', 'scgi', 'deficit'] as const).map(l => (
            <button key={l} onClick={() => setMapLayer(l)}
              style={{ padding: '7px 14px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 700, fontFamily: 'Outfit, sans-serif', transition: 'all 0.2s ease',
                background: mapLayer === l ? 'linear-gradient(135deg, #dfb15b, #b8892e)' : 'transparent',
                color: mapLayer === l ? '#070b14' : 'var(--text-secondary)' }}
            >
              {l === 'kmeans' ? 'Klaster K-Means' : l === 'scgi' ? 'Heatmap SCGI' : 'Defisit Kapasitas'}
            </button>
          ))}
        </div>
      </div>

      {/* Wilayah filter tabs */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {['Semua','Pusat','Utara','Timur','Selatan','Barat'].map(w => (
          <button key={w} onClick={() => setActiveWilayah(w)}
            style={{
              padding: '6px 16px', borderRadius: '20px', border: `1px solid ${activeWilayah === w ? 'var(--accent-gold)' : 'rgba(255,255,255,0.08)'}`,
              background: activeWilayah === w ? 'rgba(223,177,91,0.15)' : 'transparent',
              color: activeWilayah === w ? 'var(--accent-gold)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '12px', fontWeight: activeWilayah === w ? 700 : 400,
              fontFamily: 'Outfit,sans-serif', transition: 'all 0.2s ease'
            }}
          >{w === 'Semua' ? '🌐 Semua Wilayah' : `Sby ${w}`}</button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px', height: '520px' }}>
        {/* Leaflet Map — perfectly centered vertically and horizontally around the Surabaya land area */}
        <div style={{ borderRadius: '14px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)', position: 'relative' }}>
          <MapContainer
            center={[-7.26, 112.715]} zoom={12}
            minZoom={11} maxZoom={14}
            maxBounds={[[-7.42, 112.53], [-7.10, 112.90]]}
            maxBoundsViscosity={1.0}
            scrollWheelZoom={false}
            doubleClickZoom={false}
            style={{ width: '100%', height: '100%', background: '#070b14' }}
            zoomControl={true}
          >
            <TileLayer attribution='&copy; CARTO' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
            {filteredGeoJson && (
              <GeoJSON
                ref={geoJsonRef}
                key={`${mapLayer}-${forecastYears}-${activeWilayah}`}
                data={filteredGeoJson}
                style={getKecStyle}
                onEachFeature={onEachKec}
              />
            )}
            {/* Deficit proportional markers */}
            {mapLayer === 'deficit' && deficitKecs.map(k => {
              const region = WILAYAH_MAP[normName(k.kecamatan_norm)];
              if (activeWilayah !== 'Semua' && region !== activeWilayah) return null;
              return (
                <Marker key={k.kecamatan_norm} position={[k.latitude, k.longitude]}
                  icon={L.divIcon({
                    html: `<div style="background:rgba(239,68,68,0.7);border-radius:50%;border:2px solid #ef4444;width:${Math.min(Math.max((k.unserved || 0) / 50, 12), 36)}px;height:${Math.min(Math.max((k.unserved || 0) / 50, 12), 36)}px;display:flex;align-items:center;justify-content:center;font-size:8px;color:white;font-weight:bold;animation:pulse 2s infinite;">-${k.unserved}</div>`,
                    className: '', iconSize: [36, 36], iconAnchor: [18, 18]
                  })}
                >
                  <Popup>{k.kecamatan_norm}: {k.unserved} tidak tertampung</Popup>
                </Marker>
              );
            })}
            {/* OSRM Route */}
            {routeLine && <Polyline positions={routeLine} color="#dfb15b" weight={4} opacity={0.85} dashArray="8,8" />}
            {selectedKec && (selectedKec.cluster === 'Sangat Kritis' || selectedKec.cluster === 'Kritis') && (
              <Marker position={[selectedKec.latitude, selectedKec.longitude]} icon={getMarkerIcon(CLUSTER_COLORS[selectedKec.cluster]?.fill || '#ef4444', 'KR')}>
                <Popup>{selectedKec.kecamatan_norm}</Popup>
              </Marker>
            )}
            {routeTarget && (
              <Marker position={[routeTarget.latitude, routeTarget.longitude]} icon={getMarkerIcon('#10b981', 'AM')}>
                <Popup>{routeTarget.kecamatan_norm} — Aman Terdekat</Popup>
              </Marker>
            )}
          </MapContainer>

          {/* Floating Hover Info Panel — placed in the top-right to avoid covering Leaflet zoom controls (+/-) */}
          {hoveredKec && (
            <div style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              zIndex: 1000,
              background: 'rgba(7,11,20,0.92)',
              border: '1px solid rgba(223,177,91,0.3)',
              borderRadius: '8px',
              padding: '10px 14px',
              pointerEvents: 'none',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#f3f4f6' }}>{hoveredKec.kecamatan_norm}</span>
              <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>Surabaya {WILAYAH_MAP[normName(hoveredKec.kecamatan_norm)]}</span>
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px', fontSize: '11px' }}>
                <span style={{ color: CLUSTER_COLORS[hoveredKec.cluster || 'Aman']?.text, fontWeight: 700 }}>{hoveredKec.cluster}</span>
                <span style={{ color: '#9ca3af', fontFamily: 'monospace' }}>SCGI: {(hoveredKec.scgi || 0).toFixed(3)}</span>
              </div>
            </div>
          )}

          {/* Legend */}
          <div style={{ position: 'absolute', bottom: '16px', left: '16px', zIndex: 1000, background: 'rgba(7,11,20,0.92)', border: '1px solid rgba(223,177,91,0.2)', borderRadius: '10px', padding: '12px', fontSize: '11px' }}>
            <div style={{ fontWeight: 700, color: 'var(--accent-gold)', marginBottom: '6px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Keterangan</div>
            {Object.entries(CLUSTER_COLORS).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '3px', background: v.fill, flexShrink: 0 }}></span>
                <span style={{ color: v.text }}>{k}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel: filter + list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
          {/* Search & filter */}
          <div style={{ background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px', backdropFilter: 'blur(20px)' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '8px' }}>Cari Kecamatan</span>
            <input type="text" placeholder="Cari nama kecamatan..." value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '7px 12px', fontSize: '12px', color: '#f3f4f6', fontFamily: 'Outfit, sans-serif', outline: 'none', boxSizing: 'border-box' }}
            />
          </div>

          {/* Kecamatan list */}
          <div style={{ flex: 1, background: 'rgba(12,20,38,0.65)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px', overflowY: 'auto', backdropFilter: 'blur(20px)' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
              Daftar Kecamatan ({filteredData.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {filteredData.sort((a, b) => (b.scgi || 0) - (a.scgi || 0)).map(kec => {
                const c = CLUSTER_COLORS[kec.cluster || 'Aman'];
                const isSelected = selectedKec?.kecamatan_norm === kec.kecamatan_norm;
                return (
                  <div key={kec.kecamatan_norm} onClick={() => handleKecClick(kec)}
                    style={{
                      padding: '9px 12px', borderRadius: '8px', cursor: 'pointer',
                      border: `1px solid ${isSelected ? 'var(--accent-gold)' : 'rgba(255,255,255,0.05)'}`,
                      background: isSelected ? 'rgba(223,177,91,0.08)' : 'transparent',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600 }}>{kec.kecamatan_norm}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>Sby {WILAYAH_MAP[normName(kec.kecamatan_norm)] || '–'}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '10px', fontFamily: 'monospace', color: '#9ca3af' }}>{(kec.scgi || 0).toFixed(2)}</span>
                      <span style={{ padding: '2px 8px', borderRadius: '5px', fontSize: '10px', fontWeight: 700, background: c?.bg, color: c?.text, border: `1px solid ${c?.border}` }}>{kec.cluster}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Selected detail */}
      {selectedKec && (
        <div style={{ background: 'rgba(12,20,38,0.65)', border: `2px solid ${CLUSTER_COLORS[selectedKec.cluster || 'Aman']?.border || 'rgba(255,255,255,0.06)'}`, borderRadius: '14px', padding: '20px', backdropFilter: 'blur(20px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
            <div>
              <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent-gold)', textTransform: 'uppercase', letterSpacing: '1px' }}>Kecamatan Terpilih</span>
              <h3 style={{ fontSize: '20px', fontWeight: 800, marginTop: '2px' }}>
                {selectedKec.kecamatan_norm}
                <span style={{ fontSize: '12px', fontWeight: 400, color: 'var(--text-secondary)', marginLeft: '8px' }}>Surabaya {WILAYAH_MAP[normName(selectedKec.kecamatan_norm)] || ''}</span>
              </h3>
            </div>
            <button onClick={() => { setSelectedKec(null); setRouteLine(null); setRouteTarget(null); setRouteMeta(null); }}
              style={{ padding: '6px 12px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '12px', fontFamily: 'Outfit, sans-serif' }}>
              Tutup ✕
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '13px' }}>
            {[
              { label: 'Kapasitas Saat Ini', val: `${selectedKec.kapasitas.toLocaleString('id-ID')} Siswa`, color: '#f9fafb' },
              { label: `Proyeksi ${forecastYears} Thn`, val: `${(selectedKec.projectedDemand || 0).toLocaleString('id-ID')} Calon Siswa`, color: 'var(--accent-gold)' },
              { label: 'Status Kapasitas', val: (selectedKec.gapCapacity || 0) < 0 ? `Defisit ${Math.abs(selectedKec.gapCapacity || 0)} Kursi` : `Surplus ${selectedKec.gapCapacity} Kursi`, color: (selectedKec.gapCapacity || 0) < 0 ? '#ef4444' : '#10b981' },
              { label: 'SCGI Score', val: `${(selectedKec.scgi || 0).toFixed(3)} — ${selectedKec.cluster}`, color: CLUSTER_COLORS[selectedKec.cluster || 'Aman']?.text },
            ].map((item, i) => (
              <div key={i} style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '10px', padding: '14px', border: '1px solid rgba(255,255,255,0.04)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>{item.label}</span>
                <strong style={{ color: item.color, fontFamily: 'monospace', fontSize: '14px' }}>{item.val}</strong>
              </div>
            ))}
          </div>
          {routeMeta && routeTarget && (
            <div style={{ marginTop: '12px', padding: '12px 16px', background: 'rgba(223,177,91,0.05)', border: '1px solid rgba(223,177,91,0.2)', borderRadius: '10px', fontSize: '12px', display: 'flex', gap: '24px', alignItems: 'center' }}>
              <span style={{ color: 'var(--accent-gold)', fontWeight: 700 }}>🛣️ Rute OSRM → {routeTarget.kecamatan_norm}</span>
              <span>Jarak: <strong>{routeMeta.distance.toFixed(2)} km</strong></span>
              <span>Waktu: <strong>{Math.round(routeMeta.duration)} menit</strong></span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
