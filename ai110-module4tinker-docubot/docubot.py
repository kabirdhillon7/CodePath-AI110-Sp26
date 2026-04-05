"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob
import re

class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Splits each file into paragraph-level chunks (split on blank lines).
        Attaches the most recently seen section heading to each chunk for context.
        Returns a list of tuples: (display_label, chunk_text)
        where display_label is "filename > ## Heading" (or just "filename" if no heading seen yet).
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                last_heading = None
                for chunk in text.split("\n\n"):
                    chunk = chunk.strip()
                    if not chunk or len(chunk) < 30:
                        continue
                    if chunk.startswith("#"):
                        last_heading = chunk.splitlines()[0].strip()
                    label = f"{filename} > {last_heading}" if last_heading else filename
                    docs.append((label, chunk))
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, documents):
        """
        TODO (Phase 1):
        Build a tiny inverted index mapping lowercase words to the documents
        they appear in.

        Example structure:
        {
            "token": ["AUTH.md", "API_REFERENCE.md"],
            "database": ["DATABASE.md"]
        }

        Keep this simple: split on whitespace, lowercase tokens,
        ignore punctuation if needed.
        """
        index = {}
        for filename, text in documents:
            tokens = re.findall(r'\b\w+\b', text.lower())
            for token in tokens:
                if token not in index:
                    index[token] = []
                if filename not in index[token]:
                    index[token].append(filename)
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    MIN_SCORE = 2
    MIN_COVERAGE = 0.4

    STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "it", "its", "this", "that", "these",
        "those", "i", "you", "we", "he", "she", "they", "what", "how",
        "when", "where", "which", "who", "not", "no", "can", "if", "my",
    }

    def _meaningful_terms(self, query):
        """Returns non-stopword tokens from query. Empty set means no answerable content."""
        return set(re.findall(r'\b\w+\b', query.lower())) - self.STOP_WORDS

    def _no_evidence_response(self):
        return "I don't have enough information in my docs to answer that confidently."

    def score_document(self, query, text):
        """
        TODO (Phase 1):
        Return a simple relevance score for how well the text matches the query.

        Suggested baseline:
        - Convert query into lowercase words
        - Count how many appear in the text
        - Return the count as the score
        """
        query_words = set(re.findall(r'\b\w+\b', query.lower())) - self.STOP_WORDS
        text_words = set(re.findall(r'\b\w+\b', text.lower())) - self.STOP_WORDS
        return len(query_words & text_words)

    def retrieve(self, query, top_k=3):
        """
        TODO (Phase 1):
        Use the index and scoring function to select top_k relevant document snippets.

        Return a list of (filename, text) sorted by score descending.
        """
        results = []
        for filename, text in self.documents:
            score = self.score_document(query, text)
            if score >= self.MIN_SCORE:
                results.append((score, filename, text))
        results.sort(key=lambda x: x[0], reverse=True)
        return [(filename, text) for _, filename, text in results[:top_k]]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        terms = self._meaningful_terms(query)
        if not terms:
            return self._no_evidence_response()

        snippets = self.retrieve(query, top_k=top_k)
        if not snippets:
            return self._no_evidence_response()

        top_score = self.score_document(query, snippets[0][1])
        if top_score / len(terms) < self.MIN_COVERAGE:
            return self._no_evidence_response()

        formatted = []
        for label, text in snippets:
            formatted.append(f"[{label}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        terms = self._meaningful_terms(query)
        if not terms:
            return self._no_evidence_response()

        snippets = self.retrieve(query, top_k=top_k)
        if not snippets:
            return self._no_evidence_response()

        top_score = self.score_document(query, snippets[0][1])
        if top_score / len(terms) < self.MIN_COVERAGE:
            return self._no_evidence_response()

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
