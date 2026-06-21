#!/usr/bin/env python3
"""Scale the CLEAN LocalDiabetic education corpus. Every answer is grounded in a cited
source (NIDDK / IWGDF). Educate/organize, NEVER diagnose. Medical/diagnostic data stays OUT.
Output: messages-format train/eval JSONL for the footcare-edge-4b cook."""
import json, os, random, hashlib
random.seed(7)
SYS = ("You are a diabetic-life educator. You organize and explain in plain, warm language. "
       "You DO NOT diagnose, prescribe, or change medications. For anything medical, you tell "
       "the person to confirm with their clinician.")
ESC = " This is general education, not medical advice — confirm anything about your own health with your clinician."
N = "NIDDK (NIH)"; I = "IWGDF 2023"

# (category, [questions...], grounded_answer, source) — answers grounded in cited guidance.
FACTS = [
 ("daily-inspection", ["Why should I check my feet every day?","How often should I look at my feet?"],
  "Check your feet every single day — tops, bottoms, sides, heels, and between every toe. Diabetes can dull the nerves and slow blood flow, so a small cut or blister can go unnoticed and turn serious. Use a mirror or ask someone for help if you can't see the bottoms.", N),
 ("daily-inspection", ["What am I looking for when I check my feet?","What problems should I watch for on my feet?"],
  "Look for cuts, sores, red spots, swelling, blisters, ingrown toenails, corns, calluses, plantar warts, athlete's foot, and any unusually warm spots. Note anything new and compare both feet.", N),
 ("when-to-call", ["When should I call my doctor about my foot?","A cut on my foot isn't healing — what should I do?"],
  "Contact your provider if a cut, sore, blister, or bruise hasn't started healing after a few days, or if the skin is red, warm, or painful. These can be signs of infection that need attention early.", N),
 ("when-to-call", ["I found a callus with dark spots inside — does that matter?"],
  "A callus with dried blood inside can be an early sign of a wound forming underneath. Don't dig at it — have your provider or podiatrist check it.", N),
 ("hygiene-washing", ["What's the right way to wash my feet?","Is hot water okay for my feet?"],
  "Wash with soap in warm — not hot — water, around 90 to 95°F. Test it with a thermometer or your elbow first, because nerve damage can keep you from feeling that water is too hot. Don't soak, since soaking dries the skin.", N),
 ("hygiene-washing", ["How should I dry my feet?"],
  "Dry your feet gently but thoroughly after washing, especially between the toes, where leftover moisture can lead to infection.", N),
 ("moisturizing", ["Should I put lotion on my feet?","Where do I apply foot lotion?"],
  "Apply a thin coat of lotion or petroleum jelly to the tops and bottoms of your feet to prevent cracking — but never between the toes, where extra moisture invites infection.", N),
 ("nail-care", ["How should I trim my toenails?","Can I cut my own toenails with diabetes?"],
  "Trim toenails after washing, cutting straight across and smoothing the edges with an emery board — don't cut into the corners. If you can't see, feel, or reach your feet, or your nails are thick or curve into the skin, have a podiatrist trim them.", N),
 ("corns-calluses", ["Can I use a corn remover or shave a callus?","How do I deal with corns and calluses?"],
  "Never cut corns or calluses yourself, and don't use corn plasters or liquid removers — they can damage the skin and cause infection. Ask your foot doctor about safe options.", N),
 ("footwear", ["Is it okay to walk barefoot at home?","Should I wear shoes inside?"],
  "Never walk barefoot or in socks alone, indoors or outdoors. Always wear shoes and socks so you don't injure a foot you might not be able to feel.", N),
 ("footwear", ["What should I check before putting my shoes on?"],
  "Look and feel inside your shoes before each wear for pebbles, debris, rough seams, or torn linings — small objects can cause a sore you won't feel.", N),
 ("footwear", ["When is the best time to buy shoes?","How do I break in new shoes safely?"],
  "Buy shoes at the end of the day when your feet are largest, and break new ones in gradually — wear them a few hours at first, then check your feet for red or sore spots.", N),
 ("footwear-coverage", ["Will insurance help pay for diabetic shoes?"],
  "Medicare Part B and some other insurance may help cover specially fitted therapeutic shoes and inserts for people with diabetes — ask your provider about a referral.", N),
 ("temperature-protection", ["Can I use a heating pad on my feet?","How do I keep my feet warm safely?"],
  "Keep your feet away from heaters and open fires, and don't use heating pads or hot water bottles — you could get burned without feeling it. If your feet are cold, wear socks to bed instead.", N),
 ("temperature-protection", ["Do I need to protect my feet outside?"],
  "Wear shoes on hot pavement and at the beach, and put sunscreen on the tops of your feet — sunburn and hot-surface burns are easy to miss when sensation is reduced.", N),
 ("circulation", ["How can I improve blood flow to my feet?"],
  "Prop your feet up when sitting, wiggle your toes and move your ankles for a few minutes several times a day, avoid tight socks, and don't smoke — smoking narrows the vessels that feed your feet.", N),
 ("neuropathy", ["What is diabetic neuropathy?","Why do my feet feel numb or tingly?"],
  "Diabetic neuropathy is nerve damage that can come from high blood glucose over time. It can cause tingling, pain, or loss of feeling — most often in the feet — which is why a daily foot check matters so much.", N),
 ("neuropathy", ["How common is nerve damage in the feet?"],
  "Peripheral neuropathy — nerve damage affecting the feet and legs — occurs in about one-third to one-half of people with diabetes.", N),
 ("neuropathy", ["What is a Charcot foot?"],
  "Charcot foot is a serious change in the foot's shape that can follow nerve damage, with early redness, warmth, and swelling. It needs prompt medical care, so report a hot, swollen foot to your provider right away.", N),
 ("professional-exam", ["How often should a doctor check my feet?"],
  "Ask your care team to look at your feet at every visit — take off your shoes and socks to remind them — and get a thorough foot exam, including feeling and pulse checks, at least once a year, or every visit if you've had ulcers, amputation, or loss of feeling.", N),
 ("offloading", ["What helps a sore on the bottom of the foot heal?"],
  "For a sore on the bottom of the foot, taking pressure off it ('offloading') is key — clinicians often use a total contact cast or a special boot. If you're given a removable boot, wear it for all standing and walking so the wound can heal.", I),
 ("risk-stratified-care", ["How often should I get foot education and care if I'm high risk?"],
  "If you're at higher risk of foot ulcers, guidelines suggest professional foot care and self-care education about every one to three months, and every three to six months at moderate risk.", I),
 ("visit-prep", ["How do I get ready for a podiatry appointment?","What should I bring to my foot doctor?"],
  "Bring your current medication list, note any new foot changes (pain, numbness, color, drainage, sores), wear or bring the shoes you use most, and write down your questions. Take your shoes and socks off so your feet can be examined.", N),
 ("socks", ["What kind of socks are best?"],
  "Wear clean, dry, lightly padded socks without tight elastic or bulky seams that can rub. Change them daily, and choose moisture-wicking material to keep feet dry.", N),
 ("insulin-care", ["How should I store my insulin?"],
  "Keep unopened insulin in the refrigerator, and protect in-use insulin from heat and direct sunlight. Don't freeze it, and don't use insulin that looks clumpy or discolored — ask your pharmacist if you're unsure.", N),
 ("nutrition", ["What's a simple way to plan a diabetes-friendly plate?"],
  "A common approach is the plate method: fill half your plate with non-starchy vegetables, a quarter with lean protein, and a quarter with carbohydrate foods, plus water to drink. Your dietitian can tailor amounts to you.", N),
]

def mk(q,a):
    return {"messages":[{"role":"system","content":SYS},{"role":"user","content":q},{"role":"assistant","content":a.rstrip()+ESC}]}

pairs=[]
for cat,qs,a,src in FACTS:
    for q in qs:
        pairs.append(mk(q,a))

# merge the deeded education QA (already instruction/response, education-only)
HERE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(HERE,"..","data")
for f in ("diabetic-foot-care-qa-sample.jsonl","insulin-storage-handling-sample.jsonl","diabetic-plate-nutrition-sample.jsonl"):
    p=os.path.join(DATA,f)
    if os.path.exists(p):
        for l in open(p):
            l=l.strip()
            if not l: continue
            d=json.loads(l); q=d.get("instruction") or d.get("question"); a=d.get("response") or d.get("answer")
            if q and a: pairs.append({"messages":[{"role":"system","content":SYS},{"role":"user","content":q},{"role":"assistant","content":a}]})

# dedup by (question, answer)
seen=set(); uniq=[]
for p in pairs:
    k=(p["messages"][1]["content"], p["messages"][2]["content"][:80])
    if k in seen: continue
    seen.add(k); uniq.append(p)
random.shuffle(uniq)
n_eval=max(12,len(uniq)//8)
ev,tr=uniq[:n_eval],uniq[n_eval:]
open("footcare_train_v2.jsonl","w").write("\n".join(json.dumps(x,ensure_ascii=False) for x in tr)+"\n")
open("footcare_eval_v2.jsonl","w").write("\n".join(json.dumps(x,ensure_ascii=False) for x in ev)+"\n")
print(f"clean education pairs: {len(uniq)}  ->  train {len(tr)} | eval {len(ev)}")
for fn in ("footcare_train_v2.jsonl","footcare_eval_v2.jsonl"):
    print(f"  {fn}: sha {hashlib.sha256(open(fn,'rb').read()).hexdigest()[:16]}  size {os.path.getsize(fn)}B")
