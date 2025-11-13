# AAFACT Python Pipeline

This is a minimal Python translation of the AAFACT (Automatic Anatomical Foot and Ankle Coordinate Toolbox) pipeline. It removes graphical interfaces and hardcodes inputs for automated processing.

- It assumes the input is already roughly aligned and skips the trials for initial transformations which has been less robust for anatomies such as lateral cuneiforms.