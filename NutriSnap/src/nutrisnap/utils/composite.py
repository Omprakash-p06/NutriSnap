import torch


def create_composite_image(
    rgb_tensor, mask_tensor, depth_tensor, alpha_compositing=True
):
    """
    Creates a 5-channel composite image from RGB, Mask, and Depth tensors.

    Args:
        rgb_tensor (torch.Tensor): (3, 224, 224) RGB image, normalized.
        mask_tensor (torch.Tensor): (1, 224, 224) Binary mask (0 or 1).
        depth_tensor (torch.Tensor): (1, 224, 224) Depth map, normalized [0, 1].
        alpha_compositing (bool): If True, multiply RGB and Depth by Mask
                                  to clear background.

    Returns:
        torch.Tensor: (5, 224, 224) Composite tensor.
    """
    if alpha_compositing:
        rgb_tensor = rgb_tensor * mask_tensor
        depth_tensor = depth_tensor * mask_tensor

    return torch.cat([rgb_tensor, mask_tensor, depth_tensor], dim=0)
