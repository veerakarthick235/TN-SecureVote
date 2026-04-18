import { useTranslation } from 'react-i18next';

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="footer" id="app-footer">
      <div className="footer-badges">
        <div className="footer-badge">
          <span>🔐</span>
          <span>{t('common.secure')}</span>
        </div>
        <div className="footer-badge">
          <span>🕵️</span>
          <span>{t('common.anonymous')}</span>
        </div>
        <div className="footer-badge">
          <span>⛓️</span>
          <span>{t('common.blockchain')}</span>
        </div>
      </div>
      <p>{t('footer.tagline')}</p>
      <p style={{ marginTop: '0.3rem', fontSize: '0.75rem' }}>{t('footer.disclaimer')}</p>
    </footer>
  );
}
