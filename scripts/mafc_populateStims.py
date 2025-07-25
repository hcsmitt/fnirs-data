#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
save MAFC events.tsv

@author: lcarlton
"""
import cedalion
import cedalion.nirs
import numpy as np
import xarray as xr
import os.path
import pandas as pd
import pdb

xr.set_options(display_expand_data=False)

base_dir_data = "/projectnb/nphfnirs/ns/lcarlton/DATA/MAFC_raw/"

nSubj=14
subject_list = ['sub-0' + str(i+1) if i < 9 else 'sub-' + str(i+1) for i in range(13,nSubj)]

# tasks = ["RS", "WM", "MA", "MAaudio", "WSalt", "Wcont", "squats"]
tasks = ["RS", "MAS", "MASaudio", "audio"]
# nRuns_per_task = [2, 4, 1, 1, 1, 1, 1]
nRuns_per_task = [1,1,1,1]
# duration_per_task = [360, 30, 5, 3, 240, 20, 5]
duration_per_task = [360, 5, [3,5], 3]
# task_name = ['RS', 'WM', 'motion', 'audio', 'walk', 'walk', 'squat']
task_name = ["RS", "motion", ["audio", "motion"], "audio"]

# pdb.set_trace()
for subj in subject_list:
    
    for tt, task in enumerate(tasks):
        
        dur = duration_per_task[tt]
        t_name = task_name[tt]
        
        for rr in range(1, nRuns_per_task[tt]+1):
            
            file_name = f"nirs/{subj}_task-{task}_run-0{rr}_nirs"
            subj_dir = os.path.join(base_dir_data, subj)
            snirf_path = os.path.join(subj_dir, f"{file_name}.snirf")
           
            elements = cedalion.io.read_snirf(snirf_path)
            
            snirf = elements[0]
            
            aux = snirf.aux_ts['digital']
            diff = aux.diff('time')
            
            if type(dur) == list :
                
                stimDict = {t_name[0]: {},
                            t_name[1]: {}
                            }
                stimDict[t_name[0]]['onset'] =  np.where((diff > 0.0001) & (diff < 1.001))[0]
                stimDict[t_name[1]]['onset'] =  np.where(diff > 1.001)[0]
                
                onsets = []
                t_onset = []
                amplitude = []
                duration = []
                tasklist = []
                for ii,stim in enumerate(stimDict.keys()):
                    onsets_tmp =  stimDict[stim]['onset']
                    t_onset_tmp =  np.asarray(aux.time[ stimDict[stim]['onset']])
                    amplitude_tmp = np.ones(len(t_onset_tmp))
                    duration_tmp = np.ones(len(t_onset_tmp)) * dur[ii]
                    tasklist_tmp = [t_name[ii]]*len(t_onset_tmp) 
                    
                    onsets.extend(onsets_tmp)
                    t_onset.extend(t_onset_tmp)
                    amplitude.extend(amplitude_tmp)
                    duration.extend(duration_tmp)
                    tasklist.extend(tasklist_tmp)
                
                
            else  :  
                onsets = np.where(diff > 0.0001)[0]
                t_onset = np.asarray(aux.time[onsets])
                amplitude = np.ones(len(t_onset))
                duration = np.ones(len(t_onset)) * dur
                
                if task == 'WM':
                    
                    passive_index = np.arange(0,len(t_onset),2)
                    active_index = np.arange(1,len(t_onset),2)
                    
                    tasklist = ['passive'  if ii in passive_index else 'active' for ii in range(len(t_onset))]
                else:
                    tasklist = [t_name]*len(t_onset)
                    
            data = {'onset': t_onset, 'duration': duration, 'value': amplitude, 'trial_type': tasklist}
            stim_df = pd.DataFrame(data)
            stim_df = stim_df.sort_values('onset')
            
            tsv_name = f'nirs/{subj}_task-{task}_run-0{rr}_events.tsv'
            tsv_path = os.path.join(subj_dir, tsv_name)
            print(tsv_path)
            
            stim_df.to_csv(tsv_path, sep='\t', index=False, header=True)
                
    
    
