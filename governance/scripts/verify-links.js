#!/usr/bin/env node
/**
 * verify-links.js — Markdown 内部链接校验（知识库保鲜工具）
 *
 * 用途：校验 md 文件中 []() 链接指向的仓库内文件是否存在。
 *       外部链接（http/https/mailto）与纯锚点（#）跳过；目录链接跳过；
 *       链接的 #anchor 片段剥离后只校验目标文件存在（不做 slug 校验）。
 *
 * 用法：
 *   node verify-links.js                     # 校验当前目录（默认 .）
 *   node verify-links.js <file-or-dir> ...   # 校验指定文件/目录（可多个）
 *
 * 场景：
 *   - CI 全量校验（断链即 exit 1）
 *   - 单文件校验（可作为 governance 脚本规则接入 PostToolUse：
 *     规则集里声明 script 指向本文件即可，非 0 退出码即违规）
 *
 * 退出码：0 = 全部通过；1 = 存在断链或路径错误
 * 依赖：Node.js >= 12（仅标准库）
 */

const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const targets = argv.filter(a => !a.startsWith('--'));
const quiet = argv.includes('--quiet');

const LINK_RE = /\]\(([^)]+)\)/g;
const SKIP_PREFIX = ['http://', 'https://', 'mailto:', '#'];
const SKIP_DIRS = new Set(['node_modules', '.git', '.idea', '.vscode', 'dist', 'build', 'target']);

let brokenCount = 0;
let totalChecked = 0;
let fileCount = 0;

function collectMdFiles(dir) {
  const result = [];
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name) && !entry.name.startsWith('.')) {
          result.push(...collectMdFiles(fullPath));
        }
      } else if (entry.name.endsWith('.md')) {
        result.push(fullPath);
      }
    }
  } catch (err) {
    console.error(`[WARN] 无法读取目录: ${dir} — ${err.message}`);
    brokenCount++;  // 读不了目录按错误计，CI 可见
  }
  return result;
}

function verifyFile(filePath, baseDir) {
  const relPath = path.relative(baseDir, filePath).replace(/\\/g, '/') || filePath;
  let content;
  try {
    content = fs.readFileSync(filePath, 'utf-8');
  } catch (e) {
    console.log(`[BROKEN] ${relPath} (READ ERROR: ${e.message})`);
    brokenCount++;
    return;
  }
  const fileDir = path.dirname(filePath);

  for (const match of content
    // 跳过围栏代码块：块内的 []() 是示例文本（常出现在"目录组织模式"示例里），不是真实链接
    .replace(/```[\s\S]*?```/g, '')
    .matchAll(LINK_RE)) {
    const href = match[1].trim();
    if (SKIP_PREFIX.some(p => href.startsWith(p))) continue;
    if (href.endsWith('/')) continue;

    // 剥离 #anchor 后校验目标文件存在（CJK slug 不做校验）
    const hrefNoAnchor = href.split('#')[0];
    if (!hrefNoAnchor) continue;

    totalChecked++;
    const target = path.resolve(fileDir, hrefNoAnchor);
    if (!fs.existsSync(target)) {
      brokenCount++;
      console.log(`[BROKEN] ${relPath} -> ${hrefNoAnchor} (NOT FOUND)`);
    }
  }
}

// ─── 主流程 ───────────────────────────────────────────────────────────────
const files = [];
for (const t of (targets.length ? targets : ['.'])) {
  const p = path.resolve(t);
  if (!fs.existsSync(p)) {
    console.error(`[ERROR] 路径不存在: ${t}`);
    process.exit(1);
  }
  if (fs.statSync(p).isFile()) {
    files.push(p);
  } else {
    files.push(...collectMdFiles(p));
  }
}

const baseDir = process.cwd();
for (const f of [...new Set(files)]) {
  fileCount++;
  verifyFile(f, baseDir);
}

if (!quiet) {
  console.log(`🛡 QGW · verify-links · ${fileCount} md / ${totalChecked} 内链`);
}
if (brokenCount > 0) {
  console.log(`🛡 QGW · verify-links · ❌ ${brokenCount} 个断链/错误`);
  process.exit(1);
}
console.log('🛡 QGW · verify-links · ✅ 全部通过');
process.exit(0);
