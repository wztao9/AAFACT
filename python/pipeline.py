"""Main AAFACT pipeline for automatic anatomical coordinate system assignment."""
import numpy as np
import os
from icp import icp
from coordinate_system import compute_coordinate_system
from utils import center, reorient, normalize_coords
from io_utils import load_bone_file, load_stl, save_coordinates


def align_to_template(bone_points, template_points, max_iterations=200, bone_type='talus', coord_sys=None):
    """Align bone to template using ICP with multiple initial rotations.
    
    Args:
        bone_points: Nx3 bone point cloud
        template_points: Mx3 template point cloud
        max_iterations: Maximum ICP iterations
        secondary_template: Optional secondary template for additional alignment (e.g., TT/ST talus)
        bone_type: Type of bone (for determining scaling axis)
        
    Returns:
        aligned_points: Aligned bone point cloud
        R: Best rotation matrix
        T: Best translation vector
        sR: Secondary rotation (if secondary_template provided)
    """

    # Creates similar sized models for cropped tibia or fibula
    tibfib_switch = 1  # default: over 1/5 tibia/fibula is available

    if bone_type in ('tibia', 'fibula'):
        # In MATLAB, 'a' is the axis used for template length (here Z, index 2)
        a = 2  # Z axis
        # Approximate "max_nodes_length" = max span over all axes for bone_points
        max_nodes_x = bone_points[:, 0].max() - bone_points[:, 0].min()
        max_nodes_y = bone_points[:, 1].max() - bone_points[:, 1].min()
        max_nodes_z = bone_points[:, 2].max() - bone_points[:, 2].min()
        max_nodes_length = max(max_nodes_x, max_nodes_y, max_nodes_z)

        nodes_template = template_points.copy()
        nodes_template_length = nodes_template[:, a].max() - nodes_template[:, a].min()

        # MATLAB: if nodes_template_length/1.5 > max_nodes_length
        if nodes_template_length / 1.5 > max_nodes_length:
            # Crop template to same length as input along axis 'a'
            min_a = nodes_template[:, a].min()
            cutoff = min_a + max_nodes_length

            # NOTE: MATLAB code uses nodes_template(:,3) < ..., but with a=3 (Z).
            # We keep the same semantics: threshold along Z.
            z = nodes_template[:, 2]
            mask = z < cutoff
            nodes_template = nodes_template[mask, :]

            # Build helper plane at the "cut" level
            # MATLAB hard-codes x = (-20:4:10), y = (-10:4:20), z = cutoff
            xs = np.arange(-20.0, 10.0 + 1e-6, 4.0)
            ys = np.arange(-10.0, 20.0 + 1e-6, 4.0)
            X, Y = np.meshgrid(xs, ys)
            Z = np.full_like(X, cutoff, dtype=float)

            plane = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

            # Append plane to template points
            nodes_template = np.vstack([nodes_template, plane])

            # Optional centering of template for bone_coord == 1 in MATLAB:
            # we skip that here because pipeline.py doesn't pass bone_coord.
            # If needed you can add a flag or a separate align_to_template_tibia variant.
            if coord_sys not in ['tibiotalar', 'talofibular']:
                nodes_template = center(nodes_template)[0]

            # Check how short input is relative to template
            if nodes_template_length / 5.0 > max_nodes_length:
                tibfib_switch = 2  # under 1/5 tibia/fibula is available (very short)
            else:
                tibfib_switch = 1
        else:
            tibfib_switch = 1

        # Overwrite template_points with cropped+plane version
        template_points = nodes_template
    

    # Determine the axis to use for size comparison (matching MATLAB's 'a' variable)
    # Default is Y axis (index 1), but navicular and cuneiforms use different axes
    if bone_type in ['navicular']:
        axis = 0  # X axis
    elif bone_type in ['cuneiform']:
        axis = 2  # Z axis
    else:
        axis = 1  # Y axis (default for most bones)
    
    # Calculate size multiplier to scale bone to template size for better ICP accuracy
    # MATLAB: multiplier = (max(nodes_template(:,a)) - min(nodes_template(:,a)))/(max(nodes(:,b)) - min(nodes(:,b)))
    template_range = template_points[:, axis].max() - template_points[:, axis].min()
    bone_range = bone_points[:, axis].max() - bone_points[:, axis].min()
    # multiplier = template_range / bone_range if bone_range > 0 else 1.0
    st = ((template_points - template_points.mean(axis=0, keepdims=True))**2).mean()**0.5
    sb = ((bone_points - bone_points.mean(axis=0, keepdims=True))**2).mean()**0.5
    multiplier = st / sb

    # Scale bone if it's smaller than template (multiplier > 1)
    scaled_points = bone_points.copy()
    # if multiplier > 1:
    scaled_points = bone_points * multiplier
    
    # Try multiple initial rotations
    # NOTE that we assume the identity rotation is best, i.e., the bone is roughly aligned already
    rotations = [
        np.eye(3),
        # np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]),  # 90° around X
        # np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]]),  # 180° around X
        # np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),  # 90° around Y
        # np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]]),  # 90° around Z
    ]
    
    best_error = float('inf')
    best_R, best_T, best_aligned = None, None, None
    
    for rot in rotations:
        rotated = (rot @ scaled_points.T).T
        R, T, aligned = icp(template_points, rotated, max_iterations=max_iterations)
        
        # Compute error
        from scipy.spatial import KDTree
        tree = KDTree(template_points)
        distances, _ = tree.query(aligned)
        error = np.mean(distances)
        
        if error < best_error:
            best_error = error
            best_R = R @ rot
            best_T = T
            best_aligned = aligned
    
    # If secondary template provided (for TT/ST talus), do additional alignment
    sR = {
        'sR_tibia': None,
        'sT_tibia': None,
        'sR_fibula': None,
        'sT_fibula': None,
    }
    # if secondary_template is not None:
    #     # Align primary template to secondary template
    #     # MATLAB: icp(nodes_template2', nodes_template', ...) aligns template to template2
    #     sR, sT, best_aligned = icp(secondary_template, template_points, max_iterations=25)
    #     # Apply this rotation to the aligned points
    #     best_aligned = (sR @ best_aligned.T).T

    
    # Undo the scaling (scale back down to original size)
    # if multiplier > 1:
    best_aligned = best_aligned / multiplier
    
    
    sR_tibia = None
    sT_tibia = None
    sR_fibula = None
    sT_fibula = None
    sflip = np.eye(3)

    # --- Fibula TF centering (MATLAB "This ensures the fibular coordinate system is at the center of the TF joint") ---
    if tibfib_switch == 1 and bone_type == 'fibula':
        aligned_nodes = best_aligned.copy()
        nodes_template = template_points  # cropped+plane template

        max_nodes_x = aligned_nodes[:, 0].max() - aligned_nodes[:, 0].min()
        max_nodes_y = aligned_nodes[:, 1].max() - aligned_nodes[:, 1].min()

        if max_nodes_x < max_nodes_y:
            parttib_multiplier = ((nodes_template[:, 0].max() - nodes_template[:, 0].min()) /
                                  (aligned_nodes[:, 0].max() - aligned_nodes[:, 0].min()))
            aligned_nodes_temp = aligned_nodes * parttib_multiplier
        else:
            parttib_multiplier = ((nodes_template[:, 1].max() - nodes_template[:, 1].min()) /
                                  (aligned_nodes[:, 1].max() - aligned_nodes[:, 1].min()))
            aligned_nodes_temp = aligned_nodes * parttib_multiplier

        # Secondary ICP: template -> aligned_nodes_temp
        # from icp import icp as icp_func
        sR_fibula, sT_fibula, aligned_nodes2 = icp(nodes_template, aligned_nodes_temp, max_iterations=2500)

        # Apply secondary rotation to original aligned nodes
        aligned_nodes = (sR_fibula @ aligned_nodes.T).T

        # Find TF center in a distal band (z < 20 mm), then shift to that center
        sub = aligned_nodes[aligned_nodes[:, 2] < 20.0, :]
        if sub.size > 0:
            minY = sub[:, 1].min()
            maxY = sub[:, 1].max()
            centerY = np.round((minY + maxY) / 2.0)
            bandMask = np.abs(sub[:, 1] - centerY) <= 2.0
            cand = sub[bandMask, :]
            if cand.size > 0:
                k = np.argmax(cand[:, 0])
                Xp = cand[k, :]
                aligned_nodes[:, 0] -= Xp[0]
                aligned_nodes[:, 1] -= Xp[1]
                sT_fibula = np.array([-Xp[0], -Xp[1], 0.0])
            else:
                sT_fibula = np.zeros(3)
        else:
            sT_fibula = np.zeros(3)

        best_aligned = aligned_nodes
        # sflip remains identity for fibula in MATLAB

    # --- Tibial plafond centering (MATLAB "This ensures the tibial coordinate system is at the center of the tibial plafond") ---
    if tibfib_switch == 1 and bone_type == 'tibia':
        aligned_nodes = best_aligned.copy()
        nodes_template = template_points  # cropped+plane template
        iterations = max_iterations

        # Distal part (z < 150)
        mask = aligned_nodes[:, 2] < 150.0
        nodes_test = aligned_nodes[mask, :]

        # Build helper plane at distal plafond
        xs = np.arange(-20.0, 20.0 + 1e-6, 4.0)
        ys = np.arange(-20.0, 20.0 + 1e-6, 4.0)
        X, Y = np.meshgrid(xs, ys)
        z_plane = nodes_test[:, 2].max() if nodes_test.size > 0 else aligned_nodes[:, 2].max()
        Z = np.full_like(X, z_plane, dtype=float)
        plane = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

        nodes_test1 = np.vstack([nodes_test, plane])
        # Generate rotated versions around Z
        def rotz(angle_deg):
            ang = np.deg2rad(angle_deg)
            c, s = np.cos(ang), np.sin(ang)
            return np.array([[c, -s, 0],
                             [s,  c, 0],
                             [0,  0, 1]])

        nodes_test2 = (rotz(90) @ nodes_test1.T).T
        nodes_test3 = (rotz(180) @ nodes_test1.T).T
        nodes_test4 = (rotz(270) @ nodes_test1.T).T

        from icp import icp as icp_func
        Rtw1, Ttw1, _ = icp_func(nodes_template, nodes_test1, max_iterations=iterations)
        Rtw2, Ttw2, _ = icp_func(nodes_template, nodes_test2, max_iterations=iterations)
        Rtw3, Ttw3, _ = icp_func(nodes_template, nodes_test3, max_iterations=iterations)
        Rtw4, Ttw4, _ = icp_func(nodes_template, nodes_test4, max_iterations=iterations)

        # For simplicity, just pick the best by ICP RMSE (you can compute RMSE via KDTree if needed)
        # Here, we'll just select Rtw1 as MATLAB does when better_start==0,
        # or you can extend with an error comparison.
        sflip = np.eye(3)
        sR_tibia = Rtw1
        sT_tibia = Ttw1
        aligned_nodes = (sR_tibia @ aligned_nodes.T).T + sT_tibia.reshape(1, 3)

        best_aligned = aligned_nodes
    sR['sR_tibia'] = sR_tibia
    sR['sT_tibia'] = sT_tibia
    sR['sR_fibula'] = sR_fibula
    sR['sT_fibula'] = sT_fibula

    return best_aligned, best_R, best_T, sR


def process_bone(bone_file, bone_type='talus', side='left', 
                 coord_sys='default', joint_origin='center', template_dir=None, output_dir='output'):
    """Process a single bone and compute anatomical coordinate system.
    
    Args:
        bone_file: Path to bone model file
        bone_type: Type of bone
        side: Laterality (left/right)
        coord_sys: Coordinate system type (default, tibiotalar, subtalar, etc.)
        joint_origin: Origin type ('center', 'tibiotalar_surface', 'talonavicular_surface', etc.)
        template_dir: Directory containing template files (default: ../Template_Bones relative to script)
        output_dir: Output directory for results
        
    Returns:
        coords_original: Coordinate system in original space
        coords_unit: Unit coordinate system
        coords_aligned_unit: Aligned coordinate system
    """
    print(f"Processing {bone_type} ({side})...")
    
    # Determine template directory if not provided
    if template_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(os.path.dirname(script_dir), 'Template_Bones')
    
    # Determine which template(s) to use based on bone_type and coord_sys
    template_file = None
    secondary_template_file = None
    
    if bone_type == 'talus':
        if coord_sys in ['default', 'talonavicular']:
            template_file = os.path.join(template_dir, 'Talus_Template.stl')
        elif coord_sys in ['tibiotalar', 'subtalar']:
            template_file = os.path.join(template_dir, 'Talus_Template.stl')
            secondary_template_file = os.path.join(template_dir, 'Talus_Template2.stl')
    elif bone_type == 'calcaneus':
        if coord_sys in ['default', 'calcaneocuboid']:
            template_file = os.path.join(template_dir, 'Calcaneus_Template.stl')
        elif coord_sys == 'subtalar':
            template_file = os.path.join(template_dir, 'Calcaneus_Template2.stl')
    elif bone_type == 'navicular':
        template_file = os.path.join(template_dir, 'Navicular_Template.stl')
    elif bone_type == 'cuboid':
        if coord_sys == 'default':
            template_file = os.path.join(template_dir, 'Cuboid_Template.stl')
        elif coord_sys == 'radial':
            template_file = os.path.join(template_dir, 'Cuboid_Template2.stl')
        elif coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Cuboid_Template.stl')
        else:
            template_file = os.path.join(template_dir, 'Cuboid_Template.stl')
    elif bone_type == 'lat_cuneiform':
        if coord_sys == 'default':
            template_file = os.path.join(template_dir, 'Lateral_Cuneiform_Template.stl')
        elif coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Lateral_Cuneiform_Template.stl')
        elif coord_sys == 'radial':
            template_file = os.path.join(template_dir, 'Lateral_Cuneiform_Template2.stl')
        else:
            template_file = os.path.join(template_dir, 'Lateral_Cuneiform_Template.stl')
    elif bone_type == 'med_cuneiform':
        template_file = os.path.join(template_dir, 'Medial_Cuneiform_Template.stl')
    elif bone_type == 'mid_cuneiform':
        template_file = os.path.join(template_dir, 'Intermediate_Cuneiform_Template.stl')
    elif bone_type == 'tibia':
        if joint_origin == 'tibiotalar_surface':
            coord_sys = 'tibiotalar'
            template_file = os.path.join(template_dir, 'Tibia_Template_Facet.stl')
        else:
            template_file = os.path.join(template_dir, 'Tibia_Template.stl')
            coord_sys = 'default'
    elif bone_type == 'fibula':
        if joint_origin == 'talofibular_surface':
            coord_sys = 'talofibular'
            template_file = os.path.join(template_dir, 'Fibula_Template_Facet.stl')
        else:
            template_file = os.path.join(template_dir, 'Fibula_Template.stl')
            coord_sys = 'default'
    elif bone_type == 'metatarsal1':
        if coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Metatarsal1_Template.stl')
        else:
            template_file = os.path.join(template_dir, 'Metatarsal1_Template2.stl')
    elif bone_type == 'metatarsal2':
        if coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Metatarsal2_Template.stl')
        else:
            template_file = os.path.join(template_dir, 'Metatarsal2_Template2.stl')
    elif bone_type == 'metatarsal3':
        if coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Metatarsal3_Template.stl')
        else:
            template_file = os.path.join(template_dir, 'Metatarsal3_Template2.stl')
    elif bone_type == 'metatarsal4':
        if coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Metatarsal4_Template.stl')
        else:
            template_file = os.path.join(template_dir, 'Metatarsal4_Template2.stl')
    elif bone_type == 'metatarsal5':
        if coord_sys == 'vertical':
            template_file = os.path.join(template_dir, 'Metatarsal5_Template.stl')
        else:
            template_file = os.path.join(template_dir, 'Metatarsal5_Template2.stl')
    else:
        raise ValueError(f"Unknown bone type: {bone_type}")
    
    if not os.path.exists(template_file):
        raise FileNotFoundError(f"Template file not found: {template_file}")
    
    # Load bone and template
    bone_points, bone_faces = load_bone_file(bone_file)
    template_points, template_faces = load_stl(template_file)
    
    # Load secondary template if needed
    secondary_template = None
    if secondary_template_file and os.path.exists(secondary_template_file):
        secondary_template, _ = load_stl(secondary_template_file)
    
    # Flip right bones to left for processing
    if side == 'right':
        bone_points[:, 2] *= -1
    
    # Center the bone
    bone_centered, original_centroid = center(bone_points)
    
    os.makedirs(output_dir, exist_ok=True)
    # Save centered bone for debugging, use name, chosen coordinate system coord_sys for filename
    # import trimesh
    # m = trimesh.Trimesh(vertices=bone_centered, faces=bone_faces)
    # m.export(os.path.join(output_dir, f"{os.path.splitext(os.path.basename(bone_file))[0].split('_')[0]}_{coord_sys}_beforeicp_py.stl"))
    
    # Align to template
    print("  Aligning to template...")
    aligned_points, R, T, sR = align_to_template(bone_centered, secondary_template if (secondary_template is not None) else template_points, 
                                                   bone_type=bone_type, coord_sys=coord_sys)
    # # save aligned bone for debugging
    # m_aligned = trimesh.Trimesh(vertices=aligned_points, faces=bone_faces)
    # m_aligned.export(os.path.join(output_dir, f"{os.path.splitext(os.path.basename(bone_file))[0].split('_')[0]}_{coord_sys}_aftericp_py.stl"))

    # Compute coordinate system
    print("  Computing coordinate system...")
    coords_aligned = compute_coordinate_system(aligned_points, bone_type, side, coord_sys)
    
    # Apply joint origin if specified
    if joint_origin != 'center':
        print(f"  Computing joint origin: {joint_origin}...")
        from joint_origin import compute_joint_origin
        joint_origin_point, coords_aligned = compute_joint_origin(
            coords_aligned, aligned_points, bone_faces, bone_type, joint_origin, side
        )
    
    # Normalize aligned coordinates (at 0,0,0)
    coords_aligned_unit = normalize_coords(coords_aligned)
    
    # Reorient back to original space
    print("  Reorienting to original space...")
    points_final, coords_final = reorient(aligned_points, coords_aligned, 
                                          original_centroid, R, T, side, sR)
    
    # Normalize coordinates in original orientation
    coords_unit = normalize_coords(coords_final)
    
    # Save results
    subject_name = os.path.splitext(os.path.basename(bone_file))[0]
    output_file = os.path.join(output_dir, f"{bone_type}_{side}_coords.csv")
    
    # Format joint type for display
    joint_type_display = joint_origin.replace('_', ' ').title() if joint_origin != 'center' else 'Center'
    
    save_coordinates(output_file, coords_final, coords_unit, coords_aligned_unit, 
                    bone_type, side, subject_name, joint_type_display)
    print(f"  Saved to {output_file}")
    
    return coords_final, coords_unit, coords_aligned_unit


def main():
    """Main pipeline with hardcoded examples."""
    # Example configurations (hardcoded)
    examples = [
        {
            'bone_file': 'path/to/talus_left.stl',  # Replace with actual absolute path
            'bone_type': 'talus',
            'side': 'left'
        },
        {
            'bone_file': 'path/to/calcaneus_right.stl',  # Replace with actual absolute path
            'bone_type': 'calcaneus',
            'side': 'right'
        },
    ]
    
    # Process each bone
    for config in examples:
        if os.path.exists(config['bone_file']):
            try:
                coords, coords_unit = process_bone(**config)
                print(f"✓ Successfully processed {config['bone_type']} ({config['side']})")
            except Exception as e:
                print(f"✗ Error processing {config['bone_type']} ({config['side']}): {e}")
        else:
            print(f"⚠ Skipping {config['bone_type']} - file not found: {config['bone_file']}")
    
    print("\nPipeline complete!")


if __name__ == '__main__':
    main()
