"""Extractive answer generation and question-text classification."""

import re

from .models import ArticleChunk, NewsCategory
from .rss import NOISE_PHRASES


def is_summary_request(question: str) -> bool:
    return bool(re.search(r"\b(?:summari[sz]e|summary|overview|roundup)\b", question.casefold()))


def is_headline_request(question: str) -> bool:
    normalized = question.casefold()
    if is_summary_request(question) and any(category.value in normalized for category in NewsCategory):
        return False
    return bool(
        re.search(r"\bheadlines?\b", normalized)
        or re.search(r"\bwhat happened\b", normalized)
        or re.search(r"\b(?:today|latest|recent)\b.*\bnews\b", normalized)
        or re.search(r"\bnews\b.*\b(?:today|latest|recent)\b", normalized)
        or re.search(r"\bnews\b.*\bfocus\b|\bfocus\b.*\bnews\b", normalized)
        or is_summary_request(question) and re.search(r"\b(?:today|latest|recent)\b", normalized)
    )


def requests_certain_future(question: str) -> bool:
    normalized = question.casefold()
    certainty = re.search(r"\b(?:definitely|certainly|guaranteed|for sure|without fail)\b", normalized)
    future = re.search(r"\b(?:will|happen|future|next month|next year)\b", normalized)
    return bool(certainty and future)


def clean_excerpt(value: str) -> str:
    text = " ".join(value.split())
    for phrase in NOISE_PHRASES:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:Get Latest|View Market Dashboard|Read more)\b.*", "", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def summary_terms(question: str) -> set[str]:
    stopwords = {
        "a", "about", "an", "and", "are", "be", "been", "but", "bullet", "bullets", "can", "certainly",
        "did", "do", "does", "focus", "for", "from", "give", "guaranteed", "happen", "happened", "has", "have", "headline", "headlines", "how", "i",
        "in", "is", "it", "latest", "me", "more", "news", "next", "of", "on", "or", "overall", "please",
        "points", "recent", "should", "since", "summarize", "summary", "tell", "than", "that", "the", "this", "top",
        "today", "todays", "was", "were", "what", "when", "which", "why", "will", "with", "without", "would",
        "you", "s",
    }
    normalized = question.casefold().replace("’", "'")
    normalized = re.sub(r"(?<=\w)'s\b", "", normalized)
    return {
        term for term in re.findall(r"[a-z0-9]+", normalized)
        if term not in stopwords and not term.isdigit()
    }


class ExtractiveAnswerGenerator:
    """Select grounded sentences or article titles from retrieved chunks."""

    def generate(self, question: str, chunks: list[ArticleChunk]) -> str:
        if not chunks:
            return "I don't have news on that."
        query_terms = summary_terms(question)
        candidates: list[tuple[float, int, str]] = []
        seen: set[str] = set()
        order = 0
        for chunk in chunks:
            title = clean_excerpt(chunk.metadata.get("title", ""))
            headline_request = is_headline_request(question)
            using_title_fallback = headline_request
            if headline_request:
                text = title
            else:
                text = chunk.metadata.get("summary", "") if is_summary_request(question) else ""
            text = clean_excerpt(text) if text else ""
            if text and (len(text) > 600 or len(text) < 40 and is_summary_request(question)):
                text = title
                using_title_fallback = True
            if text and title and not using_title_fallback:
                text = re.sub(rf"^{re.escape(title)}[\s|:.-]*", "", text, flags=re.IGNORECASE)
            if using_title_fallback and (len(title) < 20 or title.casefold() in {"stock market news", "today news", "news"}):
                continue
            if not text:
                text = clean_excerpt(chunk.text)
            sentences = [text] if using_title_fallback else re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                sentence = sentence.strip(" -")
                sentence = re.sub(r"\s+([.!?])$", r"\1", sentence)
                key = sentence.casefold()
                if len(sentence) < 15 or key in seen:
                    continue
                seen.add(key)
                sentence_terms = set(re.findall(r"[a-z0-9]+", key))
                relevance = len(query_terms & sentence_terms) / max(1, len(query_terms))
                formatted_sentence = (
                    sentence
                    if sentence.endswith((".", "!", "?"))
                    else sentence.rstrip(" .!?") + "."
                )
                candidates.append((relevance, order, formatted_sentence))
                order += 1
        candidates.sort(key=lambda item: (-item[0], item[1]))
        excerpts = [sentence for _, _, sentence in candidates[:3]]
        if not excerpts:
            fallback = re.sub(r"\s+([.!?])$", r"\1", clean_excerpt(chunks[0].text).strip())
            if not fallback.endswith((".", "!", "?")):
                fallback = fallback.rstrip(" .!?") + "."
            excerpts = [fallback]
        return "\n".join(f"- {excerpt}" for excerpt in excerpts)