/**
 * data-home.js — 治理运行时数据的家目录（跨版本、跨重装存活）
 *
 * 运行时状态（事件流 jsonl、提示限频状态、完整性快照）不能落在会被
 * 卸载/更新清空的安装目录里——历史事件一旦随重装清零，自进化就断了。
 * 家目录固定在用户目录 ~/.zcode/governance-data，与安装方式解耦。
 * env GOVERNANCE_DATA_HOME 可覆盖（测试隔离用）。
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

let cached = null;

function getDataHome() {
  if (cached) return cached;
  const base = process.env.GOVERNANCE_DATA_HOME
    || path.join(os.homedir(), '.zcode', 'governance-data');
  try {
    fs.mkdirSync(base, { recursive: true });
  } catch (e) {
    // 创建失败（只读环境等）返回原值，调用方的 ensure/append 各自容错
  }
  cached = base;
  return base;
}

module.exports = { getDataHome };
