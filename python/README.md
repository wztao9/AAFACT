# AAFACT Python Pipeline

This is a minimal Python translation of the AAFACT (Automatic Anatomical Foot and Ankle Coordinate Toolbox) pipeline. It removes graphical interfaces and hardcodes inputs for automated processing.

## Features

- **Minimal dependencies**: NumPy, SciPy, and optional trimesh/numpy-stl
- **No GUI**: Pure command-line processing
- **Hardcoded configurations**: Pre-define bone types and lateralities
- **Core pipeline**: ICP alignment → Coordinate system calculation → Output
- **Multiple coordinate systems**: Support for different CS types (e.g., tibiotalar, subtalar for talus)

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

# Process a single bone with default coordinate system
coords, coords_unit = process_bone(
    bone_file='path/to/talus.stl',
    template_file='../Template_Bones/Talus_Template.stl',
    bone_type='talus',
    side='left',
    output_dir='output'
)

# Process talus with Tibiotalar coordinate system
coords, coords_unit = process_bone(
    bone_file='path/to/talus.stl',
    template_file='../Template_Bones/Talus_Template.stl',
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
        'template_file': os.path.join(template_dir, 'Talus_Template.stl'),
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

CSV files containing coordinate system information:
- AP (Anterior-Posterior) axis
- SI (Superior-Inferior) axis
- ML (Medial-Lateral) axis

Each axis is defined by origin and endpoint coordinates.

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

## Differences from MATLAB Version

- No GUI or user prompts
- Hardcoded bone types and lateralities
- Simplified ICP with fewer rotation attempts
- CSV output instead of Excel
- No plotting/visualization
- Single coordinate system per bone (no multiple CS options)

## Limitations

- Template files must be in `../Template_Bones/` directory
- No joint origin computation (center only)
- No similarity testing
- No troubleshooting/alignment refinement options
- Requires pre-classified bone files

## Citation

If you use this code, please cite the original paper:

Peterson, A. C., Kruger, K. M., Lenz, A. L. (2023). Automatic Anatomical Foot and Ankle Coordinate Toolbox, Frontiers in Bioengineering and Biotechnology, Oct 31:11:1255464. https://doi.org/10.3389/fbioe.2023.1255464.
