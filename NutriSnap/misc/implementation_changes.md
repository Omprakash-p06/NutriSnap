Here is a document outlining the key implementation changes required for the NutriSnap project, along with the relevant GitHub repository links.

---

## NutriSnap: External Repository Integration Plan

### 🔄 Core Strategic Shift

The project transitions from a **custom build** to a **modular integration** approach, leveraging specialized, research-backed repositories for core computer vision tasks.

| Aspect | Previous Approach | New Approach |
| :--- | :--- | :--- |
| **Segmentation** | Build / fine-tune custom model | Integrate **FoodSAM** for zero-shot, panoptic segmentation |
| **Volume Estimation** | Hybrid convex hull / alpha shape | Integrate **VolETA** (SOTA) or **FoodVolume** for 3D mesh reconstruction |
| **Architecture** | Single unified PyTorch model | **Pipeline of components**: Segmentation → Volume → Lightweight regressor |
| **Training Scope** | Train entire model from scratch | Train only nutrition mapping model; external components used as-is |

---

### 📦 External Repositories & Key Changes

#### 1. Segmentation: FoodSAM

**Repository**: [https://github.com/jamesjg/FoodSAM](https://github.com/jamesjg/FoodSAM)

**Impact**: Replaces custom segmentation module entirely. FoodSAM is the first framework to achieve instance, panoptic, and promptable segmentation on food images.

**Implementation Changes**:
- Add `third_party/FoodSAM/` as Git submodule
- Call via CLI: `python FoodSAM/semantic.py --img_path <path> --output <path>`
- Or import for panoptic segmentation: `python FoodSAM/panoptic.py --data_root <path> --output <path>`

#### 2. Volume Estimation (Option A): VolETA

**Repository**: [https://github.com/GCVCG/VolETA-MetaFood](https://github.com/GCVCG/VolETA-MetaFood)

**Impact**: CVPR 2024 Meta Food Challenge winner. Creates scaled 3D meshes from one or few RGBD images.

**Implementation Changes**:
- Clone and install submodules: Pixel-Perfect-SfM, SAM, XMem2, NeuS2
- Requires 8GB+ GPU; sequential loading recommended for 4GB constraint
- Input: one or few RGBD images; Output: scaled 3D mesh + volume

#### 3. Volume Estimation (Option B): FoodVolume (Lightweight Alternative)

**Repository**: [https://github.com/leonbegiristain/FoodVolume](https://github.com/leonbegiristain/FoodVolume)

**Impact**: Volume estimation from monocular video using openMVG/openMVS.

**Implementation Changes**:
- Integrate FastSAM for segmentation
- Use PoissonRecon for mesh reconstruction
- Scale to metric units using reference object
- Prefer for GTX 1650 4GB

#### 4. Additional Resources

**DietAI24**: [https://github.com/Runz96/DietAI24](https://github.com/Runz96/DietAI24) — Provides Nutrition5k preprocessing (`nutrition5k_proc.py`) and baseline implementations

**Nutrition5k Utilities**: [https://github.com/Oatsty/nutrition5k](https://github.com/Oatsty/nutrition5k) — Pre-generated food region masks using OpenSeeD and training scripts

---

### 🏗️ Architecture Change Summary

| Module | Previous | New | Repo |
| :--- | :--- | :--- | :--- |
| Data Loading | Custom | Custom | N/A |
| RGB Preprocessing | Custom | Unchanged | N/A |
| Depth Preprocessing | Custom | Enhanced with repo tools | VolETA / FoodVolume |
| Segmentation | Custom | **FoodSAM** | [jamesjg/FoodSAM](https://github.com/jamesjg/FoodSAM) |
| Volume Estimation | Convex hull + alpha shape | **VolETA** or **FoodVolume** | [GCVCG/VolETA-MetaFood](https://github.com/GCVCG/VolETA-MetaFood) / [leonbegiristain/FoodVolume](https://github.com/leonbegiristain/FoodVolume) |
| Nutrition Regression | Multi-task model | **Simplified model** (food class + volume → nutrients) | N/A |
| Validation | Rule-based + API | Unchanged | N/A |

---

### 🚀 Implementation Roadmap Changes

1. **Phase 1 (Data)**: Add Nutrition5k preprocessing using DietAI24's `nutrition5k_proc.py`
2. **Phase 2 (Preprocessing)**: Generate food masks using FoodSAM or Oatsty/nutrition5k
3. **Phase 3 (Model)**: Replace custom volume code with VolETA or FoodVolume integration
4. **Phase 4 (Training)**: Train only lightweight nutrition regressor
5. **Phase 5 (Evaluation)**: Add segmentation (mIoU) and volume estimation (relative error) metrics

---

### ⚠️ Key Considerations

- **Dependency Management**: Use Git submodules; manage conflicts via `pyproject.toml`
- **GPU Memory**: VolETA requires 8GB+; FoodVolume preferred for 4GB
- **Data Format**: Adapt Nutrition5k RGBD pairs to external repo requirements
- **Testing**: Add integration tests for each external component

---

### ✅ Expected Outcome

Leveraging FoodSAM and VolETA/FoodVolume will transform your project into a robust, research-backed system. The result will be **state-of-the-art accuracy** in both segmentation and volume estimation, allowing you to focus your custom development on the final nutrition regression model—the component that delivers unique value to your users.

If you'd like to explore integrating any of these repositories further, let me know.