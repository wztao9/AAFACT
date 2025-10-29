"""ICP (Iterative Closest Point) alignment module."""
import numpy as np
from scipy.spatial import KDTree


def icp(target, source, max_iterations=200, tolerance=1e-6):
    """Perform ICP alignment between target and source point clouds.
    
    Args:
        target: Nx3 target point cloud
        source: Mx3 source point cloud to align
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance
        
    Returns:
        R: 3x3 rotation matrix
        T: 3x1 translation vector
        transformed: Transformed source points
    """
    src = source.copy()
    prev_error = float('inf')
    R_total = np.eye(3)
    T_total = np.zeros((3, 1))
    
    for i in range(max_iterations):
        # Find nearest neighbors
        tree = KDTree(target)
        distances, indices = tree.query(src)
        
        # Compute transformation
        R, T = point_to_point(target[indices], src)
        
        # Apply transformation
        src = (R @ src.T).T + T.T
        
        # Update total transformation
        R_total = R @ R_total
        T_total = R @ T_total + T
        
        # Check convergence
        error = np.mean(distances)
        if abs(prev_error - error) < tolerance:
            break
        prev_error = error
    
    return R_total, T_total, src


def point_to_point(q, p):
    """Compute optimal rotation and translation using SVD."""
    # Center the points
    centroid_q = np.mean(q, axis=0)
    centroid_p = np.mean(p, axis=0)
    
    q_centered = q - centroid_q
    p_centered = p - centroid_p
    
    # Compute cross-covariance matrix
    H = p_centered.T @ q_centered
    
    # SVD
    U, _, Vt = np.linalg.svd(H)
    
    # Compute rotation
    R = Vt.T @ U.T
    
    # Ensure proper rotation (det(R) = 1)
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    
    # Compute translation
    T = centroid_q - (R @ centroid_p)
    
    return R, T.reshape(3, 1)
