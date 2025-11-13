"""Test script for AAFACT Python pipeline."""
import numpy as np
import sys
import os
import trimesh

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from pipeline import process_bone


def test_matlab_validation_template2_to_template1():
    """Validate Python results against MATLAB for Template2->Template with Talonavicular CS and Tibiotalar Surface origin.
    
    MATLAB results for Talus_Template2.stl as input with Talus_Template.stl as template,
    Talonavicular CS, Tibiotalar Surface origin, Left side:
    
    Coordinate System at Original Orientation:
    Tibiotalar Surface Origin: -0.267322312, 1.271899722, 15.2645196
    AP Axis: 0.11450734, 2.193326114, 15.1925507
    SI Axis: -0.283988183, 1.356620148, 16.260785
    ML Axis: 0.656760133, 0.892695484, 15.3122247
    
    Coordinate System at (0,0,0):
    Tibiotalar Surface Origin: -2.001143008, 0.612539525, 15.1828949
    AP Axis: -2.019383295, 1.611460746, 15.1401903
    SI Axis: -2.131710946, 0.652505696, 16.1735284
    ML Axis: -1.009871448, 0.636184822, 15.312593
    """
    print("MATLAB Validation 1: Template2 → Template (Talonavicular CS, Tibiotalar Surface)...")
    
    # MATLAB expected results (at 0,0,0)
    matlab_origin = np.array([-2.001143008, 0.612539525, 15.1828949])
    matlab_AP = np.array([-2.019383295, 1.611460746, 15.1401903])
    matlab_SI = np.array([-2.131710946, 0.652505696, 16.1735284])
    matlab_ML = np.array([-1.009871448, 0.636184822, 15.312593])
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bone_file = os.path.join(os.path.dirname(script_dir), 'Template_Bones', 'Talus_Template2.stl')
    
    if not os.path.exists(bone_file):
        print("  ⚠ Template files not found, skipping validation")
        return True  # Don't fail if templates not available
    
    try:
        coords_final, coords_unit, coords_aligned_unit = process_bone(
            bone_file=bone_file,
            bone_type='talus',
            side='left',
            coord_sys='default',  # Talonavicular CS
            joint_origin='tibiotalar_surface',
            output_dir='/tmp/test_output'
        )
        
        # Extract from aligned coordinates (at 0,0,0)
        python_origin = coords_aligned_unit[0]
        python_AP = coords_aligned_unit[1]
        python_SI = coords_aligned_unit[3]
        python_ML = coords_aligned_unit[5]
        
        # Calculate differences
        diff_origin = np.linalg.norm(python_origin - matlab_origin)
        diff_AP = np.linalg.norm(python_AP - matlab_AP)
        diff_SI = np.linalg.norm(python_SI - matlab_SI)
        diff_ML = np.linalg.norm(python_ML - matlab_ML)
        
        print(f"  Origin diff: {diff_origin:.6f}, AP diff: {diff_AP:.6f}, SI diff: {diff_SI:.6f}, ML diff: {diff_ML:.6f}")
        
        # Check if results match (tolerance for numerical precision)
        tolerance = 0.1  # More relaxed tolerance for joint surface calculation
        passed = (diff_origin < tolerance and diff_AP < tolerance and 
                 diff_SI < tolerance and diff_ML < tolerance)
        
        if passed:
            print("  ✓ MATLAB validation 1 passed")
        else:
            print("  ✗ MATLAB validation 1 failed")
        
        return passed
        
    except Exception as e:
        print(f"  ✗ MATLAB validation 1 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_matlab_validation_template1_to_template2():
    """Validate Python results against MATLAB for Template->Template2 with Tibiotalar CS and Tibiotalar Surface origin.
    
    MATLAB results for Talus_Template.stl as input with Talus_Template2.stl as template,
    Tibiotalar CS, Tibiotalar Surface origin, Left side:
    
    Coordinate System at Original Orientation:
    Tibiotalar Surface Origin: -1.617670119, -2.077675907, 15.521718
    AP Axis: -2.095737732, -1.201929585, 15.588947
    SI Axis: -1.720355704, -2.209420821, 16.5076688
    ML Axis: -0.745370269, -1.613228217, 15.6746275
    
    Coordinate System at (0,0,0):
    Tibiotalar Surface Origin: -0.957501057, -1.324681361, 15.6665587
    AP Axis: -1.035526774, -0.330885796, 15.74582
    SI Axis: -1.01828863, -1.408779613, 16.6611603
    ML Axis: 0.03759535, -1.251894963, 15.7335309
    """
    print("MATLAB Validation 2: Template → Template2 (Tibiotalar CS, Tibiotalar Surface)...")
    
    # MATLAB expected results (at 0,0,0)
    matlab_origin = np.array([-0.957501057, -1.324681361, 15.6665587])
    matlab_AP = np.array([-1.035526774, -0.330885796, 15.74582])
    matlab_SI = np.array([-1.01828863, -1.408779613, 16.6611603])
    matlab_ML = np.array([0.03759535, -1.251894963, 15.7335309])
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bone_file = os.path.join(os.path.dirname(script_dir), 'Template_Bones', 'Talus_Template.stl')
    
    if not os.path.exists(bone_file):
        print("  ⚠ Template files not found, skipping validation")
        return True  # Don't fail if templates not available
    
    try:
        coords_final, coords_unit, coords_aligned_unit = process_bone(
            bone_file=bone_file,
            bone_type='talus',
            side='left',
            coord_sys='tibiotalar',  # Tibiotalar CS
            joint_origin='tibiotalar_surface',
            output_dir='/tmp/test_output'
        )
        
        # Extract from aligned coordinates (at 0,0,0)
        python_origin = coords_aligned_unit[0]
        python_AP = coords_aligned_unit[1]
        python_SI = coords_aligned_unit[3]
        python_ML = coords_aligned_unit[5]
        
        # Calculate differences
        diff_origin = np.linalg.norm(python_origin - matlab_origin)
        diff_AP = np.linalg.norm(python_AP - matlab_AP)
        diff_SI = np.linalg.norm(python_SI - matlab_SI)
        diff_ML = np.linalg.norm(python_ML - matlab_ML)
        
        print(f"  Origin diff: {diff_origin:.6f}, AP diff: {diff_AP:.6f}, SI diff: {diff_SI:.6f}, ML diff: {diff_ML:.6f}")
        
        # Check if results match (tolerance for numerical precision)
        tolerance = 0.15  # Relaxed tolerance for joint surface with ICP variations
        passed = (diff_origin < tolerance and diff_AP < tolerance and 
                 diff_SI < tolerance and diff_ML < tolerance)
        
        if passed:
            print("  ✓ MATLAB validation 2 passed")
        else:
            print("  ✗ MATLAB validation 2 failed")
        
        return passed
        
    except Exception as e:
        print(f"  ✗ MATLAB validation 2 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("AAFACT Python Pipeline Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_point_to_point,
        test_icp,
        test_coordinate_system,
        test_center,
        test_normalize_coords,
        test_matlab_validation_template2_to_template1,
        test_matlab_validation_template1_to_template2
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


def compare_python_matlab_results(input_dir, matlab_output_dir, python_output_dir):
    """
    Compare Python and MATLAB results for all bone segmentations.
    
    Args:
        input_dir: Directory containing input segmentations organized by anatomy
        matlab_output_dir: Directory containing MATLAB output xlsx files
        python_output_dir: Directory where Python output CSVs will be saved
    
    Returns:
        Dictionary with comparison statistics
    """
    import glob
    import pandas as pd
    
    print("=" * 80)
    print("MATLAB vs Python Validation")
    print("=" * 80)
    
    # Bone type mapping for process_bone
    bone_map = {
        'talus': 'talus',
        'calcaneus': 'calcaneus',
        'navicular': 'navicular',
        'cuboid': 'cuboid',
        'med_cuneiform': 'med_cuneiform',
        'mid_cuneiform': 'mid_cuneiform',
        'lat_cuneiform': 'lat_cuneiform',
        'first_metatarsal': 'first_metatarsal',
        'second_metatarsal': 'second_metatarsal',
        'third_metatarsal': 'third_metatarsal',
        'fourth_metatarsal': 'fourth_metatarsal',
        'fifth_metatarsal': 'fifth_metatarsal',
        'tibia': 'tibia',
        'fibula': 'fibula'
    }
    
    # Coordinate system name mapping
    cs_map = {
        'Talonavicular': 'talonavicular',
        'Tibiotalar': 'tibiotalar',
        'Subtalar': 'subtalar',
        'Calcaneocuboid': 'calcaneocuboid',
        'Vertical': 'vertical',
        'Radial': 'radial'
    }
    
    # Storage for errors
    origin_errors = []
    angle_errors = []
    cases = []
    
    # Find all MATLAB output files
    matlab_files = glob.glob(os.path.join(matlab_output_dir, '**', '*.xlsx'), recursive=True)
    
    print(f"\nFound {len(matlab_files)} MATLAB result files")
    print()
    
    for matlab_file in sorted(matlab_files):
        # Parse filename: {seg_name}_{CS}_Center.xlsx
        basename = os.path.basename(matlab_file)
        # if not basename.endswith('_Center.xlsx'):
        if not basename.endswith('.xlsx'):
            continue
        
        # parts = basename[:-len('_Center.xlsx')].split('_')
        parts = basename[:-len('.xlsx')].split('_')
        if len(parts) < 3:
            continue
        
        joint_name = parts[-1]
        cs_name = parts[-2]
        seg_name = '_'.join(parts[:-2])
        
        # Determine bone type from parent directory
        parent_dir = os.path.basename(os.path.dirname(matlab_file))
        if parent_dir not in bone_map:
            continue
        
        bone_type = bone_map[parent_dir]
        coord_sys_python = cs_map.get(cs_name, 'default')
        # joint_origin = joint_name.lower()
        joint_origin = '_'.join(joint_name.lower().split(' '))  # e.g., "Tibiotalar Surface" -> "tibiotalar_surface"
        
        # Find input file
        input_file = os.path.join(input_dir, parent_dir, seg_name + '.stl')
        if not os.path.exists(input_file):
            print(f"⚠ Input file not found: {input_file}")
            continue
        
        print(f"Processing: {seg_name} ({bone_type}, {cs_name} CS, {joint_origin} origin)")
        
        try:
            # Read MATLAB results
            df_matlab = pd.read_excel(matlab_file, header=None)
            
            # Extract "Coordinate System at Original Orientation" from MATLAB
            # Find the row with this header
            orig_row = None
            for i, row in df_matlab.iterrows():
                if pd.notna(row[0]) and 'Original Orientation' in str(row[0]):
                    orig_row = i
                    break
            
            if orig_row is None:
                print(f"  ⚠ Could not find 'Original Orientation' in MATLAB file")
                continue
            
            # Read coordinate data (starting 2 rows after header)
            matlab_origin = df_matlab.iloc[orig_row + 1, 1:4].values.astype(float)
            matlab_ap = df_matlab.iloc[orig_row + 2, 1:4].values.astype(float) - matlab_origin
            matlab_si = df_matlab.iloc[orig_row + 3, 1:4].values.astype(float) - matlab_origin
            matlab_ml = df_matlab.iloc[orig_row + 4, 1:4].values.astype(float) - matlab_origin

            # Run Python pipeline
            coords_final, coords_unit, coords_aligned_unit = process_bone(
                bone_file=input_file,
                bone_type=bone_type,
                side='left',
                coord_sys=coord_sys_python,
                joint_origin= joint_origin,
                output_dir=f'{python_output_dir}/{basename[:-len(".xlsx")]}'
            )
            
            # Extract Python results (original orientation)
            # coords_final format: [origin, AP_end, origin, SI_end, origin, ML_end]
            python_origin = coords_unit[0, :]
            python_ap = coords_unit[1, :] - coords_unit[0, :]  # AP axis vector
            python_si = coords_unit[3, :] - coords_unit[2, :]  # SI axis vector
            python_ml = coords_unit[5, :] - coords_unit[4, :]  # ML axis vector
            
            
            # Note: Python output already saved by process_bone to python_output_dir
            
            # Compute errors
            # 1. Origin distance error
            origin_dist = np.linalg.norm(python_origin - matlab_origin)
            origin_errors.append(origin_dist)

            # load input file
            m = trimesh.load(input_file)
            # compute scale factor based on input mesh size
            v = m.vertices
            v = v - v.mean(axis=0, keepdims=True)
            s = ((v**2).sum(axis=1).mean())**0.5
            origin_dist_relative = origin_dist / s


            # 2. Angle errors between axes (in degrees)
            def angle_between_vectors(v1, v2):
                """Compute angle in degrees between two vectors."""
                v1_u = v1 / np.linalg.norm(v1)
                v2_u = v2 / np.linalg.norm(v2)
                cos_angle = np.degrees( np.arccos( np.clip( v1_u @ v2_u, -1.0, 1.0) ) )
                return cos_angle
            
            ap_angle = angle_between_vectors(python_ap, matlab_ap)
            si_angle = angle_between_vectors(python_si, matlab_si)
            ml_angle = angle_between_vectors(python_ml, matlab_ml)
            
            avg_angle = (ap_angle + si_angle + ml_angle) / 3.0
            angle_errors.append(avg_angle)
            
            cases.append({
                'file': basename,
                'bone': bone_type,
                'cs': cs_name,
                'origin_dist': origin_dist,
                'origin_dist_relative': origin_dist_relative,
                'ap_angle': ap_angle,
                'si_angle': si_angle,
                'ml_angle': ml_angle,
                'avg_angle': avg_angle
            })
            
            print(f"  Origin distance: {origin_dist:.2f} mm. Relative: {origin_dist_relative*100:.2f}%")
            print(f"  AP angle: {ap_angle:.2f}°, SI angle: {si_angle:.2f}°, ML angle: {ml_angle:.2f}°")
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            print()
            continue
    
    # Print summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    if len(origin_errors) == 0:
        print("No results to compare.")
        return {}
    
    origin_errors = np.array(origin_errors)
    angle_errors = np.array(angle_errors)
    
    print(f"\nTotal cases compared: {len(origin_errors)}")
    print()
    print("Origin Distance Errors (mm):")
    print(f"  Mean: {np.mean(origin_errors):.6f}")
    print(f"  Std:  {np.std(origin_errors):.6f}")
    print(f"  Min:  {np.min(origin_errors):.6f}")
    print(f"  Max:  {np.max(origin_errors):.6f}")
    print()
    print("Angle Errors (degrees, average of AP/SI/ML):")
    print(f"  Mean: {np.mean(angle_errors):.6f}")
    print(f"  Std:  {np.std(angle_errors):.6f}")
    print(f"  Min:  {np.min(angle_errors):.6f}")
    print(f"  Max:  {np.max(angle_errors):.6f}")
    print()
    
    # Find worst cases
    worst_dist_idx = np.argmax(origin_errors)
    worst_angle_idx = np.argmax(angle_errors)
    
    print("Worst Cases:")
    print()
    worst_dist_case = cases[worst_dist_idx]
    print(f"Largest Origin Distance Error ({origin_errors[worst_dist_idx]:.6f} mm, {worst_dist_case['origin_dist_relative']*100:.2f}%):")
    print(f"  File: {worst_dist_case['file']}")
    print(f"  Bone: {worst_dist_case['bone']}, CS: {worst_dist_case['cs']}")
    print(f"  AP: {worst_dist_case['ap_angle']:.4f}°, SI: {worst_dist_case['si_angle']:.4f}°, ML: {worst_dist_case['ml_angle']:.4f}°")
    print()
    
    print(f"Largest Angle Error ({angle_errors[worst_angle_idx]:.6f}°):")
    worst_angle_case = cases[worst_angle_idx]
    print(f"  File: {worst_angle_case['file']}")
    print(f"  Bone: {worst_angle_case['bone']}, CS: {worst_angle_case['cs']}")
    print(f"  Origin dist: {worst_angle_case['origin_dist']:.6f} mm, {worst_angle_case['origin_dist_relative']*100:.2f}%")
    print(f"  AP: {worst_angle_case['ap_angle']:.4f}°, SI: {worst_angle_case['si_angle']:.4f}°, ML: {worst_angle_case['ml_angle']:.4f}°")
    print()
    
    return {
        'n_cases': len(origin_errors),
        'origin_mean': np.mean(origin_errors),
        'origin_std': np.std(origin_errors),
        'angle_mean': np.mean(angle_errors),
        'angle_std': np.std(angle_errors),
        'worst_distance_case': worst_dist_case,
        'worst_angle_case': worst_angle_case,
        'all_cases': cases
    }


if __name__ == '__main__':
    sys.exit(main())
