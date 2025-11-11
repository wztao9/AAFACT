"""ICP (Iterative Closest Point) alignment module."""
import numpy as np
import open3d as o3d


def icp(target, source, max_iterations=200, tolerance=1e-6):
    """Perform ICP alignment between target and source point clouds.
    
    Uses Open3D's ICP implementation
    
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
    return icp_open3d(target, source, max_iterations, tolerance)


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

