import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { electionAPI, voteAPI, demoAPI } from '../services/api';
import { useAppStore } from '../store/useAppStore';

interface Candidate {
  id: string;
  name: string;
  name_ta: string | null;
  party: string;
  party_ta: string | null;
  symbol: string;
  candidate_index: number;
}

interface Election {
  id: string;
  title: string;
  title_ta: string | null;
  candidates: Candidate[];
  total_votes_cast: number;
}

export default function VotePage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated, selectedCandidate, setSelectedCandidate, setVoteReceipt, hasVoted, setCurrentElection } = useAppStore();

  const [election, setElection] = useState<Election | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const isTamil = i18n.language === 'ta';

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    loadElection();
  }, [isAuthenticated]);

  const loadElection = async () => {
    try {
      // Ensure demo election exists
      await demoAPI.setup();
      const res = await electionAPI.getActive();
      if (res.data && res.data.length > 0) {
        setElection(res.data[0]);
        setCurrentElection(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load election:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitVote = async () => {
    if (selectedCandidate === null || !election) return;
    setSubmitting(true);
    setError('');

    try {
      // Use the demo quick-vote endpoint for simplified flow
      const res = await demoAPI.quickVote(selectedCandidate);

      if (res.data.error) {
        setError(res.data.error);
        setSubmitting(false);
        return;
      }

      setVoteReceipt({
        receipt_hash: res.data.receipt_hash,
        block_index: res.data.block_index,
        block_hash: res.data.block_hash,
        timestamp: new Date().toISOString(),
        election_id: election.id,
      });

      navigate('/receipt');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Vote submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="page" id="vote-page">
        <div className="page-header"><h1>{t('vote.title')}</h1></div>
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="loading-shimmer" style={{ width: '200px', height: '30px', margin: '0 auto 1rem' }} />
          <div className="loading-shimmer" style={{ width: '300px', height: '20px', margin: '0 auto' }} />
        </div>
      </div>
    );
  }

  if (hasVoted) {
    return (
      <div className="page" id="vote-page">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
          <h2>{t('vote.alreadyVoted')}</h2>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1.5rem' }}>
            <button className="btn btn-primary" onClick={() => navigate('/receipt')}>
              🧾 View Receipt
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/verify')}>
              🔍 {t('nav.verify')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!election) {
    return (
      <div className="page" id="vote-page">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <h2>{t('vote.noElection')}</h2>
        </div>
      </div>
    );
  }

  const selectedCandidateData = election.candidates.find(c => c.candidate_index === selectedCandidate);

  return (
    <div className="page" id="vote-page">
      <div className="page-header">
        <h1>{t('vote.title')}</h1>
        <p>{isTamil && election.title_ta ? election.title_ta : election.title}</p>
        <p style={{ fontSize: '0.9rem' }}>{t('vote.subtitle')}</p>
      </div>

      {error && (
        <div className="card" style={{
          background: 'rgba(244, 63, 94, 0.1)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          marginBottom: '1rem',
          color: 'var(--accent-rose)',
          fontSize: '0.9rem',
          maxWidth: '600px',
          margin: '0 auto 1rem',
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Ballot Cards */}
      <div className="ballot-grid">
        {election.candidates.map((candidate) => (
          <div
            key={candidate.id}
            className={`ballot-card ${selectedCandidate === candidate.candidate_index ? 'selected' : ''}`}
            onClick={() => setSelectedCandidate(candidate.candidate_index)}
            id={`ballot-card-${candidate.candidate_index}`}
          >
            <div className="symbol">{candidate.symbol}</div>
            <div className="candidate-name">
              {isTamil && candidate.name_ta ? candidate.name_ta : candidate.name}
            </div>
            <div className="party-name">
              {isTamil && candidate.party_ta ? candidate.party_ta : candidate.party}
            </div>
            <div className="select-indicator">
              {selectedCandidate === candidate.candidate_index ? t('vote.selected') : t('vote.selectCandidate')}
            </div>
          </div>
        ))}
      </div>

      {/* Submit Button */}
      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button
          className="btn btn-primary btn-lg"
          disabled={selectedCandidate === null || submitting}
          onClick={() => setShowConfirm(true)}
          id="submit-vote-btn"
        >
          {submitting ? t('vote.submitting') : `🔐 ${t('vote.encryptSubmit')}`}
        </button>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Your vote will be encrypted with ElGamal encryption before submission
        </p>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && selectedCandidateData && (
        <div className="modal-overlay" onClick={() => setShowConfirm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{t('vote.confirmTitle')}</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{t('vote.confirmMsg')}</p>

            <div className="card" style={{
              textAlign: 'center',
              background: 'var(--bg-hover)',
              marginBottom: '1rem',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{selectedCandidateData.symbol}</div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                {isTamil && selectedCandidateData.name_ta ? selectedCandidateData.name_ta : selectedCandidateData.name}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {isTamil && selectedCandidateData.party_ta ? selectedCandidateData.party_ta : selectedCandidateData.party}
              </div>
            </div>

            <div style={{
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              padding: '0.75rem',
              background: 'rgba(99, 102, 241, 0.05)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1rem',
            }}>
              🔐 Your vote will be:
              <br />• Encrypted with ElGamal encryption
              <br />• Signed with a blind signature token
              <br />• Committed to the blockchain
              <br />• Verified with a Zero-Knowledge Proof
            </div>

            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => setShowConfirm(false)}>
                {t('common.cancel')}
              </button>
              <button className="btn btn-primary" onClick={() => { setShowConfirm(false); handleSubmitVote(); }}
                disabled={submitting}>
                {submitting ? t('vote.submitting') : t('common.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
