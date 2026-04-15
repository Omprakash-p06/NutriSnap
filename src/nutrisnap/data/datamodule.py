"""NutriSnap PyTorch Lightning DataModule. Implement in Phase 2."""
class NutriSnapDataModule:
    """DataModule for NutriSnap training and inference."""
    def setup(self, stage=None): raise NotImplementedError("Implement in Phase 2")
    def train_dataloader(self): raise NotImplementedError("Implement in Phase 2")
    def val_dataloader(self): raise NotImplementedError("Implement in Phase 2")

