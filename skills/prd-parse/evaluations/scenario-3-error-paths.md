# 场景 3：错误（无可解析文件 / 路径不存在 / 缺依赖指引）

## 输入与执行

```bash
python skills/prd-parse/scripts/prd_parse.py /tmp/empty-dir    # 空目录（无受支持扩展名）
python skills/prd-parse/scripts/prd_parse.py /tmp/no-such-path # 路径不存在
```

## 期望

- 空目录：exit 2，stderr 提示"未找到可解析文档"并列出受支持扩展名
- 路径不存在：exit 2，stderr 提示"目标不存在"
- （若本机未装 pymupdf）对 .pdf 文件：该文件 status=failed，error 含按当前解释器
  的 pip 安装指引，其余文件照常解析——单文件失败不拖垮整批
