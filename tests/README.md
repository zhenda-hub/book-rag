# 测试说明

本目录包含项目的测试用例。

## 测试文件

```bash
# 运行所有测试
uv run pytest

# 运行特定目录
uv run pytest tests/test_loaders

# 运行特定文件
uv run pytest tests/test_chunking.py -v

# 运行特定测试函数
uv run pytest tests/test_chunking.py::test_xxx -v
```

**前置条件：** 需要设置 .env的 `OPENROUTER_API_KEY` 环境变量
