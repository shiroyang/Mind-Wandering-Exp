import multimatch_gaze as m
import numpy as np

screen_size = [1920, 1080]
participant = '1Y'
stimuli1 = 'Brazil_1_MW'
stimuli2 = 'Brazil_3_MW'
stimuli3 = 'France_3_Focus'
stimuli4 = 'HongKong_3_Focus'

TDir = 45.0
TAmp = 100.0
TDur = 0.3

# read in data
fix_vector1 = np.recfromcsv(f'./Preprocess/FreeViewing/Scanpath/MultiMatch/{participant}/{participant}_{stimuli1}.tsv',
delimiter='\t', dtype={'names': ('start_x', 'start_y', 'duration'),
'formats': ('f8', 'f8', 'f8')})
fix_vector2 = np.recfromcsv(f'./Preprocess/FreeViewing/Scanpath/MultiMatch/{participant}/{participant}_{stimuli2}.tsv',
delimiter='\t', dtype={'names': ('start_x', 'start_y', 'duration'),
'formats': ('f8', 'f8', 'f8')})
fix_vector3 = np.recfromcsv(f'./Preprocess/FreeViewing/Scanpath/MultiMatch/{participant}/{participant}_{stimuli3}.tsv',
delimiter='\t', dtype={'names': ('start_x', 'start_y', 'duration'),
'formats': ('f8', 'f8', 'f8')})
fix_vector4 = np.recfromcsv(f'./Preprocess/FreeViewing/Scanpath/MultiMatch/{participant}/{participant}_{stimuli4}.tsv',
delimiter='\t', dtype={'names': ('start_x', 'start_y', 'duration'),
'formats': ('f8', 'f8', 'f8')})


print("------Same state------")
print(m.docomparison(fix_vector1, fix_vector2, screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur))
print(m.docomparison(fix_vector3, fix_vector4, screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur))
print("------Different state------")
print(m.docomparison(fix_vector1, fix_vector3, screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur))
print(m.docomparison(fix_vector1, fix_vector4, screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur))
print(m.docomparison(fix_vector2, fix_vector3, screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur))
print(m.docomparison(fix_vector2, fix_vector4, screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur))