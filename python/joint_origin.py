"""Joint origin calculation using ray-triangle intersection."""
import numpy as np
import trimesh



def compute_joint_origin(coords_aligned, aligned_points, faces, bone_type, 
                        joint_type, side='left'):
    """Compute joint origin by ray-triangle intersection.
    
    Args:
        coords_aligned: 6x3 coordinate system in aligned space
        aligned_points: Nx3 aligned bone vertices
        faces: Mx3 mesh face indices
        bone_type: Type of bone (e.g., 'talus')
        joint_type: Joint surface type (e.g., 'tibiotalar_surface')
        side: Laterality (left/right)
        
    Returns:
        joint_origin: 1x3 joint origin point
        coords_with_origin: 6x3 coordinate system translated to joint origin
    """
    # Determine axis of interest (AOI) based on bone type and joint type
    if bone_type == 'talus':
        if joint_type == 'talonavicular_surface':
            # Shoot ray in Anterior direction
            current_origin = coords_aligned[0]  # AP origin
            axis_direction = coords_aligned[1] - coords_aligned[0]  # AP direction
        elif joint_type == 'tibiotalar_surface':
            # Shoot ray in Superior direction
            current_origin = coords_aligned[2]  # SI origin
            axis_direction = coords_aligned[3] - coords_aligned[2]  # SI direction
        elif joint_type == 'subtalar_surface':
            # Shoot ray in Inferior direction
            current_origin = coords_aligned[2]  # SI origin
            axis_direction = -(coords_aligned[3] - coords_aligned[2])  # -SI direction
        else:
            # Center (default)
            return coords_aligned[0], coords_aligned
    else:
        # For other bones, implement as needed
        return coords_aligned[0], coords_aligned
    
    mesh = trimesh.Trimesh(vertices=aligned_points, faces=faces, process=False)
    locations, index_ray, index_tri = mesh.ray.intersects_location(
        ray_origins=current_origin[None, :],
        ray_directions=axis_direction[None, :]
    )
    intersections = locations
    
    if len(intersections) == 0:
        print(f"  Warning: No joint intersection found, using center origin")
        return coords_aligned[0], coords_aligned
    
    # Find closest intersection to the axis direction endpoint
    # (MATLAB finds the one with minimum distance to axis_direction)
    distances = np.linalg.norm(intersections - (current_origin + axis_direction), axis=1)
    closest_idx = np.argmin(distances)
    joint_origin = intersections[closest_idx]
    
    # Translate coordinate system to joint origin
    translation = joint_origin - coords_aligned[0]
    coords_with_origin = coords_aligned + translation
    
    return joint_origin, coords_with_origin
