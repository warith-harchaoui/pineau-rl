import json,sys
from pineau_rl.grid import load_overrides
from pineau_rl.stats import wilson as _wilson
from load import load
P2018={'Q1':1.00,'Q2':0.90,'Q3':0.90,'Q4':0.60,'Q5':0.55,'Q6':0.20,'Q7':0.10,'Q8':0.05}
LAB={'Q1':'Paper has experiments','Q2':'Uses neural networks','Q3':'All hyperparams, proposed method','Q4':'All hyperparams, baselines','Q5':'Code is linked','Q6':'Hyperparam selection method specified','Q7':'Hold-out evaluation','Q8':'Significance testing','X2':'Uncertainty reported','X3':'Best-of / top-k selection','X4':'Baselines tuned like the method','X7':'Compute reported'}
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*3
    return (k/n,)+_wilson(k,n,z)
def table(D,ov=None):
    ov=ov or {}
    rows={}
    for k in LAB:
        ys=ns=0
        for i,d in D.items():
            cr=d['criteria']; v=cr.get(k,{}).get('value')
            v=ov.get(k,{}).get(i,v)
            if k!='Q1' and cr.get('Q1',{}).get('value')=='no': continue
            if v in ('yes','no'): ns+=1; ys+= v=='yes'
        rows[k]=(ys,ns)+wilson(ys,ns)
    return rows
if __name__=='__main__':
    ov=load_overrides('overrides.json')
    D=load('ABCDE'); fam={}
    for i,d in D.items(): fam.setdefault(d['criteria']['X5']['value'],{})[i]=d
    print('families',{k:len(v) for k,v in fam.items()})
    T=table(D,ov); TL=table(fam.get('llm',{}),ov); TC=table(fam.get('classic',{}),ov)
    out=[]
    for k in LAB:
        y,n,p,lo,hi=T[k]; ref=P2018.get(k)
        verdict='' if ref is None else ('amélioré' if lo>ref else 'régressé' if hi<ref else 'pas bougé')
        line=dict(k=k,label=LAB[k],y2018=ref,k2026=y,n2026=n,p2026=round(p,3),lo=round(lo,3),hi=round(hi,3),verdict=verdict,llm=f"{TL[k][0]}/{TL[k][1]}",classic=f"{TC[k][0]}/{TC[k][1]}")
        out.append(line); print(line)
    X1=[d['criteria']['X1']['value'] for d in D.values() if d['criteria']['X5']['value']!='theory']
    print('X1 seeds (non-theory):',sorted(X1,key=lambda x:(x is None,x)))
    X6=[d['criteria']['X6']['value'] for d in fam.get('llm',{}).values()]
    print('X6 families (llm):',X6)
    json.dump(out,open('results_2026.json','w'),indent=1,ensure_ascii=False)
