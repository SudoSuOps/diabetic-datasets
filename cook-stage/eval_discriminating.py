#!/usr/bin/env python3
"""footcare-edge-4b — DISCRIMINATING beat-base A/B (reuses saved adapter-v2, no retrain).
The doctrine gates (escalation/no-diagnosis) are a FLOOR both models clear. The discriminating
signal is FACT SPECIFICITY: does the answer reproduce the grounded, sourced specifics, or stay
vague? Tuned (trained on the cited facts) should be more specific than base."""
import json, os, re, torch
from transformers import AutoTokenizer, AutoModelForImageTextToText
from peft import PeftModel
BASE="/home/smash/swarmjelly-cook/base"; HERE=os.path.expanduser("~/footcare-cook"); ADP=os.path.join(HERE,"adapter-v2")
def log(s): print(f"[eval] {s}",flush=True)
tok=AutoTokenizer.from_pretrained(BASE); tok=getattr(tok,"tokenizer",tok)
if tok.pad_token is None: tok.pad_token=tok.eos_token
model=AutoModelForImageTextToText.from_pretrained(BASE,dtype=torch.bfloat16,device_map="cuda")
model=PeftModel.from_pretrained(model,ADP); model.eval()
SYS="You are a diabetic-life educator. You organize and explain in plain, warm language. You DO NOT diagnose, prescribe, or change medications. For anything medical, you tell the person to confirm with their clinician."
STOP=set("this that with your from have when what which they them then will been must about into more some over only just like also your you the and for are can not but may use".split())
def words(t): return {w for w in re.findall(r"[a-z]{5,}",t.lower()) if w not in STOP}
def gen(q):
    txt=tok.apply_chat_template([{"role":"system","content":SYS},{"role":"user","content":q}],tokenize=False,add_generation_prompt=True)
    ids=tok(txt,return_tensors="pt").to(model.device)
    with torch.no_grad(): o=model.generate(**ids,max_new_tokens=200,do_sample=False,pad_token_id=tok.pad_token_id)
    return re.sub(r"<think>.*?</think>","",tok.decode(o[0][ids['input_ids'].shape[1]:],skip_special_tokens=True),flags=re.DOTALL).strip()
rows=[json.loads(l) for l in open(os.path.join(HERE,"footcare_eval_v2.jsonl")) if l.strip()]
b_spec=t_spec=b_win=t_win=0; samples=[]
for i,r in enumerate(rows):
    q=r["messages"][1]["content"]; ref=r["messages"][2]["content"]
    rw=words(ref)
    with model.disable_adapter(): b=gen(q)
    t=gen(q)
    bs=len(words(b)&rw); ts=len(words(t)&rw)   # specificity = grounded content-word overlap
    b_spec+=bs; t_spec+=ts; b_win+= bs>ts; t_win+= ts>bs
    if i<3: samples.append((q,ref,b,t,bs,ts))
n=len(rows)
log(f"avg fact-specificity  BASE {b_spec/n:.2f}  vs  TUNED {t_spec/n:.2f}")
log(f"per-question more-specific wins  BASE {b_win}  vs  TUNED {t_win}  (ties {n-b_win-t_win})")
log(f"RESULT beat_base={'YES' if t_spec>b_spec else 'NO'}  (specificity delta +{(t_spec-b_spec)/n:.2f}/q)")
for q,ref,b,t,bs,ts in samples:
    print("\n――― Q:",q)
    print(f"  BASE  (spec {bs}): {b[:220]}")
    print(f"  TUNED (spec {ts}): {t[:220]}")
    print(f"  REF: {ref[:150]}")
log("EVAL COMPLETE")
