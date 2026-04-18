import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { QRCodeSVG } from 'qrcode.react';
import { useState } from 'react';

export default function ReceiptPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { voteReceipt } = useAppStore();
  const [copied, setCopied] = useState('');

  if (!voteReceipt) {
    return (
      <div className="page" id="receipt-page">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧾</div>
          <h2>No receipt found</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>You need to cast a vote first.</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/vote')}>
            Go to Voting
          </button>
        </div>
      </div>
    );
  }

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopied(field);
    setTimeout(() => setCopied(''), 2000);
  };

  return (
    <div className="page" id="receipt-page">
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <div className="receipt-card fade-in">
          <div className="success-icon">✓</div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            {t('vote.success')}
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            {t('vote.saveReceipt')}
          </p>

          {/* QR Code */}
          <div className="qr-container">
            <QRCodeSVG value={voteReceipt.receipt_hash} size={150} />
          </div>

          {/* Receipt Details */}
          <div style={{ textAlign: 'left', marginTop: '1.5rem' }}>
            <div className="receipt-detail">
              <span className="label">{t('vote.receiptHash')}</span>
              <span className="value" style={{ cursor: 'pointer' }}
                onClick={() => copyToClipboard(voteReceipt.receipt_hash, 'hash')}
                title="Click to copy">
                {voteReceipt.receipt_hash.slice(0, 20)}...
                {copied === 'hash' ? ' ✓' : ' 📋'}
              </span>
            </div>
            <div className="receipt-detail">
              <span className="label">{t('vote.blockIndex')}</span>
              <span className="value">#{voteReceipt.block_index}</span>
            </div>
            <div className="receipt-detail">
              <span className="label">{t('vote.blockHash')}</span>
              <span className="value" style={{ cursor: 'pointer' }}
                onClick={() => copyToClipboard(voteReceipt.block_hash, 'block')}
                title="Click to copy">
                {voteReceipt.block_hash.slice(0, 20)}...
                {copied === 'block' ? ' ✓' : ' 📋'}
              </span>
            </div>
            <div className="receipt-detail">
              <span className="label">{t('vote.timestamp')}</span>
              <span className="value">{new Date(voteReceipt.timestamp).toLocaleString()}</span>
            </div>
          </div>

          {/* Security info */}
          <div style={{
            marginTop: '1.5rem',
            padding: '1rem',
            background: 'rgba(99, 102, 241, 0.08)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
          }}>
            <strong style={{ color: 'var(--text-primary)' }}>🔐 Security Note:</strong>
            <br />This receipt proves your vote was recorded on the blockchain.
            It does NOT reveal who you voted for — your ballot remains encrypted.
            <br />Use this hash to verify your vote anytime.
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={() => {
            copyToClipboard(voteReceipt.receipt_hash, 'hash_action');
            setTimeout(() => navigate('/verify'), 500);
          }}>
            🔍 {t('nav.verify')}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/results')}>
            📊 {t('nav.results')}
          </button>
        </div>
      </div>
    </div>
  );
}
