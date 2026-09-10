import random
from rocket import Rocket, Configuration
from components import Component


def generateRandomValidConfiguration(rocket, components, maxAttempts=1000):
    for _ in range(maxAttempts):
        placements = [(c, c.mutate(rocket.numSlots)) for c in components]
        cfg = Configuration(rocket, placements)
        if cfg.isValid()[0]:
            return cfg
    return None


def randomSearch(rocket, components, numTrials=500):
    bestCfg   = None
    bestScore = float("-inf")
    allScores = []

    for _ in range(numTrials):
        cfg = generateRandomValidConfiguration(rocket, components)
        if cfg is None:
            continue
        score = cfg.fitnessScore()
        allScores.append(score)
        if score > bestScore:
            bestScore = score
            bestCfg   = cfg

    return bestCfg, allScores