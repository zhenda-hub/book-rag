#!/usr/bin/env python
"""查看向量库中文档的 chunk 信息

用法:
    python scripts/view_chunks.py                    # 列出所有文档
    python scripts/view_chunks.py docker.md          # 查看指定文档的 chunks
    python scripts/view_chunks.py docker.md --full   # 显示完整内容
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector_store import VectorStore


def list_all_documents(vs: VectorStore):
    """列出所有已上传的文档"""
    sources = vs.get_all_sources()

    if not sources:
        print("暂无文档")
        return

    source_counts = vs.get_all_sources_with_counts()

    print("\n已上传的文档:")
    print("=" * 60)
    for source in sources:
        count = source_counts.get(source, 0)
        # 简化显示名称
        if source.startswith("upload:"):
            display_name = source.replace("upload:", "")
        elif source.startswith("http"):
            display_name = source[:60] + "..." if len(source) > 60 else source
        else:
            display_name = Path(source).name

        print(f"  {display_name:40s} ({count} chunks)")


def view_document_chunks(vs: VectorStore, filename: str, full: bool = False, limit: int = None):
    """查看指定文档的 chunk 详情"""
    # 查找匹配的 source
    sources = vs.get_all_sources()
    target_source = None

    for source in sources:
        if filename in source:
            target_source = source
            break

    if not target_source:
        print(f"未找到文档: {filename}")
        print("\n可用文档:")
        list_all_documents(vs)
        return

    # 获取该文档的所有 chunks
    results = vs.collection.get(where={"source": target_source})

    if not results or not results.get('documents'):
        print(f"文档 {filename} 没有内容")
        return

    documents = results['documents']
    metadatas = results['metadatas']

    # 应用限制
    if limit:
        documents = documents[:limit]
        metadatas = metadatas[:limit]
        display_msg = f" (显示前 {limit} 个)"
    else:
        display_msg = ""

    print(f"\n文档: {target_source}")
    print(f"总块数: {len(results['documents'])}{display_msg}")
    print("=" * 80)

    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        print(f"\n块 {i + 1}:")
        print(f"  长度: {len(doc)} 字符")

        # 显示标题信息
        headers = [f"{k}={v}" for k, v in meta.items() if k.startswith('h')]
        if headers:
            print(f"  标题: {', '.join(headers)}")

        # 显示内容
        if full and len(doc) > 100:
            print(f"  内容:\n{doc}")
        else:
            preview = doc[:100] + "..." if len(doc) > 100 else doc
            print(f"  内容: {preview}")

        # 显示其他 metadata
        other_meta = {k: v for k, v in meta.items()
                      if not k.startswith('h') and k not in ('source', 'original_filename')}
        if other_meta:
            print(f"  Meta: {other_meta}")

        print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="查看向量库中文档的 chunk 信息")
    parser.add_argument("filename", nargs="?", help="文档名称（支持部分匹配）")
    parser.add_argument("--full", action="store_true", help="显示完整内容")
    parser.add_argument("--limit", type=int, help="限制显示的块数")

    args = parser.parse_args()

    vs = VectorStore()

    if args.filename:
        view_document_chunks(vs, args.filename, args.full, args.limit)
    else:
        list_all_documents(vs)


if __name__ == "__main__":
    main()
