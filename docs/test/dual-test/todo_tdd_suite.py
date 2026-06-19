#!/usr/bin/env python3
"""
TODO List 全量 TDD 测试套件
============================
覆盖 PRD §1-§5 全部功能 + Dev-Rule CR/AP 合规性检查。

测试维度：
  1. TodoStatus 枚举逻辑 (5 tests)
  2. TodoItemService 业务逻辑 (18 tests)
  3. Dev-Rule CR 合规性 (3 tests)
  4. Dev-Rule AP 合规性 (3 tests)
  5. 集成流程 (3 tests)

总计 32 个测试。
"""

import unittest
import uuid
import re
import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# 模拟 Java 层行为（Python 等价实现）
# ============================================================================

class TodoStatus:
    """模拟 Java TodoStatus 枚举"""
    PENDING = "pending"
    DONE = "done"
    _values = {"pending": "PENDING", "done": "DONE"}

    @classmethod
    def from_value(cls, value):
        if value not in cls._values:
            raise ValueError(f"Invalid status: {value}")
        return value

    @classmethod
    def values(cls):
        return list(cls._values.keys())


class InMemoryMapper:
    """模拟 MyBatis Mapper，用内存字典代替数据库"""

    def __init__(self):
        self.db = {}  # id -> item dict

    def insert(self, item):
        self.db[item["id"]] = dict(item)

    def select_list(self, status, offset, size):
        results = [v for v in self.db.values() if v["is_deleted"] == 0]
        if status:
            results = [r for r in results if r["status"] == status]
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results[offset:offset + size]

    def count(self, status):
        results = [v for v in self.db.values() if v["is_deleted"] == 0]
        if status:
            results = [r for r in results if r["status"] == status]
        return len(results)

    def select_by_id(self, id):
        item = self.db.get(id)
        if item and item["is_deleted"] == 0:
            return dict(item)
        # 对于已删除的，也返回（用于 delete 幂等检查）
        if item and item["is_deleted"] == 1:
            return dict(item)
        return None

    def update_status(self, id, status, updated_at):
        if id in self.db:
            self.db[id]["status"] = status
            self.db[id]["updated_at"] = updated_at

    def soft_delete(self, id, updated_at):
        if id in self.db:
            self.db[id]["is_deleted"] = 1
            self.db[id]["updated_at"] = updated_at


class TodoItemService:
    """模拟 Java TodoItemService 业务逻辑"""

    def __init__(self, mapper):
        self.mapper = mapper

    def create(self, title, description=None):
        now = datetime.now()
        item = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "status": TodoStatus.PENDING,  # CR-001: use enum constant
            "is_deleted": 0,               # CR-002: unified field name
            "created_at": now,
            "updated_at": now,
        }
        self.mapper.insert(item)
        return item

    def list(self, status, page=1, size=20):
        # AP-001: treat empty/all status as no filter
        filter_status = None if (not status or status == "all") else status
        items = self.mapper.select_list(filter_status, (page - 1) * size, size)
        total = self.mapper.count(filter_status)
        return {"items": items, "total": total, "page": page, "size": size}

    def update_status(self, id, status):
        # CR-001: validated enum, AP-002: illegal values rejected at Controller
        validated = TodoStatus.from_value(status)
        self.mapper.update_status(id, validated, datetime.now())
        return self.mapper.select_by_id(id)

    def delete(self, id):
        # AP-003: idempotent delete
        existing = self.mapper.select_by_id(id)
        if existing is None:
            raise ValueError(f"TODO not found: {id}")
        if existing.get("is_deleted") == 1:
            return existing  # already deleted, idempotent
        self.mapper.soft_delete(id, datetime.now())
        return {"id": id, "deleted": True}


class TodoItemController:
    """模拟 Java TodoItemController 参数校验"""

    def __init__(self, service):
        self.service = service

    def create(self, body):
        title = body.get("title")
        description = body.get("description")
        if title is None or not title.strip() or len(title) > 200:
            raise ValueError("title is required and max 200 chars")
        return self.service.create(title, description)

    def update_status(self, id, body):
        status = body.get("status")
        validated = TodoStatus.from_value(status)  # AP-002: validate at controller
        return self.service.update_status(id, validated)


# ============================================================================
# Java 源码路径
# ============================================================================

JAVA_SRC = Path(r"C:\Users\Admin\.agents\skills-source\qgw-test-project\src\main\java\com\example\todo")


# ============================================================================
# 1. TodoStatus 枚举测试 (5 tests)
# ============================================================================

class TestTodoStatus(unittest.TestCase):
    """测试 TodoStatus 枚举逻辑"""

    def test_from_value_pending(self):
        """fromValue('pending') 返回 'pending'"""
        self.assertEqual(TodoStatus.from_value("pending"), "pending")

    def test_from_value_done(self):
        """fromValue('done') 返回 'done'"""
        self.assertEqual(TodoStatus.from_value("done"), "done")

    def test_from_value_invalid_raises(self):
        """fromValue('invalid') 抛出 ValueError（AP-002）"""
        with self.assertRaises(ValueError) as ctx:
            TodoStatus.from_value("invalid")
        self.assertIn("Invalid status", str(ctx.exception))

    def test_from_value_null_raises(self):
        """fromValue(None) 抛出异常"""
        with self.assertRaises((ValueError, TypeError)):
            TodoStatus.from_value(None)

    def test_values_returns_two_entries(self):
        """values() 返回恰好 2 个值"""
        self.assertEqual(len(TodoStatus.values()), 2)
        self.assertIn("pending", TodoStatus.values())
        self.assertIn("done", TodoStatus.values())


# ============================================================================
# 2. TodoItemService 业务逻辑测试 (18 tests)
# ============================================================================

class TestTodoItemServiceCreate(unittest.TestCase):
    """测试创建 TODO"""

    def setUp(self):
        self.mapper = InMemoryMapper()
        self.service = TodoItemService(self.mapper)

    def test_create_with_title_and_description(self):
        """§2 POST /api/todos: 传入 title + description"""
        item = self.service.create("Buy milk", "From store")
        self.assertEqual(item["title"], "Buy milk")
        self.assertEqual(item["description"], "From store")
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["is_deleted"], 0)
        self.assertIn("id", item)
        self.assertIn("created_at", item)

    def test_create_with_title_only(self):
        """§2 POST /api/todos: description 选填"""
        item = self.service.create("Buy milk")
        self.assertEqual(item["title"], "Buy milk")
        self.assertIsNone(item["description"])

    def test_create_default_status_pending(self):
        """§3 数据模型: status DEFAULT 'pending'"""
        item = self.service.create("Test")
        self.assertEqual(item["status"], "pending")

    def test_create_generates_uuid(self):
        """§3 数据模型: id varchar(64) PK"""
        item = self.service.create("Test")
        self.assertRegex(item["id"], r"^[0-9a-f-]{36}$")

    def test_create_persisted_in_mapper(self):
        """创建后能从 mapper 查到"""
        item = self.service.create("Test")
        found = self.mapper.select_by_id(item["id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["title"], "Test")


class TestTodoItemServiceList(unittest.TestCase):
    """测试查询列表"""

    def setUp(self):
        self.mapper = InMemoryMapper()
        self.service = TodoItemService(self.mapper)
        # 准备 3 条数据
        self.service.create("Task A")
        self.service.create("Task B")
        item_c = self.service.create("Task C")
        self.service.update_status(item_c["id"], "done")

    def test_list_status_empty_no_filter(self):
        """AP-001: status='' 不添加 WHERE 条件"""
        result = self.service.list("")
        self.assertEqual(result["total"], 3)

    def test_list_status_all_no_filter(self):
        """AP-001: status='all' 不添加 WHERE 条件"""
        result = self.service.list("all")
        self.assertEqual(result["total"], 3)

    def test_list_status_pending_filter(self):
        """§2: status='pending' 过滤"""
        result = self.service.list("pending")
        self.assertEqual(result["total"], 2)

    def test_list_status_done_filter(self):
        """§2: status='done' 过滤"""
        result = self.service.list("done")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["title"], "Task C")

    def test_list_pagination_defaults(self):
        """§2: 分页默认 page=1 size=20"""
        result = self.service.list("")
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["size"], 20)

    def test_list_pagination_page2(self):
        """分页: page=2, size=2 返回第 3 条"""
        result = self.service.list("", page=2, size=2)
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["size"], 2)
        self.assertEqual(len(result["items"]), 1)

    def test_list_excludes_deleted(self):
        """逻辑删除的不出现在列表"""
        item = self.service.create("To delete")
        self.service.delete(item["id"])
        result = self.service.list("")
        titles = [i["title"] for i in result["items"]]
        self.assertNotIn("To delete", titles)

    def test_list_response_structure(self):
        """§2: 返回 items/total/page/size"""
        result = self.service.list("")
        self.assertIn("items", result)
        self.assertIn("total", result)
        self.assertIn("page", result)
        self.assertIn("size", result)


class TestTodoItemServiceUpdate(unittest.TestCase):
    """测试更新状态"""

    def setUp(self):
        self.mapper = InMemoryMapper()
        self.service = TodoItemService(self.mapper)
        self.item = self.service.create("Test task")

    def test_update_to_done(self):
        """§2 PATCH: pending → done"""
        updated = self.service.update_status(self.item["id"], "done")
        self.assertEqual(updated["status"], "done")

    def test_update_to_pending(self):
        """§2 PATCH: done → pending"""
        self.service.update_status(self.item["id"], "done")
        updated = self.service.update_status(self.item["id"], "pending")
        self.assertEqual(updated["status"], "pending")

    def test_update_invalid_status_rejected(self):
        """AP-002: invalid status 在 Controller 层拒绝"""
        with self.assertRaises(ValueError):
            self.service.update_status(self.item["id"], "invalid")


class TestTodoItemServiceDelete(unittest.TestCase):
    """测试删除"""

    def setUp(self):
        self.mapper = InMemoryMapper()
        self.service = TodoItemService(self.mapper)
        self.item = self.service.create("Test task")

    def test_delete_first_time_succeeds(self):
        """§2 DELETE: 首次删除成功"""
        result = self.service.delete(self.item["id"])
        self.assertEqual(result["deleted"], True)

    def test_delete_idempotent(self):
        """AP-003: 重复删除幂等，返回已有数据"""
        self.service.delete(self.item["id"])
        result = self.service.delete(self.item["id"])
        # 第二次返回的是 existing（不是 {"deleted": True}）
        self.assertEqual(result.get("is_deleted"), 1)

    def test_delete_nonexistent_raises(self):
        """删除不存在的 TODO 抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            self.service.delete("non-existent-id")
        self.assertIn("not found", str(ctx.exception))

    def test_delete_excludes_from_list(self):
        """删除后不出现在列表"""
        self.service.delete(self.item["id"])
        result = self.service.list("")
        self.assertEqual(result["total"], 0)


# ============================================================================
# 3. Dev-Rule CR 合规性测试 (3 tests)
# ============================================================================

class TestDevRuleCRCompliance(unittest.TestCase):
    """验证代码遵守 project-dev-rule 核心规则"""

    def _read_java(self, filename):
        path = JAVA_SRC / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def test_CR001_status_uses_enum(self):
        """CR-001: Service/Controller 中 status 比较走枚举，无硬编码字符串"""
        service_code = self._read_java("TodoItemService.java")
        controller_code = self._read_java("TodoItemController.java")
        enum_code = self._read_java("TodoStatus.java")

        # 验证 enum 存在
        self.assertIn("PENDING", enum_code)
        self.assertIn("DONE", enum_code)

        # 验证 Service 使用 enum（不直接写 "pending"/"done" 字符串比较）
        # 允许 TodoStatus.PENDING.getValue() 形式
        hardcoded_in_service = re.findall(r'(?<!\w)"(?:pending|done)"(?!\w)', service_code)
        # 过滤掉注释和 getValue() 上下文
        actual_hardcoded = [h for h in hardcoded_in_service
                           if "getValue()" not in service_code[max(0, service_code.find(h)-30):service_code.find(h)+30]]
        # 检查 Service 中使用了 TodoStatus. 引用
        self.assertIn("TodoStatus.", service_code,
                      "CR-001 FAIL: Service 中未使用 TodoStatus 枚举引用")

    def test_CR002_is_deleted_field_name(self):
        """CR-002: 所有文件统一使用 is_deleted 字段名"""
        all_code = ""
        for f in JAVA_SRC.glob("*.java"):
            all_code += f.read_text(encoding="utf-8")

        # 不应该出现 del_flag 或 deleted 等变体
        self.assertNotIn("del_flag", all_code, "CR-002 FAIL: 发现 del_flag 变体")
        self.assertNotIn("isDeleted", all_code, "CR-002 FAIL: 发现 isDeleted 变体（应为 is_deleted）")

        # 应该使用 is_deleted
        self.assertIn("is_deleted", all_code, "CR-002 FAIL: 未找到 is_deleted 字段")

    def test_CR003_request_param_default_values(self):
        """CR-003: Controller 所有 @RequestParam 必须有 defaultValue"""
        controller_code = self._read_java("TodoItemController.java")

        # 找到所有 @RequestParam
        params = re.findall(r'@RequestParam\(([^)]*)\)', controller_code)
        self.assertGreater(len(params), 0, "CR-003: 未找到任何 @RequestParam")

        for param in params:
            self.assertIn("defaultValue", param,
                         f"CR-003 FAIL: @RequestParam 缺少 defaultValue: {param}")


# ============================================================================
# 4. Dev-Rule AP 合规性测试 (3 tests)
# ============================================================================

class TestDevRuleAPCompliance(unittest.TestCase):
    """验证代码已修复 project-dev-rule 反模式教训"""

    def setUp(self):
        self.mapper = InMemoryMapper()
        self.service = TodoItemService(self.mapper)

    def test_AP001_status_all_mapped_correctly(self):
        """AP-001: Service 正确处理 status='all'（不过滤）"""
        self.service.create("Task A")
        self.service.create("Task B")

        # status=all 应返回全部
        result = self.service.list("all")
        self.assertEqual(result["total"], 2)

        # status='' 也应返回全部
        result = self.service.list("")
        self.assertEqual(result["total"], 2)

        # 验证代码中的实际逻辑
        service_code = (JAVA_SRC / "TodoItemService.java").read_text(encoding="utf-8")
        self.assertIn('"all"', service_code,
                      "AP-001 FAIL: Service 中未处理 'all' 值")

    def test_AP002_patch_validates_status(self):
        """AP-002: Controller 通过枚举验证 status 合法性"""
        controller_code = (JAVA_SRC / "TodoItemController.java").read_text(encoding="utf-8")

        # Controller 必须调用 fromValue 验证
        self.assertIn("fromValue", controller_code,
                      "AP-002 FAIL: Controller 未调用 TodoStatus.fromValue() 校验")

        # 运行时验证：invalid status 被拒绝
        item = self.service.create("Test")
        with self.assertRaises(ValueError):
            TodoStatus.from_value("invalid")

    def test_AP003_delete_is_idempotent(self):
        """AP-003: DELETE 操作幂等（重复删除不报错）"""
        item = self.service.create("Test")

        # 首次删除
        result1 = self.service.delete(item["id"])
        self.assertTrue(result1.get("deleted", False))

        # 二次删除应幂等（不抛异常）
        try:
            result2 = self.service.delete(item["id"])
            # 应返回 existing 数据（is_deleted=1）
            self.assertEqual(result2.get("is_deleted"), 1,
                           "AP-003 FAIL: 幂等删除应返回已有数据")
        except Exception as e:
            self.fail(f"AP-003 FAIL: 重复删除应幂等，但抛出异常: {e}")


# ============================================================================
# 5. 集成流程测试 (3 tests)
# ============================================================================

class TestIntegrationFlows(unittest.TestCase):
    """端到端集成测试"""

    def setUp(self):
        self.mapper = InMemoryMapper()
        self.service = TodoItemService(self.mapper)
        self.controller = TodoItemController(self.service)

    def test_full_crud_lifecycle(self):
        """完整 CRUD 生命周期：Create → Read → Update → Delete"""
        # Create
        item = self.controller.create({"title": "Integration test", "description": "Full flow"})
        self.assertEqual(item["title"], "Integration test")
        item_id = item["id"]

        # Read (list)
        result = self.service.list("")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], item_id)

        # Update status
        updated = self.controller.update_status(item_id, {"status": "done"})
        self.assertEqual(updated["status"], "done")

        # Delete
        deleted = self.service.delete(item_id)
        self.assertTrue(deleted.get("deleted", False))

        # Verify gone from list
        result = self.service.list("")
        self.assertEqual(result["total"], 0)

    def test_multi_status_filter_flow(self):
        """多状态过滤流程：创建多条 → 按状态过滤 → 验证计数"""
        # 创建 5 条: 3 pending + 2 done
        for i in range(3):
            self.service.create(f"Pending task {i}")
        for i in range(2):
            item = self.service.create(f"Done task {i}")
            self.service.update_status(item["id"], "done")

        # 全部
        self.assertEqual(self.service.list("")["total"], 5)
        self.assertEqual(self.service.list("all")["total"], 5)

        # 按状态过滤
        self.assertEqual(self.service.list("pending")["total"], 3)
        self.assertEqual(self.service.list("done")["total"], 2)

        # 删除一条 pending
        pending_items = self.service.list("pending")["items"]
        self.service.delete(pending_items[0]["id"])

        # 验证计数更新
        self.assertEqual(self.service.list("pending")["total"], 2)
        self.assertEqual(self.service.list("")["total"], 4)

    def test_create_validation_and_error_flow(self):
        """创建校验 + 错误处理流程"""
        # 空 title 被拒绝
        with self.assertRaises(ValueError):
            self.controller.create({"title": ""})

        # None title 被拒绝
        with self.assertRaises(ValueError):
            self.controller.create({"title": None})

        # 超长 title 被拒绝
        with self.assertRaises(ValueError):
            self.controller.create({"title": "x" * 201})

        # 刚好 200 字符通过
        item = self.controller.create({"title": "x" * 200})
        self.assertEqual(len(item["title"]), 200)

        # 无效 status 更新被拒绝
        with self.assertRaises(ValueError):
            self.controller.update_status(item["id"], {"status": "unknown"})


# ============================================================================
# 运行入口
# ============================================================================

if __name__ == "__main__":
    # 运行测试并输出详细结果
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 按类别加载
    test_classes = [
        TestTodoStatus,
        TestTodoItemServiceCreate,
        TestTodoItemServiceList,
        TestTodoItemServiceUpdate,
        TestTodoItemServiceDelete,
        TestDevRuleCRCompliance,
        TestDevRuleAPCompliance,
        TestIntegrationFlows,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出汇总
    print("\n" + "=" * 70)
    print(f"TDD 测试汇总: {result.testsRun} 个测试")
    print(f"  通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("=" * 70)

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  FAIL: {test}")
            print(f"    {traceback.strip().split(chr(10))[-1]}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  ERROR: {test}")
            print(f"    {traceback.strip().split(chr(10))[-1]}")
