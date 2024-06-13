from tqdm import tqdm
import numpy as np
import pandas as pd
import math
import os
from collections import defaultdict

#---------- Parameters of Fixation Simplification----------#
TAmp = 100.0
TDir = 45.0
TDur = 0.3

#---------- Parameters of RQA ----------#
linelength = 2
radius = 64
mincluster = 8


taget_file = './Analysis/Summary/FreeViewing/Data/FreeViewing_Summary_30sec.csv'

result = defaultdict((lambda: defaultdict(dict)))

def cart2pol(x, y):
    """Transform cartesian into polar coordinates."""
    rho = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(y, x)
    return rho, theta

def calcangle(x1, x2):
    """Calculate angle between two vectors (saccades)."""
    angle = math.degrees(
        math.acos(np.dot(x1, x2) / (np.linalg.norm(x1) * np.linalg.norm(x2)))
    )
    return angle

def keepsaccade(i, j, sim, data):
    """Helper function for scanpath simplification."""
    for t, k in (
        ("sac", "lenx"),
        ("sac", "leny"),
        ("sac", "x"),
        ("sac", "y"),
        ("sac", "theta"),
        ("sac", "rho"),
        ("fix", "dur"),
    ):
        sim[t][k].insert(j, data[t][k][i])
    return i + 1, j + 1

def _get_empty_path():
    return dict(
        fix=dict(dur=[]),
        sac=dict(
            x=[],
            y=[],
            lenx=[],
            leny=[],
            theta=[],
            rho=[],
        ),
    )

def simlen(path, TAmp, TDur):
    """Simplify scanpaths based on saccadic length."""
    saccades = path["sac"]
    fixations = path["fix"]

    if len(saccades["x"]) < 1:
        return path

    i = 0
    j = 0
    sim = _get_empty_path()
    while i <= len(saccades["x"]) - 1:
        if i == len(saccades["x"]) - 1:
            if saccades["rho"][i] < TAmp:
                if (fixations["dur"][-1] < TDur) or (fixations["dur"][-2] < TDur):
                    v_x = saccades["lenx"][-2] + saccades["lenx"][-1]
                    v_y = saccades["leny"][-2] + saccades["leny"][-1]
                    rho, theta = cart2pol(v_x, v_y)
                    sim["sac"]["lenx"][j - 1] = v_x
                    sim["sac"]["leny"][j - 1] = v_y
                    sim["sac"]["theta"][j - 1] = theta
                    sim["sac"]["rho"][j - 1] = rho
                    sim["fix"]["dur"].insert(j, fixations["dur"][i - 1])
                    j -= 1
                    i += 1
                else:
                    i, j = keepsaccade(i, j, sim, path)
            else:
                i, j = keepsaccade(i, j, sim, path)
        else:
            if (saccades["rho"][i] < TAmp) and (i < len(saccades["x"]) - 1):
                if (fixations["dur"][i + 1] < TDur) or (fixations["dur"][i] < TDur):
                    v_x = saccades["lenx"][i] + saccades["lenx"][i + 1]
                    v_y = saccades["leny"][i] + saccades["leny"][i + 1]
                    rho, theta = cart2pol(v_x, v_y)
                    sim["sac"]["lenx"].insert(j, v_x)
                    sim["sac"]["leny"].insert(j, v_y)
                    sim["sac"]["x"].insert(j, saccades["x"][i])
                    sim["sac"]["y"].insert(j, saccades["y"][i])
                    sim["sac"]["theta"].insert(j, theta)
                    sim["sac"]["rho"].insert(j, rho)
                    sim["fix"]["dur"].insert(j, fixations["dur"][i])
                    i += 2
                    j += 1
                else:
                    i, j = keepsaccade(i, j, sim, path)
            else:
                i, j = keepsaccade(i, j, sim, path)
    sim["fix"]["dur"].append(fixations["dur"][-1])

    return sim

def simdir(path, TDir, TDur):
    """Simplify scanpaths based on angular relations between saccades (direction)."""
    saccades = path["sac"]
    fixations = path["fix"]

    if len(saccades["x"]) < 1:
        return path
    i = 0
    j = 0
    sim = _get_empty_path()
    while i <= len(saccades["x"]) - 1:
        if i < len(saccades["x"]) - 1:
            v1 = [saccades["lenx"][i], saccades["leny"][i]]
            v2 = [saccades["lenx"][i + 1], saccades["leny"][i + 1]]
            angle = calcangle(v1, v2)
        else:
            angle = float("inf")
        if (angle < TDir) & (i < len(saccades["x"]) - 1):
            if fixations["dur"][i + 1] < TDur:
                v_x = saccades["lenx"][i] + saccades["lenx"][i + 1]
                v_y = saccades["leny"][i] + saccades["leny"][i + 1]
                rho, theta = cart2pol(v_x, v_y)
                sim["sac"]["lenx"].insert(j, v_x)
                sim["sac"]["leny"].insert(j, v_y)
                sim["sac"]["x"].insert(j, saccades["x"][i])
                sim["sac"]["y"].insert(j, saccades["y"][i])
                sim["sac"]["theta"].insert(j, theta)
                sim["sac"]["rho"].insert(j, rho)
                sim["fix"]["dur"].insert(j, fixations["dur"][i])
                i += 2
                j += 1
            else:
                i, j = keepsaccade(i, j, sim, path)
        else:
            i, j = keepsaccade(i, j, sim, path)
    sim["fix"]["dur"].append(fixations["dur"][-1])

    return sim

def simplify_scanpath(path, TAmp, TDir, TDur):
    """Simplify scanpaths until no further simplification is possible."""
    prev_length = len(path["fix"]["dur"])
    while True:
        path = simdir(path, TDir, TDur)
        path = simlen(path, TAmp, TDur)
        length = len(path["fix"]["dur"])
        if length == prev_length:
            return path
        else:
            prev_length = length

def gen_scanpath_structure(data):
    """Transform a fixation vector into a vector-based scanpath representation."""
    fixations = dict(x=data["start_x"], y=data["start_y"], dur=data["duration"])

    lenx = np.diff(data["start_x"])
    leny = np.diff(data["start_y"])
    rho, theta = cart2pol(lenx, leny)

    saccades = dict(
        x=data[:-1]["start_x"],
        y=data[:-1]["start_y"],
        lenx=lenx,
        leny=leny,
        theta=theta,
        rho=rho,
    )
    return dict(fix=fixations, sac=saccades)

def get_simplified_fixation_path(simplified_scanpath):
    """Convert the simplified scanpath to the desired format with columns ["start_x", "start_y", "duration"]."""
    fix_x = simplified_scanpath["sac"]["x"] + [simplified_scanpath["sac"]["x"][-1] + simplified_scanpath["sac"]["lenx"][-1]]
    fix_y = simplified_scanpath["sac"]["y"] + [simplified_scanpath["sac"]["y"][-1] + simplified_scanpath["sac"]["leny"][-1]]
    fix_dur = simplified_scanpath["fix"]["dur"]
    simplified_fixation_path = list(zip(fix_x, fix_y, fix_dur))
    return simplified_fixation_path

def retrieve_simplified_fixation(filepath):
    fixation = np.recfromcsv(filepath, delimiter='\t', dtype={'names': ('start_x', 'start_y', 'duration'),
                                                          'formats': ('f8', 'f8', 'f8')})
    
    if not isinstance(fixation, np.recarray) or fixation.shape == () or fixation.shape == (0,) or len(fixation) < 3:
        return None, None
    
    scanpath = gen_scanpath_structure(fixation)
    simplified_scanpath = simplify_scanpath(scanpath, TAmp, TDir, TDur)
    
    simplified_fixation = get_simplified_fixation_path(simplified_scanpath)
    return fixation, simplified_fixation