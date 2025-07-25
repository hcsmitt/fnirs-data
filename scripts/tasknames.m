%% === USER-DEFINED ===
subject = '01';
sessionFolder = '/Users/smith.hail/Documents/fnirs-data/raw_data/2025-07-24';
outputBase    = '/Users/smith.hail/Documents/fnirs-data/snirf_data';

% Your fixed task order (including repeats if needed)
 taskList = {
   'restingstate'
   'fingertapping'
   'audiobook'
   'heelraise'
   'walk'
   'walk'
   'walkdual'
 };


%% === Detect next available session number ===
subjectDir = fullfile(outputBase, sprintf('sub-%s', subject));
if ~exist(subjectDir, 'dir')
    mkdir(subjectDir);
end

existingSessions = dir(fullfile(subjectDir, 'ses-*'));
existingNums = [];

for k = 1:length(existingSessions)
    tokens = regexp(existingSessions(k).name, 'ses-(\d+)', 'tokens');
    if ~isempty(tokens)
        existingNums(end+1) = str2double(tokens{1}{1});
    end
end

nextSessionNum = max([0, existingNums]) + 1;
sessionLabel   = sprintf('ses-%d', nextSessionNum);

%% === Find all .bin files (excluding LED calibration) ===
allBins  = dir(fullfile(sessionFolder, '*.bin'));
binFiles = allBins(~contains({allBins.name}, 'LEDPowerCalibration'));

% Sort by file modification time to match acquisition order
[~, idx] = sort([binFiles.datenum]);
binFiles = binFiles(idx);

% Confirm task list length matches file count
if length(binFiles) ~= length(taskList)
    error('Mismatch: %d data files found, but %d tasks listed.', length(binFiles), length(taskList));
end

%% === Loop through and convert each ===
taskRunCount = containers.Map();

for i = 1:length(taskList)
    task = taskList{i};
    [~, baseName, ~] = fileparts(binFiles(i).name);
    fullBase = fullfile(sessionFolder, baseName);

    % Convert to SNIRF (in memory only)
    snirf = convertBintoSnirfv3(fullBase, 0);

    % Create save directory
    saveDir = fullfile(subjectDir, sessionLabel);
    if ~exist(saveDir, 'dir')
        mkdir(saveDir);
    end

    % === Determine run number ===
    if isKey(taskRunCount, task)
        taskRunCount(task) = taskRunCount(task) + 1;
    else
        taskRunCount(task) = 1;
    end
    runNumber = taskRunCount(task);

    % === Filenames ===
    snirfFile = sprintf('sub-%s_%s_task-%s_run-%02d_nirs.snirf', subject, sessionLabel, task, runNumber);
    jsonFile  = replace(snirfFile, '.snirf', '.json');

    % === Save SNIRF file ===
    snirf.Save(fullfile(saveDir, snirfFile));

    % === Save JSON sidecar ===
    meta = struct( ...
        'SourceDataRawFileName', baseName, ...
        'SamplingFrequency', round(1/mean(diff(snirf.data.time)), 2), ...
        'NIRSChannelCount', size(snirf.data.dataTimeSeries, 2), ...
        'RecordingDuration', snirf.data.time(end), ...
        'SD', snirf.probe, ...
        'metaDataTags', snirf.metaDataTags ...
    );

    fid = fopen(fullfile(saveDir, jsonFile), 'w');
    fwrite(fid, jsonencode(meta, 'PrettyPrint', true));
    fclose(fid);
end
