/**
 * integrity.js — 运行时完整性检测核心（可注入路径，供 --self-test 验证检测器本身）
 *
 * 机制：安装时对运行时目录树做快照（CRLF 归一后逐文件 SHA-256）写入
 * data-home 的锚清单；SessionStart 每会话比对当前树与锚清单。
 * 威胁模型与事件流哈希链一致：篡改可见性（tamper-evidence）而非
 * 篡改防护——能改文件者理论上也能重写锚清单，但"改门禁脚本"与
 * "改锚清单"需要两步协同，单步篡改必然暴露。
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/** 收集目录下全部文件相对路径（递归，跳过 node_modules/.git）。 */
function listFiles(rootDir) {
  const out = [];
  const walk = (dir) => {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (e) {
      return;
    }
    for (const ent of entries) {
      if (ent.name === 'node_modules' || ent.name === '.git') continue;
      const p = path.join(dir, ent.name);
      if (ent.isDirectory()) walk(p);
      else if (ent.isFile()) out.push(path.relative(rootDir, p).replace(/\\/g, '/'));
    }
  };
  walk(rootDir);
  return out.sort();
}

/** CRLF 归一后的文件 SHA-256（跨平台行尾差异不算篡改）。 */
function fileHash(file) {
  const buf = fs.readFileSync(file);
  const normalized = buf.toString('utf-8').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(normalized, 'utf-8').digest('hex');
}

/** 生成目录树快照（锚清单内容）。 */
function snapshotTree(rootDir) {
  const snap = { version: 1, files: {} };
  for (const rel of listFiles(rootDir)) {
    try {
      snap.files[rel] = fileHash(path.join(rootDir, rel));
    } catch (e) { /* 单文件读失败跳过 */ }
  }
  return snap;
}

/**
 * 比对目录树与锚清单。
 * @returns {{ result: 'ok'|'drift'|'skip-no-anchor', detail: string }}
 */
function checkIntegrity({ runtimeDir, anchorPath }) {
  let anchor;
  try {
    anchor = JSON.parse(fs.readFileSync(anchorPath, 'utf-8'));
  } catch (e) {
    return { result: 'skip-no-anchor', detail: '锚清单不存在或不可读（未执行安装快照？）' };
  }
  const current = snapshotTree(runtimeDir);
  const anchorFiles = Object.keys(anchor.files || {});
  const currentFiles = Object.keys(current.files);

  const missing = anchorFiles.filter(f => !currentFiles.includes(f));
  const extra = currentFiles.filter(f => !anchorFiles.includes(f));
  const changed = anchorFiles.filter(f => currentFiles.includes(f) && anchor.files[f] !== current.files[f]);

  if (missing.length === 0 && extra.length === 0 && changed.length === 0) {
    return { result: 'ok', detail: `${anchorFiles.length} 文件一致` };
  }
  const parts = [];
  if (changed.length) parts.push(`内容变化 ${changed.length}: ${changed.slice(0, 5).join(', ')}`);
  if (extra.length) parts.push(`多出文件 ${extra.length}: ${extra.slice(0, 5).join(', ')}`);
  if (missing.length) parts.push(`缺失文件 ${missing.length}: ${missing.slice(0, 5).join(', ')}`);
  return { result: 'drift', detail: parts.join('；') };
}

module.exports = { listFiles, snapshotTree, checkIntegrity };
