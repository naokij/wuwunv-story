#!/usr/bin/env node
/**
 * 从故事 Markdown 文件生成 stories.json
 * 同时生成封面缩略图到 public/covers/
 * 用法: node scripts/generate-stories.js
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { parseFile } from 'music-metadata';
import { pinyin } from 'pinyin';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '../..');
const OUTPUT_FILE = path.resolve(__dirname, '../src/data/stories.json');
const PUBLIC_AUDIO_DIR = path.resolve(__dirname, '../public/audio');
const COVERS_DIR = path.resolve(__dirname, '../public/covers');
const COVER_THUMB_SIZE = 400;
const COVER_FULL_SIZE = 1024;

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function generateCoverThumbnail(coverPath, id, size, suffix = '') {
  const outputPath = path.join(COVERS_DIR, `${id}${suffix}.webp`);

  try {
    await sharp(coverPath)
      .resize(size, size, {
        fit: 'contain',
        background: { r: 255, g: 255, b: 255, alpha: 0 }
      })
      .webp({ quality: 85 })
      .toFile(outputPath);
    return `/covers/${id}${suffix}.webp`;
  } catch (e) {
    console.error(`  缩略图生成失败: ${coverPath}`, e.message);
    return null;
  }
}

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

const extractDescription = (content) => {
  const text = content.replace(/^#\s*.*\n/m, '').trim();
  return text.slice(0, 100).replace(/\n/g, ' ') + '...';
};

const generatePinyinContent = (content) => {
  const lines = content.split('\n');

  return lines.map(line => {
    if (!line.trim()) return '';

    let result = '';
    let currentChineseChunk = '';

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (/[\u4e00-\u9fa5]/.test(char)) {
        currentChineseChunk += char;
      } else {
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
          currentChineseChunk = '';
        }
        result += char;
      }
    }

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

  await ensureDir(COVERS_DIR);

  const files = await fs.readdir(ROOT_DIR);
  const mdFiles = files.filter(f => /^\d+-.*\.md$/.test(f));

  let processed = 0;
  let skipped = 0;

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
    let coverSourcePath = path.join(PUBLIC_AUDIO_DIR, coverJpg);
    try {
      await fs.access(coverSourcePath);
    } catch {
      try {
        coverSourcePath = path.join(PUBLIC_AUDIO_DIR, coverJpeg);
        await fs.access(coverSourcePath);
        coverFile = coverJpeg;
      } catch {
        coverSourcePath = null;
        coverFile = null;
      }
    }

    const coverThumbnail = coverSourcePath
      ? await generateCoverThumbnail(coverSourcePath, id, COVER_THUMB_SIZE, '')
      : null;

    const coverFull = coverSourcePath
      ? await generateCoverThumbnail(coverSourcePath, id, COVER_FULL_SIZE, '-full')
      : null;

    const audioFile = `${id}.mp3`;
    const audioSourcePath = path.join(PUBLIC_AUDIO_DIR, audioFile);
    const duration = await getAudioDuration(audioSourcePath);

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
      cover: coverThumbnail || '',
      coverOriginal: coverFull || '',
      coverFull: coverFull || '',
      audio: `/audio/${audioFile}`,
      content: cleanContent,
      contentWithPinyin: pinyinContent,
    });

    processed++;
    if (processed % 10 === 0) {
      console.log(`已处理 ${processed} 个故事...`);
    }
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
  console.log(`✓ 缩略图目录: ${COVERS_DIR}`);
  console.log(`✓ 音频目录: ${PUBLIC_AUDIO_DIR}`);
  console.log(`✓ 输出文件: ${OUTPUT_FILE}`);
}

generateStories().catch(console.error);