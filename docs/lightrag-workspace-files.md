# LightRAG Workspace 文件说明

每个文档 workspace 目录（如 `data/lightrag/upload_xxx_txt/`）包含 12 个文件，分为 4 类：

## 图谱结构
| 文件 | 用途 |
|------|------|
| `graph_chunk_entity_relation.graphml` | 知识图谱核心：实体（节点）和关系（边），含名称、类型、描述、权重 |

## KV 存储（JSON）
| 文件 | 用途 |
|------|------|
| `kv_store_full_docs.json` | 原始文档全文 |
| `kv_store_text_chunks.json` | 文本分块 |
| `kv_store_full_entities.json` | 所有实体汇总（名称列表 + 数量） |
| `kv_store_full_relations.json` | 所有关系汇总（实体对列表 + 数量） |
| `kv_store_entity_chunks.json` | 实体 ↔ chunk 映射 |
| `kv_store_relation_chunks.json` | 关系 ↔ chunk 映射 |
| `kv_store_doc_status.json` | 文档处理状态（已处理/chunks 数量/时间戳） |
| `kv_store_llm_response_cache.json` | LLM 响应缓存（避免重复调用） |

## 向量数据库（NanoVectorDB）
| 文件 | 用途 |
|------|------|
| `vdb_entities.json` | 实体向量索引 |
| `vdb_relationships.json` | 关系向量索引 |
| `vdb_chunks.json` | 文本块向量索引（naive 模式用） |

> 可视化只需 `graph_chunk_entity_relation.graphml`
