import time,sys
from sbx import SAC,CrossQ
A={'sac':SAC,'crossq':CrossQ}[sys.argv[1]]
m=A('MlpPolicy','HalfCheetah-v5',seed=0,verbose=0,learning_starts=100)
t=time.time(); m.learn(300); a=time.time()-t
t=time.time(); m.learn(1000,reset_num_timesteps=False); b=time.time()-t
print(sys.argv[1],'first300',round(a,1),'next1000',round(b,1),'s ->',round(b,1),'ms/step',flush=True)
