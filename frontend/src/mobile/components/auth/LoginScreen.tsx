import React, { useEffect, useState } from 'react';
import { Capacitor } from '@capacitor/core';
import logo from '../../../assets/logo.png';
import { sendSmsCode, loginWithSms } from '../../../services/backendService';
import { Smartphone, Mail } from 'lucide-react';
import { AppLanguage } from '../../../types';
import { UI_STRINGS } from '../../../constants';
// PrivacyPolicyModal removed for standalone edition

// 类型定义
interface GoogleUser {
  authentication: {
    idToken: string;
    accessToken: string;
  };
  email: string;
  familyName: string;
  givenName: string;
  id: string;
  name: string;
}

interface LoginScreenProps {
  onSuccess: (token: string, user: any) => void;
  isDark: boolean;
  language?: AppLanguage;
  variant?: 'mobile' | 'web'; // New prop
}

type AuthMethod = 'google' | 'phone';

const LoginScreen: React.FC<LoginScreenProps> = ({ onSuccess, isDark, language = 'zh', variant = 'mobile' }) => {
  const [authMethod, setAuthMethod] = useState<AuthMethod>('phone');
  const [loading, setLoading] = useState(false);

  // UI Strings
  const ui = UI_STRINGS[language];

  // Google Auth State
  const [googleAuth, setGoogleAuth] = useState<any>(null);

  // Phone Auth State
  const [phoneNumber, setPhoneNumber] = useState('');
  const [code, setCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [phoneError, setPhoneError] = useState('');

  // Privacy Policy State
  const [agreedToPrivacy, setAgreedToPrivacy] = useState(false);
  const [isPrivacyModalOpen, setIsPrivacyModalOpen] = useState(false);
  const [shakeAgreement, setShakeAgreement] = useState(false);

  // Helper to validate agreement
  const validateAgreement = () => {
    if (!agreedToPrivacy) {
      setShakeAgreement(true);
      setTimeout(() => setShakeAgreement(false), 500);
      setPhoneError('请先阅读并同意隐私政策');
      return false;
    }
    return true;
  };

  // Google Auth Init
  useEffect(() => {
    const initGoogle = async () => {
      try {
        if (Capacitor.isNativePlatform()) {
          // Dynamic import to avoid SSR/web issues if any
          const { GoogleAuth } = await import('@southdevs/capacitor-google-auth');

          // NEW: Initialize for v6+
          await GoogleAuth.initialize({
            clientId: '418591331458-h2iee0rqu2f35iim5itvqkk5liug0p88.apps.googleusercontent.com',
            scopes: ['profile', 'email'],
            grantOfflineAccess: true,
          });

          setGoogleAuth(GoogleAuth);
        }
      } catch (e: any) {
        console.error('[GoogleAuth] ❌ Initialization failed:', e);
      }
    };
    initGoogle();

    // Timer for SMS countdown
    if (countdown > 0) {
      const timer = setInterval(() => setCountdown(prev => prev - 1), 1000);
      return () => clearInterval(timer);
    }
  }, [countdown]);

  // handleGoogleLogin
  const handleGoogleLogin = async () => {
    if (!validateAgreement()) return; // Check Agreement

    setLoading(true);
    setPhoneError('');

    try {
      if (Capacitor.isNativePlatform() && googleAuth) {
        // 原生登录 - 应用内弹窗
        const result: GoogleUser = await googleAuth.signIn();

        // 发送到后端验证
        const { getApiBaseUrl } = await import('../../../services/backendService');
        const baseUrl = getApiBaseUrl(); // Already includes /api or proxy path
        const callbackUrl = `${baseUrl}/v1/auth/callback`; // Fixed: Added /v1/

        const requestBody = {
          provider: 'google',
          code: result.authentication.idToken, // 使用idToken作为验证码
        };

        const response = await fetch(callbackUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });

        const data = await response.json();

        if (response.ok) {
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          onSuccess(data.access_token, data.user);
        } else {
          const errorMsg = 'Login failed: ' + (data.detail || 'Unknown error');
          setPhoneError(errorMsg);
        }
      } else {
        // Web端 - OAuth跳转
        const redirectUri = window.location.origin + '/auth/callback';
        const clientId = '418591331458-h2iee0rqu2f35iim5itvqkk5liug0p88.apps.googleusercontent.com';

        const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
          `client_id=${clientId}&` +
          `redirect_uri=${encodeURIComponent(redirectUri)}&` +
          `response_type=code&` +
          `scope=openid email profile&` +
          `state=google`;

        window.location.href = authUrl;
      }
    } catch (error: any) {
      console.error('[GoogleLogin] ❌ 登录过程中发生错误:', error);

      if (error.error === 'popup_closed_by_user') {
        // 用户取消登录
      } else {
        setPhoneError(ui.loginFailed || '登录失败，请重试');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    if (!validateAgreement()) return; // Check Agreement

    if (!phoneNumber) return;
    if (phoneNumber.length < 11) {
      setPhoneError(ui.validPhoneReq);
      return;
    }

    setLoading(true);
    setPhoneError('');

    const result = await sendSmsCode(phoneNumber);

    setLoading(false);
    if (result.success) {
      setCountdown(60);
      setPhoneError('');
    } else {
      setPhoneError(result.message);
    }
  };

  const handlePhoneLogin = async () => {
    if (!validateAgreement()) return; // Check Agreement

    if (!phoneNumber || !code) {
      setPhoneError(ui.enterBothReq);
      return;
    }

    setLoading(true);
    setPhoneError('');

    try {
      const result = await loginWithSms(phoneNumber, code);

      if (result.success) {
        const { access_token, user } = result.data;
        localStorage.setItem('token', access_token);
        // Safely store user if exists
        if (user) {
          localStorage.setItem('user', JSON.stringify(user));
        }

        // This might throw if userStore.login fails, so we wrap in try/catch
        onSuccess(access_token, user);
      } else {
        setPhoneError(result.message);
        setLoading(false);
      }
    } catch (error: any) {
      console.error('Phone login error:', error);
      setPhoneError('登录处理失败，请重试');
      setLoading(false);
    }
  };

  const isWeb = variant === 'web';

  const containerClass = isWeb
    ? `flex flex-col items-center w-full max-w-sm mx-auto`
    : `flex flex-col items-center justify-between min-h-[100dvh] w-full px-8 pt-20 pb-12 transition-colors duration-500 ${isDark ? 'bg-black text-white' : 'bg-gray-50 text-gray-900'}`;

  return (
    <div className={containerClass}>
      {/* PrivacyPolicyModal removed for standalone edition */}

      {/* 1. Logo & Branding Area */}
      <div className={`flex flex-col items-center flex-1 justify-center ${isWeb ? 'mb-8' : '-mt-20'}`}>
        <div className="relative mb-8 group">
          <div className={`absolute inset-0 rounded-3xl blur-2xl opacity-40 transition-opacity duration-1000 ${isDark ? 'bg-blue-600' : 'bg-blue-400'} group-hover:opacity-60`}></div>
          <img
            src={logo}
            alt="FloPap Logo"
            className={`relative rounded-3xl shadow-2xl z-10 transform transition-transform duration-500 hover:scale-105 hover:rotate-3 ${isWeb ? 'w-20 h-20' : 'w-32 h-32'}`}
          />
        </div>

        <h1 className={`${isWeb ? 'text-3xl' : 'text-4xl'} font-black tracking-tight mb-2 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500`}>
          FloPap
        </h1>
        <h2 className={`${isWeb ? 'text-xl' : 'text-2xl'} font-bold tracking-wide ${isDark ? (isWeb ? 'text-white' : 'text-white/90') : 'text-gray-800'}`}>
          刷论文
        </h2>

        {!isWeb && (
          <p className={`mt-4 text-center max-w-xs font-medium leading-relaxed whitespace-pre-line ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            {ui.loginSlogan}
          </p>
        )}
      </div>

      {/* 2. Authentication Tabs */}
      <div className="w-full max-w-sm mb-6">
        <div className={`flex p-1 rounded-xl ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`}>
          <button
            onClick={() => setAuthMethod('phone')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-bold transition-all ${authMethod === 'phone'
              ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
              : (isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900')
              }`}
          >
            <Smartphone size={16} />
            {ui.loginPhone}
          </button>
          <button
            onClick={() => setAuthMethod('google')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-bold transition-all ${authMethod === 'google'
              ? (isDark ? 'bg-gray-700 text-white shadow' : 'bg-white text-gray-900 shadow')
              : (isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900')
              }`}
          >
            <Mail size={16} />
            {ui.loginGoogleBtn}
          </button>
        </div>
      </div>

      {/* 3. Authentication Forms */}
      <div className="w-full max-w-sm space-y-6 animate-fade-in-up min-h-[160px]">

        {/* PRIVACY CHECKBOX (NEW) */}
        <div
          className={`flex items-start gap-3 px-2 transition-transform ${shakeAgreement ? 'animate-shake text-red-500' : ''}`}
          onClick={() => setAgreedToPrivacy(!agreedToPrivacy)}
        >
          <div className={`mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition-colors cursor-pointer ${agreedToPrivacy
            ? 'bg-blue-600 border-blue-600'
            : isDark ? 'border-gray-600 bg-gray-800' : 'border-gray-300 bg-white'
            }`}>
            {agreedToPrivacy && <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
          </div>
          <div className={`text-xs select-none cursor-pointer leading-tight pt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            我已阅读并同意
            <span
              className="text-blue-500 font-bold hover:underline mx-1"
              onClick={(e) => { e.stopPropagation(); setIsPrivacyModalOpen(true); }}
            >
              《隐私政策与用户协议》
            </span>
            包括API使用和内容共享条款。
          </div>
        </div>

        {authMethod === 'google' ? (
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className={`w-full relative overflow-hidden group flex items-center justify-center gap-3 px-6 py-4 rounded-2xl font-bold text-lg transition-all duration-300 transform active:scale-95 shadow-xl ${isDark
              ? 'bg-white text-gray-900 hover:bg-gray-100'
              : 'bg-black text-white hover:bg-gray-900'
              }`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                <span>{ui.connecting}</span>
              </div>
            ) : (
              <>
                <svg className="w-6 h-6" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                <span>{ui.loginGoogle}</span>
              </>
            )}
          </button>
        ) : (
          <div className="space-y-4">
            {/* Phone Input */}
            <div className={`flex items-center px-4 py-3 rounded-xl border ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'}`}>
              <span className={`mr-3 font-bold ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>+86</span>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder={ui.enterPhone}
                className="flex-1 bg-transparent outline-none font-medium placeholder-gray-400"
              />
            </div>

            {/* Code Input */}
            <div className="flex gap-3">
              <div className={`flex-1 px-4 py-3 rounded-xl border ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'}`}>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder={ui.enterCode}
                  className="w-full bg-transparent outline-none font-medium placeholder-gray-400 text-center tracking-widest"
                />
              </div>
              <button
                onClick={handleSendCode}
                disabled={countdown > 0 || loading || !phoneNumber}
                className={`px-4 rounded-xl font-bold whitespace-nowrap transition-colors ${countdown > 0
                  ? (isDark ? 'bg-gray-800 text-gray-500' : 'bg-gray-200 text-gray-500')
                  : 'bg-blue-600 text-white hover:bg-blue-500'
                  }`}
              >
                {countdown > 0 ? `${countdown}s` : ui.sendCode}
              </button>
            </div>

            {/* Login Button */}
            <button
              onClick={handlePhoneLogin}
              disabled={loading || !phoneNumber || !code}
              className={`w-full py-4 rounded-2xl font-bold text-lg shadow-lg transition-all active:scale-95 ${loading || !phoneNumber || !code
                ? (isDark ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-gray-200 text-gray-400 cursor-not-allowed')
                : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:opacity-90'
                }`}
            >
              {loading ? ui.verifying : ui.loginRegister}
            </button>
          </div>
        )}

        {/* Error Message */}
        {phoneError && (
          <div className="text-red-500 text-sm font-medium text-center animate-pulse">
            {phoneError}
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginScreen;
