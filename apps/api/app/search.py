"""BM25 search over project entities, cards, and chapter content."""

import math
import re
from collections import Counter
from typing import Any


class BM25:
    """Simple BM25 implementation for entity/paragraph retrieval without external deps."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: list[dict[str, Any]] = []
        self.doc_terms: list[dict[str, int]] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_len: float = 0
        self.total_docs: int = 0
        self.term_df: dict[str, int] = Counter()
        self._built = False

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Chinese-friendly tokenizer: extract CJK characters individually, words as groups."""
        tokens = []
        # extract Chinese character sequences as individual chars (bigram style for BM25)
        chinese_seq = []
        for ch in text:
            if '一' <= ch <= '鿿' or '㐀' <= ch <= '䶿':
                chinese_seq.append(ch)
            else:
                if chinese_seq:
                    # bigram style for Chinese
                    for i in range(len(chinese_seq)):
                        tokens.append(chinese_seq[i])
                    chinese_seq = []
        if chinese_seq:
            for ch in chinese_seq:
                tokens.append(ch)
        # also add word tokens for alphanumeric
        for token in re.findall(r'[a-zA-Z0-9]+', text):
            tokens.append(token.lower())
        return tokens

    def add_document(self, doc_id: str, title: str, content: str, meta: dict = None) -> None:
        text = f"{title} {content}"
        tokens = self.tokenize(text)
        term_freq = Counter(tokens)
        self.documents.append({"id": doc_id, "title": title, "content": content, "meta": meta or {}, "tokens": tokens})
        self.doc_terms.append(dict(term_freq))
        self.doc_lengths.append(len(tokens))
        for term in set(tokens):
            self.term_df[term] = self.term_df.get(term, 0) + 1
        self.total_docs += 1
        self._built = False

    def build(self) -> None:
        if self.total_docs == 0:
            self.avg_doc_len = 1
        else:
            self.avg_doc_len = sum(self.doc_lengths) / self.total_docs
        self._built = True

    def _idf(self, term: str) -> float:
        df = self.term_df.get(term, 0)
        return math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        if not self._built:
            self.build()
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []
        scores = []
        for i, doc_terms in enumerate(self.doc_terms):
            score = 0.0
            doc_len = self.doc_lengths[i]
            for token in query_tokens:
                tf = doc_terms.get(token, 0)
                if tf == 0:
                    continue
                idf = self._idf(token)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                score += idf * numerator / denominator
            if score > 0:
                scores.append({**self.documents[i], "score": score})
        scores.sort(key=lambda x: -x["score"])
        return scores[:top_k]


class SearchIndex:
    """Unified search across entities, cards, chapters."""

    entity_index: BM25
    card_index: BM25

    def __init__(self):
        self.entity_index = BM25()
        self.card_index = BM25()

    def index_entity(self, entity: Any) -> None:
        attrs_str = " ".join(str(v) for v in (entity.attributes or {}).values())
        self.entity_index.add_document(
            doc_id=entity.id,
            title=entity.label,
            content=f"{entity.entity_type} {entity.label} {' '.join(entity.aliases or [])} {attrs_str}",
            meta={"entity_type": entity.entity_type},
        )

    def index_card(self, card: Any) -> None:
        content_str = " ".join(str(v) for v in (card.content or {}).values())
        self.card_index.add_document(
            doc_id=card.id,
            title=card.label,
            content=f"{card.card_type} {card.label} {content_str}",
            meta={"card_type": card.card_type},
        )

    def search_entities(self, query: str, top_k: int = 5) -> list[dict]:
        return self.entity_index.search(query, top_k)

    def search_cards(self, query: str, top_k: int = 5) -> list[dict]:
        return self.card_index.search(query, top_k)
