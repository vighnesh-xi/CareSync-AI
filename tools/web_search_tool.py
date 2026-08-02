from typing import Dict, Any, List

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


class WebSearchTool:
    def __init__(self, logger):
        self.logger = logger

    def search(self, query: str) -> Dict[str, Any]:
        self.logger.info(f"WebSearchTool: Searching web for query: {query}")

        if DDGS is None:
            self.logger.error("WebSearchTool: duckduckgo_search package not installed.")
            return {
                "success": False,
                "summary": "",
                "sources": [],
            }

        try:
            results = []
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=3):
                    results.append(item)

            if not results:
                self.logger.warning("WebSearchTool: No web results found.")
                return {
                    "success": False,
                    "summary": "",
                    "sources": [],
                }

            summary_parts = []
            sources = []

            for item in results:
                title = item.get("title", "Untitled")
                body = item.get("body", "")
                href = item.get("href", "Unknown URL")

                summary_parts.append(f"{title}: {body}")
                sources.append({
                    "title": title,
                    "source": href,
                    "url": href
                })

            summary = " ".join(summary_parts)

            self.logger.info(f"WebSearchTool: Retrieved {len(sources)} web results.")
            return {
                "success": True,
                "summary": summary,
                "sources": sources,
            }

        except Exception as exc:
            self.logger.exception(f"WebSearchTool: Search failed with error: {exc}")
            return {
                "success": False,
                "summary": "",
                "sources": [],
            }