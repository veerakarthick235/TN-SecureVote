import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { auditAPI, demoAPI } from '../services/api';

interface CandidateResult {
  candidate_id: string;
  candidate_name: string;
  candidate_name_ta?: string;
  party: string;
  party_ta?: string;
  symbol: string;
  vote_count: number;
  percentage: number;
}

export default function ResultsPage() {
  const { t, i18n } = useTranslation();
  const isTamil = i18n.language === 'ta';

  const [results, setResults] = useState<CandidateResult[]>([]);
  const [totalVotes, setTotalVotes] = useState(0);
  const [chainVerified, setChainVerified] = useState(false);
  const [electionTitle, setElectionTitle] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    try {
      const statusRes = await demoAPI.status();
      if (statusRes.data.demo_active) {
        const res = await auditAPI.getResults(statusRes.data.election_id);
        setResults(res.data.results || []);
        setTotalVotes(res.data.total_votes || 0);
        setChainVerified(res.data.chain_verified || false);
        setElectionTitle(isTamil ? (res.data.election_title_ta || res.data.election_title) : res.data.election_title);
      }
    } catch (err) {
      console.error('Failed to load results:', err);
    } finally {
      setLoading(false);
    }
  };

  const maxVotes = Math.max(...results.map(r => r.vote_count), 1);

  return (
    <div className="page" id="results-page">
      <div className="page-header">
        <h1>{t('results.title')}</h1>
        {electionTitle && <p>{electionTitle}</p>}
        <p>{t('results.subtitle')}</p>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid" style={{ maxWidth: '600px', margin: '0 auto 2rem' }}>
        <div className="stat-card">
          <div className="stat-value">{totalVotes}</div>
          <div className="stat-label">{t('results.totalVotes')}</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{
            background: chainVerified ? 'var(--gradient-success)' : 'var(--gradient-danger)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            {chainVerified ? '✓' : '✗'}
          </div>
          <div className="stat-label">
            {chainVerified ? t('results.chainVerified') : t('results.chainInvalid')}
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="loading-shimmer" style={{ height: '80px', marginBottom: '1rem' }} />
          ))}
        </div>
      ) : results.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
          <h3>{t('results.noResults')}</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>Cast some demo votes to see results here!</p>
        </div>
      ) : (
        <div className="results-grid" style={{ maxWidth: '700px', margin: '0 auto' }}>
          {results.map((candidate, idx) => (
            <div key={candidate.candidate_id} className={`result-bar ${idx === 0 ? 'leader' : ''}`}>
              <div className="bar-fill" style={{ width: `${(candidate.vote_count / maxVotes) * 100}%` }} />
              <div className="bar-content">
                <div className="candidate-info">
                  <div className="symbol">{candidate.symbol}</div>
                  <div>
                    <div style={{ fontWeight: 700 }}>
                      {isTamil && candidate.candidate_name_ta ? candidate.candidate_name_ta : candidate.candidate_name}
                      {idx === 0 && candidate.vote_count > 0 && (
                        <span className="badge badge-active" style={{ marginLeft: '0.5rem' }}>
                          {t('results.winner')}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {isTamil && candidate.party_ta ? candidate.party_ta : candidate.party}
                    </div>
                  </div>
                </div>
                <div className="vote-count">
                  <div className="count">{candidate.vote_count}</div>
                  <div className="pct">{candidate.percentage}%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Refresh button */}
      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button className="btn btn-ghost" onClick={loadResults}>
          🔄 Refresh Results
        </button>
      </div>
    </div>
  );
}
