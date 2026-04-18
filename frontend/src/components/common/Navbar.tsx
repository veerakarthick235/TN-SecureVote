import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';

export default function Navbar() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const { isAuthenticated, voter, logout } = useAppStore();

  const toggleLang = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  const isActive = (path: string) => location.pathname === path ? 'active' : '';

  return (
    <nav className="navbar" id="main-navbar">
      <Link to="/" className="navbar-brand">
        <div className="logo-icon">🗳️</div>
        <span>{t('app.title')}</span>
      </Link>

      <ul className="navbar-links">
        <li><Link to="/" className={isActive('/')}>{t('nav.home')}</Link></li>
        {isAuthenticated && (
          <li><Link to="/vote" className={isActive('/vote')}>{t('nav.vote')}</Link></li>
        )}
        <li><Link to="/verify" className={isActive('/verify')}>{t('nav.verify')}</Link></li>
        <li><Link to="/results" className={isActive('/results')}>{t('nav.results')}</Link></li>
        <li><Link to="/admin" className={isActive('/admin')}>{t('nav.admin')}</Link></li>
      </ul>

      <div className="navbar-actions">
        <div className="lang-toggle">
          <button
            className={i18n.language === 'en' ? 'active' : ''}
            onClick={() => toggleLang('en')}
          >
            EN
          </button>
          <button
            className={i18n.language === 'ta' ? 'active' : ''}
            onClick={() => toggleLang('ta')}
          >
            தமிழ்
          </button>
        </div>

        {isAuthenticated ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {voter?.name}
              {voter?.is_demo && <span className="badge badge-upcoming" style={{ marginLeft: '0.5rem' }}>Demo</span>}
            </span>
            <button className="btn btn-ghost" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={logout}>
              {t('nav.logout')}
            </button>
          </div>
        ) : (
          <Link to="/login" className="btn btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
            {t('nav.login')}
          </Link>
        )}
      </div>
    </nav>
  );
}
