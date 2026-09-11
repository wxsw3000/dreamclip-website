/**
 * DreamClip · 一键高光海报生成器 (Poster Generator)
 * 基于 HTML5 Canvas 的纯前端零成本、高品质二次元观影/游戏打卡海报生成器
 */

class DreamClipPoster {
    constructor() {
        this.initModal();
    }

    initModal() {
        if (document.getElementById('posterModal')) return;

        const modalHTML = `
        <div id="posterModal" class="poster-modal-overlay">
            <div class="poster-modal-content">
                <button class="poster-modal-close" id="posterCloseBtn">&times;</button>
                <div class="poster-modal-header">
                    <h3><i class="fas fa-sparkles" style="color:#a78bfa;"></i> 跨次元观测打卡 · 高光海报生成</h3>
                    <p>将属于你的情绪刻在时空海报中，分享给同好</p>
                </div>
                
                <div class="poster-modal-body">
                    <div class="poster-form">
                        <div class="form-group">
                            <label><i class="far fa-user"></i> 观测者昵称</label>
                            <input type="text" id="posterObserverName" value="观测者 #9527" placeholder="输入你的昵称..." />
                        </div>
                        <div class="form-group">
                            <label><i class="far fa-bookmark"></i> 结局/记录名</label>
                            <input type="text" id="posterEndingTitle" value="True End: 雨夜的再会" placeholder="例如：True End..." />
                        </div>
                        <div class="form-group">
                            <label><i class="far fa-comment-alt"></i> 高光台词/感言</label>
                            <textarea id="posterQuote" rows="3" placeholder="写下最触动你的台词或感言...">「樱花飘落的速度是每秒五厘米，而我们之间的告别，用了整整三年。」</textarea>
                        </div>
                        <button class="btn-primary-glow" id="posterReGenerateBtn">
                            <i class="fas fa-sync-alt"></i> 重新绘制海报
                        </button>
                    </div>

                    <div class="poster-preview-area">
                        <div class="canvas-wrapper">
                            <canvas id="posterCanvas" width="800" height="1200"></canvas>
                        </div>
                        <div class="poster-actions">
                            <button class="btn-download" id="posterDownloadBtn">
                                <i class="fas fa-download"></i> 保存海报到本地
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Bind events
        document.getElementById('posterCloseBtn').addEventListener('click', () => this.close());
        document.getElementById('posterModal').addEventListener('click', (e) => {
            if (e.target.id === 'posterModal') this.close();
        });
        document.getElementById('posterReGenerateBtn').addEventListener('click', () => this.generateCurrent());
        document.getElementById('posterDownloadBtn').addEventListener('click', () => this.download());
    }

    open(data = {}) {
        this.currentData = {
            title: data.title || "樱花的告别",
            mood: data.mood || "#心碎 · 致郁系",
            coverImg: data.coverImg || "../images/placeholder.jpg",
            ending: data.ending || "True End: 雨夜的再会",
            quote: data.quote || "「樱花飘落的速度是每秒五厘米，而我们之间的告别，用了整整三年。」",
            observer: data.observer || "观测者 #9527"
        };

        document.getElementById('posterEndingTitle').value = this.currentData.ending;
        document.getElementById('posterQuote').value = this.currentData.quote;
        document.getElementById('posterObserverName').value = this.currentData.observer;

        document.getElementById('posterModal').classList.add('active');
        this.generateCurrent();
    }

    close() {
        document.getElementById('posterModal').classList.remove('active');
    }

    generateCurrent() {
        const title = this.currentData.title;
        const mood = this.currentData.mood;
        const ending = document.getElementById('posterEndingTitle').value.trim() || this.currentData.ending;
        const quote = document.getElementById('posterQuote').value.trim() || this.currentData.quote;
        const observer = document.getElementById('posterObserverName').value.trim() || "观测者";

        this.renderCanvas({
            title,
            mood,
            ending,
            quote,
            observer,
            coverImgUrl: this.currentData.coverImg
        });
    }

    renderCanvas(params) {
        const canvas = document.getElementById('posterCanvas');
        const ctx = canvas.getContext('2d');
        const W = 800;
        const H = 1200;

        canvas.width = W;
        canvas.height = H;

        // 1. 背景色与星空暗纹渐变
        const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
        bgGrad.addColorStop(0, '#0c0818');
        bgGrad.addColorStop(0.5, '#130c24');
        bgGrad.addColorStop(1, '#07040d');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, W, H);

        // 顶部与底部光晕效果
        const topGlow = ctx.createRadialGradient(W / 2, 0, 10, W / 2, 0, 450);
        topGlow.addColorStop(0, 'rgba(167, 139, 250, 0.25)');
        topGlow.addColorStop(1, 'transparent');
        ctx.fillStyle = topGlow;
        ctx.fillRect(0, 0, W, H);

        const bottomGlow = ctx.createRadialGradient(W / 2, H, 10, W / 2, H, 500);
        bottomGlow.addColorStop(0, 'rgba(244, 114, 182, 0.2)');
        bottomGlow.addColorStop(1, 'transparent');
        ctx.fillStyle = bottomGlow;
        ctx.fillRect(0, 0, W, H);

        // 2. 边框装饰与卡片容器
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 2;
        ctx.strokeRect(30, 30, W - 60, H - 60);

        ctx.strokeStyle = 'rgba(167, 139, 250, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(36, 36, W - 72, H - 72);

        // 3. 头部 Brand / Header
        ctx.fillStyle = '#a78bfa';
        ctx.font = 'bold 24px "Inter", "Noto Sans SC", sans-serif';
        ctx.fillText('DREAMCLIP', 60, 85);

        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = '14px "Inter", sans-serif';
        ctx.fillText('PROJECT: NEXUS · 跨次元观测记录', 60, 110);

        // 绘制情绪标签 Badge
        const tagX = W - 240;
        const tagY = 70;
        ctx.fillStyle = 'rgba(244, 114, 182, 0.15)';
        this.roundRect(ctx, tagX, tagY, 180, 36, 18, true, false);
        ctx.strokeStyle = 'rgba(244, 114, 182, 0.4)';
        ctx.lineWidth = 1;
        this.roundRect(ctx, tagX, tagY, 180, 36, 18, false, true);

        ctx.fillStyle = '#f472b6';
        ctx.font = 'bold 15px "Noto Sans SC", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(params.mood, tagX + 90, tagY + 23);
        ctx.textAlign = 'left';

        // 4. 封面/主图展示区
        const imgY = 145;
        const imgH = 460;
        const imgW = W - 120;
        const imgX = 60;

        // 绘制图片阴影框
        ctx.fillStyle = '#18122c';
        this.roundRect(ctx, imgX, imgY, imgW, imgH, 20, true, false);

        // 尝试加载图片
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            ctx.save();
            this.roundRect(ctx, imgX, imgY, imgW, imgH, 20, false, false);
            ctx.clip();
            
            // 保持比例居中裁剪
            const imgAspect = img.width / img.height;
            const targetAspect = imgW / imgH;
            let renderW, renderH, renderX, renderY;

            if (imgAspect > targetAspect) {
                renderH = imgH;
                renderW = imgH * imgAspect;
                renderX = imgX - (renderW - imgW) / 2;
                renderY = imgY;
            } else {
                renderW = imgW;
                renderH = imgW / imgAspect;
                renderX = imgX;
                renderY = imgY - (renderH - imgH) / 2;
            }

            ctx.drawImage(img, renderX, renderY, renderW, renderH);

            // 给图片覆盖渐变暗层
            const imgGrad = ctx.createLinearGradient(0, imgY + imgH - 160, 0, imgY + imgH);
            imgGrad.addColorStop(0, 'transparent');
            imgGrad.addColorStop(1, 'rgba(15, 10, 26, 0.95)');
            ctx.fillStyle = imgGrad;
            ctx.fillRect(imgX, imgY, imgW, imgH);

            ctx.restore();
            this.renderTextPart(ctx, W, H, params);
        };
        img.onerror = () => {
            // 图片无法加载时的后备美化方案
            const fallbackGrad = ctx.createLinearGradient(imgX, imgY, imgX + imgW, imgY + imgH);
            fallbackGrad.addColorStop(0, '#2d1b4e');
            fallbackGrad.addColorStop(1, '#180e2b');
            ctx.fillStyle = fallbackGrad;
            this.roundRect(ctx, imgX, imgY, imgW, imgH, 20, true, false);

            ctx.fillStyle = '#a78bfa';
            ctx.font = '50px "Font Awesome 5 Free", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('🌸', W / 2, imgY + imgH / 2);
            ctx.textAlign = 'left';

            this.renderTextPart(ctx, W, H, params);
        };
        img.src = params.coverImgUrl;
    }

    renderTextPart(ctx, W, H, params) {
        // 5. 剧情标题
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 36px "Noto Sans SC", sans-serif';
        ctx.fillText(params.title, 60, 655);

        // 结局名称 Tag
        ctx.fillStyle = 'rgba(167, 139, 250, 0.2)';
        this.roundRect(ctx, 60, 675, 240, 32, 8, true, false);
        ctx.fillStyle = '#c4b5fd';
        ctx.font = 'bold 14px "Noto Sans SC", sans-serif';
        ctx.fillText('🏆 ' + params.ending, 75, 696);

        // 分隔虚线
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.setLineDash([6, 6]);
        ctx.beginPath();
        ctx.moveTo(60, 730);
        ctx.lineTo(W - 60, 730);
        ctx.stroke();
        ctx.setLineDash([]); // 还原线型

        // 6. 高光金句 / 评论区
        ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        this.roundRect(ctx, 60, 755, W - 120, 260, 16, true, false);
        ctx.strokeStyle = 'rgba(167, 139, 250, 0.15)';
        ctx.lineWidth = 1;
        this.roundRect(ctx, 60, 755, W - 120, 260, 16, false, true);

        // 引用符号
        ctx.fillStyle = 'rgba(167, 139, 250, 0.3)';
        ctx.font = '700 48px Georgia, serif';
        ctx.fillText('“', 85, 810);

        // 金句多行自动折行渲染
        ctx.fillStyle = '#e2e8f0';
        ctx.font = 'italic 20px "Noto Sans SC", sans-serif';
        this.wrapText(ctx, params.quote, 130, 805, W - 230, 34);

        // 7. 页脚 / 二维码及观测者水印
        const footerY = 1050;
        
        // 观测者签名
        ctx.fillStyle = '#94a3b8';
        ctx.font = '15px "Noto Sans SC", sans-serif';
        ctx.fillText(`观者签名：${params.observer}`, 60, footerY);

        const nowStr = new Date().toLocaleDateString('zh-CN').replace(/\//g, '.');
        ctx.fillStyle = '#64748b';
        ctx.font = '13px "Inter", sans-serif';
        ctx.fillText(`TIMESTAMP: ${nowStr} · OBSERVED AT DREAMCLIP`, 60, footerY + 28);

        // 模拟美化二维码 (Micro QR code block)
        const qrSize = 80;
        const qrX = W - 140;
        const qrY = footerY - 25;

        ctx.fillStyle = '#ffffff';
        this.roundRect(ctx, qrX, qrY, qrSize, qrSize, 8, true, false);

        // 简易伪二维码点阵图形
        ctx.fillStyle = '#0b0712';
        ctx.fillRect(qrX + 8, qrY + 8, 22, 22);
        ctx.fillRect(qrX + qrSize - 30, qrY + 8, 22, 22);
        ctx.fillRect(qrX + 8, qrY + qrSize - 30, 22, 22);

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(qrX + 13, qrY + 13, 12, 12);
        ctx.fillRect(qrX + qrSize - 25, qrY + 13, 12, 12);
        ctx.fillRect(qrX + 13, qrY + qrSize - 25, 12, 12);

        ctx.fillStyle = '#0b0712';
        ctx.fillRect(qrX + 38, qrY + 38, 8, 8);
        ctx.fillRect(qrX + 48, qrY + 28, 8, 14);
        ctx.fillRect(qrX + 38, qrY + 54, 18, 8);
        ctx.fillRect(qrX + 18, qrY + 38, 12, 8);
    }

    // 圆角矩形绘制辅助函数
    roundRect(ctx, x, y, width, height, radius, fill, stroke) {
        if (typeof radius === 'number') {
            radius = { tl: radius, tr: radius, br: radius, bl: radius };
        }
        ctx.beginPath();
        ctx.moveTo(x + radius.tl, y);
        ctx.lineTo(x + width - radius.tr, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
        ctx.lineTo(x + width, y + height - radius.br);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
        ctx.lineTo(x + radius.bl, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
        ctx.lineTo(x, y + radius.tl);
        ctx.quadraticCurveTo(x, y, x + radius.tl, y);
        ctx.closePath();
        if (fill) ctx.fill();
        if (stroke) ctx.stroke();
    }

    // 文字自动换行处理
    wrapText(ctx, text, x, y, maxWidth, lineHeight) {
        const words = text.split('');
        let line = '';
        let currentY = y;

        for (let n = 0; n < words.length; n++) {
            const testLine = line + words[n];
            const metrics = ctx.measureText(testLine);
            const testWidth = metrics.width;
            if (testWidth > maxWidth && n > 0) {
                ctx.fillText(line, x, currentY);
                line = words[n];
                currentY += lineHeight;
            } else {
                line = testLine;
            }
        }
        ctx.fillText(line, x, currentY);
    }

    download() {
        const canvas = document.getElementById('posterCanvas');
        const ending = document.getElementById('posterEndingTitle').value.trim() || '高光打卡';
        const image = canvas.toDataURL('image/png').replace('image/png', 'image/octet-stream');
        
        const link = document.createElement('a');
        link.download = `DreamClip_${this.currentData.title}_${ending}.png`;
        link.href = image;
        link.click();
    }
}

// 实例挂载到 window 对象供随时调用
window.dreamClipPoster = new DreamClipPoster();
