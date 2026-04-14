"""Trainer for the NutriSnap Nutrition Regressor.

Handles training/validation loops, loss calculation, and hardware-specific
optimizations like Mixed Precision (AMP) and Gradient Accumulation.
"""
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader
from tqdm import tqdm

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class NutritionTrainer:
    """Trainer for multi-modal regression under 4GB VRAM constraints."""

    def __init__(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler=None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        use_amp: bool = True,
        grad_accum_steps: int = 1,
    ):
        self.model = model.to(device)
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device
        self.use_amp = use_amp
        self.grad_accum_steps = grad_accum_steps
        
        self.scaler = GradScaler(enabled=use_amp)
        # Huber loss is more robust to outliers than MSE
        self.criterion = nn.HuberLoss(delta=1.0)
        
        # Target weights [cal, fat, carb, prot] - optional balancing
        self.target_weights = torch.tensor([1.0, 1.0, 1.0, 1.0]).to(device)

    def train_epoch(self, dataloader: DataLoader, epoch: int) -> dict:
        self.model.train()
        total_loss = 0.0
        
        pbar = tqdm(dataloader, desc=f"Epoch {epoch} [Train]", leave=False)
        self.optimizer.zero_grad()
        
        for i, batch in enumerate(pbar):
            rgbd = batch["rgbd"].to(self.device)
            scalars = batch["scalar_features"].to(self.device)
            targets = batch["targets"].to(self.device)
            
            with autocast(enabled=self.use_amp):
                preds = self.model(rgbd, scalars)
                loss = self.criterion(preds, targets)
                # Scale loss for gradient accumulation
                loss = loss / self.grad_accum_steps
                
            self.scaler.scale(loss).backward()
            
            if (i + 1) % self.grad_accum_steps == 0:
                self.scaler.step(self.optimizer)
                self.scaler.update()
                self.optimizer.zero_grad()
                if self.scheduler:
                    self.scheduler.step()
            
            total_loss += loss.item() * self.grad_accum_steps
            pbar.set_postfix({"loss": f"{total_loss / (i+1):.4f}"})
            
        return {"loss": total_loss / len(dataloader)}

    def validate(self, dataloader: DataLoader) -> dict:
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Validating", leave=False):
                rgbd = batch["rgbd"].to(self.device)
                scalars = batch["scalar_features"].to(self.device)
                targets = batch["targets"].to(self.device)
                
                preds = self.model(rgbd, scalars)
                loss = self.criterion(preds, targets)
                
                total_loss += loss.item()
                all_preds.append(preds.cpu())
                all_targets.append(targets.cpu())
                
        avg_loss = total_loss / len(dataloader)
        
        # Calculate metrics (Simple MAE/MAPE)
        all_preds = torch.cat(all_preds)
        all_targets = torch.cat(all_targets)
        
        mae = torch.mean(torch.abs(all_preds - all_targets), dim=0)
        mape = torch.mean(torch.abs((all_preds - all_targets) / (all_targets + 1e-6)), dim=0) * 100
        
        # [cal, fat, carb, prot]
        return {
            "loss": avg_loss,
            "mae": mae.tolist(),
            "mape": mape.tolist()
        }
