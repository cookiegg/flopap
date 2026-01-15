import React, { useEffect, useState } from 'react';
import { Paper } from '../../../types';
import { Loader2 } from 'lucide-react';
import { Capacitor } from '@capacitor/core';
import { getInfographic } from '../../../services/backendService';

interface PaperInfographicRealProps {
  paper: Paper;
  isDark: boolean;
  onHtmlLoaded?: (html: string) => void;
  onSwipe?: (direction: 'left' | 'right') => void;
}

const PaperInfographicReal: React.FC<PaperInfographicRealProps> = ({ paper, isDark, onHtmlLoaded, onSwipe }) => {
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [iframeHeight, setIframeHeight] = useState<number | string>('100vh');

  useEffect(() => {
    const fetchInfographic = async () => {
      console.log(`[Infographic] Fetching for paper:`, {
        id: paper.id,
        title: paper.title.substring(0, 40)
      });

      try {
        let html = await getInfographic(paper.id);

        if (!html) {
          throw new Error('信息图尚未生成');
        }

        const titleMatch = html.match(/<title>(.*?)<\/title>/);
        console.log(`[Infographic] Loaded ${html.length} chars, HTML title: ${titleMatch ? titleMatch[1] : 'not found'}`);

        // Inject script for resize and swipe detection
        const script = `
          <script>
            // 1. Resize Logic with ResizeObserver (Stable & Efficient)
            const ro = new ResizeObserver(entries => {
              for (let entry of entries) {
                // Add buffer to ensure no cut-off
                const height = document.documentElement.scrollHeight + 40;
                window.parent.postMessage({ type: 'infographic-resize', height: height }, '*');
              }
            });

            // Observe the body and html
            ro.observe(document.body);
            ro.observe(document.documentElement);
            
            // Backup: report on load and periodically checks (but less frequent)
            window.addEventListener('load', () => { 
                // Initial check
                setTimeout(() => {
                   const height = document.documentElement.scrollHeight + 40;
                   window.parent.postMessage({ type: 'infographic-resize', height: height }, '*');
                }, 100);
            });

            // 2. Swipe Logic (Stricter)
            var touchStartX = 0;
            var touchStartY = 0;

            window.addEventListener('touchstart', (e) => {
              touchStartX = e.touches[0].clientX;
              touchStartY = e.touches[0].clientY;
            }, { passive: true });

            window.addEventListener('touchend', (e) => {
              const touchEndX = e.changedTouches[0].clientX;
              const touchEndY = e.changedTouches[0].clientY;
              
              const deltaX = touchEndX - touchStartX;
              const deltaY = touchEndY - touchStartY;
              
              const MIN_DISTANCE = 80;
              const RATIO = 3.0; 
              
              if (Math.abs(deltaX) > MIN_DISTANCE && Math.abs(deltaX) > Math.abs(deltaY) * RATIO) {
                if (deltaX > 0) {
                  window.parent.postMessage({ type: 'infographic-swipe', direction: 'right' }, '*');
                } else {
                  window.parent.postMessage({ type: 'infographic-swipe', direction: 'left' }, '*');
                }
              }
            }, { passive: true });
          </script>
          <style>
            /* Reset and Responsive Config */
            html, body {
                margin: 0;
                padding: 0;
                width: 100vw; /* Force viewport width */
                max-width: 100vw;
                overflow-x: hidden !important; /* Prevent horizontal scroll */
                overflow-y: hidden !important; /* Hide internal scrollbars (height driven by parent) */
                height: auto !important;
                min-height: auto !important;
                box-sizing: border-box;
            }
            body {
                padding: 10px;
                padding-bottom: 20px; /* Reduced specific bottom padding */
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            
            /* Responsive Content */
            img, svg, video, canvas {
                max-width: 100% !important;
                height: auto !important;
                display: block;
                margin: 0 auto;
            }
            
            /* Ensure container divs don't overflow */
            div, p, h1, h2, h3, h4, section, main {
                max-width: 100%;
                box-sizing: border-box;
                overflow-wrap: break-word; /* Prevent text overflow */
            }
          </style>
        `;

        if (html.includes('</body>')) {
          html = html.replace('</body>', script + '</body>');
        } else {
          html += script;
        }

        setHtmlContent(html);
        if (onHtmlLoaded) {
          onHtmlLoaded(html);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '未知错误');
      } finally {
        setLoading(false);
      }
    };

    fetchInfographic();
  }, [paper.id]); // Only refetch when paper changes, not on callback changes

  // Handle messages from iframe
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (!event.data) return;

      if (event.data.type === 'infographic-resize') {
        const h = event.data.height;
        // Only update if difference is significant (> 10px) to prevent flicker loops
        if (typeof h === 'number' && h > 0) {
          setIframeHeight(prev => {
            const prevNum = typeof prev === 'number' ? prev : 0;
            if (Math.abs(prevNum - h) > 10) {
              return h;
            }
            return prev;
          });
        }
      } else if (event.data.type === 'infographic-swipe') {
        if (onSwipe) {
          onSwipe(event.data.direction);
        }
      }
    };

    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [onSwipe]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500 mb-4" />
        <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>
          加载信息图...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <div className={`text-center p-6 rounded-lg ${isDark ? 'bg-slate-800 border border-slate-700' : 'bg-slate-100 border border-slate-300'}`}>
          <p className="text-red-500 mb-2">⚠️ {error}</p>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            该论文的信息图正在生成中
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full relative" style={{ minHeight: '100px' }}>
      <iframe
        srcDoc={htmlContent}
        sandbox="allow-same-origin allow-scripts"
        title={`${paper.title} Infographic`}
        className="w-full border-none block"
        scrolling="no"
        style={{
          height: typeof iframeHeight === 'number' ? `${iframeHeight}px` : iframeHeight,
          backgroundColor: '#0f172a'
        }}
      />
    </div>
  );
};

export default PaperInfographicReal;
