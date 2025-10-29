"""File I/O utilities for loading bone models."""
import numpy as np


def load_stl(filepath):
    """Load STL file and return vertices.
    
    Args:
        filepath: Path to STL file
        
    Returns:
        vertices: Nx3 array of vertices
    """
    try:
        import trimesh
        mesh = trimesh.load(filepath)
        return np.array(mesh.vertices)
    except ImportError:
        # Fallback to numpy-stl
        from stl import mesh as stl_mesh
        mesh = stl_mesh.Mesh.from_file(filepath)
        # Get unique vertices
        vertices = mesh.vectors.reshape(-1, 3)
        return np.unique(vertices, axis=0)


def load_ply(filepath):
    """Load PLY file and return vertices.
    
    Args:
        filepath: Path to PLY file
        
    Returns:
        vertices: Nx3 array of vertices
    """
    try:
        import trimesh
        mesh = trimesh.load(filepath)
        return np.array(mesh.vertices)
    except ImportError:
        # Basic PLY parser
        vertices = []
        with open(filepath, 'r') as f:
            header = True
            vertex_count = 0
            for line in f:
                if header:
                    if line.startswith('element vertex'):
                        vertex_count = int(line.split()[2])
                    if line.startswith('end_header'):
                        header = False
                        continue
                else:
                    if len(vertices) < vertex_count:
                        parts = line.strip().split()
                        vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])
        return np.array(vertices)


def load_bone_file(filepath):
    """Load bone model from file.
    
    Args:
        filepath: Path to bone model file
        
    Returns:
        vertices: Nx3 array of vertices
    """
    if filepath.endswith('.stl'):
        return load_stl(filepath)
    elif filepath.endswith('.ply'):
        return load_ply(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")


def save_coordinates(filepath, coords, bone_name, side):
    """Save coordinate system to CSV file.
    
    Args:
        filepath: Output file path
        coords: 6x3 coordinate system
        bone_name: Name of bone
        side: Laterality (left/right)
    """
    with open(filepath, 'w') as f:
        f.write(f"Bone,{bone_name}\n")
        f.write(f"Side,{side}\n")
        f.write("Coordinate,X,Y,Z\n")
        f.write(f"AP_origin,{coords[0,0]:.6f},{coords[0,1]:.6f},{coords[0,2]:.6f}\n")
        f.write(f"AP_end,{coords[1,0]:.6f},{coords[1,1]:.6f},{coords[1,2]:.6f}\n")
        f.write(f"SI_origin,{coords[2,0]:.6f},{coords[2,1]:.6f},{coords[2,2]:.6f}\n")
        f.write(f"SI_end,{coords[3,0]:.6f},{coords[3,1]:.6f},{coords[3,2]:.6f}\n")
        f.write(f"ML_origin,{coords[4,0]:.6f},{coords[4,1]:.6f},{coords[4,2]:.6f}\n")
        f.write(f"ML_end,{coords[5,0]:.6f},{coords[5,1]:.6f},{coords[5,2]:.6f}\n")
