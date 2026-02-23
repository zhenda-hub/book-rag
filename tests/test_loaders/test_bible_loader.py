"""测试圣经文本加载器"""
import pytest
from pathlib import Path
from src.loaders.bible_loader import BibleLoader, is_bible_text, VERSE_PATTERN
from src.loaders.base import Document, CHUNKING_STRATEGY, STRATEGY_NONE


class TestVersePattern:
    """测试经文格式正则"""

    def test_genesis_1_1(self):
        """测试创世记 1:1"""
        line = "Gen 1:1 起初神创造天地。"
        match = VERSE_PATTERN.match(line)
        assert match is not None
        book, chapter, verse, content = match.groups()
        assert book == "Gen"
        assert chapter == "1"
        assert verse == "1"
        assert content == "起初神创造天地。"

    def test_exodus_2_1(self):
        """测试出埃及记 2:1"""
        line = "Exo 2:1 有一个利未家的人娶了一个利未女子为妻。"
        match = VERSE_PATTERN.match(line)
        assert match is not None
        book, chapter, verse, content = match.groups()
        assert book == "Exo"
        assert chapter == "2"
        assert verse == "1"
        assert content == "有一个利未家的人娶了一个利未女子为妻。"

    def test_invalid_format(self):
        """测试无效格式"""
        line = "这不是经文格式"
        match = VERSE_PATTERN.match(line)
        assert match is None


class TestIsBibleText:
    """测试圣经文本检测"""

    def test_detect_bible_text(self, tmp_path):
        """测试检测圣经格式文本"""
        bible_file = tmp_path / "bible.txt"
        bible_file.write_text("""Holy Bible, Chinese Union Version (GB), Textfile 20010201.
Gen 1:1 起初神创造天地。
Gen 1:2 地是空虚混沌。渊面黑暗。神的灵运行在水面上。
Gen 1:3 神说，要有光，就有了光。
""")
        assert is_bible_text(str(bible_file)) is True

    def test_reject_normal_text(self, tmp_path):
        """测试拒绝普通文本"""
        normal_file = tmp_path / "normal.txt"
        normal_file.write_text("""这是一篇普通文章。
这里没有圣经格式的内容。
只是普通的文本段落。
""")
        assert is_bible_text(str(normal_file)) is False

    def test_require_minimum_verses(self, tmp_path):
        """测试至少需要 3 行经文格式"""
        # 只有 2 行经文格式
        short_file = tmp_path / "short.txt"
        short_file.write_text("""Gen 1:1 起初神创造天地。
Gen 1:2 地是空虚混沌。
""")
        assert is_bible_text(str(short_file)) is False


class TestBibleLoader:
    """测试圣经加载器"""

    def test_load_bible_file(self, tmp_path):
        """测试加载圣经文件"""
        # 创建测试文件
        bible_file = tmp_path / "test_bible.txt"
        bible_file.write_text("""Holy Bible, Chinese Union Version (GB), Textfile 20010201.
Gen 1:1 起初神创造天地。
Gen 1:2 地是空虚混沌。渊面黑暗。神的灵运行在水面上。
Gen 1:3 神说，要有光，就有了光。
Gen 1:4 神看光是好的，就把光暗分开了。
Gen 1:5 神称光为昼，称暗为夜。有晚上，有早晨，这是头一日。
Gen 2:1 天地万物都造齐了。
Gen 2:2 到第七日，神造物的工已经完毕，就在第七日歇了他一切的工，安息了。
Exo 1:1 以色列的众子，各带家眷和雅各一同来到埃及，他们的名字记在下面。
Exo 1:2 有流便，西缅，利未，犹大，
""")

        loader = BibleLoader()
        docs = loader.load(str(bible_file))

        # 应该有 3 个章节：Gen 1, Gen 2, Exo 1
        assert len(docs) == 3

        # 检查 Gen 1 章
        gen_1 = next(d for d in docs if d.metadata.get("book") == "Gen" and d.metadata.get("chapter") == 1)
        assert gen_1.metadata["verse_range"] == "1-5"
        assert gen_1.metadata["total_verses"] == 5
        assert "Gen 1:1 起初神创造天地。" in gen_1.content
        assert "Gen 1:5 神称光为昼" in gen_1.content

        # 检查 Gen 2 章
        gen_2 = next(d for d in docs if d.metadata.get("book") == "Gen" and d.metadata.get("chapter") == 2)
        assert gen_2.metadata["verse_range"] == "1-2"
        assert gen_2.metadata["total_verses"] == 2

        # 检查 Exo 1 章
        exo_1 = next(d for d in docs if d.metadata.get("book") == "Exo" and d.metadata.get("chapter") == 1)
        assert exo_1.metadata["verse_range"] == "1-2"

    def test_verses_sorted(self, tmp_path):
        """测试经节按节号排序"""
        bible_file = tmp_path / "unordered.txt"
        # 经文故意不按顺序
        bible_file.write_text("""Gen 1:3 第三节内容。
Gen 1:1 第一节内容。
Gen 1:2 第二节内容。
""")

        loader = BibleLoader()
        docs = loader.load(str(bible_file))

        assert len(docs) == 1
        content = docs[0].content
        # 检查顺序是否正确
        lines = content.strip().split("\n")
        assert "Gen 1:1" in lines[0]
        assert "Gen 1:2" in lines[1]
        assert "Gen 1:3" in lines[2]

    def test_empty_lines_skipped(self, tmp_path):
        """测试空行被跳过"""
        bible_file = tmp_path / "with_blanks.txt"
        bible_file.write_text("""Gen 1:1 第一节。

Gen 1:2 第二节。


Gen 1:3 第三节。
""")

        loader = BibleLoader()
        docs = loader.load(str(bible_file))

        assert len(docs) == 1
        assert docs[0].metadata["total_verses"] == 3

    def test_metadata_fields(self, tmp_path):
        """测试 metadata 包含所有必要字段"""
        bible_file = tmp_path / "metadata.txt"
        bible_file.write_text("""Gen 1:1 第一节。
Gen 1:2 第二节。
""")

        loader = BibleLoader()
        docs = loader.load(str(bible_file))

        doc = docs[0]
        metadata = doc.metadata
        assert metadata["type"] == "bible"
        assert metadata["book"] == "Gen"
        assert metadata["chapter"] == 1
        assert metadata["verse_range"] == "1-2"
        assert metadata["total_verses"] == 2
        assert metadata["book_chapter"] == "Gen 1"
        # source 是 Document 的属性，不是 metadata
        assert doc.source == str(bible_file)

    def test_file_header_skipped(self, tmp_path):
        """测试文件头被正确跳过"""
        bible_file = tmp_path / "with_header.txt"
        bible_file.write_text("""Holy Bible, Chinese Union Version (GB), Textfile 20010201.
Some additional header info.
Gen 1:1 第一节。
Gen 1:2 第二节。
""")

        loader = BibleLoader()
        docs = loader.load(str(bible_file))

        assert len(docs) == 1
        assert docs[0].metadata["total_verses"] == 2

    def test_chunking_strategy_flag(self, tmp_path):
        """测试切分策略标志"""
        bible_file = tmp_path / "strategy.txt"
        bible_file.write_text("""Gen 1:1 第一节。
Gen 1:2 第二节。
""")

        loader = BibleLoader()
        docs = loader.load(str(bible_file))

        # 所有文档应该标记为 STRATEGY_NONE（已切分）
        for doc in docs:
            assert doc.metadata.get(CHUNKING_STRATEGY) == STRATEGY_NONE


class TestBibleLoaderIntegration:
    """集成测试"""

    def test_actual_hgb_sub_file(self):
        """测试实际的 hgb_sub.txt 文件"""
        file_path = Path(__file__).parent.parent.parent / "data" / "documents" / "hgb_sub.txt"

        if not file_path.exists():
            pytest.skip(f"测试文件 {file_path} 不存在")

        loader = BibleLoader()
        docs = loader.load(str(file_path))

        # 验证文件被正确解析
        assert len(docs) > 0

        # 检查是否有预期的章节
        chapters = [(d.metadata["book"], d.metadata["chapter"]) for d in docs]
        assert ("Gen", 1) in chapters
        assert ("Gen", 2) in chapters
        assert ("Exo", 1) in chapters
        assert ("Exo", 2) in chapters

        # 验证每个文档都有必要的 metadata
        for doc in docs:
            assert "book" in doc.metadata
            assert "chapter" in doc.metadata
            assert "verse_range" in doc.metadata
            assert "total_verses" in doc.metadata
