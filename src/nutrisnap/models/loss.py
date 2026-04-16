"""Uncertainty-weighted multi-task loss for NutriSnap.

Implements the Kendall et al. (2018) homoscedastic uncertainty weighting:
    L = Σ_i [ L_i / (2 * σ_i²) + log(σ_i) ]

where σ_i are learnable (log) uncertainty parameters per task.
This automatically balances the contribution of each nutritional target
without manually tuned loss weights.

Reference:
    Kendall, A., Gal, Y., & Cipolla, R. (2018). Multi-task learning using
    uncertainty to weigh losses for scene geometry and semantics.
    CVPR 2018. https://arxiv.org/abs/1705.07115
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class UncertaintyWeightedLoss(nn.Module):
    """Learnable homoscedastic uncertainty weighting for 4 regression tasks.

    Tasks: [calories, fat, carbs, protein]

    Args:
        n_tasks:    Number of regression tasks (default 4).
        base_loss:  Base loss function per task ('huber' or 'mse').
        huber_delta: Delta for Huber loss (default 1.0).
    """

    def __init__(
        self,
        n_tasks: int = 4,
        base_loss: str = "huber",
        huber_delta: float = 1.0,
    ):
        super().__init__()
        # log(σ²) initialized to zero → σ = 1 (equal weighting at start)
        self.log_vars = nn.Parameter(torch.zeros(n_tasks))
        self.n_tasks = n_tasks
        self.base_loss = base_loss
        self.huber_delta = huber_delta

    def forward(
        self,
        preds: torch.Tensor,
        targets: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute uncertainty-weighted loss.

        Args:
            preds:   (B, n_tasks) predicted values.
            targets: (B, n_tasks) ground truth values.

        Returns:
            Tuple of (total_loss scalar, per_task_losses tensor of shape (n_tasks,)).
        """
        per_task_losses = []
        for i in range(self.n_tasks):
            if self.base_loss == "huber":
                task_loss = F.huber_loss(
                    preds[:, i], targets[:, i], delta=self.huber_delta, reduction="mean"
                )
            else:
                task_loss = F.mse_loss(preds[:, i], targets[:, i], reduction="mean")
            per_task_losses.append(task_loss)

        per_task_losses = torch.stack(per_task_losses)  # (n_tasks,)

        # Uncertainty weighting: L_i / (2σ_i²) + log(σ_i)
        # log_var = log(σ²), so σ² = exp(log_var), log(σ) = 0.5 * log_var
        precision = torch.exp(-self.log_vars)  # 1/σ²
        weighted = 0.5 * precision * per_task_losses + 0.5 * self.log_vars
        total_loss = weighted.sum()

        return total_loss, per_task_losses.detach()

    @property
    def task_uncertainties(self) -> torch.Tensor:
        """Current σ values (standard deviations) per task."""
        return torch.exp(0.5 * self.log_vars).detach()
