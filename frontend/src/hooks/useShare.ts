import { useState } from 'react';
import html2canvas from 'html2canvas';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Share } from '@capacitor/share';
import { Capacitor } from '@capacitor/core';
import QRCode from 'qrcode';

export const useShare = () => {
  const [isGenerating, setIsGenerating] = useState(false);

  const share = async (element: HTMLElement, title: string, action: 'save' | 'share' = 'share') => {
    setIsGenerating(true);
    try {
      // 1. 先截图主要内容（不包含二维码）
      console.log('[Share] Capturing main content...');
      const contentCanvas = await html2canvas(element, {
        backgroundColor: '#0f172a',
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: true,
      });

      console.log('[Share] Content captured:', contentCanvas.width, 'x', contentCanvas.height);

      // 2. 创建最终 Canvas，增加底部空间放二维码
      const finalCanvas = document.createElement('canvas');
      const qrHeight = 280; // 增加二维码区域高度
      finalCanvas.width = contentCanvas.width;
      finalCanvas.height = contentCanvas.height + qrHeight;

      const ctx = finalCanvas.getContext('2d');
      if (!ctx) throw new Error('Cannot get canvas context');

      // 3. 绘制主要内容
      ctx.drawImage(contentCanvas, 0, 0);

      // 4. 绘制底部二维码区域背景
      ctx.fillStyle = '#020617'; // slate-950
      ctx.fillRect(0, contentCanvas.height, finalCanvas.width, qrHeight);

      // 5. 绘制标题
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 32px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('📚 FloPap', finalCanvas.width / 2, contentCanvas.height + 50);

      // 6. 生成并绘制二维码
      const qrSize = 160;
      const qrGithub = await QRCode.toDataURL('https://github.com/cookiegg/flopap', { width: qrSize, margin: 0 });
      const qrWebsite = await QRCode.toDataURL('https://flopap.com', { width: qrSize, margin: 0 });

      const imgGithub = new Image();
      const imgWebsite = new Image();

      await Promise.all([
        new Promise(resolve => {
          imgGithub.onload = resolve;
          imgGithub.src = qrGithub;
        }),
        new Promise(resolve => {
          imgWebsite.onload = resolve;
          imgWebsite.src = qrWebsite;
        })
      ]);

      // 绘制二维码
      const qrY = contentCanvas.height + 70;
      const spacing = finalCanvas.width / 3;

      // GitHub 二维码
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(spacing - qrSize / 2 - 6, qrY - 6, qrSize + 12, qrSize + 12);
      ctx.drawImage(imgGithub, spacing - qrSize / 2, qrY, qrSize, qrSize);
      ctx.fillStyle = '#cbd5e1';
      ctx.font = '24px sans-serif';
      ctx.fillText('GitHub 开源', spacing, qrY + qrSize + 30);

      // Website 二维码
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(spacing * 2 - qrSize / 2 - 6, qrY - 6, qrSize + 12, qrSize + 12);
      ctx.drawImage(imgWebsite, spacing * 2 - qrSize / 2, qrY, qrSize, qrSize);
      ctx.fillStyle = '#cbd5e1';
      ctx.fillText('在线体验', spacing * 2, qrY + qrSize + 30);

      console.log('[Share] Final canvas generated:', finalCanvas.width, 'x', finalCanvas.height);

      // 7. 保存或分享
      const imageData = finalCanvas.toDataURL('image/png');
      const base64Data = imageData.split(',')[1];
      const fileName = `flopap-${Date.now()}.png`;

      if (action === 'save') {
        if (!Capacitor.isNativePlatform()) {
          // Web: Trigger download
          const link = document.createElement('a');
          link.href = imageData;
          link.download = fileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          console.log('[Share] Download triggered for Web');
        } else {
          // Mobile: Save to Documents
          await Filesystem.writeFile({
            path: fileName,
            data: base64Data,
            directory: Directory.Documents,
          });
          console.log('[Share] Saved to Documents');
        }
        return true;
      } else {
        const result = await Filesystem.writeFile({
          path: fileName,
          data: base64Data,
          directory: Directory.Cache,
        });

        await Share.share({
          title: title,
          text: '在 FloPap 发现的精彩论文 📚',
          url: result.uri,
          dialogTitle: '分享论文',
        });
        console.log('[Share] Shared successfully');
        return true;
      }
    } catch (error) {
      console.error('[Share] Error:', error);
      return false;
    } finally {
      setIsGenerating(false);
    }
  };

  return { share, isGenerating };
};
