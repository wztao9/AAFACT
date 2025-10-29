"""Main AAFACT pipeline for automatic anatomical coordinate system assignment."""
import numpy as np
import os
from icp import icp
from coordinate_system import compute_coordinate_system
from utils import center, reorient, normalize_coords
from io_utils import load_bone_file, load_stl, save_coordinates


def align_to_template(bone_points, template_points, max_iterations=200):
    """Align bone to template using ICP with multiple initial rotations.
    
    Args:
        bone_points: Nx3 bone point cloud
        template_points: Mx3 template point cloud
        max_iterations: Maximum ICP iterations
        
    Returns:
        aligned_points: Aligned bone point cloud
        R: Best rotation matrix
        T: Best translation vector
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
    
    return best_aligned, best_R, best_T


def process_bone(bone_file, template_file, bone_type='talus', side='left', output_dir='output'):
    """Process a single bone and compute anatomical coordinate system.
    
    Args:
        bone_file: Path to bone model file
        template_file: Path to template bone file
        bone_type: Type of bone
        side: Laterality (left/right)
        output_dir: Output directory for results
        
    Returns:
        coords_original: Coordinate system in original space
        coords_unit: Unit coordinate system
    """
    print(f"Processing {bone_type} ({side})...")
    
    # Load bone and template
    bone_points = load_bone_file(bone_file)
    template_points = load_stl(template_file)
    
    # Flip right bones to left for processing
    if side == 'right':
        bone_points[:, 2] *= -1
    
    # Center the bone
    bone_centered, original_centroid = center(bone_points)
    
    # Align to template
    print("  Aligning to template...")
    aligned_points, R, T = align_to_template(bone_centered, template_points)
    
    # Compute coordinate system
    print("  Computing coordinate system...")
    coords_aligned = compute_coordinate_system(aligned_points, bone_type, side)
    
    # Reorient back to original space
    print("  Reorienting to original space...")
    points_final, coords_final = reorient(aligned_points, coords_aligned, 
                                          original_centroid, R, T, side)
    
    # Normalize coordinates
    coords_unit = normalize_coords(coords_final)
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{bone_type}_{side}_coords.csv")
    save_coordinates(output_file, coords_final, bone_type, side)
    print(f"  Saved to {output_file}")
    
    return coords_final, coords_unit


def main():
    """Main pipeline with hardcoded examples."""
    # Configuration - MODIFY THESE FOR YOUR DATA
    template_dir = '../Template_Bones'
    
    # Example configurations (hardcoded)
    examples = [
        {
            'bone_file': 'path/to/talus_left.stl',
            'template_file': os.path.join(template_dir, 'Talus_Template.stl'),
            'bone_type': 'talus',
            'side': 'left'
        },
        {
            'bone_file': 'path/to/calcaneus_right.stl',
            'template_file': os.path.join(template_dir, 'Calcaneus_Template.stl'),
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
