"""load("ABCDEF"): {paper id: v1 reading} of codes/<reader>/*.json, for the readers in that order (pineau_rl.grid)."""
from pineau_rl.grid import load_reads


def load(coders):
    return load_reads("codes", coders)
