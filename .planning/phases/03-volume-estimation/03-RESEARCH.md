# Phase 3 Research: Volume Estimation Integration

Research into lightweight volume estimation strategies suitable for 4GB VRAM hardware, focusing on the Hybrid Convex Hull / Alpha Shape approach.

## Standard Stack

- **Geometry Processing**: `scipy.spatial.ConvexHull` for basic volumes.
- **Concave Surface Modeling**: `alphashape` (Python package) for tighter fitting on complex food shapes (pasta, bowls).
- **Mesh Utils**: `trimesh` for calculating volume from Alpha Shape meshes.
- **Optimization**: `numpy` for vectorized point cloud operations.
- **Validation**: `matplotlib` or `open3d` (headless) for cross-section visualization.

## Architecture Patterns

### 1. RGBD to Point Cloud
- Convert masked pixel coordinates $(u, v)$ and depth $d$ into $(X, Y, Z)$ coordinates using camera intrinsics.
- $Z = d$
- $X = (u - c_x) \times Z / f_x$
- $Y = (v - c_y) \times Z / f_y$
- Use Nutrition5k overhead camera defaults: $f_x=f_y=617.0$, $c_x=320.0$, $c_y=240.0$ (standard Realsense D435).

### 2. Reference Plane Subtraction
- Volume must be measured relative to the "empty plate" or "tabletop" depth ($Z_{ref}$).
- For many samples, the average depth of the non-masked plate area can serve as $Z_{ref}$.
- Food height $h = Z_{ref} - Z_{food}$.

### 3. Hybrid Selection Logic
- **Convex Hull (CH)**: Fast, robust, but overestimates volume for concave shapes.
- **Alpha Shape (AS)**: Tight fit, accurately captures concavity, but sensitive to the $\alpha$ parameter.
- **Selection Rule**: Implement a density-based switcher. If $V_{AS} / V_{CH} < 0.6$, the food is likely concave (deep bowl), prefer AS. Otherwise, prefer CH for stability.

## Don't Hand-Roll

- **Alpha Shape Algorithm**: Use the `alphashape` library; don't attempt to implement Delaunay triangulation-based filtering manually.
- **Volume Calculations**: Use `hull.volume` or `mesh.volume`; avoid manual tetrahedron summation unless necessary for performance.

## Common Pitfalls

- **Floating Points**: Ensure all calculations use `float64` for volume accumulation to avoid precision loss on small pixel triangles.
- **Zero-Depth Inpainting**: Raw Realsense data has holes. Use `cv2.inpaint` (TELEA) on the depth map *before* point cloud generation.
- **Scale Confusion**: Always work in meters or centimeters. Nutrition5k volumes are ground-truthed in $cm^3$ (mL).

## Code Examples

### Point Cloud Projection
```python
def project_points(mask, depth, intrinsics):
    v, u = np.where(mask)
    z = depth[v, u]
    x = (u - intrinsics['cx']) * z / intrinsics['fx']
    y = (v - intrinsics['cy']) * z / intrinsics['fy']
    return np.column_stack((x, y, z))
```

### Volume Calculation
```python
from scipy.spatial import ConvexHull
import alphashape

def get_hybrid_volume(points):
    hull = ConvexHull(points)
    v_ch = hull.volume
    
    # Simple alpha shape
    alpha_shape = alphashape.alphashape(points, 2.0)
    v_as = alpha_shape.volume if hasattr(alpha_shape, 'volume') else v_ch
    
    return min(v_ch, v_as) # Example logic
```

## Confidence Levels

- **Geometric Logic**: HIGH. Well-understood computer vision problem.
- **Nutrition5k Intrinsics**: MEDIUM. Need to verify exact $c_x, c_y$ from dataset metadata if possible.
- **HW Feasibility**: HIGH. Geometry calculations are CPU-bound and very lightweight.
