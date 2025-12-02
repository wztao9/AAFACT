"""File I/O utilities for loading bone models."""
import numpy as np


def load_stl(filepath):
    """Load STL file and return vertices and faces.
    
    Args:
        filepath: Path to STL file
        
    Returns:
        vertices: Nx3 array of vertices
        faces: Mx3 array of face indices
    """
    try:
        import trimesh
        mesh = trimesh.load(filepath)
        return np.array(mesh.vertices), np.array(mesh.faces)
    except ImportError:
        # Fallback to numpy-stl
        from stl import mesh as stl_mesh
        mesh_data = stl_mesh.Mesh.from_file(filepath)
        # Get unique vertices and build face indices
        vertices = mesh_data.vectors.reshape(-1, 3)
        unique_vertices, inverse_indices = np.unique(vertices, axis=0, return_inverse=True)
        faces = inverse_indices.reshape(-1, 3)
        return unique_vertices, faces


def load_bone_file(filepath):
    """Load bone model from file.
    
    Args:
        filepath: Path to bone model file
        
    Returns:
        vertices: Nx3 array of vertices
        faces: Mx3 array of face indices
    """
    if filepath.endswith('.stl'):
        return load_stl(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")


def save_coordinates(filepath, coords_final, coords_unit, coords_aligned_unit, 
                    bone_name, side, subject_name=None, joint_type='Center'):
    """Save coordinate system to CSV file matching MATLAB format.
    
    Args:
        filepath: Output file path
        coords_final: 6x3 coordinate system in original orientation
        coords_unit: 6x3 normalized coordinates in original orientation
        coords_aligned_unit: 6x3 normalized coordinates at (0,0,0)
        bone_name: Name of bone
        side: Laterality (left/right)
        subject_name: Subject/file name (optional)
        joint_type: Joint origin type (e.g., 'Center', 'Tibiotalar Surface')
    """
    if subject_name is None:
        subject_name = os.path.splitext(os.path.basename(filepath))[0]
    
    with open(filepath, 'w') as f:
        # Header
        f.write(f"Subject,{subject_name}\n")
        f.write(f"Bone Model,{bone_name.capitalize()}\n")
        f.write(f"Side,{side.capitalize()}\n")
        f.write("\n")
        
        # Coordinate System at Original Orientation
        f.write("Coordinate System at Original Orientation,X,Y,Z\n")
        f.write(f"{joint_type} Origin,{coords_unit[0,0]:.9f},{coords_unit[0,1]:.9f},{coords_unit[0,2]:.9f}\n")
        f.write(f"AP Axis,{coords_unit[1,0]:.9f},{coords_unit[1,1]:.9f},{coords_unit[1,2]:.9f}\n")
        f.write(f"SI Axis,{coords_unit[3,0]:.9f},{coords_unit[3,1]:.9f},{coords_unit[3,2]:.9f}\n")
        f.write(f"ML Axis,{coords_unit[5,0]:.9f},{coords_unit[5,1]:.9f},{coords_unit[5,2]:.9f}\n")
        
        # Coordinate System at (0,0,0)
        f.write("Coordinate System at (0,0,0),X,Y,Z\n")
        f.write(f"{joint_type} Origin,{coords_aligned_unit[0,0]:.9f},{coords_aligned_unit[0,1]:.9f},{coords_aligned_unit[0,2]:.9f}\n")
        f.write(f"AP Axis,{coords_aligned_unit[1,0]:.9f},{coords_aligned_unit[1,1]:.9f},{coords_aligned_unit[1,2]:.9f}\n")
        f.write(f"SI Axis,{coords_aligned_unit[3,0]:.9f},{coords_aligned_unit[3,1]:.9f},{coords_aligned_unit[3,2]:.9f}\n")
        f.write(f"ML Axis,{coords_aligned_unit[5,0]:.9f},{coords_aligned_unit[5,1]:.9f},{coords_aligned_unit[5,2]:.9f}\n")
