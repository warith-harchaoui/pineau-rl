import json,glob
def load(coders):
    D={}
    for c in coders:
        for f in sorted(glob.glob(f'codes/{c}/*.json')):
            d=json.load(open(f)); D[d['id']]=d
    return D
