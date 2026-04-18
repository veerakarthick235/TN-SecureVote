import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { electionAPI, auditAPI, demoAPI } from '../services/api';

export default function AdminPage() {
  const { t } = useTranslation();

  const [elections, setElections] = useState<any[]>([]);
  const [chainInfo, setChainInfo] = useState<any>(null);
  const [fraudAlerts, setFraudAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'elections' | 'blockchain' | 'fraud'>('elections');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [electionsRes, statusRes] = await Promise.all([
        electionAPI.getAll(),
        demoAPI.status(),
      ]);
      setElections(electionsRes.data || []);

      if (statusRes.data.demo_active) {
        const [chainRes, fraudRes] = await Promise.all([
          auditAPI.getBlockchain(statusRes.data.election_id),
          auditAPI.getFraudAlerts(statusRes.data.election_id),
        ]);
        setChainInfo(chainRes.data);
        setFraudAlerts(fraudRes.data.alerts || []);
      }
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const castDemoVotes = async () => {
    setLoading(true);
    try {
      // Cast 5 random votes
      for (let i = 0; i < 5; i++) {
        const candidateIndex = Math.floor(Math.random() * 4);
        await demoAPI.quickVote(candidateIndex);
      }
      await loadData();
    } catch (err) {
      console.error('Demo vote failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetDemo = async () => {
    setLoading(true);
    try {
      await demoAPI.reset();
      await demoAPI.setup();
      await loadData();
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const runFraudAnalysis = async () => {
    try {
      const statusRes = await demoAPI.status();
      if (statusRes.data.demo_active) {
        await auditAPI.runAnalysis(statusRes.data.election_id);
        await loadData();
      }
    } catch (err) {
      console.error('Fraud analysis failed:', err);
    }
  };

  return (
    <div className="page" id="admin-page">
      <div className="page-header">
        <h1>{t('admin.title')}</h1>
      </div>

      {/* Quick Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{elections.length}</div>
          <div className="stat-label">{t('admin.elections')}</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{elections.reduce((s, e) => s + (e.total_votes_cast || 0), 0)}</div>
          <div className="stat-label">{t('admin.totalVotes')}</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{chainInfo?.total_blocks || 0}</div>
          <div className="stat-label">{t('admin.chainBlocks')}</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{
            background: chainInfo?.is_valid ? 'var(--gradient-success)' : 'var(--gradient-danger)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            {chainInfo?.is_valid ? '✓' : '—'}
          </div>
          <div className="stat-label">{t('admin.chainValid')}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={castDemoVotes} disabled={loading}>
          🗳️ Cast 5 Demo Votes
        </button>
        <button className="btn btn-secondary" onClick={runFraudAnalysis}>
          🤖 Run AI Analysis
        </button>
        <button className="btn btn-danger" onClick={resetDemo} disabled={loading}>
          🔄 Reset Demo
        </button>
        <button className="btn btn-ghost" onClick={loadData}>
          ↻ Refresh
        </button>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '0.25rem',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '1.5rem',
      }}>
        {(['elections', 'blockchain', 'fraud'] as const).map(tab => (
          <button key={tab}
            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-ghost'}`}
            style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', fontSize: '0.85rem' }}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'elections' && `📋 ${t('admin.elections')}`}
            {tab === 'blockchain' && `⛓️ ${t('admin.blockchain')}`}
            {tab === 'fraud' && `🚨 ${t('admin.fraudAlerts')} (${fraudAlerts.length})`}
          </button>
        ))}
      </div>

      {/* Elections Tab */}
      {activeTab === 'elections' && (
        <div className="card fade-in">
          <table className="data-table">
            <thead>
              <tr>
                <th>Election</th>
                <th>{t('admin.status')}</th>
                <th>{t('admin.totalVotes')}</th>
                <th>{t('admin.eligible')}</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>
              {elections.map(e => (
                <tr key={e.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{e.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{e.region}</div>
                  </td>
                  <td>
                    <span className={`badge badge-${e.status === 'active' ? 'active' : e.status === 'upcoming' ? 'upcoming' : 'closed'}`}>
                      {e.status}
                    </span>
                  </td>
                  <td>{e.total_votes_cast}</td>
                  <td>{e.total_eligible_voters?.toLocaleString()}</td>
                  <td>{e.election_type}</td>
                </tr>
              ))}
              {elections.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No elections found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Blockchain Tab */}
      {activeTab === 'blockchain' && chainInfo && (
        <div className="fade-in">
          <div className="card" style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Chain Summary</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div className="receipt-detail">
                <span className="label">Total Blocks</span>
                <span className="value">{chainInfo.total_blocks}</span>
              </div>
              <div className="receipt-detail">
                <span className="label">Total Votes</span>
                <span className="value">{chainInfo.total_votes}</span>
              </div>
              <div className="receipt-detail">
                <span className="label">Chain Valid</span>
                <span className="value" style={{ color: chainInfo.is_valid ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {chainInfo.is_valid ? '✓ Valid' : '✗ Invalid'}
                </span>
              </div>
              <div className="receipt-detail">
                <span className="label">Last Block Hash</span>
                <span className="value">{chainInfo.last_block_hash?.slice(0, 16)}...</span>
              </div>
            </div>
          </div>

          {/* Block list */}
          <div className="card">
            <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Block Explorer</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Timestamp</th>
                  <th>Votes</th>
                  <th>Hash</th>
                  <th>Merkle Root</th>
                </tr>
              </thead>
              <tbody>
                {(chainInfo.blocks || []).map((block: any) => (
                  <tr key={block.index}>
                    <td style={{ fontWeight: 700 }}>{block.index}</td>
                    <td style={{ fontSize: '0.8rem' }}>
                      {new Date(block.timestamp).toLocaleTimeString()}
                    </td>
                    <td>{block.vote_count}</td>
                    <td style={{ fontFamily: "'Courier New', monospace", fontSize: '0.75rem' }}>
                      {block.block_hash?.slice(0, 16)}...
                    </td>
                    <td style={{ fontFamily: "'Courier New', monospace", fontSize: '0.75rem' }}>
                      {block.merkle_root?.slice(0, 16)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fraud Alerts Tab */}
      {activeTab === 'fraud' && (
        <div className="card fade-in">
          {fraudAlerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
              <p>No fraud alerts detected</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Description</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {fraudAlerts.map((alert: any) => (
                  <tr key={alert.alert_id}>
                    <td>{alert.alert_type}</td>
                    <td>
                      <span className={`badge badge-${alert.severity === 'high' ? 'high' : 'medium'}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem' }}>{alert.description}</td>
                    <td style={{ fontSize: '0.8rem' }}>
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
