"""
30秒のscanpathを使用して、MultiMatch用にペアを作成する
ただし、MW率が25% 〜 75%のもののみを使用する、
処理の流れ

1. black_listに含まれない人をランダムで選ぶ
2. その人のMWとFocusのscanpathを読み込む
3. trainとtestに分ける
4. MW-MW, Focus-Focus, MW-Focusのpairを作成し、ラベルを付ける (MW-MW: 0, Focus-Focus: 0, MW-Focus: 1)
5. Random Forestで学習し、精度を出力する

"""

from random import choice, shuffle
import numpy as np
import multimatch_gaze as mm
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report

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

def evaluate_parameters(TDir, TAmp, TDur, MW_training_list, Focus_training_list, MW_test_list, Focus_test_list):
    MW_MW_pair = create_pairs(MW_training_list, MW_training_list, 0, TDir, TAmp, TDur)
    Focus_Focus_pair = create_pairs(Focus_training_list, Focus_training_list, 0, TDir, TAmp, TDur)
    MW_Focus_pair = create_pairs(MW_training_list, Focus_training_list, 1, TDir, TAmp, TDur)

    training_data = MW_MW_pair + Focus_Focus_pair + MW_Focus_pair
    X_train = [pair[0] for pair in training_data]
    y_train = [pair[1] for pair in training_data]

    # Set the best hyperparameters directly
    best_params = {
        'bootstrap': True,
        'max_depth': None,
        'max_features': 'sqrt',
        'min_samples_leaf': 4,
        'min_samples_split': 2,
        'n_estimators': 100
    }

    best_clf = RandomForestClassifier(**best_params, random_state=42)
    best_clf.fit(X_train, y_train)

    test_pairs = create_pairs(MW_test_list, MW_test_list, 0, TDir, TAmp, TDur)
    test_pairs += create_pairs(Focus_test_list, Focus_test_list, 0, TDir, TAmp, TDur)
    test_pairs += create_pairs(MW_test_list, Focus_test_list, 1, TDir, TAmp, TDur)

    X_test = [pair[0] for pair in test_pairs]
    y_test = [pair[1] for pair in test_pairs]

    y_pred = best_clf.predict(X_test)
    
    # Performance Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, best_clf.predict_proba(X_test)[:, 1])
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    return accuracy, precision, recall, f1, roc_auc, cm, report

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

    accuracy, precision, recall, f1, roc_auc, cm, report = evaluate_parameters(TDir, TAmp, TDur, MW_training_list, Focus_training_list, MW_test_list, Focus_test_list)
    print(f"Parameters: TDir={TDir}, TAmp={TAmp}, TDur={TDur} => Accuracy: {accuracy:.2f}%")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1:.2f}")
    print(f"ROC-AUC Score: {roc_auc:.2f}")
    print("Confusion Matrix:")
    print(cm)
    print("Classification Report:")
    print(report)