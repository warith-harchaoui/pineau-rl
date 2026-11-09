import time,torch,gymnasium as gym
torch.set_num_threads(1)
from stable_baselines3 import PPO,SAC
for env_id in ['HalfCheetah-v5','Hopper-v5']:
    e=gym.make(env_id); e.reset(seed=0)
    t=time.time(); PPO('MlpPolicy',env_id,seed=0,verbose=0,device='cpu').learn(20000); print(env_id,'PPO 20k',round(time.time()-t,1),'s')
t=time.time(); SAC('MlpPolicy','HalfCheetah-v5',seed=0,verbose=0,device='cpu').learn(3000); print('SAC 3k',round(time.time()-t,1),'s')
