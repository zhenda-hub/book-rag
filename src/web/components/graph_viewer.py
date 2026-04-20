"""图谱可视化组件"""
import streamlit as st
import networkx as nx
import tempfile
from pathlib import Path
from pyvis.network import Network

from src.lightrag_adapter import get_graph_sources, _get_workspace_dir, _safe_dirname


def render_graph_viewer() -> None:
    """渲染图谱可视化面板"""
    sources = get_graph_sources()

    if not sources:
        st.info("暂无图谱数据，请先上传文档并构建图谱")
        return

    # 还原显示名
    display_names = {s: s.replace("_", ":").rsplit(":", 1)[0].replace("upload:", "") if s.startswith("upload") else s for s in sources}

    selected = st.selectbox("选择文档图谱", sources, format_func=lambda s: display_names.get(s, s))

    if not selected:
        return

    workspace = _get_workspace_dir(selected)
    graphml_path = workspace / "graph_chunk_entity_relation.graphml"

    if not graphml_path.exists():
        st.warning("图谱文件不存在")
        return

    # 读取图谱
    G = nx.read_graphml(str(graphml_path))

    # 统计
    col1, col2, col3 = st.columns(3)
    col1.metric("节点（实体）", G.number_of_nodes())
    col2.metric("边（关系）", G.number_of_edges())

    entity_types = set(data.get("entity_type", "unknown") for _, data in G.nodes(data=True))
    col3.metric("实体类型", len(entity_types))

    # pyvis 渲染
    net = Network(height="800px", width="100%", directed=False)
    net.toggle_physics(True)

    for node, data in G.nodes(data=True):
        net.add_node(
            node,
            label=node,
            title=data.get("description", ""),
            group=data.get("entity_type", ""),
        )

    for src, tgt, data in G.edges(data=True):
        net.add_edge(
            src, tgt,
            label=data.get("keywords", ""),
            title=data.get("description", ""),
        )

    # 中文字体
    net.set_options("""
    {
        "nodes": {
            "font": {"face": "Microsoft YaHei", "size": 14}
        },
        "edges": {
            "font": {"face": "Microsoft YaHei", "size": 10, "align": "middle"},
            "color": {"inherit": true},
            "smooth": {"type": "continuous"}
        },
        "physics": {
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {"gravitationalConstant": -80}
        }
    }
    """)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, encoding="utf-8", mode="w") as f:
        net.save_graph(f.name)
        html_path = f.name

    st.components.v1.html(open(html_path, "r", encoding="utf-8").read(), height=820)


def render_mindmap_viewer() -> None:
    """渲染思维导图面板（使用 LLM 生成 + ECharts 渲染 + 文件缓存）"""
    from src.lightrag_adapter import get_mindmap_by_llm, run_async
    from src.web.components.state import get_vector_store
    from src.config import Config
    import json
    import re
    from pathlib import Path
    import os

    # 获取向量库中的文档
    vector_store = get_vector_store()
    vector_sources = vector_store.get_all_sources()

    if not vector_sources:
        st.info("暂无文档，请先上传文档")
        return

    display_names = {s: s.replace("upload:", "") if s.startswith("upload") else s for s in vector_sources}
    selected = st.selectbox("选择文档", vector_sources, format_func=lambda s: display_names.get(s, s), key="mindmap_doc")

    if not selected:
        return

    # 文件缓存路径
    mindmaps_dir = Config.DATA_DIR / "mindmaps"
    mindmaps_dir.mkdir(parents=True, exist_ok=True)
    # 将 source 转换为安全的文件名
    safe_filename = selected.replace(":", "_").replace("/", "_") + ".md"
    cache_file = mindmaps_dir / safe_filename

    # 尝试从文件读取缓存
    md_tree = None
    cache_info = None
    if cache_file.exists():
        try:
            md_tree = cache_file.read_text(encoding="utf-8")
            file_mtime = cache_file.stat().st_mtime
            from datetime import datetime
            cache_time = datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M")
            cache_info = f"📁 缓存时间: {cache_time}"
        except Exception as e:
            cache_info = f"⚠️ 缓存读取失败: {e}"

    # 显示生成按钮和状态
    col1, col2 = st.columns([1, 4])
    with col1:
        generate = st.button("🔄 生成思维导图", use_container_width=True)

    with col2:
        if md_tree:
            st.success(f"✅ {cache_info}（点击按钮重新生成）")
        else:
            st.info("💡 点击按钮生成思维导图")

    # 只有点击按钮时才生成
    if generate:
        with st.spinner("AI 正在生成思维导图（需要调用 LLM，请稍候）..."):
            try:
                md_tree = run_async(get_mindmap_by_llm(
                    selected,
                    api_key=st.session_state.api_key,
                    model=st.session_state.selected_model,
                    provider=st.session_state.get("llm_provider", "openrouter"),
                ))
                # 保存到文件
                cache_file.write_text(md_tree, encoding="utf-8")
                st.success("✅ 思维导图已生成并保存")
                st.rerun()
            except Exception as e:
                st.error(f"生成失败: {e}")
                st.error("请检查 API Key 和模型配置是否正确")
                return

    # 如果没有缓存，显示提示
    if not md_tree:
        st.warning("请点击上方按钮生成思维导图")
        return

    if not md_tree.strip():
        st.error("LLM 返回空内容，请重试或更换模型")
        return

    with st.expander("查看生成的 Markdown", expanded=False):
        st.code(md_tree, language="markdown")

    # 将 Markdown 转换为 ECharts 树图数据
    def markdown_to_echart_tree(md_text: str) -> dict:
        """将 Markdown 层级转换为 ECharts 树图数据"""
        lines = md_text.strip().split('\n')
        root_node = None
        stack = []

        for line in lines:
            if not line.strip():
                continue
            match = re.match(r'^(#+)\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                node = {"name": text, "children": []}

                if level == 1:
                    if root_node is None:
                        root_node = node
                        stack = [(level, node)]
                    else:
                        root_node["children"].append(node)
                        stack = [(level, node)]
                else:
                    while stack and stack[-1][0] >= level:
                        stack.pop()
                    if stack:
                        stack[-1][1]["children"].append(node)
                    stack.append((level, node))

        return root_node or {"name": "思维导图", "children": []}

    tree_data = markdown_to_echart_tree(md_tree)

    # 移除空的 children 数组
    def clean_empty_children(node):
        if "children" in node:
            if not node["children"]:
                del node["children"]
            else:
                for child in node["children"]:
                    clean_empty_children(child)
    clean_empty_children(tree_data)

    # 统计节点数量用于动态高度计算
    def count_tree_nodes(node: dict) -> int:
        """递归统计树节点数量"""
        count = 1  # 当前节点
        if "children" in node:
            for child in node["children"]:
                count += count_tree_nodes(child)
        return count

    node_count = count_tree_nodes(tree_data)
    # 每节点约 25px，设置最小 300px，最大 1500px
    dynamic_height = max(300, min(1500, node_count * 25))

    # 使用 ECharts 渲染
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
    html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; }}
    #main {{ width:100%; height:100%; }}
</style>
</head>
<body>
<div id="main"></div>
<script>
    const treeData = {json.dumps(tree_data, ensure_ascii=False)};

    const chart = echarts.init(document.getElementById('main'));

    const option = {{
        tooltip: {{
            trigger: 'item',
            triggerOn: 'mousemove',
            formatter: '{{b}}'
        }},
        series: [
            {{
                type: 'tree',
                data: [treeData],
                top: '5%',
                left: '10%',
                bottom: '5%',
                right: '20%',
                symbol: 'emptyCircle',
                orient: 'LR',
                label: {{
                    position: 'left',
                    verticalAlign: 'middle',
                    align: 'right',
                    fontSize: 14,
                    fontFamily: 'Microsoft YaHei, sans-serif'
                }},
                leaves: {{
                    label: {{
                        position: 'right',
                        verticalAlign: 'middle',
                        align: 'left'
                    }}
                }},
                emphasis: {{
                    focus: 'descendant'
                }},
                expandAndCollapse: true,
                initialTreeDepth: -1,  // -1 表示全部展开
                animationDuration: 550,
                animationDurationUpdate: 750
            }}
        ]
    }};

    chart.setOption(option);

    // 响应式
    window.addEventListener('resize', function() {{
        chart.resize();
    }});
</script>
</body>
</html>"""

    st.components.v1.html(html, height=dynamic_height)
