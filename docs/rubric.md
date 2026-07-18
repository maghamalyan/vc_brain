# VC Brain — Rubric & Constraints (extracted from the official brief)

Source: `research/1784381921507-02-Maschmeyer-Group-The-VC-Brain.docx.pdf` (Hack-Nation ×
Maschmeyer Group, 6th Global AI Hackathon, Challenge 02). Read 2026-07-19.

## Evaluation criteria (exact weights)
| Criterion | Weight | What they look for |
|---|---|---|
| Data Architecture & Intelligence | **30%** | Smart ingestion, dedup, enrichment, reasoning honest about what it knows/doesn't. **Explicit note: generic ingestion won't score highly unless it addresses the cold-start, pre-track-record case.** |
| Investment Utility & Execution | **30%** | Produces a recommendation a human investor could genuinely act on within 24h. Instrumenting speed from first signal → decision. |
| Intelligent Analysis & Trust | **25%** | Synthesizes fragmented signals into decision-ready insights; memo Trust Scores surface evidence + uncertainty transparently. |
| User Experience & Design | **15%** | "Notion-level approachability, Bloomberg-level analytical depth." Usable without technical support. |

## Scope
Sourcing → Screening → Diligence → Decision. Downstream (portfolio monitoring,
follow-on, fund ops, exit) explicitly OUT of scope (FAQ 16). No UI for those.

## MVP must demonstrate (8 items)
1. **Thesis Engine** — configurable (sectors, stage, geography, check size, ownership,
   risk appetite); every recommendation filtered/scored through this lens (FAQ 15:
   hardcoded thesis misses the point).
2. **Smart Data Collection & Management** — heterogeneous sources; data layer matters
   as much as intelligence on top.
3. **Multi-Attribute Reasoning** — compound NL queries in one pass, e.g. "technical
   founder, Berlin, AI infra, enterprise traction, no prior VC backing" (FAQ 12: not
   five manual filters).
4. **Inbound** — apply with deck + company name (minimum bar); fast first-pass screen.
   Over-collecting fields counts against you (FAQ 4).
5. **Outbound** — continuously scan GitHub, launches, hackathons, papers/patents,
   accelerator cohorts; scored the same way as inbound; Activate = trigger a real
   application; both tracks converge into one Screening funnel.
6. **Multi-Axis Screening** — Founder / Market / Idea-vs-Market scored independently,
   each with trend (improving/declining/stable), **never averaged** (FAQ 5).
7. **Evidence-Backed Memos + Trust Score** — Trust Score is **per claim**, not per
   company (FAQ 7); verify externally where possible; flag contradictions.
8. **Investor-Grade UX**.

## Memo requirements (Appendix 1)
- Required sections: Company snapshot, Investment hypotheses, SWOT, Problem & product,
  Traction & KPIs. Others optional — **padding counts against you** (FAQ 8).
- Missing data must be explicitly flagged ("Cap table: not disclosed"), never fabricated
  or silently omitted (FAQ 9). A memo that marks its own gaps scores as MORE trustworthy.

## Founder Score vs 3-axis score (FAQ 6)
Founder Score lives in Memory, persists across applications, never resets, follows the
person. The 3-axis score is per-opportunity. Founder Score is one input into the Founder
axis, not a substitute.

## Strategic guidance from FAQ
- FAQ 1–2: Sourcing is the priority and the least commercially competitive area — "go
  further here than anywhere else." Build sourcing deep + thin-but-transparent
  intelligence layer. Rich data with no honest reasoning scores poorly too.
- FAQ 10–11: Cold-start is THE differentiator. Explicit method for pre-track-record
  founders required. Area of Research 3 (how much do public footprints predict success,
  and how would you test it) is "the most direct lever" — teams that take a real stab
  are "documenting exactly the kind of approach the brief says could be
  industry-defining." → Our retrospective backtest IS this test. Document it as such.
- FAQ 13: If only one stretch goal → **Agentic Traceability** (cite exact data point
  behind each conclusion; step-level reasoning log). Highest leverage, reinforces Trust.
- FAQ 14: If forced to trade, protect data + reasoning (55% combined) over UX (15%).

## Implications for our build (decisions)
1. Sourcing detector + backtest (P2–P5) targets Data Architecture 30% and is framed as
   the Area-of-Research-3 experiment ("we found them first, median lead X months").
2. A thin **end-to-end vertical slice** is required for Utility 30% + Trust 25% + UX 15%:
   discovered founder → 3-axis screen (with trend) → memo (5 required sections,
   per-claim evidence links, explicit gaps) → small investor dashboard (ranked list +
   momentum + memo view + thesis filter).
3. Pitch-deck/idea scoring (user's "objective 2") = the inbound track of core scope,
   not a stretch goal. Minimum input: deck + company name.
4. Trust Score implementation: per-claim `{claim, evidence_refs[], confidence,
   verification_status, contradictions[]}` — flows through memo AND dashboard.
