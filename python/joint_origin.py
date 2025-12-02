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
    # Map AOI like MATLAB JointOrigin.m
    ao = None

    if bone_type == 'talus':
        if joint_type == 'talonavicular_surface':
            ao = ('ap', +1)   # Anterior
        elif joint_type == 'tibiotalar_surface':
            ao = ('si', +1)   # Superior
        elif joint_type == 'subtalar_surface':
            ao = ('si', -1)   # Inferior

    elif bone_type == 'calcaneus':
        if joint_type == 'calcaneocuboid_surface':
            ao = ('ap', +1)   # Anterior
        elif joint_type == 'subtalar_surface':
            ao = ('ap', +1)   # Anterior

    elif bone_type == 'navicular':
        if joint_type == 'talonavicular_surface':
            ao = ('ap', -1)   # Posterior
        elif joint_type == 'navicular-cuneiform_surface':
            ao = ('ap', +1)   # Anterior

    elif bone_type == 'cuboid':
        if joint_type == 'calcaneocuboid_surface':
            ao = ('ap', -1)   # Posterior

    elif bone_type == 'med_cuneiform':
        if joint_type == 'navicular-cuneiform_surface':
            ao = ('ap', -1)                 # Posterior
        elif joint_type == 'cuneiform-metatarsal_surface':
            ao = ('ap', +1)                 # Anterior
        elif joint_type == 'intercuneiform_surface':
            ao = ('ml', -1)    # Lateral

    elif bone_type == 'mid_cuneiform':
        if joint_type == 'navicular-cuneiform_surface':
            ao = ('ap', -1)                 # Posterior
        elif joint_type == 'cuneiform-metatarsal_surface':
            ao = ('ap', +1)                 # Anterior
        elif joint_type == 'medial_intercuneiform_surface':
            ao = ('ml', +1)     # Medial
        elif joint_type == 'lateral_intercuneiform_surface':
            ao = ('ml', -1)    # Lateral

    elif bone_type == 'lat_cuneiform':
        if joint_type == 'navicular-cuneiform_surface':
            ao = ('ap', -1)                 # Posterior
        elif joint_type == 'cuneiform-metatarsal_surface':
            ao = ('ap', +1)                 # Anterior
        elif joint_type == 'intercuneiform_surface':
            ao = ('ml', +1)     # Medial

    elif bone_type in ('metatarsal1','metatarsal2','metatarsal3',
                       'metatarsal4','metatarsal5'):
        if joint_type == 'posterior_metatarsal_surface':
            ao = ('ap', -1)                 # Posterior

    elif bone_type == 'tibia':
        if joint_type == 'tibiotalar_surface':
            ao = ('si', -1)                 # CheckSI (prefer Inferior; fallback handled below)

    elif bone_type == 'fibula':
        if joint_type == 'talofibular_surface':
            ao = ('ml', +1)     # CheckML (Medial; fallback handled below)

    else:
        return coords_aligned[0], coords_aligned  # Center

    if ao is None:
        return coords_aligned[0], coords_aligned

    # Build origin and direction from coords_aligned
    axis, sign = ao
    if axis == 'ap':
        origin = coords_aligned[0]
        vec = coords_aligned[1] - coords_aligned[0]
    elif axis == 'si':
        origin = coords_aligned[2]
        vec = coords_aligned[3] - coords_aligned[2]
    elif axis == 'ml':
        origin = coords_aligned[4]
        vec = coords_aligned[5] - coords_aligned[4]
    else:
        return coords_aligned[0], coords_aligned

    dir_vec = sign * vec
    if np.linalg.norm(dir_vec) == 0:
        return coords_aligned[0], coords_aligned

    # Emulate MATLAB lineType='line': cast both +dir and -dir, pick best
    mesh = trimesh.Trimesh(vertices=aligned_points, faces=faces, process=False)
    dirs = np.vstack([dir_vec, -dir_vec]) / np.linalg.norm(dir_vec)
    origins = np.vstack([origin, origin])

    locations, _, _ = mesh.ray.intersects_location(
        ray_origins=origins,
        ray_directions=dirs
    )
    if len(locations) == 0:
        # Optional fallback: try only the intended direction
        locations, _, _ = mesh.ray.intersects_location(
            ray_origins=origin[None, :],
            ray_directions=(dir_vec / np.linalg.norm(dir_vec))[None, :]
        )
    if len(locations) == 0:
        # As in MATLAB, keep center if no hit
        return coords_aligned[0], coords_aligned

    # Choose intersection closest to axis endpoint (MATLAB logic)
    endpoint = origin + dir_vec
    d = np.linalg.norm(locations - endpoint, axis=1)
    joint_origin = locations[np.argmin(d)]

    # Translate CS to joint origin
    translation = joint_origin - coords_aligned[0]
    coords_with_origin = coords_aligned + translation
    return joint_origin, coords_with_origin
