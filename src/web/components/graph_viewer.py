"""图谱可视化组件"""
import streamlit as st
import networkx as nx
import tempfile
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
