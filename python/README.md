# AAFACT Python Pipeline

This is a minimal Python translation of the AAFACT (Automatic Anatomical Foot and Ankle Coordinate Toolbox) pipeline. It removes graphical interfaces and hardcodes inputs for automated processing.

It produces same results as AAFACT under certain scenarios:

- It assumes the input is already roughly aligned and skips the trials for initial transformations which has been less robust for anatomies such as lateral cuneiforms.
- It aims for complete data only. Thus, it removes worst/edge rejection of MATLAB ICP, which are missing in Python ICP packages
- It unifies scale with root mean squared distance to center in icp and recover it afterwards
- It removes subtalus coordinate system for talus because those from AAFACT are not orthogonal