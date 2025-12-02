"""AAFACT Python Pipeline - Automatic Anatomical Foot and Ankle Coordinate Toolbox."""

__version__ = '1.0.0'
__author__ = 'AAFACT Contributors'

from .icp import icp
from .coordinate_system import compute_coordinate_system
from .utils import center, reorient, normalize_coords
from .io_utils import load_bone_file, save_coordinates
from .pipeline import process_bone

__all__ = [
    'icp',
    'compute_coordinate_system',
    'center',
    'reorient',
    'normalize_coords',
    'load_bone_file',
    'save_coordinates',
    'process_bone',
]
