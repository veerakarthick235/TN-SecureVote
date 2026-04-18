import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';

export default function HomePage() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAppStore();

  return (
    <div className="page" id="home-page">
      <div className="hero">
        <h1>
          <span className="gradient-text">{t('app.title')}</span>
          <br />
          <span style={{ fontSize: '0.5em', fontWeight: 400, color: 'var(--text-secondary)' }}>
            {t('app.subtitle')}
          </span>
        </h1>
        <p>{t('app.tagline')}</p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          {isAuthenticated ? (
            <Link to="/vote" className="btn btn-primary btn-lg">
              🗳️ {t('nav.vote')}
            </Link>
          ) : (
            <Link to="/login" className="btn btn-primary btn-lg">
              🔐 {t('nav.login')}
            </Link>
          )}
          <Link to="/verify" className="btn btn-secondary btn-lg">
            🔍 {t('nav.verify')}
          </Link>
          <Link to="/results" className="btn btn-ghost btn-lg">
            📊 {t('nav.results')}
          </Link>
        </div>

        <div className="hero-features">
          <div className="hero-feature">
            <div className="icon">🔐</div>
            <div>
              <div className="text" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>RSA Blind Signatures</div>
              <div className="text">Anonymous vote tokens</div>
            </div>
          </div>
          <div className="hero-feature">
            <div className="icon">🔒</div>
            <div>
              <div className="text" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>ElGamal Encryption</div>
              <div className="text">Homomorphic tallying</div>
            </div>
          </div>
          <div className="hero-feature">
            <div className="icon">⛓️</div>
            <div>
              <div className="text" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Blockchain Storage</div>
              <div className="text">Tamper-proof records</div>
            </div>
          </div>
          <div className="hero-feature">
            <div className="icon">🧮</div>
            <div>
              <div className="text" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Zero-Knowledge Proofs</div>
              <div className="text">Vote validity without disclosure</div>
            </div>
          </div>
        </div>
      </div>

      {/* Architecture overview */}
      <div style={{ maxWidth: '800px', margin: '3rem auto', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
          How It Works
        </h2>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { icon: '👤', label: 'Authenticate' },
            { icon: '→', label: '' },
            { icon: '🎫', label: 'Get Blind Token' },
            { icon: '→', label: '' },
            { icon: '🗳️', label: 'Encrypt & Vote' },
            { icon: '→', label: '' },
            { icon: '⛓️', label: 'Blockchain Commit' },
            { icon: '→', label: '' },
            { icon: '🧾', label: 'Get Receipt' },
          ].map((step, i) => (
            <div key={i} style={{
              padding: step.label ? '1rem' : '0',
              background: step.label ? 'var(--bg-card)' : 'none',
              border: step.label ? '1px solid var(--border-color)' : 'none',
              borderRadius: 'var(--radius-md)',
              textAlign: 'center',
              minWidth: step.label ? '100px' : 'auto',
              color: step.label ? 'var(--text-primary)' : 'var(--text-muted)',
              fontSize: step.label ? '1rem' : '1.2rem',
            }}>
              <div style={{ fontSize: step.label ? '1.5rem' : '1rem', marginBottom: step.label ? '0.3rem' : '0' }}>{step.icon}</div>
              {step.label && <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{step.label}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
