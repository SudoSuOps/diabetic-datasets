# Defendable Diabetic Foot-Care Hard-Facts — Corpus Card

**Status:** CANARY (stage 1 of canary-then-cook) · **Records:** 20 · **Date:** 2026-06-20
**Lane:** foot care (the spear tip) · **Destined for:** the LocalDiabetic foot-care specialist cook → hosted on **diabeticModels.com**

## What this is
The grounded, **cited** knowledge base for the first diabetes cook. Every record is one
hard fact a person can act on, tied to an authoritative source and URL so the reader can
**verify it against the original** — "crystal clear, the recipient verifies." The model is
cooked to ORGANIZE and EDUCATE from these facts; it is **never** cooked to diagnose.

## Doctrine (the guardrails baked into every record)
- **Educate / organize / surface — never diagnose.** `mode` is one of `educate`,
  `surface-to-clinician` (presents a "discuss with your clinician" threshold), or facts
  that describe standard-of-care. No record tells a person "you have X" or "take this dose."
- **Every fact is sourced.** `source` + `source_url` + `retrieved` on every line. A fact
  with no source does not enter the corpus.
- **Open data only.** Public clinical guidance — never a person's vault/PHI. This corpus
  lives on the OpenDiabetic (hive/compute) side; it flows DOWN. PHI never flows up.

## Schema (one JSON object per line)
`id` · `category` · `fact` (the actionable hard fact) · `mode` · `source` · `source_url` ·
`retrieved` · `doctrine`

## Sources in this canary
- **NIDDK / NIH** — "Diabetes & Foot Problems" (patient guidance):
  https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/foot-problems
- **IWGDF 2023** — Practical guidelines on prevention & management of diabetes-related foot
  disease (Schaper et al.): https://iwgdfguidelines.org/guidelines-2023/ · Offloading guideline PDF:
  https://iwgdfguidelines.org/wp-content/uploads/2023/07/IWGDF-2023-06-Offloading-Guideline.pdf

## Categories covered (canary)
daily-inspection · when-to-call · hygiene-washing · moisturizing · nail-care · corns-calluses ·
footwear · footwear-coverage · temperature-protection · circulation · neuropathy ·
professional-exam · risk-stratified-care · offloading · prevention-footwear

## Path from here (canary → cook → show → host)
1. **Canary review (now):** Donovan/SR-hack reads the 20 facts — accurate? on-doctrine
   (no diagnosis creep)? sources trustworthy? Fix before scaling. *(this is the gate)*
2. **Scale the corpus:** add ADA Standards of Care, CDC, Medicare therapeutic-shoe criteria,
   ulcer-stage/Wagner basics (educational), emergency red-flags. Target a few hundred cited facts.
3. **Make training pairs:** turn facts → Q&A / organize / appointment-prep pairs (grounded,
   citation-preserving). Grade with the curator; tier by Royal Jelly.
4. **Cook:** fine-tune a small open base (LFM2.5 / Qwen3.5-class) on a clean rig. Flightsheet first.
5. **Beat-base or kill:** held-out foot-care knowledge eval, deterministic gates, vs the base
   model. Honest receipt into the Gold-Cooks ledger. No beat = no ship.
6. **Show + host:** publish the build on **diabeticModels.com** — the corpus (cited), the recipe,
   the beat-base math, the receipt — and host the model so it flows DOWN to edge brains.
