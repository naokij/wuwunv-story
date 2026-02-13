#!/usr/bin/env node
/**
 * 从故事 Markdown 文件生成 stories.json
 * 用法: node scripts/generate-stories.js
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { parseFile } from 'music-metadata';
import { pinyin } from 'pinyin';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '../..');
const OUTPUT_FILE = path.resolve(__dirname, '../src/data/stories.json');

// GitHub 仓库配置
const GITHUB_USER = 'naokij';
const REPO_NAME = 'wuwunv-story';
const BRANCH = 'main';

// 生成 GitHub Raw URL
const getAudioUrl = (filename) => {
  return `https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/audio/${filename}`;
};

// 生成列表封面 URL（使用 CDN 压缩）
const getCoverUrl = (filename, timestamp = Date.now()) => {
  const rawUrl = `https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/audio/${filename}`;
  return `https://images.weserv.nl/?url=${encodeURIComponent(rawUrl)}&w=400&h=500&fit=contain&q=85&output=webp&ts=${timestamp}`;
};

// 生成详情封面 URL（使用原始图片）
const getCoverUrlOriginal = (filename) => {
  return `https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/${BRANCH}/audio/${filename}`;
};

// 解析 frontmatter
const parseFrontmatter = (content) => {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return { data: {}, content: content.trim() };
  
  const fm = match[1];
  const body = match[2].trim();
  
  const data = {};
  fm.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.slice(0, colonIndex).trim();
      let value = line.slice(colonIndex + 1).trim();
      if (value.startsWith('"') && value.endsWith('"')) {
        value = value.slice(1, -1);
      }
      data[key] = value;
    }
  });
  
  return { data, content: body };
};

const extractTitle = (markdownTitle) => {
  return markdownTitle.replace(/^#\s*/, '').trim();
};

// 从音频文件获取实际时长
const getAudioDuration = async (audioPath) => {
  try {
    const metadata = await parseFile(audioPath);
    const duration = metadata.format.duration;
    if (duration) {
      const minutes = Math.floor(duration / 60);
      const seconds = Math.floor(duration % 60);
      if (seconds > 0) {
        return `${minutes}分${seconds}秒`;
      }
      return `${minutes} 分钟`;
    }
  } catch (e) {
    // 如果读取失败，返回空字符串
  }
  return '';
};

const extractDescription = (content) => {
  const text = content.replace(/^#\s*.*\n/m, '').trim();
  return text.slice(0, 100).replace(/\n/g, ' ') + '...';
};

// 生成带拼音的 HTML 内容
const generatePinyinContent = (content) => {
  // 对内容按行处理
  const lines = content.split('\n');
  
  return lines.map(line => {
    if (!line.trim()) return '';
    
    let result = '';
    let currentChineseChunk = '';
    let chunkStartIndices = [];
    
    // 第一遍：收集连续汉字段落
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (/[\u4e00-\u9fa5]/.test(char)) {
        currentChineseChunk += char;
        chunkStartIndices.push(i);
      } else {
        // 遇到非汉字，处理之前的汉字段落
        if (currentChineseChunk) {
          const pyArray = pinyin(currentChineseChunk, {
            toneType: 'symbol',
            type: 'array',
            segment: true
          });
          // 回填拼音
          for (let j = 0; j < currentChineseChunk.length; j++) {
            const char = currentChineseChunk[j];
            const py = pyArray[j] ? pyArray[j][0] : '';
            result += `<ruby class="pinyin-ruby"><rb>${char}</rb><rt>${py}</rt></ruby>`;
          }
          currentChineseChunk = '';
          chunkStartIndices = [];
        }
        result += char;
      }
    }
    
    // 处理行尾可能剩余的汉字
    if (currentChineseChunk) {
      const pyArray = pinyin(currentChineseChunk, {
        toneType: 'symbol',
        type: 'array',
        segment: true
      });
      for (let j = 0; j < currentChineseChunk.length; j++) {
        const char = currentChineseChunk[j];
        const py = pyArray[j] ? pyArray[j][0] : '';
        result += `<ruby class="pinyin-ruby"><rb>${char}</rb><rt>${py}</rt></ruby>`;
      }
    }
    
    return result;
  }).join('\n');
};

async function generateStories() {
  const stories = [];
  
  const files = await fs.readdir(ROOT_DIR);
  const mdFiles = files.filter(f => /^\d+-.*\.md$/.test(f));
  
  for (const file of mdFiles.sort()) {
    const id = file.replace('.md', '');
    const num = id.split('-')[0];
    
    if (num === '00') continue;
    
    const filePath = path.join(ROOT_DIR, file);
    const content = await fs.readFile(filePath, 'utf-8');
    const { data, content: body } = parseFrontmatter(content);
    
    const titleMatch = body.match(/^#\s*(.+)$/m);
    const title = data.title || (titleMatch ? extractTitle(titleMatch[0]) : id);
    
    const coverJpg = `${id}.jpg`;
    const coverJpeg = `${id}.jpeg`;
    let coverFile = coverJpg;
    try {
      await fs.access(path.join(ROOT_DIR, 'audio', coverJpg));
    } catch {
      try {
        await fs.access(path.join(ROOT_DIR, 'audio', coverJpeg));
        coverFile = coverJpeg;
      } catch {
        coverFile = null;
      }
    }
    
    const audioFile = `${id}.mp3`;
    const audioPath = path.join(ROOT_DIR, 'audio', audioFile);
    const duration = await getAudioDuration(audioPath);
    
    const cleanContent = body.replace(/^#\s*.*\n/m, '').trim();
    const pinyinContent = generatePinyinContent(cleanContent);
    const titleWithPinyin = generatePinyinContent(title);
    
    stories.push({
      id,
      title,
      titleWithPinyin,
      description: extractDescription(body),
      date: '',
      duration,
      cover: coverFile ? getCoverUrl(coverFile) : '',
      coverOriginal: coverFile ? getCoverUrlOriginal(coverFile) : '',
      audio: getAudioUrl(audioFile),
      content: cleanContent,
      contentWithPinyin: pinyinContent,
    });
  }
  
  stories.sort((a, b) => {
    const numA = parseInt(a.id.split('-')[0]);
    const numB = parseInt(b.id.split('-')[0]);
    return numA - numB;
  });
  
  const output = { stories };
  
  await fs.mkdir(path.dirname(OUTPUT_FILE), { recursive: true });
  await fs.writeFile(OUTPUT_FILE, JSON.stringify(output, null, 2), 'utf-8');
  
  console.log(`✓ 已生成 ${stories.length} 个故事的数据`);
  console.log(`✓ 输出文件: ${OUTPUT_FILE}`);
}

generateStories().catch(console.error);
