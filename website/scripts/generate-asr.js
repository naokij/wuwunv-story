#!/usr/bin/env node
/**
 * 为故事音频生成逐字时间戳（ASR 对齐数据），用于故事详情页的字高亮+滚动跟随。
 *
 * 用法:
 *   node scripts/generate-asr.js --only 01-巫巫女的心变了
 *   node scripts/generate-asr.js --all
 *   node scripts/generate-asr.js --all --model small    # 更高精度
 *
 * 流程:
 *   1) 调用本地 whisper CLI 生成 word-level timestamps (.json)
 *   2) 用 LCS (Longest Common Subsequence) 把 whisper 输出对齐到 markdown 原文
 *   3) 输出 <id>.aligned.json 到 website/data/asr/
 *
 * 对齐策略:
 *   - 原文（含标点）作为 ref；whisper 输出按词展开为字符序列作为 asr
 *   - LCS 找出最长公共子序列 → 每个原文字符尽量继承最近的 asr 字符时间戳
 *   - 标点零时长（start === end === prev_end），二分查找不会命中
 *   - 漏识别的字继承前字结束时间（保持顺序朗读感）
 */
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '../..');
const AUDIO_DIR = path.resolve(ROOT_DIR, 'website/public/audio');
const OUTPUT_DIR = path.resolve(__dirname, '../data/asr');
const WHISPER_TMP = '/tmp/whisper-tmp';

const PUNCT = new Set([
  '\uFF0C', '\u3002', '\uFF01', '\uFF1F', '\u3001', '\uFF1B', '\uFF1A',
  '\u201C', '\u201D', '\u2018', '\u2019',
  '\uFF08', '\uFF09', '\u300A', '\u300B',
  '\u2026', '\u2014', '\uFF5E', '\u00B7',
  '\u300C', '\u300D', '\u300E', '\u300F',
  '\n', '\r', '\t', ' ',
]);
function isPunct(c) { return PUNCT.has(c); }
function isMatchChar(c) {
  return /[一-龥]/.test(c) || /[a-zA-Z0-9]/.test(c) || isPunct(c);
}

/**
 * 计算两个字符串的最长公共子序列（按字符粒度），返回配对索引数组。
 * 用动态规划做 O(n*m)，字符串一般 < 2000 字符，性能足够。
 */
function lcsPairs(a, b) {
  const n = a.length, m = b.length;
  if (n === 0 || m === 0) return [];
  // dp[i][j] = LCS 长度
  const dp = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (a[i - 1] === b[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
      else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  // 回溯找配对
  const pairs = [];
  let i = n, j = m;
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      pairs.push([i - 1, j - 1]);
      i--; j--;
    } else if (dp[i - 1][j] >= dp[i][j - 1]) i--;
    else j--;
  }
  return pairs.reverse();
}

/**
 * 把 whisper .json 输出的 words 展开为 (char, start, end) 序列。
 * whisper 词级时间戳粒度已够用（每个字继承所属词的时间戳）。
 */
function expandAsrChars(asrWords) {
  const out = [];
  for (const w of asrWords) {
    const text = (w.text || w.word || '').trim();
    if (!text || w.start == null || w.end == null) continue;
    for (const c of text) {
      if (isMatchChar(c)) out.push({ c, t: +w.start.toFixed(2), d: +w.end.toFixed(2) });
    }
  }
  return out;
}

/**
 * 从 markdown 文件提取正文（去 frontmatter + H1 标题）。
 * 仅保留汉字/字母数字/标点（剔除空白/换行）。
 */
function extractRefChars(mdPath) {
  const md = fs.readFileSync(mdPath, 'utf-8');
  let text = md.replace(/^---[\s\S]*?---\n/m, '');
  text = text.replace(/^#\s*.+\n/m, '');
  const chars = [];
  for (const c of text) {
    if (/\s/.test(c)) continue; // 过滤所有空白
    if (isMatchChar(c)) chars.push(c);
  }
  return chars;
}

/**
 * 把 ref_chars 与 asr_chars 通过 LCS 对齐。
 * 输出 [{c, t, d}]：每个 ref 字符尽量继承最近 asr 字符的时间戳。
 * 标点零时长（继承 prev_end），汉字继承前/后字时间戳。
 */
function alignRefToAsr(refChars, asrChars) {
  if (refChars.length === 0) return [];
  const refStr = refChars.join('');
  const asrStr = asrChars.map(x => x.c).join('');
  const pairs = lcsPairs(refStr, asrStr);

  // 建立 ref_idx → asr_idx 映射（一个 ref 可能没有匹配的 asr）
  const refToAsr = new Map();
  for (const [ri, ai] of pairs) refToAsr.set(ri, ai);

  const result = [];
  let prevEnd = 0;
  let lastMatchedAsrIdx = -1;

  // 找到 ref 中第一个匹配到的 asr idx 作为初始 prev_end 锚点
  for (let i = 0; i < refChars.length; i++) {
    const c = refChars[i];
    const matchedAsrIdx = refToAsr.get(i);
    let startTime, endTime;

    if (matchedAsrIdx != null) {
      const ac = asrChars[matchedAsrIdx];
      startTime = ac.t;
      endTime = ac.d;
      prevEnd = endTime;
      lastMatchedAsrIdx = matchedAsrIdx;
    } else {
      // 没匹配上：根据前后已匹配的 asr 字估算
      if (isPunct(c)) {
        // 标点零时长：紧贴前字末尾
        startTime = prevEnd;
        endTime = prevEnd;
      } else {
        // 漏识别的字：用 prevEnd 到下一个 asr 字的时间插值
        const nextAsrIdx = (() => {
          for (let k = i + 1; k < refChars.length; k++) {
            const idx = refToAsr.get(k);
            if (idx != null) return idx;
          }
          return -1;
        })();
        if (nextAsrIdx >= 0) {
          const next = asrChars[nextAsrIdx];
          startTime = prevEnd;
          endTime = next.t;
        } else {
          startTime = prevEnd;
          endTime = prevEnd;
        }
      }
    }
    result.push({ c, t: +startTime.toFixed(2), d: +endTime.toFixed(2) });
  }

  // 修复时序单调性：确保 t 单调不减（漏识别字插值偶尔会倒序）
  for (let i = 1; i < result.length; i++) {
    if (result[i].t < result[i - 1].t) {
      result[i].t = result[i - 1].t;
      if (result[i].d < result[i].t) result[i].d = result[i].t;
    }
  }

  return result;
}

/**
 * 调用本地 whisper 生成 word-level 时间戳。
 * 模型默认 tiny（速度优先，词级时间戳足够）。
 */
function runWhisper(mp3Path, model = 'tiny') {
  const name = path.basename(mp3Path, '.mp3');
  const outTmp = path.join(WHISPER_TMP, `${name}.json`);
  fs.mkdirSync(WHISPER_TMP, { recursive: true });

  if (fs.existsSync(outTmp)) {
    console.log(`  ↳ 缓存命中: ${outTmp}`);
    return outTmp;
  }

  console.log(`  ↳ 调用 whisper (model=${model})...`);
  const cmd = `whisper "${mp3Path}" --language Chinese --model ${model} --output_format json --output_dir ${WHISPER_TMP} --word_timestamps True`;
  execSync(cmd, { stdio: 'inherit' });

  if (!fs.existsSync(outTmp)) {
    throw new Error(`whisper 未生成 ${outTmp}`);
  }
  return outTmp;
}

/**
 * 处理单个故事 mp3 → 输出 aligned.json
 */
function processStory(mp3Path, mdPath, model = 'tiny') {
  const id = path.basename(mp3Path, '.mp3');
  const outFile = path.join(OUTPUT_DIR, `${id}.aligned.json`);

  if (fs.existsSync(outFile)) {
    console.log(`✓ 已存在: ${outFile}`);
    return { skipped: true, file: outFile };
  }

  console.log(`▶ 处理: ${id}`);
  const whisperJson = runWhisper(mp3Path, model);

  const whisperData = JSON.parse(fs.readFileSync(whisperJson, 'utf-8'));
  const words = [];
  for (const seg of whisperData.segments || []) {
    for (const w of seg.words || []) {
      const t = (w.text || w.word || '').trim();
      if (t && w.start != null && w.end != null) {
        words.push({ text: t, start: w.start, end: w.end });
      }
    }
  }
  console.log(`  ↳ whisper 输出 ${words.length} 词`);

  const refChars = extractRefChars(mdPath);
  console.log(`  ↳ 原文 ${refChars.length} 字`);

  const asrChars = expandAsrChars(words);
  const aligned = alignRefToAsr(refChars, asrChars);

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(outFile, JSON.stringify(aligned), 'utf-8');

  // 报告覆盖率
  const covered = aligned.filter(x => x.t > 0 || x.d > 0).length;
  console.log(`  ✓ 写出: ${outFile}（${aligned.length} 字，覆盖 ${covered}/${refChars.length} = ${(covered / refChars.length * 100).toFixed(1)}%）`);
  return { skipped: false, file: outFile, count: aligned.length };
}

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { only: null, all: false, model: 'tiny' };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--only' && args[i + 1]) { opts.only = args[i + 1]; i++; }
    else if (args[i] === '--all') opts.all = true;
    else if (args[i] === '--model' && args[i + 1]) { opts.model = args[i + 1]; i++; }
  }
  return opts;
}

function main() {
  const opts = parseArgs();
  if (!opts.only && !opts.all) {
    console.error('用法: node scripts/generate-asr.js --only <故事id> | --all  [--model tiny|base|small]');
    process.exit(1);
  }

  const audioFiles = fs.readdirSync(AUDIO_DIR)
    .filter(f => /^\d+-.*\.mp3$/.test(f) && !f.startsWith('00-'))
    .sort();

  const targets = opts.all
    ? audioFiles
    : audioFiles.filter(f => f.startsWith(opts.only));

  if (targets.length === 0) {
    console.error(`未找到匹配 "${opts.only}" 的音频文件`);
    process.exit(1);
  }

  console.log(`将处理 ${targets.length} 个故事\n`);
  let processed = 0, skipped = 0, failed = 0;

  for (const mp3 of targets) {
    const id = mp3.replace('.mp3', '');
    const mdPath = path.join(ROOT_DIR, `${id}.md`);
    if (!fs.existsSync(mdPath)) {
      console.warn(`⚠ 跳过 ${id}: 找不到 ${mdPath}`);
      failed++;
      continue;
    }
    try {
      const r = processStory(path.join(AUDIO_DIR, mp3), mdPath, opts.model);
      if (r.skipped) skipped++; else processed++;
    } catch (e) {
      console.error(`✗ 失败 ${id}: ${e.message}`);
      failed++;
    }
    console.log();
  }

  console.log(`\n=== 完成: 处理 ${processed}, 跳过 ${skipped}, 失败 ${failed} ===`);
}

main();