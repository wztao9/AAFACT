"""Validation test comparing Python results with MATLAB results."""
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from pipeline import process_bone

def test_talus_tibiotalar():
    """Test Talus with Tibiotalar CS against MATLAB results.
    
    MATLAB results for Talus_Template2.stl as input with Talus_Template.stl as template,
    Tibiotalar CS, Center origin, Left side:
    
    Coordinate System at (0,0,0):
    Center Origin: 0, 0, 0
    AP Axis: -0.078247832, 0.993714396, 0.08005608
    SI Axis: -0.058819152, -0.08476412, 0.994663436
    ML Axis: 0.995197259, 0.073121427, 0.065082047
    """
    print("=" * 70)
    print("Validation Test: Talus Tibiotalar CS")
    print("=" * 70)
    
    # MATLAB expected results (normalized coordinates at origin)
    matlab_AP = np.array([-0.078247832, 0.993714396, 0.08005608])
    matlab_SI = np.array([-0.058819152, -0.08476412, 0.994663436])
    matlab_ML = np.array([0.995197259, 0.073121427, 0.065082047])
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bone_file = os.path.join(os.path.dirname(script_dir), 'Template_Bones', 'Talus_Template2.stl')
    template_file = os.path.join(os.path.dirname(script_dir), 'Template_Bones', 'Talus_Template.stl')
    
    print(f"\nInput bone: {bone_file}")
    print(f"Template: {template_file}")
    print(f"Bone type: talus (Tibiotalar CS)")
    print(f"Side: left")
    print(f"Origin: center")
    
    # Process with Python
    try:
        coords, coords_unit = process_bone(
            bone_file=bone_file,
            template_file=template_file,
            bone_type='talus',
            side='left',
            coord_sys='tibiotalar',  # Specify Tibiotalar CS
            output_dir='/tmp/validate_output'
        )
        
        # Extract unit vectors (coords_unit has origin at indices 0,2,4 and endpoints at 1,3,5)
        python_AP = coords_unit[1] - coords_unit[0]
        python_SI = coords_unit[3] - coords_unit[2]
        python_ML = coords_unit[5] - coords_unit[4]
        
        print("\n" + "-" * 70)
        print("MATLAB Results (expected):")
        print("-" * 70)
        print(f"AP Axis: [{matlab_AP[0]:14.9f}, {matlab_AP[1]:14.9f}, {matlab_AP[2]:14.9f}]")
        print(f"SI Axis: [{matlab_SI[0]:14.9f}, {matlab_SI[1]:14.9f}, {matlab_SI[2]:14.9f}]")
        print(f"ML Axis: [{matlab_ML[0]:14.9f}, {matlab_ML[1]:14.9f}, {matlab_ML[2]:14.9f}]")
        
        print("\n" + "-" * 70)
        print("Python Results (actual):")
        print("-" * 70)
        print(f"AP Axis: [{python_AP[0]:14.9f}, {python_AP[1]:14.9f}, {python_AP[2]:14.9f}]")
        print(f"SI Axis: [{python_SI[0]:14.9f}, {python_SI[1]:14.9f}, {python_SI[2]:14.9f}]")
        print(f"ML Axis: [{python_ML[0]:14.9f}, {python_ML[1]:14.9f}, {python_ML[2]:14.9f}]")
        
        # Calculate differences
        diff_AP = np.linalg.norm(python_AP - matlab_AP)
        diff_SI = np.linalg.norm(python_SI - matlab_SI)
        diff_ML = np.linalg.norm(python_ML - matlab_ML)
        
        print("\n" + "-" * 70)
        print("Differences (L2 norm):")
        print("-" * 70)
        print(f"AP Axis difference: {diff_AP:.9f}")
        print(f"SI Axis difference: {diff_SI:.9f}")
        print(f"ML Axis difference: {diff_ML:.9f}")
        
        # Check if results match (tolerance)
        tolerance = 0.015  # Allow small numerical differences from ICP convergence
        passed = (diff_AP < tolerance and diff_SI < tolerance and diff_ML < tolerance)
        
        print("\n" + "=" * 70)
        if passed:
            print("✓ VALIDATION PASSED - Results match MATLAB")
        else:
            print("✗ VALIDATION FAILED - Results differ from MATLAB")
        print("=" * 70)
        
        return passed
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_talus_tibiotalar()
    sys.exit(0 if success else 1)
