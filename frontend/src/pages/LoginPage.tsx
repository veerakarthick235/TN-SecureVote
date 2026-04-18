import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { authAPI, demoAPI } from '../services/api';
import { useAppStore } from '../store/useAppStore';

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setVoter, setLoading, isLoading } = useAppStore();

  const [step, setStep] = useState(1);
  const [voterId, setVoterId] = useState('');
  const [demoOtp, setDemoOtp] = useState('');

  // Form fields
  const [aadhaar, setAadhaar] = useState('');
  const [name, setName] = useState('');
  const [district, setDistrict] = useState('Chennai');
  const [constituency, setConstituency] = useState('Mylapore');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await authAPI.register({
        aadhaar_number: aadhaar,
        name,
        district,
        constituency,
        phone,
      });
      setVoterId(res.data.voter_id);
      // Extract OTP from message for demo purposes
      const otpMatch = res.data.message.match(/Demo OTP: (\d{6})/);
      if (otpMatch) setDemoOtp(otpMatch[1]);
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    setError('');
    setLoading(true);
    try {
      await authAPI.verifyOTP({ voter_id: voterId, otp });
      setStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBiometric = async () => {
    setError('');
    setLoading(true);
    try {
      const fingerprintHash = Array.from(crypto.getRandomValues(new Uint8Array(32)))
        .map(b => b.toString(16).padStart(2, '0')).join('');
      const res = await authAPI.biometric({
        voter_id: voterId,
        fingerprint_hash: fingerprintHash,
      });
      setVoter(
        {
          voter_id: res.data.voter_id,
          name: res.data.name,
          is_demo: res.data.is_demo,
        },
        res.data.access_token
      );
      // Setup demo election
      await demoAPI.setup();
      navigate('/vote');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Biometric verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await authAPI.demoLogin('Demo Voter');
      setVoter(
        {
          voter_id: res.data.voter_id,
          name: res.data.name,
          is_demo: true,
        },
        res.data.access_token
      );
      await demoAPI.setup();
      navigate('/vote');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { num: 1, label: t('auth.step1') },
    { num: 2, label: t('auth.step2') },
    { num: 3, label: t('auth.step3') },
    { num: 4, label: t('auth.step4') },
  ];

  return (
    <div className="page" id="login-page">
      <div className="page-header">
        <h1>{t('auth.title')}</h1>
      </div>

      {/* Stepper */}
      <div className="stepper">
        {steps.map((s, i) => (
          <div key={s.num} style={{ display: 'flex', alignItems: 'center' }}>
            <div className={`stepper-step ${step === s.num ? 'active' : step > s.num ? 'done' : ''}`}>
              <div className="stepper-circle">
                {step > s.num ? '✓' : s.num}
              </div>
              <span className="stepper-label">{s.label}</span>
            </div>
            {i < steps.length - 1 && (
              <div className={`stepper-line ${step > s.num ? 'done' : ''}`} />
            )}
          </div>
        ))}
      </div>

      <div style={{ maxWidth: '500px', margin: '0 auto' }}>
        {error && (
          <div className="card" style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            marginBottom: '1rem',
            color: 'var(--accent-rose)',
            fontSize: '0.9rem'
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Step 1: Registration */}
        {step === 1 && (
          <div className="card fade-in">
            <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem' }}>{t('auth.step1')}</h3>
            <div className="input-group" style={{ marginBottom: '0.75rem' }}>
              <label>{t('auth.aadhaar')}</label>
              <input className="input" type="text" maxLength={12} placeholder={t('auth.aadhaarPlaceholder')}
                value={aadhaar} onChange={e => setAadhaar(e.target.value.replace(/\D/g, ''))} />
            </div>
            <div className="input-group" style={{ marginBottom: '0.75rem' }}>
              <label>{t('auth.name')}</label>
              <input className="input" type="text" placeholder="Enter your name"
                value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <div className="input-group">
                <label>{t('auth.district')}</label>
                <input className="input" type="text" value={district} onChange={e => setDistrict(e.target.value)} />
              </div>
              <div className="input-group">
                <label>{t('auth.constituency')}</label>
                <input className="input" type="text" value={constituency} onChange={e => setConstituency(e.target.value)} />
              </div>
            </div>
            <div className="input-group" style={{ marginBottom: '1.25rem' }}>
              <label>{t('auth.phone')}</label>
              <input className="input" type="text" maxLength={10} placeholder="10-digit mobile number"
                value={phone} onChange={e => setPhone(e.target.value.replace(/\D/g, ''))} />
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleRegister}
              disabled={isLoading || aadhaar.length !== 12 || !name || phone.length !== 10}>
              {isLoading ? t('common.loading') : t('auth.register')}
            </button>

            <div style={{ textAlign: 'center', margin: '1.5rem 0', color: 'var(--text-muted)' }}>
              ── {t('auth.orSeparator')} ──
            </div>

            <button className="btn btn-success" style={{ width: '100%' }} onClick={handleDemoLogin} disabled={isLoading}>
              🚀 {t('auth.demoLogin')}
            </button>
            <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              {t('auth.demoDesc')}
            </p>
          </div>
        )}

        {/* Step 2: OTP */}
        {step === 2 && (
          <div className="card fade-in">
            <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem' }}>{t('auth.step2')}</h3>
            {demoOtp && (
              <div className="card" style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                marginBottom: '1rem',
                fontSize: '0.85rem',
              }}>
                🔑 Demo OTP: <strong>{demoOtp}</strong>
              </div>
            )}
            <div className="input-group" style={{ marginBottom: '1.25rem' }}>
              <label>{t('auth.otp')}</label>
              <input className="input" type="text" maxLength={6} placeholder={t('auth.otpPlaceholder')}
                value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
                style={{ fontSize: '1.5rem', textAlign: 'center', letterSpacing: '0.5rem' }} />
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleVerifyOtp}
              disabled={isLoading || otp.length !== 6}>
              {isLoading ? t('common.loading') : t('auth.verifyOtp')}
            </button>
          </div>
        )}

        {/* Step 3: Biometric */}
        {step === 3 && (
          <div className="card fade-in" style={{ textAlign: 'center' }}>
            <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem' }}>{t('auth.biometric')}</h3>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>👆</div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              Place your finger on the scanner to verify your identity.
              <br /><span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>(Simulated — click to proceed)</span>
            </p>
            <button className="btn btn-primary btn-lg" style={{ width: '100%' }} onClick={handleBiometric} disabled={isLoading}>
              {isLoading ? t('common.loading') : t('auth.biometricBtn')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
