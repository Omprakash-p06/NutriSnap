"""PyTorch Lightning module for NutriSnap. Implement in Phase 4."""
class NutriSnapLitModule:
    """Lightning module wrapping backbone + heads + loss."""
    def training_step(self, batch, idx): raise NotImplementedError("Implement in Phase 4")
    def validation_step(self, batch, idx): raise NotImplementedError("Implement in Phase 4")

