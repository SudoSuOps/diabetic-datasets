#!/usr/bin/env python3
"""LocalDiabetic Foot-Care Specialist — CANARY cook (pipeline validation).
8-cap discipline: prove model-load -> LoRA(attn+mlp) -> gradients -> eval -> save -> A/B,
doctrine-pure on the clean 60 deeded education pairs. NO medical/diagnostic data."""
import json, os, sys, time, torch
from transformers import AutoTokenizer, AutoModelForImageTextToText, AutoModelForCausalLM, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model

BASE = "/home/smash/swarmjelly-cook/base"
HERE = os.path.expanduser("~/footcare-cook")
OUT  = os.path.join(HERE, "adapter-canary")
MAXLEN = 1024

def log(s): print(f"[canary] {s}", flush=True)

# ---- gate 1: tokenizer + model load ----
log("loading tokenizer...")
tok = AutoTokenizer.from_pretrained(BASE)
tok = getattr(tok, "tokenizer", tok)            # inner tokenizer if a processor slipped through
if tok.pad_token is None: tok.pad_token = tok.eos_token
log(f"tokenizer ok: {type(tok).__name__}  pad={tok.pad_token}")

log("loading base model (bf16, cuda)...")
t0=time.time()
try:
    model = AutoModelForImageTextToText.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cuda")
    log("loaded via AutoModelForImageTextToText")
except Exception as e:
    log(f"ITT load failed ({e.__class__.__name__}); trying CausalLM")
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cuda")
    log("loaded via AutoModelForCausalLM")
model.config.use_cache = False
log(f"model loaded in {time.time()-t0:.1f}s | params {sum(p.numel() for p in model.parameters())/1e9:.2f}B")

# ---- gate 2: LoRA on attn+mlp ONLY (gold_standard_4b doctrine, NOT linear_attn) ----
lcfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                  target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
model = get_peft_model(model, lcfg)
tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
log(f"LoRA attached | trainable params {tr/1e6:.1f}M ({100*tr/sum(p.numel() for p in model.parameters()):.3f}%)")
if tr == 0: log("FATAL: no trainable params — target_modules did not match"); sys.exit(2)

# ---- data: render chat -> tokenize (labels = input_ids; canary uses full-seq LM loss) ----
def load(fn):
    rows=[json.loads(l) for l in open(os.path.join(HERE,fn)) if l.strip()]
    out=[]
    for r in rows:
        text = tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=False)
        enc = tok(text, truncation=True, max_length=MAXLEN)
        enc["labels"] = enc["input_ids"].copy()
        out.append(enc)
    return out
train_ds, eval_ds = load("footcare_train.jsonl"), load("footcare_eval.jsonl")
log(f"data: train {len(train_ds)} | eval {len(eval_ds)}")

class Collator:
    def __call__(self, feats):
        m = max(len(f["input_ids"]) for f in feats)
        ids=[]; att=[]; lab=[]
        for f in feats:
            p = m - len(f["input_ids"])
            ids.append(f["input_ids"] + [tok.pad_token_id]*p)
            att.append(f["attention_mask"] + [0]*p)
            lab.append(f["labels"] + [-100]*p)
        return {"input_ids":torch.tensor(ids), "attention_mask":torch.tensor(att), "labels":torch.tensor(lab)}

args = TrainingArguments(output_dir=OUT, per_device_train_batch_size=2, gradient_accumulation_steps=4,
    num_train_epochs=3, learning_rate=2e-4, lr_scheduler_type="cosine", warmup_ratio=0.1,
    logging_steps=1, eval_strategy="epoch", save_strategy="no", bf16=True, report_to=[], seed=7)
trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=eval_ds, data_collator=Collator())

# ---- gate 3+4: gradients + eval trajectory ----
log("eval BEFORE training...")
e0 = trainer.evaluate(); log(f"eval_loss before: {e0['eval_loss']:.4f}")
log("training (3 epochs)...")
trainer.train()
e1 = trainer.evaluate(); log(f"eval_loss after:  {e1['eval_loss']:.4f}  (delta {e1['eval_loss']-e0['eval_loss']:+.4f})")

# ---- gate 5: save adapter ----
model.save_pretrained(OUT); log(f"adapter saved -> {OUT}")
log(f"RESULT eval_before={e0['eval_loss']:.4f} eval_after={e1['eval_loss']:.4f} learned={'YES' if e1['eval_loss']<e0['eval_loss'] else 'NO'}")
log("CANARY COMPLETE")
