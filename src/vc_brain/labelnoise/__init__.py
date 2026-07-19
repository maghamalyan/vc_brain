"""Label-noise quantification at scale (Pod C).

Two jobs building on the deep-slice pilot and the HN linkage probe:

- ``screen``: current-day founder-evidence screening of annotated controls
  (LABEL USE ONLY — never features) to estimate label-noise rates among
  high- vs low-gestation controls.
- ``harvest``: HN Algolia "Launch HN"/"Show HN" story harvest for companies
  of scored founders — dated post-founding OUTCOME events (labels).
"""
