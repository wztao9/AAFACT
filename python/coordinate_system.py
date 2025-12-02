"""Coordinate system calculation module."""
import numpy as np


def compute_coordinate_system(nodes, bone_type='talus', side='left', coord_sys='default'):
    """Compute anatomical coordinate system for aligned bone.
    
    Args:
        nodes: Nx3 aligned bone point cloud
        bone_type: Type of bone (talus, calcaneus, navicular, etc.)
        side: Laterality (left/right)
        coord_sys: Coordinate system type (default, tibiotalar, subtalar, etc.)
        
    Returns:
        coords: 6x3 array of coordinate system points (origin + 3 axis endpoints)
    """
    # Remove zero rows
    nodes_original = nodes[~np.all(nodes == 0, axis=1)]
    nodes = nodes_original.copy()
    
    # Special handling for TT CS (Tibiotalar) and ST CS (Subtalar) of talus
    if bone_type == 'talus' and coord_sys in ['tibiotalar', 'subtalar']:
        # Filter nodes with y < 10 for TT/ST coordinate systems
        # Note: This is a hardcoded value from MATLAB that may not scale well
        mask = nodes[:, 1] < 10
        nodes = nodes[mask]
    
    # Special handling for tibia - remove tibial plafond and shorten
    if bone_type == 'tibia':
        z_min = nodes[:, 2].min()
        cutting_plane = z_min + 14  # Removes tibial plafond
        cutting_plane2 = z_min + 100  # Shortens the tibia
        mask = (nodes[:, 2] > cutting_plane) & (nodes[:, 2] < cutting_plane2)
        nodes = nodes[mask]
    
    # Determine number of sections based on bone type
    n_sections = {'talus': 3, 'calcaneus': 10, 'navicular': 5, 'cuboid': 5,
                  'cuneiform': 3, 'metatarsal': 3, 'tibia': 3, 'fibula': 3}
    n = n_sections.get(bone_type, 3)
    
    # Get bone bounds
    mins = nodes.min(axis=0)
    maxs = nodes.max(axis=0)
    ranges = maxs - mins
    nth = ranges / n
    
    # Extract regions of interest
    if bone_type in ['navicular']:
        # Use X axis as primary
        pos_mask = nodes[:, 0] >= maxs[0] - nth[0]
        neg_mask = nodes[:, 0] <= mins[0] + nth[0]
        sup_mask = nodes[:, 2] >= maxs[2] - nth[2]
        pos_roi = nodes[pos_mask]
        neg_roi = nodes[neg_mask]
        sup_roi = nodes[sup_mask]
        first_point = pos_roi.mean(axis=0)
        second_point = neg_roi.mean(axis=0)
        third_point = sup_roi.mean(axis=0)
    elif bone_type in ['tibia', 'fibula']:
        # Use Z axis as primary
        pos_mask = nodes[:, 2] >= maxs[2] - nth[2]
        neg_mask = nodes[:, 2] <= mins[2] + nth[2]
        neg_x_mask = nodes[:, 0] <= mins[0] + nth[0]
        pos_roi = nodes[pos_mask]
        neg_roi = nodes[neg_mask]
        neg_x_roi = nodes[neg_x_mask]
        first_point = pos_roi.mean(axis=0)
        second_point = neg_roi.mean(axis=0)
        third_point = neg_x_roi.mean(axis=0)
        if second_point[2] > third_point[2]:
            third_point = third_point.copy()
            third_point[2] = 0
    else:
        # Use Y axis as primary (most bones)
        pos_mask = nodes[:, 1] >= maxs[1] - nth[1]
        neg_mask = nodes[:, 1] <= mins[1] + nth[1]
        sup_mask = nodes[:, 2] >= maxs[2] - nth[2]
        pos_roi = nodes[pos_mask]
        neg_roi = nodes[neg_mask]
        sup_roi = nodes[sup_mask]
        first_point = pos_roi.mean(axis=0)
        second_point = neg_roi.mean(axis=0)
        third_point = sup_roi.mean(axis=0)
    
    # Compute orthogonal coordinate system
    origin = np.array([0, 0, 0])
    
    # Primary axis
    primary = first_point - second_point
    primary_unit = primary / np.linalg.norm(primary)
    
    # Project third point onto primary axis
    proj_length = np.dot(third_point - second_point, primary_unit)
    closest_point = second_point + proj_length * primary_unit
    
    # Secondary axis (orthogonal to primary)
    secondary = third_point - closest_point
    secondary_unit = secondary / np.linalg.norm(secondary)
    
    # Tertiary axis (cross product)
    tertiary_unit = np.cross(primary_unit, secondary_unit)
    tertiary_unit = tertiary_unit / np.linalg.norm(tertiary_unit)
    
    # Assign to anatomical directions based on bone type
    ml_factor = -1 if side == 'right' else 1
    
    if bone_type == 'navicular':
        ML = ml_factor * primary_unit * 50
        SI = secondary_unit * 50
        AP = -tertiary_unit * 50
    elif bone_type in ['tibia', 'fibula']:
        SI = primary_unit * 50
        ML = -ml_factor * secondary_unit * 50
        AP = -tertiary_unit * 50
    else:
        AP = primary_unit * 50
        SI = secondary_unit * 50
        ML = ml_factor * tertiary_unit * 50
    
    # Build coordinate system
    coords = np.array([
        origin, origin + AP,
        origin, origin + SI,
        origin, origin + ML
    ])
    
    return coords
