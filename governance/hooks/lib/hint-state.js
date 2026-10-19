/**
 * hint-state.js — 提示限频共享状态（run-checks / prompt-inject 共用）
 *
 * 无限频的重复提示会沦为噪音，模型会学会忽略。规则：
 *   - 同一 (kind, key) 每会话只提示一次
 *   - 每会话每 kind 总量封顶（cap 由调用方定）
 * 状态文件 ~/.zcode/governance-data/hint-state.json，按会话 keyed，
 * 7 天 TTL 淘汰防膨胀。env GOVERNANCE_HINT_STATE_FILE 可覆盖（测试隔离用）。
 */

const fs = require('fs');
const path = require('path');
const { getDataHome } = require('./data-home');

const STATE_PATH = process.env.GOVERNANCE_HINT_STATE_FILE
  || path.join(getDataHome(), 'hint-state.json');
const SESSION_TTL_MS = 7 * 24 * 3600 * 1000;

function load() {
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, 'utf-8'));
  } catch (e) {
    return {};
  }
}

function save(state) {
  try {
    // TTL 淘汰，防状态文件无限膨胀
    const cutoff = Date.now() - SESSION_TTL_MS;
    for (const [sid, s] of Object.entries(state)) {
      if (!s || !s.ts || s.ts < cutoff) delete state[sid];
    }
    fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
    fs.writeFileSync(STATE_PATH, JSON.stringify(state));
  } catch (e) {
    // 状态持久化失败不致命：最坏情况多提示一次
  }
}

/**
 * 判定是否应注入提示：首次（且未超 cap）返回 true 并落账，之后返回 false。
 * @param {string} sessionId 会话标识（空则不限频——手动调用等场景）
 * @param {string} kind      提示类别（如 contract / init / 自定义）
 * @param {string} key       去重键（通常为文件绝对路径；全局提示用 '*'）
 * @param {number} cap       该 kind 每会话独立 key 数上限
 */
function shouldHint(sessionId, kind, key, cap) {
  if (!sessionId) return true;
  const state = load();
  const s = state[sessionId] || (state[sessionId] = { ts: Date.now() });
  s.ts = Date.now();
  const keys = s[kind] || (s[kind] = {});
  if (keys[key]) return false;
  if (Object.keys(keys).length >= cap) return false;
  keys[key] = 1;
  save(state);
  return true;
}

module.exports = { shouldHint, STATE_PATH };
