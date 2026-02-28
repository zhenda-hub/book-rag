"""CSV 文档加载器"""
import csv
from typing import List
from src.loaders.base import BaseLoader, Document
from src.logger import get_logger

logger = get_logger("csv_loader")


class CSVLoader(BaseLoader):
    """CSV 文档加载器 - 每行独立成块"""

    def load(self, path: str) -> List[Document]:
        path_obj = self.validate_file_path(path, file_type="CSV")

        documents = []
        with open(path_obj, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            for i, row in enumerate(rows):
                # 将每行转换为可搜索的文本
                content_parts = [f"{k}: {v}" for k, v in row.items() if v]
                content = ", ".join(content_parts)

                documents.append(Document(
                    content=content,
                    metadata={
                        "type": "csv",
                        "row_index": i,
                        "total_rows": len(rows),
                        **row,  # 包含所有列的原始值
                    },
                    source=str(path_obj),
                ))

        logger.info(f"CSV 加载完成: {len(documents)} 行")
        return documents
