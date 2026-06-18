// quality-dev-skills — OpenCode plugin.
//
// 注入质量门禁工作流规则到每个聊天的系统提示中。
// 复用共享的指令构建器，确保所有平台读取同一个真实来源。

import { createRequire } from 'module';
import fs from 'fs';
import os from 'os';
import path from 'path';

// 共享指令构建器是CommonJS；从ES模块桥接。
const require = createRequire(import.meta.url);
const { getQualityGateInstructions } = require('../../hooks/quality-instructions');

// OpenCode没有自己的标志文件约定；在配置旁边保存模式。
const statePath = path.join(
  process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
  'opencode',
  '.quality-dev-skills-active',
);

function readMode() {
  try {
    return fs.readFileSync(statePath, 'utf8').trim() || 'full';
  } catch (e) {
    return 'full';
  }
}

function writeMode(mode) {
  fs.mkdirSync(path.dirname(statePath), { recursive: true });
  fs.writeFileSync(statePath, mode);
}

export default async ({ client } = {}) => {
  const log = (level, message) => {
    try { client && client.app && client.app.log({ body: { service: 'quality-dev-skills', level, message } }); } catch (e) {}
  };

  return {
    // 每轮将规则集附加到系统提示。
    'experimental.chat.system.transform': async (_input, output) => {
      const mode = readMode();
      if (mode === 'off') return;
      output.system.push(getQualityGateInstructions(mode));
    },

    // 持久化 `/quality-dev-skills <level>` 以便下一轮注入遵循它。
    'command.execute.before': async (input) => {
      if (!input || input.command !== 'quality-dev-skills') return;
      const mode = (input.arguments || '').trim() || 'full';
      writeMode(mode);
      log('info', 'quality-dev-skills ' + mode);
    },
  };
};
