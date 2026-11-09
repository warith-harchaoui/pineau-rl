import time,os
os.environ['XLA_FLAGS']='--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1'
from sbx import SAC,CrossQ,PPO,TD3
for A,n in [(SAC,5000),(CrossQ,5000),(TD3,5000),(PPO,20000)]:
    t=time.time(); A('MlpPolicy','HalfCheetah-v5',seed=0,verbose=0).learn(n); print(A.__name__,n,round(time.time()-t,1),'s',flush=True)
