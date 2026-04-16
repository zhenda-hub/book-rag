# LightRAG 图谱缓存机制

## 核心规则
- 每个文档 source 拥有独立 workspace：`data/lightrag/{safe_source_name}/`
- 同名文件已存在 workspace → 跳过构建（缓存命中）
- 不同名文件 → 新建 workspace 独立构建

## 目录结构
```
data/lightrag/
├── upload_dockers_md/     # upload:dockers.md 的图谱
│   ├── graph_chunk_entity_relation.graphml
│   ├── kv_store_*.json
│   └── vdb_*.json
├── upload_guide_txt/      # upload:guide.txt 的图谱
└── ...
```

## 联动
- **删除文档**：同步删除对应 workspace 目录
- **查询**：仅检索启用文档的图谱，逐个 workspace 查询后合并
