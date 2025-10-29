"""Utility functions for AAFACT pipeline."""
import numpy as np


def center(points):
    """Center point cloud at origin.
    
    Args:
        points: Nx3 point cloud
        
    Returns:
        centered: Centered point cloud
        centroid: Original centroid
    """
    centroid = points.mean(axis=0)
    centered = points - centroid
    return centered, centroid


def reorient(aligned_points, coords_aligned, original_centroid, R, T, side='left'):
    """Reorient aligned points and coordinates back to original orientation.
    
    Args:
        aligned_points: Nx3 aligned point cloud
        coords_aligned: 6x3 aligned coordinate system
        original_centroid: Original centroid before alignment
        R: Rotation matrix from ICP
        T: Translation vector from ICP
        side: Laterality (left/right)
        
    Returns:
        points_final: Points in original orientation
        coords_final: Coordinates in original orientation
    """
    # Combine points and coordinates
    combined = np.vstack([aligned_points, coords_aligned])
    
    # Inverse transform
    R_inv = R.T
    combined_inv = (R_inv @ (combined - T.T).T).T
    
    # Add back original centroid
    combined_final = combined_inv + original_centroid
    
    # Flip back if right side
    if side == 'right':
        combined_final[:, 2] *= -1
    
    # Split back
    points_final = combined_final[:-6]
    coords_final = combined_final[-6:]
    
    return points_final, coords_final


def normalize_coords(coords):
    """Normalize coordinate system to unit vectors.
    
    Args:
        coords: 6x3 coordinate system (origin + 3 axis endpoints)
        
    Returns:
        coords_unit: Normalized coordinates
    """
    origin = coords[0]
    coords_centered = coords - origin
    
    # Normalize each axis
    coords_unit = np.zeros_like(coords)
    coords_unit[0] = origin
    coords_unit[1] = origin + coords_centered[1] / np.linalg.norm(coords_centered[1])
    coords_unit[2] = origin
    coords_unit[3] = origin + coords_centered[3] / np.linalg.norm(coords_centered[3])
    coords_unit[4] = origin
    coords_unit[5] = origin + coords_centered[5] / np.linalg.norm(coords_centered[5])
    
    return coords_unit
