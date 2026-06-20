import React from 'react';
import { 
  Map, 
  TrendingUp, 
  Layers, 
  FileText,
  Server
} from 'lucide-react';

interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  dbConnected: boolean;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab, dbConnected }) => {
  const menuItems = [
    { id: 'map', label: 'Peta Audit Spasial', icon: Map },
    { id: 'forecast', label: 'Proyeksi & Gap', icon: TrendingUp },
    { id: 'cluster', label: 'K-Means Prioritas', icon: Layers },
    { id: 'rekomendasi', label: 'Rekomendasi USB/RKB', icon: FileText },
  ];

  return (
    <aside className="sidebar">
      <div className="logo-container">
        <Server className="nav-icon" style={{ color: 'var(--accent-gold)' }} />
        <h1 className="logo-text">
          Audit<span className="logo-highlight">Capacity</span>
        </h1>
      </div>
      
      <nav style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between' }}>
        <ul className="nav-menu">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.id}>
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                  style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
                >
                  <Icon className="nav-icon" />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
        
        <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: dbConnected ? 'var(--color-aman)' : 'var(--color-kritis)',
            display: 'inline-block',
            boxShadow: dbConnected ? '0 0 8px var(--color-aman)' : '0 0 8px var(--color-kritis)'
          }}></span>
          <span>PostgreSQL: {dbConnected ? 'CONNECTED' : 'DISCONNECTED'}</span>
        </div>
      </nav>
    </aside>
  );
};
