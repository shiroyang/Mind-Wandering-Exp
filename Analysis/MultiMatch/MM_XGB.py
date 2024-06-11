import xgboost as xgb
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score

from random import choice, shuffle
import numpy as np
import multimatch_gaze as mm
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV

screen_size = [1920, 1080]
TDir = 45.0
TAmp = 100.0
TDur = 0.3

# training_num <= 5
training_num = 3
missing_data = ["22K", "25I", "29N", "39Y"]
too_focus = ["8I", "32S", "37T", "30Y", "27I", "7Y", "19M", "23H", "34I", "35S"]
too_MW = ["24K", "31M", "26K", "21H", "10H"]
black_list = set(missing_data + too_focus + too_MW)
print(len(black_list))

def read_scanpaths(input_dir, file_list):
    return [np.recfromcsv(os.path.join(input_dir, file), delimiter='\t', dtype=[('start_x', 'f8'), ('start_y', 'f8'), ('duration', 'f8')]) for file in file_list]

def create_pairs(scanpath_list1, scanpath_list2, label, TDir, TAmp, TDur):
    pairs = []
    for i in range(len(scanpath_list1)):
        for j in range(len(scanpath_list2)):
            similarity = mm.docomparison(scanpath_list1[i], scanpath_list2[j], screensize=screen_size, grouping=True, TDir=TDir, TAmp=TAmp, TDur=TDur)
            pairs.append((similarity, label))
    return pairs

def evaluate_xgboost_parameters(TDir, TAmp, TDur, MW_training_list, Focus_training_list, MW_test_list, Focus_test_list):
    MW_MW_pair = create_pairs(MW_training_list, MW_training_list, 0, TDir, TAmp, TDur)
    Focus_Focus_pair = create_pairs(Focus_training_list, Focus_training_list, 0, TDir, TAmp, TDur)
    MW_Focus_pair = create_pairs(MW_training_list, Focus_training_list, 1, TDir, TAmp, TDur)

    training_data = MW_MW_pair + Focus_Focus_pair + MW_Focus_pair
    X_train = [pair[0] for pair in training_data]
    y_train = [pair[1] for pair in training_data]

    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.6, 0.8, 1.0],
        'colsample_bytree': [0.6, 0.8, 1.0]
    }

    clf = xgb.XGBClassifier(random_state=42, use_label_encoder=False)
    grid_search = GridSearchCV(estimator=clf, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2)

    grid_search.fit(X_train, y_train)
    
    print(f"Best parameters: {grid_search.best_params_}")
    best_clf = grid_search.best_estimator_

    test_pairs = create_pairs(MW_test_list, MW_test_list, 0, TDir, TAmp, TDur)
    test_pairs += create_pairs(Focus_test_list, Focus_test_list, 0, TDir, TAmp, TDur)
    test_pairs += create_pairs(MW_test_list, Focus_test_list, 1, TDir, TAmp, TDur)

    X_test = [pair[0] for pair in test_pairs]
    y_test = [pair[1] for pair in test_pairs]

    y_pred = best_clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    return accuracy

if __name__ == '__main__':
    input_dir = "./Preprocess/FreeViewing/Scanpath/MultiMatch"
    name_list = [name for name in os.listdir(input_dir) if name not in black_list and not name.startswith(".")]
    name = choice(name_list)
    print("Choosing {} as the individual test".format(name))
    input_dir = os.path.join(input_dir, name)
    Focus_stim_list = [name for name in os.listdir(input_dir) if name.endswith("Focus.tsv")]
    MW_stim_list = [name for name in os.listdir(input_dir) if name.endswith("MW.tsv")]
    Focus_list = read_scanpaths(input_dir, Focus_stim_list)
    MW_list = read_scanpaths(input_dir, MW_stim_list)

    print("Participant {} has {} Focus and {} MW stimuli".format(name, len(Focus_list), len(MW_list)))
    print("Choosing {} MW and {} Focus stimuli for training".format(training_num, training_num))
    
    shuffle(Focus_stim_list)
    shuffle(MW_stim_list)
    
    MW_training_list = MW_list[:training_num]
    Focus_training_list = Focus_list[:training_num]
    
    MW_test_list = MW_list[training_num:]
    Focus_test_list = Focus_list[training_num:]
    
    # Ensure balanced test set
    min_test_samples = min(len(MW_test_list), len(Focus_test_list))
    MW_test_list = MW_test_list[:min_test_samples]
    Focus_test_list = Focus_test_list[:min_test_samples]

    accuracy = evaluate_xgboost_parameters(TDir, TAmp, TDur, MW_training_list, Focus_training_list, MW_test_list, Focus_test_list)
    print(f"Parameters: TDir={TDir}, TAmp={TAmp}, TDur={TDur} => Accuracy: {accuracy:.2f}%")
