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
    """渲染思维导图面板（使用 LLM 生成 + ECharts 树图）"""
    from src.lightrag_adapter import get_mindmap_by_llm, run_async
    from src.web.components.state import get_vector_store
    import json
    import re

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

    # 用 LLM 生成思维导图
    with st.spinner("AI 正在生成思维导图（需要调用 LLM，请稍候）..."):
        try:
            md_tree = run_async(get_mindmap_by_llm(
                selected,
                api_key=st.session_state.api_key,
                model=st.session_state.selected_model,
                provider=st.session_state.get("llm_provider", "openrouter"),
            ))
        except Exception as e:
            st.error(f"生成失败: {e}")
            return

    # 调试：显示生成的 markdown
    with st.expander("查看生成的 Markdown", expanded=False):
        st.code(md_tree, language="markdown")

    # 解析 markdown 树结构，转换为 ECharts 树图数据
    lines = md_tree.strip().split('\n')

    def build_tree(lines):
        """从 markdown 行构建树结构"""
        # 收集所有一级标题（多个根节点）
        level_1_nodes = []
        current_node = None
        current_level_1 = None
        stack = []

        for line in lines:
            if not line.strip():
                continue
            match = re.match(r'^(#+)\s+(.+)$', line)
            if match:
                # 有 # 符号，是标题
                level = len(match.group(1))
                text = match.group(2).strip()

                if level == 1:
                    # 一级标题，作为根节点
                    current_node = {"name": text, "children": []}
                    level_1_nodes.append(current_node)
                    current_level_1 = current_node
                    stack = [(level, current_node)]
                else:
                    # 二级及以下标题
                    if current_level_1 is None:
                        continue
                    node = {"name": text, "children": []}

                    # 找到父节点
                    while stack and stack[-1][0] >= level:
                        stack.pop()
                    if stack:
                        stack[-1][1]["children"].append(node)
                    else:
                        # 没有父节点，添加到当前一级节点
                        current_level_1["children"].append(node)
                    stack.append((level, node))
            else:
                # 没有 # 符号，是叶子节点
                if current_level_1 is None:
                    continue
                text = line.strip()
                node = {"name": text, "children": []}

                # 添加到当前一级节点的子节点（或最后一个有 ## 的节点）
                if stack:
                    stack[-1][1]["children"].append(node)
                else:
                    current_level_1["children"].append(node)

        # 如果有多个一级标题，添加虚拟根节点
        if len(level_1_nodes) > 1:
            return {"name": "思维导图", "children": level_1_nodes}
        elif level_1_nodes:
            return level_1_nodes[0]
        else:
            return None

    tree_data = build_tree(lines)

    if not tree_data:
        st.warning("无法生成思维导图")
        return

    # ECharts 树图配置（原生 JS）
    option = {
        "tooltip": {
            "trigger": "item",
            "triggerOn": "mousemove"
        },
        "series": [
            {
                "type": "tree",
                "data": [tree_data],
                "top": "5%",
                "left": "10%",
                "bottom": "5%",
                "right": "20%",
                "symbolSize": 14,
                "label": {
                    "position": "left",
                    "verticalAlign": "middle",
                    "align": "right",
                    "fontSize": 14,
                    "fontFamily": "Microsoft YaHei, sans-serif"
                },
                "leaves": {
                    "label": {
                        "position": "right",
                        "verticalAlign": "middle",
                        "align": "left"
                    }
                },
                "emphasis": {
                    "focus": "descendant"
                },
                "expandAndCollapse": True,
                "animationDuration": 550,
                "animationDurationUpdate": 750
            }
        ]
    }

    # 使用本地 markmap JS 渲染（不依赖 CDN）
    import os
    static_dir = Path(__file__).parent.parent.parent.parent / "static" / "js"

    d3_js = (static_dir / "d3.min.js").read_text(encoding="utf-8")
    markmap_view_js = (static_dir / "markmap-view.js").read_text(encoding="utf-8")
    markmap_lib_js = (static_dir / "markmap-lib.js").read_text(encoding="utf-8")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; }}
            svg {{ width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <svg id="markmap" style="width: 100%; height: 100%;"></svg>
        <script>
        {d3_js}
        {markmap_view_js}
        </script>
        <script type="module">
        {markmap_lib_js}
        const {{ transformer, Markmap }} = window.markmap;

        const markdown = {repr(md_tree)};
        const {{ root }} = transformer.transform(markdown);

        const mm = Markmap.create('#markmap', null, {{
            embedGlobalCSS: true,
            duration: 500,
        }});

        mm.setData(root);
        mm.fit();

        // 自动缩放
        window.addEventListener('resize', () => mm.fit());
        </script>
    </body>
    </html>
    """

    st.components.v1.html(html, height=600)
