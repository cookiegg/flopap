import React from 'react';
import { AppLanguage, AppTheme } from '../../types';
import { UI_STRINGS } from '../../constants';
import { Smartphone, Monitor, ChevronRight, Zap, Globe, MousePointer2, X } from 'lucide-react';
import logo from '../../assets/logo.png';
import screenshot1 from '../../assets/app-screenshot-1.png';
import screenshot2 from '../../assets/app-screenshot-2.png';
import qrWebsite from '../../assets/qr-website.png';
import { motion, AnimatePresence } from 'framer-motion';
import LoginScreen from './LoginScreen';
import MockAppUI from './LandingPage/MockAppUI';

// ... Mock Data for CSS UI ...
const MOCK_PAPER = {
    title: "Attention Is All You Need",
    authors: "Ashish Vaswani, Noam Shazeer...",
    abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
};

interface LandingPageProps {
    onStart: () => void;
    language: AppLanguage;
    onToggleLanguage: () => void;
    theme: AppTheme;
    showLoginModal?: boolean;
    onCloseLogin?: () => void;
    onLoginSuccess?: (token: string, user: any) => void;
}

const LandingPage: React.FC<LandingPageProps> = ({
    onStart,
    language,
    onToggleLanguage,
    theme,
    showLoginModal,
    onCloseLogin,
    onLoginSuccess
}) => {
    const ui = UI_STRINGS[language];
    const isDark = theme === 'dark';

    const features = [
        {
            icon: Zap,
            title: ui.feature1Title,
            desc: ui.feature1Desc,
            color: 'text-yellow-400',
            bg: 'bg-yellow-400/10'
        },
        {
            icon: Globe,
            title: ui.feature2Title,
            desc: ui.feature2Desc,
            color: 'text-blue-400',
            bg: 'bg-blue-400/10'
        },
        {
            icon: MousePointer2,
            title: ui.feature3Title,
            desc: ui.feature3Desc,
            color: 'text-purple-400',
            bg: 'bg-purple-400/10'
        }
    ];

    return (
        <div className={`min-h-screen w-full flex flex-col relative overflow-x-hidden ${isDark ? 'bg-black text-white' : 'bg-gray-50 text-gray-900'}`}>

            {/* Background Elements */}
            <div className="absolute top-0 left-0 w-full h-[800px] overflow-hidden pointer-events-none">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[100%] bg-blue-600/20 blur-[120px] rounded-full mix-blend-screen" />
                <div className="absolute top-[10%] left-[40%] w-[40%] h-[80%] bg-purple-600/20 blur-[120px] rounded-full mix-blend-screen" />
                <div className="absolute -bottom-[20%] right-[10%] w-[40%] h-[80%] bg-pink-600/20 blur-[120px] rounded-full mix-blend-screen" />
            </div>

            {/* Navigation */}
            <nav className="w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center z-20 relative">
                <div className="flex items-center gap-3">
                    <img src={logo} alt="FloPap" className="w-10 h-10 rounded-lg shadow-lg" />
                    <span className="font-bold text-xl tracking-tight hidden sm:block">FloPap</span>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={onToggleLanguage}
                        className={`px-4 py-2 rounded-full text-sm font-bold border transition-all hover:scale-105 active:scale-95 ${isDark ? 'border-white/10 hover:bg-white/10 bg-black/20 backdrop-blur-md' : 'border-gray-200 hover:bg-gray-100 bg-white/50'
                            }`}
                    >
                        {language === 'en' ? 'CN' : 'EN'}
                    </button>
                    {!showLoginModal && (
                        <button
                            onClick={onStart}
                            className="bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full font-bold transition-all hover:scale-105 active:scale-95 shadow-lg shadow-white/10"
                        >
                            {ui.loginRegister}
                        </button>
                    )}
                </div>
            </nav>

            {/* Hero Section */}
            <main className="flex-1 w-full max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-center gap-12 lg:gap-32 relative z-10 py-12 md:py-0">

                {/* Left Content */}
                <div className="flex-1 text-center md:text-left space-y-8 max-w-2xl relative">
                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[0.9] md:leading-[0.95]">
                        <span className="block text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-gray-400">
                            Research
                        </span>
                        <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 pb-4">
                            Reimagined.
                        </span>
                    </h1>

                    <p className={`text-xl md:text-2xl font-medium leading-relaxed max-w-lg mx-auto md:mx-0 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        {language === 'zh'
                            ? '像刷抖音一样刷论文。智能解读，一触即达。专为现代研究者打造的沉浸式阅读体验。'
                            : 'Swipe through the latest research like never before. AI-powered insights at your fingertips.'}
                    </p>

                    <div className="flex flex-col sm:flex-row items-center gap-6 pt-4 justify-center md:justify-start">
                        <button
                            onClick={onStart}
                            className="group relative w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl font-bold text-lg flex items-center justify-center gap-3 shadow-2xl shadow-blue-500/30 transition-all hover:scale-105 active:scale-95 overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 pointer-events-none" />
                            <Monitor size={20} />
                            <span>{ui.startReading}</span>
                            <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                        </button>

                        <div className="flex items-center gap-2 px-6 py-4 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm cursor-pointer hover:bg-white/10 transition-colors group relative">
                            <Smartphone size={20} className="text-gray-400 group-hover:text-white transition-colors" />
                            <div className="text-left">
                                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Download App</div>
                            </div>

                            {/* QR Popover */}
                            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-4 w-40 p-3 rounded-2xl bg-white shadow-2xl opacity-0 group-hover:opacity-100 transition-all pointer-events-none group-hover:pointer-events-auto transform translate-y-2 group-hover:translate-y-0 z-50">
                                <img src={qrWebsite} alt="Download QR" className="w-full h-auto rounded-lg" />
                                <p className="text-center text-[10px] font-bold text-gray-900 mt-2">Scan to Install</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Content - Interactive App Showcase */}
                <div className="flex-1 relative w-full max-w-[500px] md:max-w-none perspective-1000 hidden md:flex items-center justify-center -mr-12 lg:-mr-24">
                    {/* Decorative Background */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/10 to-purple-500/10 rounded-full blur-[80px] animate-pulse-slow pointer-events-none" />

                    <div className="relative w-full h-[640px] flex items-center justify-center transform scale-90 lg:scale-100">

                        {/* Main Phone Frame */}
                        <motion.div
                            initial={{ opacity: 0, y: 50, rotateY: -10 }}
                            animate={{ opacity: 1, y: 0, rotateY: -5, rotateZ: 0 }}
                            transition={{ delay: 0.2, duration: 0.8 }}
                            className="absolute z-20 w-[300px] h-[620px] bg-gray-900 rounded-[2.5rem] border-[8px] border-gray-800 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col"
                        >
                            {/* Phone Notch */}
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 h-6 w-32 bg-black rounded-b-xl z-30" />

                            {/* Interactive Mock UI */}
                            <div className="flex-1 bg-black w-full h-full pt-6"> {/* pt-6 to clear notch */}
                                <MockAppUI />
                            </div>

                            {/* Interactive Hint Overlay */}
                            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 bg-black/60 backdrop-blur-md rounded-full border border-white/10 flex items-center gap-2 animate-bounce-slow shadow-xl z-40 pointer-events-none">
                                <Zap size={12} className="text-yellow-400" />
                                <span className="text-[10px] font-bold text-white tracking-wide">Live Demo • Auto Cycles</span>
                            </div>
                        </motion.div>

                        {/* Decorative Elements behind */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 0.5, scale: 1 }}
                            transition={{ delay: 0.4 }}
                            className="absolute -z-10 w-[280px] h-[580px] bg-gradient-to-br from-blue-600 to-purple-600 rounded-[2rem] blur-2xl opacity-40 transform translate-x-4 translate-y-4"
                        />

                    </div>
                </div>
            </main>

            {/* Features Stripe */}
            <section className="w-full border-t border-white/5 bg-black/40 backdrop-blur-md z-10 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
                <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-3 gap-8">
                    {features.map((f, i) => (
                        <div key={i} className="group p-6 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all duration-300">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${f.bg} ${f.color} group-hover:scale-110 transition-transform`}>
                                <f.icon size={24} />
                            </div>
                            <h3 className="text-lg font-bold mb-2 text-white">{f.title}</h3>
                            <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* FOOTER */}
            <footer className="w-full py-8 border-t border-white/5 bg-black text-center relative z-10">
                <p className="text-xs text-gray-500">© 2024 FloPap. Research made accessible.</p>
            </footer>

            {/* LOGIN MODAL OVERLAY */}
            <AnimatePresence>
                {showLoginModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-black/60 backdrop-blur-md"
                            onClick={onCloseLogin}
                        />

                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="relative w-full max-w-sm z-10 bg-gray-900 rounded-3xl border border-white/10 shadow-2xl shadow-black/50 overflow-hidden"
                        >
                            {/* Close Button */}
                            <button
                                onClick={onCloseLogin}
                                className="absolute top-4 right-4 p-2 rounded-full text-gray-400 hover:text-white hover:bg-white/10 transition-colors z-20"
                            >
                                <X size={20} />
                            </button>

                            {/* Login Screen in Web Variant */}
                            <div className="p-8">
                                <LoginScreen
                                    onSuccess={(token, user) => onLoginSuccess && onLoginSuccess(token, user)}
                                    isDark={true} // Force dark mode for modal
                                    language={language}
                                    variant="web"
                                />
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

        </div>
    );
};

export default LandingPage;
