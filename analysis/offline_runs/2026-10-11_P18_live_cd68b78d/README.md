# P18 live cd68b78dfb23022c (2026-10-11 06:11 CEST, local, `noidea_p18_coda2.py`): **0.688 - normal round 2 again; the 2% fix banked its 5.00 floor**

User: "run both" (this record attempt v2, then 5.01 @ 14 d db5 in the 0c968aae state). Offline I passed first (5d29c19).

| our msg | sheets (24 m) | its answer |
|---:|---|---|
| 1 | 6c2813ce's msg 1 byte for byte: 4.77 @ 45 d, no clause | 5.20 @ 45 d (+ 5.30 db5): reproduced, 6 of 6 |
| 2 | 6c2813ce's msg 2 byte for byte except the ask: **4.88** @ 45 d db0 (6c2813ce: 4.90 -> soft 5.00 + 5.10 db5) | **5.10 @ 45 d** (normal): "In response to your improved offer, we are prepared to lower our base price to EUR 5.10"; forecast "does not change our calculation"; "a binding higher volume would help us" |
| 3 | the fix, inside its 2%: 5.10 @ 45 d db5 (0.6957) + 5.00 @ 45 d db0 (0.6883) + labour index (6c2813ce's msg 3 text) | **agreed 5.00 @ 45 d db0**: "We can accept your terms and await your order"; labour "negligible" |
| - | accept | 5.00 @ 45 d db0 = **0.6883** (C 245,255.50) |

## What it establishes
- **6c2813ce's soft round 2 is not reproducible with a changed ask.** Same msg 1, same msg-2 text, ask 4.88 instead of 4.90 ->
  5.10 instead of 5.00. With v1 (07836ace, 4.84 + db5 request) the new msg 2s are 0 of 2 soft; 6c2813ce's 5.00 belongs to its
  exact text. A soft round 2 stays a ~1-in-5 draw per new msg 2.
- **The fix works:** an ask inside its 2% authority of its 5.10 (5.00 db0 / 5.10 db5, both 5.00 to it) was agreed at once: 0.688
  instead of v1's 0.621 on the same branch (+0.067).
- **Given db5 and db0 at the same value it picked db0** (5.00 db0, 0.6883, not 5.10 db5, 0.6957). Lead with db5 only if it is the
  only sheet at that value.
- Team best on P18 stays 0.727 (0c968aae); record 0.756 (Codacabana). Practice sessions left: 325.
