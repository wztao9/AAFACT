# AAFACT Python Pipeline

This is a minimal Python translation of the AAFACT (Automatic Anatomical Foot and Ankle Coordinate Toolbox) pipeline. It removes graphical interfaces and hardcodes inputs for automated processing.

## Features

- **Minimal dependencies**: NumPy, SciPy, and optional trimesh/numpy-stl
- **No GUI**: Pure command-line processing
- **Hardcoded configurations**: Pre-define bone types and lateralities
- **Core pipeline**: ICP alignment → Coordinate system calculation → Output
- **Multiple coordinate systems**: Support for different CS types (e.g., tibiotalar, subtalar for talus)
- **Size-adaptive processing**: Automatically handles different bone sizes using relative measurements
- **Joint origin support**: Ray-triangle intersection for anatomical joint surface origins

## Installation

```bash
pip install numpy scipy trimesh
# OR
pip install numpy scipy numpy-stl
```

## Usage

### Basic Usage

Edit `pipeline.py` to configure your bone files and run:

```bash
cd python
python pipeline.py
```

### Programmatic Usage

```python
from pipeline import process_bone

# Process a single bone with default coordinate system (templates auto-selected)
coords, coords_unit = process_bone(
    bone_file='path/to/talus.stl',
    bone_type='talus',
    side='left',
    output_dir='output'
)

# Process talus with Tibiotalar coordinate system
coords, coords_unit = process_bone(
    bone_file='path/to/talus.stl',
    bone_type='talus',
    side='left',
    coord_sys='tibiotalar',  # Specify coordinate system type
    output_dir='output'
)
```

## Configuration

Modify the `examples` list in `pipeline.py`:

```python
examples = [
    {
        'bone_file': 'data/subject01_talus_left.stl',
        'bone_type': 'talus',
        'side': 'left',
        'coord_sys': 'tibiotalar'  # Optional: specify coordinate system type
    },
    # Add more bones...
]
```

## Supported Bone Types

- `talus` (coordinate systems: default/talonavicular, tibiotalar, subtalar)
- `calcaneus` (coordinate systems: default/calcaneocuboid, subtalar)
- `navicular`
- `cuboid`
- `cuneiform`
- `metatarsal`
- `tibia`
- `fibula`

## Coordinate System Types

For certain bones, multiple coordinate system options are available:

### Talus
- `'default'` or `'talonavicular'` - Talonavicular coordinate system (default)
- `'tibiotalar'` - Tibiotalar coordinate system
- `'subtalar'` - Subtalar coordinate system

### Calcaneus
- `'default'` or `'calcaneocuboid'` - Calcaneocuboid coordinate system (default)
- `'subtalar'` - Subtalar coordinate system

Other bones use `'default'` coordinate system only.

## Output

CSV files matching MATLAB format with two coordinate systems:
1. **Coordinate System at Original Orientation** - Coordinates in the original bone orientation
2. **Coordinate System at (0,0,0)** - Normalized coordinates in the aligned template space

Each coordinate system includes:
- Center Origin
- AP (Anterior-Posterior) axis unit vector
- SI (Superior-Inferior) axis unit vector
- ML (Medial-Lateral) axis unit vector

Example CSV format:
```csv
Subject,Talus_Template2
Bone Model,Talus
Side,Left

Coordinate System at Original Orientation,X,Y,Z
Center Origin,0.000000000,0.000000000,0.000000000
AP Axis,-0.069279525,0.994574933,0.077595487
SI Axis,-0.064409896,-0.082079562,0.994542259
ML Axis,0.995515802,0.063903504,0.069746899
Coordinate System at (0,0,0),X,Y,Z
Center Origin,0.000000000,0.000000000,0.000000000
AP Axis,-0.084944776,0.992540473,0.087451669
SI Axis,-0.060725157,-0.092762759,0.993834758
ML Axis,0.994533479,0.079110555,0.068151888
```

## Pipeline Overview

1. **Load bone model** (STL/PLY)
2. **Flip right bones to left** (standardization)
3. **Center at origin**
4. **ICP alignment to template** (with multiple initial rotations)
5. **Compute anatomical coordinate system**
6. **Reorient to original space**
7. **Save coordinates to CSV**

## Files

- `pipeline.py` - Main processing pipeline
- `icp.py` - ICP alignment algorithm
- `coordinate_system.py` - Coordinate system calculation
- `utils.py` - Utility functions (centering, reorientation)
- `io_utils.py` - File I/O for bone models
- `joint_origin.py` - Ray-triangle intersection for joint surface detection

## Bone Size Handling

The pipeline automatically adapts to different bone sizes using **relative measurements**:

1. **ICP size scaling**: Before alignment, bones are temporarily scaled to match template size
   - Calculates size ratio between template and bone along the primary axis
   - Scales bone UP if smaller than template (improves ICP accuracy)
   - Scales back DOWN after alignment to preserve original proportions
   - Uses Y-axis for most bones, X-axis for navicular, Z-axis for cuneiforms

2. **Adaptive sectioning**: Divides each bone into regions based on its own dimensions
   - Calculates bone range in each axis (max - min)
   - Creates sections as fractions of the bone's size (e.g., 1/3 for talus, 1/10 for calcaneus)
   - Extracts representative points from these relative regions

3. **Size-independent features**: 
   - Uses proportional regions rather than absolute distances
   - Coordinate axes are normalized to unit length
   - Works with both pediatric and adult bone sizes

4. **Special bone handling**:
   - **Tibia**: Removes distal 14mm (plafond) and processes only proximal 100mm
   - **Talus (TT/ST CS)**: Filters superior portion (y < 10mm) for tibiotalar/subtalar systems
   - Note: These hardcoded values may need adjustment for significantly different scales

**Recommendation**: For bones with unusual sizes (e.g., very small pediatric bones or pathological specimens), verify that the hardcoded filters (14mm, 100mm, 10mm) are appropriate for your data.

## Differences from MATLAB Version

- No GUI or user prompts
- Hardcoded bone types and lateralities
- Simplified ICP with fewer rotation attempts (5 vs 20+)
- CSV output instead of Excel
- No plotting/visualization

## Limitations

- Template files must be in `../Template_Bones/` directory
- Some hardcoded anatomical cutoffs may not scale well for extreme bone sizes
- No similarity testing
- No troubleshooting/alignment refinement options
- Requires pre-classified bone files

## Citation

If you use this code, please cite the original paper:

Peterson, A. C., Kruger, K. M., Lenz, A. L. (2023). Automatic Anatomical Foot and Ankle Coordinate Toolbox, Frontiers in Bioengineering and Biotechnology, Oct 31:11:1255464. https://doi.org/10.3389/fbioe.2023.1255464.
