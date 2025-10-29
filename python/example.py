"""Example usage of AAFACT Python pipeline."""
import os
from pipeline import process_bone

# Example 1: Process a single talus bone
print("Example 1: Processing talus bone")
print("-" * 50)

bone_file = 'example_data/talus_left.stl'
template_file = '../Template_Bones/Talus_Template.stl'

if os.path.exists(bone_file) and os.path.exists(template_file):
    try:
        coords, coords_unit = process_bone(
            bone_file=bone_file,
            template_file=template_file,
            bone_type='talus',
            side='left',
            output_dir='example_output'
        )
        print("Success!")
        print(f"Coordinate system origin: {coords[0]}")
        print(f"AP axis endpoint: {coords[1]}")
        print(f"SI axis endpoint: {coords[3]}")
        print(f"ML axis endpoint: {coords[5]}")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("⚠ Example files not found - this is a demonstration")
    print(f"  Looking for: {bone_file}")
    print(f"  and: {template_file}")
    print("  Update paths to process your actual bone files")

print("\n")

# Example 2: Batch process multiple bones
print("Example 2: Batch processing")
print("-" * 50)

bones_to_process = [
    ('talus', 'left', 'Talus_Template.stl'),
    ('calcaneus', 'left', 'Calcaneus_Template.stl'),
    ('navicular', 'left', 'Navicular_Template.stl'),
]

template_dir = '../Template_Bones'
data_dir = 'example_data'  # Replace with your data directory
output_dir = 'batch_output'

for bone_type, side, template_name in bones_to_process:
    bone_file = os.path.join(data_dir, f'{bone_type}_{side}.stl')
    template_file = os.path.join(template_dir, template_name)
    
    if os.path.exists(bone_file):
        try:
            coords, coords_unit = process_bone(
                bone_file=bone_file,
                template_file=template_file,
                bone_type=bone_type,
                side=side,
                output_dir=output_dir
            )
            print(f"✓ {bone_type} ({side}) processed successfully")
        except Exception as e:
            print(f"✗ {bone_type} ({side}) failed: {e}")
    else:
        print(f"⚠ {bone_type} ({side}) - file not found")

print("\n")

# Example 3: Programmatic usage without file I/O
print("Example 3: Using individual components")
print("-" * 50)

import numpy as np
from icp import icp
from coordinate_system import compute_coordinate_system
from utils import center, normalize_coords

# Create synthetic bone data for demonstration
print("Creating synthetic bone data...")
np.random.seed(42)
theta = np.linspace(0, 2*np.pi, 100)
phi = np.linspace(0, np.pi, 50)
theta, phi = np.meshgrid(theta, phi)

# Ellipsoid shape (elongated in Y, like a bone)
x = 10 * np.sin(phi) * np.cos(theta)
y = 30 * np.sin(phi) * np.sin(theta)
z = 15 * np.cos(phi)
bone_points = np.stack([x.flatten(), y.flatten(), z.flatten()], axis=1)

# Center the bone
bone_centered, centroid = center(bone_points)
print(f"Original centroid: {centroid}")

# Compute coordinate system
coords = compute_coordinate_system(bone_centered, bone_type='talus', side='left')
print(f"Coordinate system computed")
print(f"  AP axis: {coords[0]} -> {coords[1]}")
print(f"  SI axis: {coords[2]} -> {coords[3]}")
print(f"  ML axis: {coords[4]} -> {coords[5]}")

# Normalize to unit vectors
coords_unit = normalize_coords(coords)
print(f"Normalized coordinate system:")
print(f"  AP unit: {coords_unit[1] - coords_unit[0]}")
print(f"  SI unit: {coords_unit[3] - coords_unit[2]}")
print(f"  ML unit: {coords_unit[5] - coords_unit[4]}")

print("\n" + "=" * 50)
print("Examples complete!")
print("\nTo use with your data:")
print("1. Update bone_file paths in Example 1 or 2")
print("2. Ensure Template_Bones directory is accessible")
print("3. Run: python example.py")
