import sys,time,torch
from transformers import AutoModelForCausalLM, AutoTokenizer
for M in ["Qwen/Qwen2.5-0.5B-Instruct","unsloth/Llama-3.2-1B-Instruct"]:
    tok=AutoTokenizer.from_pretrained(M); tok.pad_token=tok.pad_token or tok.eos_token; tok.padding_side="left"
    m=AutoModelForCausalLM.from_pretrained(M,torch_dtype=torch.float32).to("mps").eval()
    for q in ["What is 37 + 58 + 91?","What is 34 * 27?"]:
        p=tok.apply_chat_template([{"role":"user","content":q+" Think step by step, then finish with the final answer as an integer."}],tokenize=False,add_generation_prompt=True)
        e=tok(p,return_tensors="pt").to("mps"); t=time.time()
        o=m.generate(**e,max_new_tokens=160,do_sample=False,pad_token_id=tok.pad_token_id)
        s=o[0][e["input_ids"].shape[1]:]; print(M.split('/')[1],len(s),'tok',round(time.time()-t,1),'s |',repr(tok.decode(s,skip_special_tokens=True)))
