import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.flopap.app',
  appName: 'FloPap',
  webDir: 'dist',
  server: {
    cleartext: true,
    // 开发环境用 http，生产环境用 https
    androidScheme: process.env.NODE_ENV === 'production' ? 'https' : 'http'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: "#0f172a",
      androidSplashResourceName: "splash",
      androidScaleType: "CENTER_CROP",
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },
    GoogleAuth: {
      scopes: ['profile', 'email'],
      serverClientId: '418591331458-h2iee0rqu2f35iim5itvqkk5liug0p88.apps.googleusercontent.com',
      forceCodeForRefreshToken: true
    }
  },
};

export default config;
