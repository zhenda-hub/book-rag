"""圣经文本专用加载器

支持识别圣经格式文本并按章节进行智能分块。

文本格式示例：
    Gen 1:1 起初神创造天地。
    Gen 1:2 地是空虚混沌。
    Exo 2:1 有一个利未家的人...

分块策略：
    - 按章节（Chapter）切分
    - 保留完整经文引用（Book Chapter:Verse-Verses）
    - 在 metadata 中保存 book, chapter, verse_range
"""
import re
from typing import List, Optional
from src.loaders.base import BaseLoader, Document
from src.logger import get_logger

logger = get_logger("bible_loader")

# 圣经经文格式正则：Book Chapter:Verse 内容
# 例如：Gen 1:1 起初神创造天地。
VERSE_PATTERN = re.compile(r'^([A-Z][a-z]+)\s+(\d+):(\d+)\s+(.+)$')


class BibleLoader(BaseLoader):
    """
    圣经文本加载器

    识别圣经格式文本，按章节进行智能分块。

    处理策略：
    - 解析每行经文，提取 book, chapter, verse, content
    - 按章节分组所有经节
    - 每章作为一个 Document chunk
    - metadata 包含：book, chapter, verse_range, total_verses
    """

    def load(self, path: str) -> List[Document]:
        """
        加载圣经文本文件

        Args:
            path: 圣经文本文件路径

        Returns:
            按章节切分的文档列表
        """
        path_obj = self.validate_file_path(path, file_type="Text")

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 解析经文
        verses = self._parse_verses(lines)

        if not verses:
            logger.warning(f"文件 {path} 中未找到圣经格式经文，回退到普通文本加载器")
            # 回退到普通文本处理
            content = "".join(lines)
            return [Document(
                content=content,
                metadata={"type": "txt", "bible_format": False},
                source=str(path_obj),
            )]

        # 按章节分组
        chapters = self._group_by_chapter(verses)

        # 生成 Document 列表
        documents = []
        for (book, chapter), chapter_verses in chapters.items():
            verse_range = f"{chapter_verses[0]['verse']}-{chapter_verses[-1]['verse']}"
            content = self._format_chapter_content(chapter_verses)

            doc = Document(
                content=content,
                metadata={
                    "type": "bible",
                    "book": book,
                    "chapter": chapter,
                    "verse_range": verse_range,
                    "total_verses": len(chapter_verses),
                    "book_chapter": f"{book} {chapter}",  # 用于显示和检索
                },
                source=str(path_obj),
            )
            documents.append(doc)

            logger.debug(f"生成章节块: {book} {chapter}:{verse_range} ({len(chapter_verses)} 节)")

        logger.info(f"圣经加载完成: {len(documents)} 个章节")
        return documents

    def _parse_verses(self, lines: List[str]) -> List[dict]:
        """
        解析经文行，提取结构化信息

        Args:
            lines: 文本行列表

        Returns:
            经文信息列表，每项包含 book, chapter, verse, content
        """
        verses = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过文件头（如第一行标识）
            if line.startswith("Holy Bible") or "Textfile" in line:
                continue

            match = VERSE_PATTERN.match(line)
            if match:
                book, chapter, verse, content = match.groups()
                verses.append({
                    "book": book,
                    "chapter": int(chapter),
                    "verse": int(verse),
                    "content": content,
                })
            else:
                # 非经文格式的行，记录日志但不中断
                logger.debug(f"跳过非经文格式行: {line[:50]}...")

        return verses

    def _group_by_chapter(self, verses: List[dict]) -> dict:
        """
        按章节分组经节

        Args:
            verses: 经文信息列表

        Returns:
            按章节分组的字典 {(book, chapter): [verse_list]}
        """
        chapters = {}

        for verse in verses:
            key = (verse["book"], verse["chapter"])
            if key not in chapters:
                chapters[key] = []
            chapters[key].append(verse)

        # 对每个章节内的经节按节号排序
        for chapter_verses in chapters.values():
            chapter_verses.sort(key=lambda v: v["verse"])

        return chapters

    def _format_chapter_content(self, chapter_verses: List[dict]) -> str:
        """
        格式化章节内容

        将章节内的所有经节组合成可读文本。

        Args:
            chapter_verses: 章节内的经节列表

        Returns:
            格式化后的章节文本
        """
        lines = []
        for verse in chapter_verses:
            # 格式：book chapter:verse content
            # 例如：Gen 1:1 起初神创造天地。
            line = f"{verse['book']} {verse['chapter']}:{verse['verse']} {verse['content']}"
            lines.append(line)

        return "\n".join(lines)


def is_bible_text(path: str) -> bool:
    """
    检测文件是否为圣经格式文本

    通过检查前几行是否有圣经经文格式来判断。

    Args:
        path: 文件路径

    Returns:
        是否为圣经格式文本
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[:20]  # 只检查前 20 行
    except Exception:
        return False

    verse_count = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Holy Bible"):
            continue
        if VERSE_PATTERN.match(line):
            verse_count += 1
            if verse_count >= 3:  # 至少 3 行符合格式
                return True

    return verse_count >= 3
