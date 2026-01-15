/**
 * SplashScreen - 启动页面
 * 显示品牌 Logo 和标语，几秒后自动进入主应用
 */

import React, { useEffect, useState } from 'react';
import logo from '../../assets/logo.png';
import { motion } from 'framer-motion';

interface SplashScreenProps {
    onComplete: () => void;
    isDark?: boolean;
    duration?: number; // 显示时长（毫秒）
}

const SplashScreen: React.FC<SplashScreenProps> = ({
    onComplete,
    isDark = true,
    duration = 2500
}) => {
    const [fadeOut, setFadeOut] = useState(false);

    useEffect(() => {
        // 开始淡出动画
        const fadeTimer = setTimeout(() => {
            setFadeOut(true);
        }, duration - 500);

        // 完成后回调
        const completeTimer = setTimeout(() => {
            onComplete();
        }, duration);

        return () => {
            clearTimeout(fadeTimer);
            clearTimeout(completeTimer);
        };
    }, [duration, onComplete]);

    return (
        <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: fadeOut ? 0 : 1 }}
            transition={{ duration: 0.5 }}
            className={`fixed inset-0 flex flex-col items-center justify-center z-[100] transition-colors duration-500 ${isDark ? 'bg-black text-white' : 'bg-gray-50 text-gray-900'
                }`}
        >
            {/* Logo with Glow Effect */}
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="relative mb-8 group"
            >
                <div className={`absolute inset-0 rounded-3xl blur-2xl opacity-40 ${isDark ? 'bg-blue-600' : 'bg-blue-400'
                    }`} />
                <img
                    src={logo}
                    alt="FloPap Logo"
                    className="relative w-32 h-32 rounded-3xl shadow-2xl z-10"
                />
            </motion.div>

            {/* App Name */}
            <motion.h1
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="text-4xl font-black tracking-tight mb-2 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
            >
                FloPap
            </motion.h1>

            {/* Chinese Name */}
            <motion.h2
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className={`text-2xl font-bold tracking-wide ${isDark ? 'text-white/90' : 'text-gray-800'
                    }`}
            >
                刷论文
            </motion.h2>

            {/* Slogan */}
            <motion.p
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className={`mt-6 text-center max-w-xs font-medium leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'
                    }`}
            >
                AI驱动的论文浏览体验
                {'\n'}
                让前沿研究触手可及
            </motion.p>

            {/* Loading Indicator */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                className="mt-12 flex items-center gap-2"
            >
                <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                        <motion.div
                            key={i}
                            className={`w-2 h-2 rounded-full ${isDark ? 'bg-blue-500' : 'bg-blue-600'}`}
                            animate={{
                                scale: [1, 1.3, 1],
                                opacity: [0.5, 1, 0.5]
                            }}
                            transition={{
                                duration: 1,
                                repeat: Infinity,
                                delay: i * 0.2
                            }}
                        />
                    ))}
                </div>
            </motion.div>
        </motion.div>
    );
};

export default SplashScreen;
