# LightRAG 缓存机制

## 1. 文档上传缓存（图谱构建）

同名文件已存在 workspace → 跳过构建（缓存命中）。
构建失败（如 429 限流）→ 自动清理 workspace，不缓存半成品，下次可重新构建。

```
data/lightrag/
├── upload_dockers_md/          # upload:dockers.md 的图谱
│   ├── graph_chunk_entity_relation.graphml
│   ├── kv_store_*.json
│   ├── vdb_*.json
│   ├── _meta.json              # 语言、LLM 调用次数
│   └── _query_cache.json       # 查询结果缓存
├── upload_guide_txt/           # upload:guide.txt 的图谱
└── ...
```

### _meta.json
```json
{
  "language": "Chinese",       // 自动检测：中文 > 15% → Chinese
  "llm_calls": 12              // 构建时 LLM API 调用次数
}
```

## 2. 图谱查询缓存

同样的问题 + 同样的查询模式 → 直接返回缓存结果，不调 API。
只有成功的回答才缓存，失败的不缓存。

缓存 key = `{mode}:{question}`（naive/local/global/hybrid 四种模式独立缓存）。

## 联动
- **删除文档**：同步删除对应 workspace 目录（含缓存）
- **查询**：仅检索启用文档的图谱，逐个 workspace 查询后合并
- **错误处理**：区分 429 限流 / 内容审核拦截 / 未找到内容，显示具体原因
