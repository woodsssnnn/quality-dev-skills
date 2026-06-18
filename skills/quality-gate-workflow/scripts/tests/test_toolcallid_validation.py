"""test_toolcallid_validation.py — validate_toolcallid() 格式验证测试"""

import pytest

from tests.conftest import gate_enforcer


class TestValidateToolCallId:

    def test_valid_toolcallid(self):
        """格式正确的 toolCallId"""
        ok, msg = gate_enforcer.validate_toolcallid("Agent|P4|2026-01-01T00:00:00", "P4")
        assert ok is True
        assert "有效" in msg

    def test_empty_toolcallid(self):
        """空 toolCallId"""
        ok, msg = gate_enforcer.validate_toolcallid("", "P4")
        assert ok is False
        assert "空" in msg

    def test_wrong_prefix(self):
        """前缀不是 Agent"""
        ok, msg = gate_enforcer.validate_toolcallid("main|P4|2026-01-01T00:00:00", "P4")
        assert ok is False
        assert "Agent" in msg

    def test_step_mismatch(self):
        """步骤标识不匹配"""
        ok, msg = gate_enforcer.validate_toolcallid("Agent|S4|2026-01-01T00:00:00", "P4")
        assert ok is False
        assert "不匹配" in msg

    def test_invalid_timestamp(self):
        """时间戳格式无效"""
        ok, msg = gate_enforcer.validate_toolcallid("Agent|P4|not-a-timestamp", "P4")
        assert ok is False
        assert "时间戳" in msg or "timestamp" in msg.lower()

    def test_toolcallid_too_few_parts(self):
        """分隔符不足（少于 3 段）"""
        ok, msg = gate_enforcer.validate_toolcallid("Agent|P4", "P4")
        assert ok is False
        assert "3 段" in msg or "分隔" in msg
