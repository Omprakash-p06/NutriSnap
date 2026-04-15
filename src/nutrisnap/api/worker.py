import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
import torch
import yaml

from nutrisnap.api.models import JobStatus
from nutrisnap.api.store import ResultStore
from nutrisnap.pipeline.segmenter import FoodSegmenter
from nutrisnap.pipeline.volume import VolumeEstimator
from nutrisnap.pipeline.inference import NutritionPredictor
from nutrisnap.pipeline.validator import NutritionValidator
from nutrisnap.pipeline.fallback import GeminiFallback

logger = logging.getLogger(__name__)


class JobWorker:
    """Orchestrates the CV pipeline with GPU serialization."""

    def __init__(self, store: ResultStore, config_path: str = "configs/api/config.yaml"):
        self.store = store
        self.gpu_lock = asyncio.Lock()
        logger.info(f"Initialized JobWorker with store {id(store)} and lock {id(self.gpu_lock)}")
        
        # Load API Config
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
            
        # Initialize Pipeline Components (Lazy load if needed, but let's pre-load for performance)
        self.segmenter = FoodSegmenter(self.cfg["pipeline"]["segmenter_config"])
        self.volume_estimator = VolumeEstimator(self.cfg["pipeline"]["volume_config"])
        self.validator = NutritionValidator(self.cfg["pipeline"]["validator_config"])
        self.fallback = GeminiFallback(config_path)
        
        # Nutrition Predictor might fail if weights are missing — handle gracefully
        try:
            self.predictor = NutritionPredictor(
                checkpoint_dir=self.cfg["pipeline"]["nutrition_predictor"]["checkpoint_dir"],
                model_config_path=self.cfg["pipeline"]["nutrition_predictor"]["model_config"],
                num_folds=self.cfg["pipeline"]["nutrition_predictor"]["num_folds"]
            )
        except Exception as e:
            logger.warning(f"NutritionPredictor failed to load (missing weights?): {e}")
            self.predictor = None

    async def process_job(self, job_id: str, image_bytes: bytes):
        """Execute the full pipeline for a job."""
        print(f"DEBUG: WORKER STARTING FOR {job_id}")
        start_time = time.time()
        logger.info(f"Worker received job {job_id}")
        
        try:
            print(f"DEBUG: UPDATING STATUS TO PROCESSING FOR {job_id}")
            await self.store.update_status(job_id, JobStatus.PROCESSING)
            print(f"DEBUG: STATUS UPDATED FOR {job_id}")
            
            # 1. Save and Decode Image
            image_path = Path("data/uploads") / f"{job_id}.jpg" # Assume jpg for now
            # Image is already saved by main.py, but we might want to reload it as np array
            img_bgr = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise ValueError("Failed to decode image")
            
            # 2. Sequential Pipeline Execution with GPU Locking
            async with self.gpu_lock:
                logger.info(f"Job {job_id} acquired GPU lock")
                
                # Check for Mock Mode
                if os.environ.get("NUTRISNAP_MOCK_CV") == "true":
                    logger.info(f"Job {job_id} running in MOCK CV mode")
                    await asyncio.sleep(0.5)
                    pred_res = {"calories": 450.0, "fat": 15.0, "carbs": 50.0, "protein": 25.0}
                    volume_m3, area_m2 = 0.0005, 0.01
                else:
                    # A. Segmentation
                    seg_res = await asyncio.to_thread(self.segmenter.segment, image_path)
                    combined_mask = seg_res["combined_mask"]
                    
                    # B. Synthetic Depth (MVP Fallback)
                    h, w = combined_mask.shape
                    depth = np.full((h, w), 0.35, dtype=np.float32)
                    depth[combined_mask > 0] = 0.33 # Food is 2cm closer
                    
                    # C. Volume Estimation
                    pc = await asyncio.to_thread(self.volume_estimator.project_to_pc, depth, combined_mask)
                    pc_h = await asyncio.to_thread(self.volume_estimator.get_food_heights, pc)
                    volume_m3, area_m2, vol_type = await asyncio.to_thread(self.volume_estimator.estimate_volume, pc_h)
                    
                    # D. Nutrition Regression
                    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    img_224 = cv2.resize(img_rgb, (224, 224))
                    depth_224 = cv2.resize(depth, (224, 224))
                    
                    rgbd = np.concatenate([img_224, depth_224[:, :, None]], axis=-1)
                    rgbd_t = torch.from_numpy(rgbd).permute(2, 0, 1).float().unsqueeze(0) / 255.0
                    scalars_t = torch.tensor([[volume_m3 * 1e6, area_m2 * 1e4, np.mean(combined_mask > 0)]]).float()
                    
                    if self.predictor:
                        pred_res = await asyncio.to_thread(self.predictor.predict, rgbd_t, scalars_t)
                    else:
                        pred_res = {"calories": 0.0, "fat": 0.0, "carbs": 0.0, "protein": 0.0}
                        logger.warning("Predictor not loaded")

                # E. Validation
                # convert m3 to cm3 and m2 to cm2
                vol_cm3 = volume_m3 * 1e6
                area_cm2 = area_m2 * 1e4
                is_valid, reason = self.validator.validate(pred_res, vol_cm3, area_cm2)
                
                # F. LLM Fallback (VERI-02)
                llm_refinement = None
                if not is_valid:
                    logger.info(f"Prediction flagged: {reason}. Triggering LLM fallback...")
                    llm_refinement = await self.fallback.refine(image_path, pred_res)
                
                final_result = {
                    "calories": round(pred_res["calories"], 1),
                    "fat": round(pred_res["fat"], 1),
                    "carbs": round(pred_res["carbs"], 1),
                    "protein": round(pred_res["protein"], 1),
                    "is_flagged": not is_valid,
                    "verification_reason": reason if not is_valid else None,
                    "llm_refinement": llm_refinement,
                    "latency_sec": round(time.time() - start_time, 2)
                }
                
                await self.store.save_result(job_id, final_result)
                logger.info(f"Job {job_id} completed in {final_result['latency_sec']}s")
                
        except Exception as e:
            logger.exception(f"Error processing job {job_id}: {str(e)}")
            await self.store.update_status(job_id, JobStatus.FAILED, error=str(e))
