"""Joint origin calculation using ray-triangle intersection."""
import numpy as np


def ray_triangle_intersection(ray_origin, ray_direction, vertices, faces):
    """Find intersection points between a ray and triangular mesh.
    
    Args:
        ray_origin: 1x3 ray origin point
        ray_direction: 1x3 ray direction vector
        vertices: Nx3 mesh vertices
        faces: Mx3 mesh face indices
        
    Returns:
        intersect_points: Kx3 array of intersection points
    """
    # Möller–Trumbore intersection algorithm
    ray_direction = ray_direction / np.linalg.norm(ray_direction)
    epsilon = 1e-6
    
    intersections = []
    
    for face in faces:
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        h = np.cross(ray_direction, edge2)
        a = np.dot(edge1, h)
        
        if abs(a) < epsilon:
            continue  # Ray parallel to triangle
        
        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)
        
        if u < 0.0 or u > 1.0:
            continue
        
        q = np.cross(s, edge1)
        v = f * np.dot(ray_direction, q)
        
        if v < 0.0 or u + v > 1.0:
            continue
        
        t = f * np.dot(edge2, q)
        
        # Ray intersects triangle
        intersection_point = ray_origin + t * ray_direction
        intersections.append(intersection_point)
    
    if intersections:
        return np.array(intersections)
    else:
        return np.array([]).reshape(0, 3)


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
    
    # Find intersections
    intersections = ray_triangle_intersection(current_origin, axis_direction, 
                                              aligned_points, faces)
    
    # If no intersections found, try opposite direction for CheckSI/CheckML cases
    if len(intersections) == 0 and joint_type in ['tibiotalar_surface']:
        intersections = ray_triangle_intersection(current_origin, -axis_direction,
                                                  aligned_points, faces)
    
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
