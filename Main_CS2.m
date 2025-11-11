%% Main_CS2 - Automated Batch Processing (No GUI)
% This script processes all bone segmentations in an input directory structure
% and outputs coordinate system results in XLSX format matching Main_CS.m
%
% Input Directory Structure:
%   InputDir/talus/*.stl
%   InputDir/calcaneus/*.stl
%   InputDir/navicular/*.stl
%   etc.
%
% Output: OutputDir/{anatomy}/{seg_name}_{CS}_{ORIGIN}.xlsx
%
% All bones are processed as LEFT side
% All origins are CENTER only

clear, clc, close all

%% Hardcoded Paths
InputDir = 'Input';  % Change this to your input directory
OutputDir = 'Output'; % Change this to your output directory

%% Bone Configuration
% List of supported bone names (must match folder names in InputDir)
bone_list = {'talus', 'calcaneus', 'navicular', 'cuboid', ...
             'med_cuneiform', 'mid_cuneiform', 'lat_cuneiform', ...
             'metatarsal1', 'metatarsal2', 'metatarsal3', 'metatarsal4', 'metatarsal5', ...
             'tibia', 'fibula'};

% Bone indices for internal processing
bone_names = {'Talus', 'Calcaneus', 'Navicular', 'Cuboid', 'Medial_Cuneiform','Intermediate_Cuneiform',...
    'Lateral_Cuneiform','Metatarsal1','Metatarsal2','Metatarsal3','Metatarsal4','Metatarsal5',...
    'Tibia','Fibula'};

% Coordinate system lists for each bone type
cs_configs = containers.Map();
cs_configs('Talus') = {{'Talonavicular', 'Tibiotalar', 'Subtalar'}, [1,2,3]};
cs_configs('Calcaneus') = {{'Calcaneocuboid', 'Subtalar'}, [1,2]};
cs_configs('Navicular') = {{'Default'}, [1]};
cs_configs('Cuboid') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Medial_Cuneiform') = {{'Default'}, [1]};
cs_configs('Intermediate_Cuneiform') = {{'Default'}, [1]};
cs_configs('Lateral_Cuneiform') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Metatarsal1') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Metatarsal2') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Metatarsal3') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Metatarsal4') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Metatarsal5') = {{'Vertical', 'Radial'}, [1,2]};
cs_configs('Tibia') = {{'Default'}, [1]};
cs_configs('Fibula') = {{'Default'}, [1]};

% All bones are LEFT side, CENTER origin only
side_indx = 2;  % Left
joint_indx = 1; % Center

%% Create Output Directory
if ~exist(OutputDir, 'dir')
    mkdir(OutputDir);
end

%% Process Each Anatomy
fprintf('Starting batch processing...\n');

for b = 1:length(bone_list)
    anatomy_folder = bone_list{b};
    bone_indx = b;
    bone_name = bone_names{bone_indx};
    
    % Check if anatomy folder exists
    anatomy_path = fullfile(InputDir, anatomy_folder);
    if ~exist(anatomy_path, 'dir')
        fprintf('Skipping %s (folder not found)\n', anatomy_folder);
        continue;
    end
    
    % Get all STL files in this anatomy folder
    files = dir(fullfile(anatomy_path, '*.stl'));
    if isempty(files)
        fprintf('Skipping %s (no STL files found)\n', anatomy_folder);
        continue;
    end
    
    % Create output subfolder for this anatomy
    output_anatomy_path = fullfile(OutputDir, anatomy_folder);
    if ~exist(output_anatomy_path, 'dir')
        mkdir(output_anatomy_path);
    end
    
    % Get coordinate system configurations for this bone
    config = cs_configs(bone_name);
    cs_names = config{1};
    cs_indices = config{2};
    
    fprintf('\nProcessing %s (%d files, %d coordinate systems)...\n', ...
            anatomy_folder, length(files), length(cs_indices));
    
    % Process each segmentation file
    for f = 1:length(files)
        file_name = files(f).name;
        [~, name_only, ~] = fileparts(file_name);
        file_path = fullfile(anatomy_path, file_name);
        
        fprintf('  [%d/%d] %s\n', f, length(files), file_name);
        
        % Load the bone model
        try
            TR = stlread(file_path);
            nodes_original = TR.Points;
            conlist_original = TR.ConnectivityList;
        catch
            fprintf('    ERROR: Could not load file, skipping.\n');
            continue;
        end
        
        % Process each coordinate system for this bone
        for cs = 1:length(cs_indices)
            bone_coord = cs_indices(cs);
            cs_name = cs_names{cs};
            
            % Prepare nodes (flip to left if needed - already left, so just copy)
            nodes = nodes_original;
            conlist = conlist_original;
            
            % Center the bone
            [nodes, cm_nodes] = center(nodes, 1);
            
            % ICP alignment to template
            better_start = 1;
            [aligned_nodes, RTs] = icp_template(bone_indx, nodes, bone_coord, better_start);
            
            % Calculate coordinate system
            [Temp_Coordinates, Temp_Nodes] = CoordinateSystem(aligned_nodes, bone_indx, bone_coord, side_indx);
            
            % Joint origin is always center (joint_indx = 1)
            Joint = "Center";
            
            % Attach coordinate system to nodes
            Temp_Nodes_Coords = [Temp_Nodes; Temp_Coordinates];
            
            % Reorient back to original orientation
            [~, ~, coords_final_unit, Temp_Coordinates_Unit] = reorient(Temp_Nodes_Coords, cm_nodes, side_indx, RTs);
            
            % Special handling for Talus Subtalar CS
            if bone_indx == 1 && bone_coord == 3
                [aligned_nodes_TST, RTs_TST] = icp_template(bone_indx, nodes, 1, better_start);
                [Temp_Coordinates_TST, Temp_Nodes_TST] = CoordinateSystem(aligned_nodes_TST, bone_indx, 1, side_indx);
                Temp_Nodes_Coords_TST = [Temp_Nodes_TST; Temp_Coordinates_TST];
                [~, ~, coords_final_unit_TST, Temp_Coordinates_Unit_TST] = reorient(Temp_Nodes_Coords_TST, cm_nodes, side_indx, RTs_TST);
                
                % Average with talonavicular
                coords_final_unit = [coords_final_unit(1,:); ((coords_final_unit_TST(2,:) + coords_final_unit(2,:)).'/2)'
                    coords_final_unit(3,:); ((coords_final_unit_TST(4,:) + coords_final_unit(4,:)).'/2)'
                    coords_final_unit(5,:); ((coords_final_unit_TST(6,:) + coords_final_unit(6,:)).'/2)'];
                
                Temp_Coordinates_Unit = [Temp_Coordinates_Unit(1,:); ((Temp_Coordinates_Unit_TST(2,:) + Temp_Coordinates_Unit(2,:)).'/2)'
                    Temp_Coordinates_Unit(3,:); ((Temp_Coordinates_Unit_TST(4,:) + Temp_Coordinates_Unit(4,:)).'/2)'
                    Temp_Coordinates_Unit(5,:); ((Temp_Coordinates_Unit_TST(6,:) + Temp_Coordinates_Unit(6,:)).'/2)'];
            end
            
            % Prepare output file name: {seg_name}_{CS}_Center.xlsx
            output_name = sprintf('%s_%s_Center.xlsx', name_only, cs_name);
            output_path = fullfile(output_anatomy_path, output_name);
            
            % Write to Excel
            try
                % Prepare data matching Main_CS.m format (use cell arrays)
                A = {'Subject'; 'Bone Model'; 'Side'};
                B = {name_only; bone_names{bone_indx}; 'Left'};
                C = {'Coordinate System at Original Orientation'
                    'Center Origin'
                    'AP Axis'
                    'SI Axis'
                    'ML Axis'
                    'Coordinate System at (0,0,0)'
                    'Center Origin'
                    'AP Axis'
                    'SI Axis'
                    'ML Axis'};
                D = {'X' 'Y' 'Z'};
                
                % Create sheet name (limit to 31 chars)
                sheet_name = name_only;
                if length(sheet_name) > 31
                    sheet_name = sheet_name(1:31);
                end
                
                % Write data
                writecell(A, output_path, 'Sheet', sheet_name, 'Range', 'A1');
                writecell(B, output_path, 'Sheet', sheet_name, 'Range', 'B1');
                writecell(C, output_path, 'Sheet', sheet_name, 'Range', 'A5');
                writecell(D, output_path, 'Sheet', sheet_name, 'Range', 'B5');
                writecell(D, output_path, 'Sheet', sheet_name, 'Range', 'B10');
                writematrix(coords_final_unit(1,:), output_path, 'Sheet', sheet_name, 'Range', 'B6');
                writematrix(coords_final_unit(2,:), output_path, 'Sheet', sheet_name, 'Range', 'B7');
                writematrix(coords_final_unit(4,:), output_path, 'Sheet', sheet_name, 'Range', 'B8');
                writematrix(coords_final_unit(6,:), output_path, 'Sheet', sheet_name, 'Range', 'B9');
                writematrix(Temp_Coordinates_Unit(1,:), output_path, 'Sheet', sheet_name, 'Range', 'B11');
                writematrix(Temp_Coordinates_Unit(2,:), output_path, 'Sheet', sheet_name, 'Range', 'B12');
                writematrix(Temp_Coordinates_Unit(4,:), output_path, 'Sheet', sheet_name, 'Range', 'B13');
                writematrix(Temp_Coordinates_Unit(6,:), output_path, 'Sheet', sheet_name, 'Range', 'B14');
                
                fprintf('    -> Saved: %s\n', output_name);
            catch ME
                fprintf('    ERROR: Could not write Excel file: %s\n', ME.message);
            end
        end
    end
end

fprintf('\nBatch processing complete!\n');
