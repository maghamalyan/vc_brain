# False-Positive Portrait: The Top 25 Highest-Scoring Non-Founders

**Question.** Who are the humans behind our detector's highest-scoring *controls* (test-pool
logins absent from `data/labels/founders.parquet`, case-insensitive)? How many are actually
founders we failed to label (label noise), how many are people a VC sourcer would want to
meet anyway, and how many are plain false positives?

**Method.** Peak score per control from `data/scores/trajectories.parquet` (2,075 controls);
top 25 by peak. Each person deep-read via authenticated read-only GitHub API
(`users/<login>`, `/repos?sort=updated`, `/orgs`) plus their linked websites/blogs
(2026-07-19). Public data only; every claim carries a URL.

## Classification table

Classes: **NOISE** = evidence of actually founding a company; **INT** = interesting — a
sourcer would plausibly take the meeting; **FP** = clear false positive; **UNVERIFIABLE** =
account no longer exists.

| # | login | peak | peak month | class | one-line evidence | URL |
|---|-------|------|-----------|-------|-------------------|-----|
| 1 | itechdivyanshu | 0.336 | 2025-03 | UNVERIFIABLE | `gh api users/itechdivyanshu` → HTTP 404; account deleted or renamed since scoring | https://github.com/itechdivyanshu |
| 2 | g0rd0n2007 | 0.333 | 2024-09 | FP | Anonymous RC-hobbyist: FrSky telemetry, lidar, oven-control boards; 0 followers, no bio/site | https://github.com/g0rd0n2007 |
| 3 | dimasrmp | 0.309 | 2023-03 | FP | 4 repos, all learning exercises ("learn next js nft", pokemon-nestjs, ekomoditi-test) | https://github.com/dimasrmp |
| 4 | keneth180 | 0.309 | 2025-04 | FP | 5 repos: two static shop pages (MercyVariedades, LicoresYa), a study notebook; 0 followers | https://github.com/keneth180 |
| 5 | fengzi3340 | 0.309 | 2024-01 | FP | Git-mechanics practice repos (submodule-parent/child, learngit) and old Java labs | https://github.com/fengzi3340 |
| 6 | seyyedalimirhoseini | 0.309 | 2024-01 | FP | Laravel course-project repos (webamooz, online_exam, Restaurant_Project); 1 follower | https://github.com/seyyedalimirhoseini |
| 7 | mcolus97 | 0.309 | 2024-05 | FP | ALX bootcamp curriculum repos ("I'm now a ALX Student…"); 2 followers | https://github.com/mcolus97 |
| 8 | abaksy | 0.298 | 2024-09 | FP | MS CS student at UCSD (bio); repos are course notes/projects (CSE221, BranchPredictor) | https://github.com/abaksy |
| 9 | hexondev | 0.298 | 2024-06 | FP | Hobby Godot RTS prototypes, C# recruitment-task repos; no bio, 7 followers | https://github.com/hexondev |
| 10 | joaopaulonsoares | 0.298 | 2023-12 | FP | Employee: company `@gympass`, bio links a work account (joaopaulonsoares-gympass); repos are bootcamp/thesis | https://github.com/joaopaulonsoares |
| 11 | edwardchamberlain | 0.298 | 2023-10 | FP | Maker hobbyist: ESP32 print-plate button, PCB coil generator, IPMI fan GUI; no company traces | https://github.com/edwardchamberlain |
| 12 | ahmedkhlief | 0.298 | 2023-10 | INT | Security researcher; APT-Hunter (1.4k stars), Ninja C2 (841); 351 followers; publishes at shells.systems (personal research blog, no company) | https://github.com/ahmedkhlief/APT-Hunter |
| 13 | lehuygiang28 | 0.297 | 2025-04 | INT | Prolific product-shaped OSS: vnpay payments lib (317 stars), vkara karaoke app, self-created org MixiLabs (2025, empty); no company entity found | https://github.com/lehuygiang28 |
| 14 | dadish | 0.297 | 2023-04 | FP | Nurguly Ashyrov — Software Engineer at Automattic / Toptal freelancer; ProcessGraphQL author, no founding evidence | https://www.toptal.com/resume/nurguly-ashyrov |
| 15 | jimmydalecleveland | 0.297 | 2023-10 | FP | Bio: "Staff Software Engineer", company Denari (employee per LinkedIn); repos are tutorials/demos for blog+YouTube | https://www.linkedin.com/in/jimmy-cleveland-41625442/ |
| 16 | jwetzell | 0.297 | 2024-04 | INT | Building a coherent show-control protocol suite (showbridge + psn-js/osc-go/rttrp-js) with own domain showbridge.io — OSS today, product-shaped; no entity/pricing | https://showbridge.io |
| 17 | agittins | 0.297 | 2024-04 | INT | Maintainer of Bermuda BLE trilateration for Home Assistant (1,881 stars); solo systems consultant ("Hire Me") at ajg.net.au; no company | https://github.com/agittins/bermuda |
| 18 | caioguedesam | 0.297 | 2023-06 | FP | Graphics/games portfolio (Vulkan renderers, game jams); CS graduate building skills, no product/company | https://github.com/caioguedesam |
| 19 | ankansikdar | 0.297 | 2022-10 | FP | Bio: "SAP Technical Consultant"; dozens of sap-cap/sap-build tutorial repos; hireable=true | https://github.com/ankansikdar |
| 20 | athulpg007 | 0.297 | 2023-05 | FP | Planetary-science researcher (AMAT mission-analysis tool) now grinding web-framework tutorial repos | https://github.com/athulpg007 |
| 21 | tuanlc | 0.297 | 2022-10 | FP | Employee: company SKUTOPIA, member of Skutopia-org; repos are boilerplates and a Medium blog | https://github.com/tuanlc |
| 22 | camjjack | 0.297 | 2022-12 | FP | Small personal Rust CLIs (constgrep, preso) + homebrew tap; 2 followers, no bio/site | https://github.com/camjjack |
| 23 | roger-rodriguez | 0.297 | 2023-07 | FP | Employee: `@movableink` (company + org membership); repos incl. employer hiring-challenge forks, Zendesk CLIs | https://github.com/roger-rodriguez |
| 24 | hyrmm | 0.297 | 2024-01 | FP | Chinese dev: WMS admin-panel template (72 stars), CocosCreator plugins, coursework-style projects | https://github.com/hyrmm |
| 25 | samyakkkk | 0.297 | 2024-06 | **NOISE** | Samyak Jain — bio "Build beautiful websites in one prompt", company **LandingHero AI**, site footer "© 2026 LandingHero AI, Inc."; publicly billed as "Founder at LandingHero.AI" | https://www.landinghero.ai |

Supporting URLs for row 25: profile https://github.com/samyakkkk ; founder billing
https://www.instagram.com/p/DT17NjXEZa7/ ("Excited to host Samyak Jain, Founder at
LandingHero.AI"); X handle https://x.com/samyakjain963 (bio: landinghero.ai).

## Counts

| Class | n | share |
|-------|---|-------|
| LABEL NOISE (actual founder, unlabeled) | 1 | 4% |
| INTERESTING (sourcer would plausibly meet) | 4 | 16% |
| CLEAR FALSE POSITIVE | 19 | 76% |
| UNVERIFIABLE (account gone) | 1 | 4% |

Implied label-noise rate among top-scoring negatives: **~4% point estimate (1/25;
exact 95% binomial CI 0.1%–20%)**. The noise case is exactly the predicted species:
a *non-YC* founder (LandingHero AI, Inc. — not in the YC directory), invisible to a
YC-only label source by construction.

## Score-distribution context

Peak scores barely separate the classes at the top: founder peaks (n=690) have median
0.186 / p90 0.293 / max 0.333; control peaks (n=2,075) median 0.206 / p90 0.290 / max
0.336. Above 0.297 sit exactly 27 founders and 27 controls — with a ~3:1 control:founder
pool, that is real lift, but the top of the ranking is a 50/50 coin flip, and the massive
score ties (five people at exactly 0.3090, five at 0.2984, thirteen at 0.2970) show the
model saturating on a few coarse feature buckets rather than producing a continuous
ranking at the top.

## What fools the model (systematic patterns)

1. **Learning bursts masquerade as gestation bursts (11/25).** Bootcamp curricula (ALX),
   university coursework (abaksy, fengzi3340), tutorial grinding (ankansikdar's ~20
   `sap-*` repos; athulpg007's `*-beginner-tutorial` series). A student starting a course
   and a founder starting a company produce the same signature in count-space:
   repo-creation burst + new-language influx + activity acceleration. This is the single
   dominant failure mode.
2. **Content creators & portfolio builders (3/25).** Devs producing demo repos for
   blogs/YouTube (jimmydalecleveland) or job-hunt portfolios (caioguedesam, hexondev)
   generate many small fresh repos with descriptive READMEs.
3. **Hobbyist makers (3/25).** Electronics/RC/3D-printing side projects (g0rd0n2007,
   edwardchamberlain, camjjack): bursty, multi-repo, product-*sounding* descriptions
   ("control board", "button that…"), zero commercial substance.
4. **The interesting near-misses look exactly like pre-founders (4/25).** Own domain +
   docs site + coherent multi-repo product suite (jwetzell/showbridge.io), payments
   library + self-created org (lehuygiang28/MixiLabs), high-adoption OSS tools
   (agittins/bermuda 1.9k stars, ahmedkhlief/APT-Hunter 1.4k stars). These are the FPs a
   sourcing product should *keep* — arguably the detector working as intended.
5. **Employer signals we don't use (4/25).** joaopaulonsoares, tuanlc, roger-rodriguez,
   jimmydalecleveland all declare an employer in `company`/org membership. The model never
   sees this (correctly, for leakage reasons, since features are event-counts ≤ t), but at
   *evaluation/triage* time it is free precision.
6. **Data hygiene:** 1/25 top control (the #1!) is a deleted/renamed account — top-of-list
   candidates should be re-validated against the live API before any demo.

## Implications

### 1. Reported precision is biased downward — modestly

Real founders sitting in the control pool count as false positives, so every reported
precision@k is a floor. Quantified from this sample: at the top of the ranking, ~4% of
"negatives" (1/25) are demonstrably mislabeled founders. Mechanically, if precision@k is
measured on a bucket like the ≥0.297 region (27 labeled founders / 54 people = 50%),
reclassifying the noise case moves it to 28/54 ≈ 52% — roughly a **+2pp absolute / +4%
relative** understatement, with wide uncertainty (1 event). The honest headline: measured
precision is a lower bound, and the bound is tight to within a few points. Two caveats cut
in opposite directions: (a) noise is concentrated exactly where it hurts metrics most
(high scorers get investigated; the 2,050 low-scoring controls are cheap to leave
unaudited), and (b) if we also credit the 4 "interesting" profiles as sourcing successes —
the metric a VC actually cares about — the meet-worthy rate in the top-25 controls is
5/25 = 20%, i.e. **utility-precision runs ~20% higher than label-precision at the top of
the ranking**.

### 2. What should change

- **Negative pool screening (cheap, high value):** before computing metrics, run every
  control's *current* profile through a screen — bio regex (`founder|co-founder|CEO|CTO|
  building X`), `company` field vs. an accelerator+Crunchbase+Form D name list, personal
  `blog` domain that resolves to a product page with an "Inc." footer. Drop or down-weight
  hits (samyakkkk fails three of these checks at once). This is evaluation-time hygiene,
  not a training feature, so no leakage concern.
- **Broaden labels beyond YC:** the one confirmed noise case is a non-YC founder.
  SEC Form D officer names and Product Hunt/Show HN launches (already Pillar 3 of the
  research program) would have caught LandingHero. Every non-YC label source added moves
  metric floors up and cleans the negative pool simultaneously.
- **Drop dead accounts:** re-validate top-k logins against the live API (404s → exclude);
  our single highest-scoring control is unverifiable.
- **Discriminate learning from building:** the dominant FP class (bootcamp/tutorial
  bursts) is trivially separable by *content*, not counts — repo names matching
  curriculum patterns (`alx-*`, `*-tutorial`, course codes), forked-from-education orgs,
  README language. This is precisely the semantic-trajectory annotation of Pillar 1
  (`building_what` = coursework vs. product; `audience_orientation` = self); this portrait
  is direct evidence that Pillar 1 attacks the right failure mode.
- **Report the FP portrait as a product feature:** 20% of the top-scoring "misses" are
  people a sourcer would want to meet anyway. The frozen-clock evaluation should report
  meet-worthy rate alongside strict label precision.

*Compiled 2026-07-19. All GitHub reads via authenticated read-only API as `maghamalyan`;
raw JSON snapshots in the session scratchpad (`user_*.json`, `repos_*.json`, `orgs_*.json`).*
