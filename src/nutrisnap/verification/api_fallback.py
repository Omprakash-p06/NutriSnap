"""Optional LLM fallback for flagged nutrition predictions. Implement in Phase 5."""
class LLMFallback:
    """Invokes LLM second-opinion when rule validator flags output."""
    def query(self, prediction, image): raise NotImplementedError("Implement in Phase 5")

