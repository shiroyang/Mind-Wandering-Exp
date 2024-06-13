"""
In this code, we will directly read the scanpath data prepared for the MultiMatch

However the format of the scanpath is slightly different so we need to adjust the code accordingly.
MM: [x, y, duration], (pixel, pixel, second)
RQA: [x, y, duration], (pixel, pixel, millisecond)
"""

from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import os
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import entropy
from skimage.measure import label, regionprops

# ------------Parameters of RQA------------
linelength = 2
radius = 64
mincluster = 8

result = defaultdict((lambda: defaultdict(dict)))

# -----------------RqaDur.py starts here-----------------

def RqaDur(fixations, dur, param):
    """Computes RQA of fixations with durations dur
    result = Rqa(fixations, dur, param)

    parameter:

    fixations             list of [x,y] fixations or
                          list of categories
    dur                   list of fixation durations
    param['linelength']   threshold linelength, e.g. 2
    param['radius']       e.g. 64. For categories use 0.1
    param['mincluster']   e.g. 8, minimum size of clusters in recurrence matrix

    result:

    result['n']           n (length of fixations)
    result['recmat']      recurrence matrix
    result['nrec']        number of recurrences
    result['rec']         percentage of recurrences
    result['det']         determinism
    result['meanline']    meanline
    result['maxline']     maxline
    result['ent']         entropy
    result['relent']      relative entropy
    result['lam']         laminarity
    result['tt']          TT
    result['corm']        center of recurrence mass
    result['clusters']    number of recurrence clusters / nTriangle

    Author                Walter F. Bischof
    Date                  October 2018
    """

    # Default return values
    result = {}
    result['n'] = np.nan
    result['recmat'] = np.nan
    result['nrec'] = np.nan
    result['rec'] = np.nan
    result['det'] = np.nan
    result['revdet'] = np.nan
    result['meanline'] = np.nan
    result['maxline'] = np.nan
    result['ent'] = np.nan
    result['relent'] = np.nan
    result['lam'] = np.nan
    result['tt'] = np.nan
    result['corm'] = np.nan
    result['clusters'] = np.nan

    n = len(fixations)
    result['n'] = n

    if n <= 1:
        return result

    # Distance matrix

    if not isinstance(fixations[0], list):
        fixations = [[v] for v in fixations]
    distance_matrix = cdist(fixations, fixations)
    ntriangle = n * (n - 1) / 2

    # Recurrence matrix
    recurrence_matrix = (distance_matrix <= param['radius']) * 1
    dm = np.tile(dur,[n,1])
    duration_matrix = dm + np.transpose(dm)
    recurrence_matrix = recurrence_matrix * duration_matrix
    result['recmat'] = recurrence_matrix.tolist()

    # Diagonal not needed for most measures
    partial_recurrence_matrix = np.triu(recurrence_matrix, 1)

    # Diagonals of recurrence matrix, excluding main diagonal
    recurrence_diagonals = [np.diag(recurrence_matrix, d) for d in range(1, n)]

    # Sums
    sum_r = np.sum(partial_recurrence_matrix)
    sum_t = np.sum(dur)

    # Global measures
    result['nrec'] = sum_r
    result['rec'] = 100.0 * sum_r / ((n - 1) * sum_t)

    # Diagonal line measures
    ndiagonals = n - 1
    thresholded_diagonals = []
    for diag in recurrence_diagonals:
        durlist = compute_duration_list(diag,param['linelength'])
        thresholded_diagonals.extend(durlist)

    if thresholded_diagonals:
        result['det'] = 100 * np.sum(thresholded_diagonals) / sum_r
        result['meanline'] = np.mean(thresholded_diagonals)
        result['maxline'] = np.max(thresholded_diagonals)
        result['ent'], result['relent'] = compute_entropy(thresholded_diagonals, \
                param['linelength'], result['maxline'])

    # Corm
    corm = 0
    for i in range(ndiagonals):
        corm = corm + np.sum(recurrence_diagonals[i]) * (i + 1)
    corm = 100.0 * corm / ((n - 1) * sum_r)
    result['corm'] = corm

    # Reverse det is like det but on the minor diagonal.
    # Revdet indicates a scanpath that is repeated in the opposite direction.
    flip_partial_recurrence_matrix = np.flipud(np.triu(recurrence_matrix, 1))
    recurrence_diagonals = \
        [np.diag(flip_partial_recurrence_matrix, d) for d in range(-n+1, n)]
    thresholded_diagonals = []
    for diag in recurrence_diagonals:
        durlist = compute_duration_list(diag,param['linelength'])
        thresholded_diagonals.extend(durlist)

    if thresholded_diagonals:
        result['revdet'] = 100 * np.sum(thresholded_diagonals) / sum_r

    # horizontal+vertical line measures: laminarity and TT.
    # These are slightly different from Zbilut & Webber and Marwan
    # #(verticals + horizontals) in upper triangle =
    # #(verticals) in upper + #(verticals) in lower triangle
    # Set diagonal to zero to avoid counting over the diagonal

    rm = recurrence_matrix.copy()
    np.fill_diagonal(rm, 0)
    thresholded_verticals = []
    for vertical in rm:
        durlist = compute_duration_list(vertical,param['linelength'])
        thresholded_verticals.extend(durlist)

    if thresholded_verticals:
        result['lam'] = 100.0 * np.sum(thresholded_verticals) / np.sum(recurrence_matrix)
        result['tt'] = np.mean(thresholded_verticals)

    # Recurrence clusters
    result['clusters'] = \
        compute_recurrence_clusters(recurrence_matrix, param['mincluster'], ntriangle)

    return result

# -----------------------------------------------------------------------------
# Compute_entropy
# -----------------------------------------------------------------------------

def compute_entropy(a, min_length, max_length):
    """Computes entropy and relative entropy of length vectors."""

    _, counts = np.unique(a, return_counts=True)
    ent = entropy(counts, base=2)
    if min_length == max_length:
        rel_ent = np.nan
    else:
        rel_ent = ent / np.log2(max_length - min_length + 1)
    return ent, rel_ent

# -----------------------------------------------------------------------------
# Compute_recurrence_clusters
# -----------------------------------------------------------------------------

def compute_recurrence_clusters(recmat, threshold, ntriangle):
    """Compute number of recurrence clusters normalized by ntriangle
    see www.programcreek.com/python/example/88831/skimage.measure.regionprops
    """
    recmat = np.triu(recmat, 1)
    label_image = label(recmat, connectivity=2)
    total = 0
    for region in regionprops(label_image):
        if region.area >= threshold:
            total += region.area
    clusters = total * 100 / ntriangle
    return clusters

# -----------------------------------------------------------------------------
# Compute_duration_list
# -----------------------------------------------------------------------------

def compute_duration_list(a,minline):
    count = 0
    dursum = 0
    durlist = []
    a = np.r_[0, a, 0]
    for i in range(len(a)):
        if a[i] > 0:
            count+=1
            dursum += a[i]
        elif count > 0:
            if count >= minline:
                durlist.append(dursum)
            count = 0
            dursum = 0
    return durlist


# -----------------RqaDur.py ends here--------------------


def exract_RQA_features(filepath, participant, stimuli, result):

    # Example 1:
    # The input consists of a n x 3 matrix of fixations in (x,y) coordinates.
    # plus fixation durations
    df = pd.read_csv(filepath, delimiter='\t')
    df["duration"] = df["duration"] * 1000
    fixation_duration = df.values.tolist()
    

    fixations = [[fd[0],fd[1]] for fd in fixation_duration]
    durations = [fd[2] for fd in fixation_duration]

    param = {}
    param['linelength'] = linelength
    param['radius'] = radius
    param['mincluster'] = mincluster

    d = RqaDur(fixations, durations, param)
    d['recmat']='suppressed'
    for key, value in d.items():
        result[participant][stimuli][key] = value
    

def save_RQA_features(filepath):
    pass

# ----------------------------------------------------------------------
# Program Start
# ----------------------------------------------------------------------

if __name__ == "__main__":
    input_dir = './Preprocess/FreeViewing/Scanpath/MultiMatch'
    name_list = [name for name in os.listdir(input_dir) if not name.startswith('.')]
    for name in tqdm(name_list):
        name_dir = os.path.join(input_dir, name)    
        file_list = [file for file in os.listdir(name_dir) if not file.startswith('.')]
        for file in file_list:
            file_path = os.path.join(name_dir, file)
            participant = name
            stimuli = file.split('_')[1] + '_' + file.split('_')[2]
            exract_RQA_features(file_path, participant, stimuli)
            break
        break
    
    print(result)