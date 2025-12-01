# AAFACT Python Pipeline

AAFACT (Automatic Anatomical Foot and Ankle Coordinate Toolbox) is a MATLAB toolkit that defines anatomical coordinate systems for foot and ankle bones from 3D segmentations.

This Python project is a minimal, non‑GUI translation of the AAFACT pipeline intended for automated batch processing and direct comparison against the MATLAB implementation with necessary adaptations. It removes graphical interfaces for automated processing.

It produces effectively the same coordinate systems as AAFACT under these conditions:

- Complete bone models (except for tibias and fibulas).
- Input meshes are already roughly in the same pose as the AAFACT templates (no arbitrary large rotations).

Below are the ways in which the Python pipeline intentionally differs from the original MATLAB implementation.


## ICP and alignment differences

Relative to MATLAB’s `icp.m`:

- **Initial rotation trials removed**  
  MATLAB tries multiple initial rotations and runs short ICPs to select a good starting pose.  
  Python assumes the input is already roughly aligned and skips these trials, using only the identity rotation as the initial guess. Beacause this transformtion search has been less robust for anatomies such as lateral cuneiforms which is highly rotational symmetrical and has been reversed incorrectly. GUI (`Main_CS.m`) and interactive “better starting point” tools (`better_starting_point.m`) are not translated because the Python version is for automated batch processing.

- **Rejection and matching differences**  
  MATLAB can use `WorstRejection` and `EdgeRejection` on the triangulated surface; in this Python translation those are removed.  
  Python uses Open3D point‑to‑point ICP with a large `max_correspondence_distance` (1e10) and no explicit edge/boundary logic. All reasonably close correspondences are used, but the exact set can differ slightly from MATLAB’s KD‑tree matching.

- **Scaling logic unified**  
  In both MATLAB and Python, bones are scaled to the template using RMS size about the centroid before ICP and then rescaled back afterward.  
  Python makes this explicit and uniform across bones, whereas MATLAB uses some anatomy‑specific axis choices internally.

## Talus‑specific differences

- The talus **subtalar CS is not computed** in Python, because the original AAFACT subtalar axes are computed as averages of two sets of axes, which are not strictly orthogonal; only talonavicular (TN) and tibiotalar (TT) CS are available.

## Metatarsal‑specific differences

- MATLAB recenters metatarsals between ICP and axis computation to account for partial bones; Python does not.  
  Python always uses the template‑based origin for metatarsals. Because the recentering in MATLAB is only needed for partial bones, this change improves consistency when processing complete metatarsals.

## Empirical agreement with MATLAB

On complete, well‑aligned datasets for the supported bone / CS / origin combinations described above, the Python pipeline has been validated against modified AAFACT MATLAB outputs. The maximum observed differences are approximately:

- Maximum origin differences of **0.1 mm**.
- Maximum axis angle differences of **0.5°**.

Within these bounds, the Python results can be considered practically equivalent to the MATLAB AAFACT outputs for most applications.