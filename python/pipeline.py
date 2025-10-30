"""Main AAFACT pipeline for automatic anatomical coordinate system assignment."""
import numpy as np
import os
from icp import icp
from coordinate_system import compute_coordinate_system
from utils import center, reorient, normalize_coords
from io_utils import load_bone_file, load_stl, save_coordinates


def align_to_template(bone_points, template_points, max_iterations=200, secondary_template=None):
    """Align bone to template using ICP with multiple initial rotations.
    
    Args:
        bone_points: Nx3 bone point cloud
        template_points: Mx3 template point cloud
        max_iterations: Maximum ICP iterations
        secondary_template: Optional secondary template for additional alignment (e.g., TT/ST talus)
        
    Returns:
        aligned_points: Aligned bone point cloud
        R: Best rotation matrix
        T: Best translation vector
        sR: Secondary rotation (if secondary_template provided)
    """
    # Try multiple initial rotations
    rotations = [
        np.eye(3),
        np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]),  # 90° around X
        np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]]),  # 180° around X
        np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),  # 90° around Y
        np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]]),  # 90° around Z
    ]
    
    best_error = float('inf')
    best_R, best_T, best_aligned = None, None, None
    
    for rot in rotations:
        rotated = (rot @ bone_points.T).T
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
    sR = None
    if secondary_template is not None:
        # Align primary template to secondary template
        # MATLAB: icp(nodes_template2', nodes_template', ...) aligns template to template2
        sR, _, _ = icp(secondary_template, template_points, max_iterations=25)
        # Apply this rotation to the aligned points
        best_aligned = (sR @ best_aligned.T).T
    
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
        else:
            template_file = os.path.join(template_dir, 'Cuboid_Template2.stl')
    elif bone_type == 'cuneiform':
        # Would need more specific handling for medial/intermediate/lateral
        template_file = os.path.join(template_dir, 'Medial_Cuneiform_Template.stl')
    elif bone_type == 'metatarsal':
        # Would need more specific handling for MT1-MT5
        template_file = os.path.join(template_dir, 'Metatarsal1_Template.stl')
    elif bone_type == 'tibia':
        template_file = os.path.join(template_dir, 'Tibia_Template.stl')
    elif bone_type == 'fibula':
        template_file = os.path.join(template_dir, 'Fibula_Template.stl')
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
    
    # Align to template
    print("  Aligning to template...")
    aligned_points, R, T, sR = align_to_template(bone_centered, template_points, 
                                                   secondary_template=secondary_template)
    
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
    os.makedirs(output_dir, exist_ok=True)
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
