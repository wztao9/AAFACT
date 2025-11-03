"""ICP (Iterative Closest Point) alignment module."""
import numpy as np

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    from scipy.spatial import KDTree


def icp(target, source, max_iterations=200, tolerance=1e-6):
    """Perform ICP alignment between target and source point clouds.
    
    Uses Open3D's ICP implementation if available, otherwise falls back to custom implementation.
    
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
    if HAS_OPEN3D:
        return icp_open3d(target, source, max_iterations, tolerance)
    else:
        return icp_custom(target, source, max_iterations, tolerance)


def icp_open3d(target, source, max_iterations=200, tolerance=1e-6):
    """ICP alignment using Open3D."""
    # Create point clouds
    pcd_target = o3d.geometry.PointCloud()
    pcd_target.points = o3d.utility.Vector3dVector(target)
    
    pcd_source = o3d.geometry.PointCloud()
    pcd_source.points = o3d.utility.Vector3dVector(source)
    
    # Set convergence criteria
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(
        relative_fitness=tolerance,
        relative_rmse=tolerance,
        max_iteration=max_iterations
    )
    
    # Run ICP
    result = o3d.pipelines.registration.registration_icp(
        pcd_source, pcd_target, 
        max_correspondence_distance=10.0,  # Adjust based on scale
        init=np.eye(4),
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        criteria=criteria
    )
    
    # Extract transformation
    T_matrix = result.transformation
    R = T_matrix[:3, :3]
    T = T_matrix[:3, 3].reshape(3, 1)
    
    # Transform source
    transformed = (R @ source.T).T + T.T
    
    return R, T, transformed


def icp_custom(target, source, max_iterations=200, tolerance=1e-6):
    """Custom ICP implementation using scipy."""
    from scipy.spatial import KDTree
    
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
