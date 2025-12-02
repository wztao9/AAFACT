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

def reorient(aligned_points, coords_aligned, original_centroid, R, T,
             side='left', RTs=None):
    """Reorient aligned points and coordinates back to original orientation.
    
    RTs is a dict mirroring MATLAB's RTs struct:
      - 'sR_talus': 3x3 or None
      - 'sT_tibia': 3x1 or None
      - 'sR_tibia': 3x3 or None
      - 'sT_fibula': 3x1 or None
      - 'sR_fibula': 3x3 or None
      - 'cm_meta': 1x3 or None (for metatarsals)
      - 'iflip': 3x3 (inverse of initial flip), default = I
      - 'red', 'yellow': 3x3 or None (for special talus rotation)
    """
    if RTs is None:
        RTs = {}

    sR_talus  = RTs.get('sR_talus',  None)
    sT_tibia  = RTs.get('sT_tibia',  None)
    sR_tibia  = RTs.get('sR_tibia',  None)
    sT_fibula = RTs.get('sT_fibula', None)
    sR_fibula = RTs.get('sR_fibula', None)
    cm_meta   = RTs.get('cm_meta',   None)
    iflip     = RTs.get('iflip',     np.eye(3))
    red       = RTs.get('red',       None)
    yellow    = RTs.get('yellow',    None)

    # Combine points and coordinates from aligned space
    Temp_Nodes_Coords = np.vstack([aligned_points, coords_aligned])

    # --- MATLAB reorient.m: first conditional block (sR_talus / tibia / fibula / cm_meta) ---
    # This operates in the aligned frame, before undoing main ICP R,T.
    if sR_talus is not None:
        # nodes_coords_final_i4 = inv(sR_talus) * Temp_Nodes_Coords'
        nodes_coords_final_i4 = (np.linalg.inv(sR_talus) @ Temp_Nodes_Coords.T).T
    elif sT_tibia is not None and sR_tibia is not None:
        # subtract sT_tibia, then apply inv(sR_tibia), then divide by sflip
        nodes_coords_final_i6 = (Temp_Nodes_Coords.T - sT_tibia.reshape(3, 1)).T
        nodes_coords_final_i5 = (np.linalg.inv(sR_tibia) @ nodes_coords_final_i6.T).T
        nodes_coords_final_i4 = (nodes_coords_final_i5 @ np.linalg.inv(iflip).T)
    elif sT_fibula is not None and sR_fibula is not None:
        # subtract sT_fibula, then apply inv(sR_fibula), then divide by sflip
        nodes_coords_final_i6 = (Temp_Nodes_Coords.T - sT_fibula.reshape(3, 1)).T
        nodes_coords_final_i5 = (np.linalg.inv(sR_fibula) @ nodes_coords_final_i6.T).T
        nodes_coords_final_i4 = (nodes_coords_final_i5 @ np.linalg.inv(iflip).T)
    elif cm_meta is not None:
        # undo metatarsal centering
        nodes_coords_final_i4 = Temp_Nodes_Coords + cm_meta.reshape(1, 3)
    else:
        nodes_coords_final_i4 = Temp_Nodes_Coords

    # --- Undo main ICP translation & rotation and initial flip (MATLAB iT, iR, iflip) ---
    R_inv = R.T
    # nodes_coords_final_i3 = nodes_coords_final_i4' - iT
    nodes_coords_final_i3 = (nodes_coords_final_i4.T - T.reshape(3, 1)).T
    # nodes_coords_final_i2 = inv(iR) * nodes_coords_final_i3'
    nodes_coords_final_i2 = (R_inv @ nodes_coords_final_i3.T).T
    # nodes_coords_final_i1 = nodes_coords_final_i2 / iflip
    nodes_coords_final_i1 = (nodes_coords_final_i2 @ np.linalg.inv(iflip).T)

    # --- Optional extra talus rotations red/yellow ---
    if red is not None:
        nodes_coords_final_i1_red = (np.linalg.inv(red) @ nodes_coords_final_i1.T).T
        if yellow is not None:
            nodes_coords_final_i1 = (np.linalg.inv(yellow) @ nodes_coords_final_i1_red.T).T
        else:
            nodes_coords_final_i1 = nodes_coords_final_i1_red

    # --- Re-center around origin as MATLAB does, then add back original centroid ---
    nodes_coords_final_i1, _ = center(nodes_coords_final_i1)
    nodes_coords_final = nodes_coords_final_i1 + original_centroid.reshape(1, 3)

    # Flip back to right side if needed
    if side == 'right':
        nodes_coords_final[:, 2] *= -1

    # Extract coordinates and units (same logic as MATLAB)
    coords_final_origin = nodes_coords_final[-2, :]   # row end-1 in MATLAB
    coords_final_temp = nodes_coords_final[-6:, :] - coords_final_origin
    coords_final_temp = np.vstack([
        [0, 0, 0], coords_final_temp[1] / np.linalg.norm(coords_final_temp[1]),
        [0, 0, 0], coords_final_temp[3] / np.linalg.norm(coords_final_temp[3]),
        [0, 0, 0], coords_final_temp[5] / np.linalg.norm(coords_final_temp[5]),
    ])
    coords_final_unit = coords_final_temp + coords_final_origin

    points_final = nodes_coords_final[:-6, :]
    coords_final = nodes_coords_final[-6:, :]

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
