# Team 🃏 NoIdea: Tacto Negotiation Arena plan

**Goal:** an autonomous buyer agent that wins the Live Final (Sun 12:00, 5 waves × 8 min, hidden
suppliers, no human in the loop). Score = total cost C (price, payment, freight, quality,
relationship, …) vs the best achievable deal. See `tacto/brief/brief.md` and `docs/EDA_FINDINGS.md`.

**Baseline:** naive agent on P01 = **0.58** (replay https://arena.tacto.ai/replay/a44d915880203878).

## Architecture

```
case file ──► PREPARE (code, no LLM)                     ──► NEGOTIATE (LLM)                 ──► CLOSE (code)
              dossier (A) + concessions (B) + verified        playbook for case type (E)          accept best standing sheet
              arguments (C) + lever € values + targets        + dossier + 1-2 best past           if C < alternative and
              (cost-justified change, should-cost floor,      e-mails (D) → e-mail +              must-haves hold; else push
               notice check, motives)                         3 term sheets                       or walk away
```

No fine-tuning: few-shot + retrieval over A–E (reasoning in `docs/EDA_FINDINGS.md` and chat notes).
Models: local Qwen3.5-9B (MLX, `~/Dhruv/local-llm/serve-qwen`, port 8081) for free practice;
a hosted model for the final.

## Workstreams and ownership (each person owns their folders, so no merge conflicts)

| # | Workstream | Owner | Folders / files |
|---|---|---|---|
| W1 | Datasets A/B/C builder + EDA | **Dhruv** | `src/datasets/`, `src/eda/`, `datasets/A_*`, `B_*`, `C_*`, `datasets/dossiers/`, `docs/EDA_FINDINGS.md` |
| W2 | Agent: prepare → negotiate → close, model wiring, Live Final runner | **Dhruv** | `src/agent/`, `tacto/starter-kit/` (kit code) |
| W3 | Per-case deep dives (19 practice cases) | **Neel** | `analysis/cases/` |
| W4 | Supplier economics model (cost floor, cash value, margin) | **Neel** | `analysis/supplier_economics/` |
| W5 | Playbooks per case type (E) | **Neel** | `playbooks/` |
| W6 | Replay collector + episode dataset (D) + lessons | **Neel** | `tools/replays/`, `datasets/D_episodes.jsonl`, `analysis/replay_lessons.md` |
| W7 | Sunday 08:00 release: diff + rebuild | **Neel** writes the diff tool, **Dhruv** reruns W1 | `tools/sunday_release/` |
| W8 | Pitch: slides + one replay walkthrough | both, at the end | `pitch/` |

Interfaces between the workstreams (agree, then don't change silently):
- W2 reads `datasets/dossiers/<sup>.md`, `datasets/C_arguments.jsonl`, `playbooks/<case_type>.md`,
  `analysis/supplier_economics/suppliers.csv` (columns defined in `docs/TASKS_NEEL.md`), and few-shot
  examples from `datasets/D_episodes.jsonl`.
- `<case_type>` is the arena's `type`: `price_increase`, `renewal`, `rfq`, `bundling`, `raw_material`, `capacity`, `quality`.

## Testing workflow
Every agent change: (1) offline trial with Qwen on the Mac, (2) offline trial with gpt-6-astra, (3) live only when both are clean. Details: notes/agent_changelog.md.

## Shared rules
- `git pull --rebase` before every push; commit only inside your own folders.
- **Practice quota: 200 sessions / 24 h per team.** Split: Dhruv 120, Neel 80. Log every session
  you play in `notes/quota_log.md` (time, who, case, score).
- **The API key is never committed.** It's in `.env` (gitignored); get it from Dhruv directly.
- Never let the agent read `/v1/events`, `/screen`, `/leaderboard`, `/results`.

## Milestones
1. A/B/C + EDA done ✅ (this commit)
2. Agent v1 = kit LLM agent + dossier/arguments in the prompt → beat 0.58 on P01
3. Playbooks + per-case briefs wired in → beat the house agent on ≥ 5/10 practice cases
4. Robustness: 10 parallel sessions, timeouts, retries, logging → full practice run
5. Sunday 08:00: `arena data`, rebuild A/B/C, 09:00 pre-flight, 11:30 checklist (`tacto/brief/submission.md`), start the runner before 12:00
