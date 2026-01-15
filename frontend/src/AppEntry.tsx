import React, { Suspense, useState, useEffect } from 'react';
import { Capacitor } from '@capacitor/core';

// Lazy load apps to split bundles
const MobileApp = React.lazy(() => import('./mobile/App'));
const WebApp = React.lazy(() => import('./web/App'));

export const AppEntry: React.FC = () => {
    const [isMobile, setIsMobile] = useState(true);

    useEffect(() => {
        const checkPlatform = () => {
            const isNative = Capacitor.isNativePlatform();
            const isSmallScreen = window.innerWidth <= 768;
            setIsMobile(isNative || isSmallScreen);
        };

        checkPlatform();
        window.addEventListener('resize', checkPlatform);
        return () => window.removeEventListener('resize', checkPlatform);
    }, []);

    return (
        <Suspense fallback={
            <div className="flex h-screen w-full items-center justify-center bg-gray-900 text-white">
                <div className="animate-pulse">Loading App...</div>
            </div>
        }>
            {isMobile ? <MobileApp /> : <WebApp />}
        </Suspense>
    );
};
