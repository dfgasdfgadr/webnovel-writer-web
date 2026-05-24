"""Persisted BM25 search documents for fast index rebuild on restart."""
import json
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from app.database import Base


class SearchDoc(Base):
    __tablename__ = "search_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False, default="")
    meta_json = Column(Text, nullable=False, default="{}")
    tokens_json = Column(Text, nullable=False, default="[]")

    def get_meta(self) -> dict:
        try:
            return json.loads(self.meta_json) if self.meta_json else {}
        except json.JSONDecodeError:
            return {}

    def set_meta(self, meta: dict) -> None:
        self.meta_json = json.dumps(meta, ensure_ascii=False)

    def get_tokens(self) -> list[str]:
        try:
            return json.loads(self.tokens_json) if self.tokens_json else []
        except json.JSONDecodeError:
            return []

    def set_tokens(self, tokens: list[str]) -> None:
        self.tokens_json = json.dumps(tokens, ensure_ascii=False)
