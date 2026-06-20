#!/usr/bin/env python3
"""evolve-engine.py — Knowledge Compounding 引擎

从 verifier 报告中提取 FAIL/PARTIAL 模式，去重后写入 error-patterns.json，
检查阈值并输出升级建议。

依赖: Python 3 stdlib only（无第三方依赖）
"""

import datetime
import json
import os
import sys
from pathlib import Path


# ===== 常量 =====

THRESHOLDS = {
    "promote_to_dev_rule": 3,
    "promote_to_gate_rules": 5,
    "promote_to_red_lines": 8,
}

KNOWLEDGE_DIR = ".qgw/knowledge"


class EvolveEngine:
    """Knowledge Compounding 引擎。"""

    def __init__(self, workspace_root="."):
        self.workspace_root = Path(workspace_root)
        self.knowledge_dir = self.workspace_root / KNOWLEDGE_DIR

    def evolve(self, gate, dry_run=False):
        """主入口：执行 evolve 检查。

        Args:
            gate: "gate1" 或 "gate2"
            dry_run: 仅分析不写入

        Returns:
            dict: 包含 new_patterns, suggestions, evolve_log, dry_run
        """
        ver_dir = str(self.workspace_root / "docs" / "verification")

        # 1. 提取新模式
        new_patterns = self._extract_patterns(ver_dir)

        # 2. 读取已有模式
        existing = self._load_existing_patterns()

        # 3. 去重
        unique_new = self._deduplicate(new_patterns, existing)

        # 4. 更新 error-patterns（非 dry-run）
        updated_count = 0
        if not dry_run and unique_new:
            updated_count = self._update_error_patterns(unique_new, str(self.knowledge_dir))

        # 5. 阈值检测
        all_patterns = existing + unique_new
        suggestions = self._check_thresholds(all_patterns)

        # 6. 写入 evolve log（非 dry-run）
        log_path = None
        if not dry_run:
            log_path = self._write_evolve_log({
                "gate": gate,
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "new_patterns": len(unique_new),
                "updated_count": updated_count,
                "suggestions": suggestions,
                "total_patterns": len(all_patterns),
            })

        return {
            "new_patterns": len(unique_new),
            "updated_count": updated_count,
            "suggestions": suggestions,
            "evolve_log": log_path,
            "dry_run": dry_run,
            "total_patterns": len(all_patterns),
        }

    def _extract_patterns(self, verification_dir):
        """从 verifier 报告中提取 FAIL/PARTIAL 模式。

        Returns:
            list[dict]: 提取的模式列表
        """
        ver_path = Path(verification_dir)
        if not ver_path.is_dir():
            return []

        patterns = []
        for jf in sorted(ver_path.glob("unit-*.json")):
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            for unit in data.get("units", []):
                for item in unit.get("items", []):
                    status = item.get("status", "")
                    if status in ("FAIL", "PARTIAL"):
                        patterns.append({
                            "id": f"EP_{item.get('id', 'unknown')}_{datetime.datetime.now().strftime('%Y%m%d')}",
                            "description": item.get("spec", item.get("description", "")),
                            "category": item.get("category", "verification"),
                            "source": item.get("source", ""),
                            "item_id": item.get("id", ""),
                            "root_cause": item.get("rootCause", ""),
                            "frequency": 1,
                        })
        return patterns

    def _deduplicate(self, new_patterns, existing):
        """与已有模式去重。

        Returns:
            list[dict]: 去重后的新模式
        """
        existing_descs = {p.get("description", "").strip().lower() for p in existing}
        unique = []
        seen = set()
        for p in new_patterns:
            desc = p.get("description", "").strip().lower()
            if desc and desc not in existing_descs and desc not in seen:
                unique.append(p)
                seen.add(desc)
        return unique

    def _load_existing_patterns(self):
        """从 .qgw/knowledge/error-patterns.json 加载已有模式。"""
        ep_path = self.knowledge_dir / "error-patterns.json"
        if not ep_path.exists():
            return []
        try:
            with open(ep_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("patterns", [])
        except (json.JSONDecodeError, IOError):
            return []

    def _update_error_patterns(self, new_patterns, knowledge_dir):
        """将新模式写入 error-patterns.json。

        Returns:
            int: 更新的模式数量
        """
        k_dir = Path(knowledge_dir)
        k_dir.mkdir(parents=True, exist_ok=True)
        ep_path = k_dir / "error-patterns.json"

        # 加载或初始化
        if ep_path.exists():
            try:
                with open(ep_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {"version": "2.0", "scope": "workspace", "patterns": [],
                        "upgradeLog": [], "promoteLog": []}
        else:
            data = {"version": "2.0", "scope": "workspace", "patterns": [],
                    "upgradeLog": [], "promoteLog": []}

        patterns = data.get("patterns", [])
        updated = 0

        for new_p in new_patterns:
            # 检查是否已有相同描述 → 递增 frequency
            matched = False
            for existing in patterns:
                if existing.get("description", "").strip().lower() == new_p.get("description", "").strip().lower():
                    existing["frequency"] = existing.get("frequency", 1) + 1
                    updated += 1
                    matched = True
                    break
            if not matched:
                patterns.append(new_p)
                updated += 1

        data["patterns"] = patterns
        with open(ep_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return updated

    def _check_thresholds(self, patterns):
        """检查频率阈值，返回升级建议列表。"""
        suggestions = []
        for p in patterns:
            freq = p.get("frequency", 1)
            desc = p.get("description", "未知")
            if freq >= THRESHOLDS["promote_to_red_lines"]:
                suggestions.append(f"建议升级 '{desc}' 到 Red Lines / 合理化借口表 (frequency={freq})")
            elif freq >= THRESHOLDS["promote_to_gate_rules"]:
                suggestions.append(f"建议升级 '{desc}' 到 gate_dev_rules (frequency={freq})")
            elif freq >= THRESHOLDS["promote_to_dev_rule"]:
                suggestions.append(f"建议升级 '{desc}' 到项目 dev_rule (frequency={freq})")
        return suggestions

    def _write_evolve_log(self, log_data):
        """写入 evolution-log.json。"""
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.knowledge_dir / "evolution-log.json"

        # 追加模式
        logs = []
        if log_path.exists():
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        if not isinstance(logs, list):
            logs = []

        logs.append(log_data)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        return str(log_path)


# ===== CLI =====

def main():
    import argparse
    parser = argparse.ArgumentParser(description="QGW Knowledge Compounding 引擎")
    parser.add_argument("action", choices=["evolve"], help="操作")
    parser.add_argument("--gate", default="gate2", choices=["gate1", "gate2"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workspace", default=".")

    args = parser.parse_args()

    if args.action == "evolve":
        engine = EvolveEngine(args.workspace)
        result = engine.evolve(args.gate, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
