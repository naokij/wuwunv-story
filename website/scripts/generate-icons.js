#!/usr/bin/env node
/**
 * 生成网站图标（favicon 和 iOS 图标）
 * 用法: node scripts/generate-icons.js
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = path.resolve(__dirname, '../public');
const ICONS_DIR = path.resolve(__dirname, '../public/icons');

// SVG 源文件
const svgSource = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#B8A9C9"/>
      <stop offset="100%" style="stop-color:#9A8AAF"/>
    </linearGradient>
    <linearGradient id="star" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FDF8F3"/>
      <stop offset="100%" style="stop-color:#F5D0C5"/>
    </linearGradient>
  </defs>
  
  <!-- 背景圆角矩形 -->
  <rect x="5" y="5" width="90" height="90" rx="22" fill="url(#bg)"/>
  
  <!-- 星星 -->
  <path d="M50 20 L54 38 L72 38 L58 49 L63 67 L50 56 L37 67 L42 49 L28 38 L46 38 Z" 
        fill="url(#star)" 
        transform="translate(0, 5)"/>
  
  <!-- 小光点装饰 -->
  <circle cx="25" cy="35" r="3" fill="#FDF8F3" opacity="0.6"/>
  <circle cx="75" cy="40" r="2" fill="#FDF8F3" opacity="0.4"/>
  <circle cx="70" cy="65" r="2.5" fill="#FDF8F3" opacity="0.5"/>
  <circle cx="30" cy="70" r="2" fill="#FDF8F3" opacity="0.4"/>
</svg>`;

// 需要生成的图标配置
const icons = [
  { name: 'favicon-16x16.png', size: 16 },
  { name: 'favicon-32x32.png', size: 32 },
  { name: 'apple-touch-icon.png', size: 180 },
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-512.png', size: 512 },
];

async function generateIcons() {
  // 确保目录存在
  await fs.mkdir(ICONS_DIR, { recursive: true });
  
  // 读取 SVG 为 buffer
  const svgBuffer = Buffer.from(svgSource);
  
  console.log('开始生成图标...\n');
  
  for (const icon of icons) {
    const outputPath = path.join(
      icon.name === 'apple-touch-icon.png' ? PUBLIC_DIR : ICONS_DIR,
      icon.name
    );
    
    await sharp(svgBuffer)
      .resize(icon.size, icon.size)
      .png()
      .toFile(outputPath);
    
    console.log(`✓ ${icon.name} (${icon.size}x${icon.size})`);
  }
  
  // 生成 favicon.ico (多尺寸)
  const favicon16 = await sharp(svgBuffer).resize(16, 16).png().toBuffer();
  const favicon32 = await sharp(svgBuffer).resize(32, 32).png().toBuffer();
  
  // 使用 sharp 生成 ico (使用 PNG 格式作为基础)
  // 注意：sharp 不直接支持 ico，我们生成一个 PNG 作为 favicon.ico 的替代
  // 现代浏览器都支持 PNG 格式的 favicon
  await sharp(svgBuffer)
    .resize(32, 32)
    .png()
    .toFile(path.join(PUBLIC_DIR, 'favicon.png'));
  
  console.log(`✓ favicon.png (32x32)`);
  console.log(`\n所有图标生成完成！`);
  console.log(`\n生成的文件:`);
  console.log(`  - public/favicon.svg (源文件)`);
  console.log(`  - public/favicon.png (32x32)`);
  console.log(`  - public/icons/favicon-16x16.png`);
  console.log(`  - public/icons/favicon-32x32.png`);
  console.log(`  - public/apple-touch-icon.png (180x180, iOS图标)`);
  console.log(`  - public/icons/icon-192.png`);
  console.log(`  - public/icons/icon-512.png`);
}

generateIcons().catch(err => {
  console.error('生成图标失败:', err);
  process.exit(1);
});
