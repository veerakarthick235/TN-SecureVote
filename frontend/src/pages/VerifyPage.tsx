import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { voteAPI } from '../services/api';
import { useAppStore } from '../store/useAppStore';

export default function VerifyPage() {
  const { t } = useTranslation();
  const { voteReceipt } = useAppStore();

  const [receiptHash, setReceiptHash] = useState(voteReceipt?.receipt_hash || '');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    if (!receiptHash.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await voteAPI.verify(receiptHash.trim());
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page" id="verify-page">
      <div className="page-header">
        <h1>{t('verify.title')}</h1>
        <p>{t('verify.subtitle')}</p>
      </div>

      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label>{t('verify.inputLabel')}</label>
            <input
              className="input"
              type="text"
              placeholder={t('verify.inputPlaceholder')}
              value={receiptHash}
              onChange={e => setReceiptHash(e.target.value)}
              style={{ fontFamily: "'Courier New', monospace", fontSize: '0.85rem' }}
              id="verify-receipt-input"
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: '100%' }}
            onClick={handleVerify}
            disabled={loading || !receiptHash.trim()}
            id="verify-btn"
          >
            {loading ? t('verify.verifying') : `🔍 ${t('verify.verifyBtn')}`}
          </button>
        </div>

        {error && (
          <div className="card fade-in" style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: 'var(--accent-rose)',
            textAlign: 'center',
          }}>
            ⚠️ {error}
          </div>
        )}

        {result && (
          <div className={`verify-result fade-in ${result.is_valid ? 'success' : 'failure'}`}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
              {result.is_valid ? '✅' : '❌'}
            </div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              {result.is_valid ? t('verify.verified') : t('verify.notFound')}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              {result.is_valid ? t('verify.verifiedMsg') : t('verify.notFoundMsg')}
            </p>

            {result.is_valid && (
              <div style={{ textAlign: 'left' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
                  {t('verify.blockDetails')}
                </h3>
                <div className="receipt-detail">
                  <span className="label">{t('vote.receiptHash')}</span>
                  <span className="value">{result.receipt_hash?.slice(0, 24)}...</span>
                </div>
                <div className="receipt-detail">
                  <span className="label">{t('vote.blockIndex')}</span>
                  <span className="value">#{result.block_index}</span>
                </div>
                <div className="receipt-detail">
                  <span className="label">{t('vote.blockHash')}</span>
                  <span className="value">{result.block_hash?.slice(0, 24)}...</span>
                </div>
                <div className="receipt-detail">
                  <span className="label">{t('vote.timestamp')}</span>
                  <span className="value">{result.timestamp ? new Date(result.timestamp).toLocaleString() : 'N/A'}</span>
                </div>

                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(16, 185, 129, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.85rem',
                }}>
                  <span>⛓️</span>
                  <span>{t('verify.chainIntegrity')}: <strong style={{ color: 'var(--accent-emerald)' }}>✓ Valid</strong></span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
