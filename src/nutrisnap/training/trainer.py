"""Updated NutriSnap Trainer with 3-phase transfer learning and cosine LR schedule.

Phase 1 (epochs 1–phase1_epochs):   Freeze backbone, LR=lr_heads
Phase 2 (phase1–phase2_epochs):     Unfreeze last 3 backbone layers, LR=lr_backbone_partial
Phase 3 (phase2_epochs–max_epochs): Unfreeze full backbone, LR=lr_backbone_full

Mixed precision, gradient accumulation, and early stopping are all built in.
"""

import torch
import torch.nn as nn
from torch.amp import GradScaler, autocast
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
from torch.utils.data import DataLoader
from tqdm import tqdm

try:
    from scipy.stats import spearmanr as _spearmanr

    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class NutritionTrainer:
    """Trainer for dual-branch NutritionRegressor under 4GB VRAM constraints."""

    def __init__(
        self,
        model: nn.Module,
        criterion: nn.Module,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        use_amp: bool = True,
        grad_accum_steps: int = 4,
        # Learning rates per phase
        lr_heads: float = 1e-4,
        lr_backbone_partial: float = 1e-5,
        lr_backbone_full: float = 1e-6,
        weight_decay: float = 1e-5,
        # Phase boundaries
        phase1_epochs: int = 10,
        phase2_epochs: int = 20,
        max_epochs: int = 100,
        # Early stopping
        early_stopping_patience: int = 10,
    ):
        self.model = model.to(device)
        self.criterion = criterion.to(device)
        self.device = device
        self.use_amp = use_amp
        self.grad_accum_steps = grad_accum_steps
        self.lr_heads = lr_heads
        self.lr_backbone_partial = lr_backbone_partial
        self.lr_backbone_full = lr_backbone_full
        self.weight_decay = weight_decay
        self.phase1_epochs = phase1_epochs
        self.phase2_epochs = phase2_epochs
        self.max_epochs = max_epochs
        self.early_stopping_patience = early_stopping_patience

        # AMP scaler (fixed deprecation: use torch.amp namespace)
        self.scaler = GradScaler("cuda", enabled=use_amp)

        # Optimizer & LR scheduler are built at the start of each fold
        self.optimizer: torch.optim.Optimizer | None = None
        self.scheduler = None
        self._current_phase = 1

        self._log_gpu_stats("Initialization")

        # Early stopping state
        self.best_val_loss = float("inf")
        self.patience_counter = 0

    # ------------------------------------------------------------------
    # Optimizer & Scheduler Setup
    # ------------------------------------------------------------------

    def _build_optimizer(self) -> torch.optim.Optimizer:
        """Configures optimizer with two parameter groups: heads and backbone."""
        head_params = []
        backbone_params = []

        for name, param in self.model.named_parameters():
            if "rgb_branch" in name:
                backbone_params.append(param)
            else:
                head_params.append(param)

        return torch.optim.AdamW(
            [
                {"params": head_params, "lr": self.lr_heads},
                {
                    "params": backbone_params,
                    "lr": 0,
                },  # Included but zeroed out for Phase 1
            ],
            weight_decay=self.weight_decay,
        )

    def _build_scheduler(self, optimizer) -> SequentialLR:
        """Linear warmup (5 epochs) → CosineAnnealingLR for remaining epochs."""
        warmup = LinearLR(optimizer, start_factor=0.1, end_factor=1.0, total_iters=5)
        cosine = CosineAnnealingLR(optimizer, T_max=self.max_epochs - 5, eta_min=1e-7)
        return SequentialLR(optimizer, schedulers=[warmup, cosine], milestones=[5])

    def setup_fold(self):
        """Call once per fold before the epoch loop."""
        self.model.freeze_backbone()
        self.optimizer = self._build_optimizer()
        self.scheduler = self._build_scheduler(self.optimizer)
        self._current_phase = 1
        self.best_val_loss = float("inf")
        self.patience_counter = 0
        logger.info("Phase 1: backbone frozen, training heads only")

    # ------------------------------------------------------------------
    # Phase transitions
    # ------------------------------------------------------------------

    def _maybe_transition_phase(self, epoch: int):
        """Unfreeze layers at phase boundaries and update optimizer parameter groups."""
        if epoch == self.phase1_epochs and self._current_phase == 1:
            self._current_phase = 2
            self.model.unfreeze_last_n_layers(3)

            # Update backbone params (Group 1) to partial LR
            self.optimizer.param_groups[1]["lr"] = self.lr_backbone_partial

            logger.info(
                f"[Epoch {epoch}] Phase 2: unfroze last 3 backbone layers (LR={self.lr_backbone_partial})"
            )

        elif epoch == self.phase2_epochs and self._current_phase == 2:
            self._current_phase = 3
            self.model.unfreeze_all()

            # Update backbone params (Group 1) to full LR
            self.optimizer.param_groups[1]["lr"] = self.lr_backbone_full

            logger.info(
                f"[Epoch {epoch}] Phase 3: full backbone unfrozen (LR={self.lr_backbone_full})"
            )

    # ------------------------------------------------------------------
    # Training epoch
    # ------------------------------------------------------------------

    def train_epoch(self, dataloader: DataLoader, epoch: int) -> dict:
        self.model.train()
        total_loss = 0.0

        self._maybe_transition_phase(epoch)

        pbar = tqdm(dataloader, desc=f"Epoch {epoch} [Train]", leave=False)
        self.optimizer.zero_grad()

        for i, batch in enumerate(pbar):
            rgb = batch["rgb"].to(self.device)
            depth = batch["depth"].to(self.device)
            scalars = batch["scalar_features"].to(self.device)
            targets = batch["targets"].to(self.device)

            with autocast("cuda", enabled=self.use_amp):
                preds = self.model(rgb, depth, scalars)
                loss, per_task = self.criterion(preds, targets)
                loss = loss / self.grad_accum_steps

            self.scaler.scale(loss).backward()

            if (i + 1) % self.grad_accum_steps == 0:
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.scaler.step(self.optimizer)
                self.scaler.update()
                self.optimizer.zero_grad()

            if i % 100 == 0:  # Periodically log stats
                self._log_gpu_stats(f"Epoch {epoch} Step {i}")

            total_loss += loss.item() * self.grad_accum_steps
            pbar.set_postfix({"loss": f"{total_loss / (i + 1):.4f}"})

        if self.scheduler:
            self.scheduler.step()

        return {"loss": total_loss / len(dataloader)}

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, dataloader: DataLoader) -> dict:
        self.model.eval()
        total_loss = 0.0
        all_preds: list[torch.Tensor] = []
        all_targets: list[torch.Tensor] = []

        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Validating", leave=False):
                rgb = batch["rgb"].to(self.device)
                depth = batch["depth"].to(self.device)
                scalars = batch["scalar_features"].to(self.device)
                targets = batch["targets"].to(self.device)

                preds = self.model(rgb, depth, scalars)
                loss, _ = self.criterion(preds, targets)
                total_loss += loss.item()
                all_preds.append(preds.cpu())
                all_targets.append(targets.cpu())

        if len(dataloader) == 0:
            return {
                "loss": 0.0,
                "mae": torch.zeros(4),
                "mape": torch.zeros(4),
                "std": torch.zeros(4),
            }

        avg_loss = total_loss / len(dataloader)
        preds_t = torch.cat(all_preds)
        targets_t = torch.cat(all_targets)

        # Denormalize to original units for interpretable metrics
        from nutrisnap.data.dataset import TARGET_SCALES

        preds_real = preds_t * TARGET_SCALES
        targets_real = targets_t * TARGET_SCALES

        mae = torch.mean(torch.abs(preds_real - targets_real), dim=0)
        # Stable MAPE: only calculate for targets > 5.0 (kcal or grams)
        # to prevent division-by-zero or near-zero scaling artifacts
        mask = targets_real > 5.0

        # Initialize with zeros
        mape = torch.zeros_like(mae)

        # Only compute where mask is true
        if mask.any():
            # Calculate MAPE per dimension [cal, fat, carb, prot]
            for i in range(targets_real.shape[1]):
                m = mask[:, i]
                if m.any():
                    mape[i] = (
                        torch.mean(
                            torch.abs(
                                (preds_real[m, i] - targets_real[m, i])
                                / (targets_real[m, i] + 1e-2)
                            )
                        )
                        * 100
                    )
        std = preds_real.std(dim=0)

        # ------------------------------------------------------------------
        # R² score per nutrient  (variance explained)
        # R² = 1 - SS_res / SS_tot
        # ------------------------------------------------------------------
        ss_res = torch.sum((targets_real - preds_real) ** 2, dim=0)
        ss_tot = torch.sum((targets_real - targets_real.mean(dim=0)) ** 2, dim=0)
        r2 = 1.0 - ss_res / (ss_tot + 1e-8)  # clamp denominator to avoid NaN
        r2 = r2.clamp(min=-1.0)  # cap at -1 for degenerate predictions

        # ------------------------------------------------------------------
        # Spearman rank correlation per nutrient  (ranking ability)
        # ------------------------------------------------------------------
        spearman = torch.zeros(4)
        if _SCIPY_AVAILABLE:
            for i in range(4):
                p_np = preds_real[:, i].numpy()
                t_np = targets_real[:, i].numpy()
                if len(p_np) > 1:
                    rho, _ = _spearmanr(p_np, t_np)
                    spearman[i] = float(rho) if not (rho != rho) else 0.0  # NaN guard
        else:
            logger.debug("scipy not available — Spearman not computed")

        return {
            "loss": avg_loss,
            "mae": mae.tolist(),  # [cal, fat, carb, prot]
            "mape": mape.tolist(),
            "std_dev": std.tolist(),
            "r2": r2.tolist(),  # [cal, fat, carb, prot] — higher is better
            "spearman": spearman.tolist(),  # Spearman ρ per nutrient
        }

    # ------------------------------------------------------------------
    # Early stopping
    # ------------------------------------------------------------------

    def is_improved(self, val_loss: float) -> bool:
        """Returns True if val_loss improved; updates patience counter."""
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.patience_counter = 0
            return True
        self.patience_counter += 1
        return False

    def _log_gpu_stats(self, step_name: str):
        """Log current GPU memory utilization if using CUDA."""
        if "cuda" in self.device:
            allocated = torch.cuda.memory_allocated(self.device) / 1024**2
            reserved = torch.cuda.memory_reserved(self.device) / 1024**2
            logger.debug(
                f"[{step_name}] GPU Memory: {allocated:.1f}MB allocated, {reserved:.1f}MB reserved"
            )
            if allocated > 0:
                # Once per fold info log
                if "Initialization" in step_name:
                    logger.info(
                        f"GPU verified: {torch.cuda.get_device_name(0)} | Memory: {allocated:.1f}MB used"
                    )

    @property
    def should_stop_early(self) -> bool:
        return self.patience_counter >= self.early_stopping_patience
