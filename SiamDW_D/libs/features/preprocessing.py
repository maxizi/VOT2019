import cv2
import torch
import numpy as np
import torch.nn.functional as F

from torch.autograd import Variable

def numpy_to_torch(a: np.ndarray):
    return torch.from_numpy(a).float().permute(2, 0, 1).unsqueeze(0)


def torch_to_numpy(a: torch.Tensor):
    return a.squeeze(0).permute(1,2,0).numpy()

def sample_patch(im: torch.Tensor, pos: torch.Tensor, sample_sz: torch.Tensor, output_sz: torch.Tensor = None):
    """Sample an image patch.

    args:
        im: Image
        pos: center position of crop
        sample_sz: size to crop
        output_sz: size to resize to
    """

    # copy and convert
    posl = pos.long().clone()

    # Compute pre-downsampling factor
    if output_sz is not None:
        resize_factor = torch.min(sample_sz.float() / output_sz.float())
        df = int(max(int(resize_factor - 0.1), 1))
    else:
        df = int(1)

    sz = sample_sz.float() / df     # new size

    # Do downsampling
    if df > 1:
        os = posl % df              # offset
        posl = (posl - os) / df     # new position
        im2 = im[..., os[0]::df, os[1]::df]   # downsample
    else:
        im2 = im

    # compute size to crop
    szl = torch.max(sz.round(), torch.Tensor([2])).long()

    # Extract top and bottom coordinates
    tl = posl - (szl - 1)/2
    br = posl + szl/2

    # Get image patch
    im_patch = F.pad(im2, (-tl[1], br[1]- im2.shape[3] + 1, -tl[0], br[0] - im2.shape[2] + 1), 'replicate')

    if output_sz is None or (im_patch.shape[-2] == output_sz[0] and im_patch.shape[-1] == output_sz[1]):
        return im_patch

    # Resample
    im_patch = pytorch_interplote(im_patch, output_sz.long().tolist()[0])

    return im_patch

def pytorch_interplote(a, size):
    # a is a Variable
    temp = a.data.squeeze(0).numpy()
    temp = np.transpose(temp, (1, 2, 0))
    temp2 = cv2.resize(temp, (int(size), int(size)))
    temp3 = np.transpose(temp2, (2, 0, 1))
    return Variable(torch.from_numpy(temp3).unsqueeze(0).contiguous())
