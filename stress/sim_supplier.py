"""A simulated arena supplier with HIDDEN parameters, built from the families measured in
stress/ENGINE_MODEL.md (archived real games). It answers buyer e-mails in the arena's message format.

Everything the supplier decides happens in VALUE space: what a term sheet is worth to it per unit in
cash (the arena's own `arena_kit.cost.supplier_value`: payment days at its cash rate, units sold at
the current price before the effective date, freight leg, tooling, chargebacks at its real ppm) plus
per-unit `extras` for lead time, volume and ppm commitment, plus a decision-only `security` bonus for
contract length and an index clause (security, not cash - the arena excludes them from the margin).

Families (see ENGINE_MODEL.md for the evidence):
  first counter   a fraction `first_frac` of its room (standing value - current reservation)
  later steps     reciprocity: `recip` x the buyer's value step, capped at `cap` x opening value per
                  message; no buyer move and no new verified fact -> it holds
  verified facts  a fact counts if its id exists (tacto/data/facts.json, case facts, session offers),
                  is relevant (this supplier / part / index window) and is not a duplicate; each claim
                  TYPE unlocks a hidden lever (lowers the reservation; repeats of a type unlock
                  `lever_repeat` x) and `fact_pass` of it is passed on at once; types without a lever
                  are "true, but it does not change our calculation"
  rival quotes    a verified, cheaper rival offer/quote: it closes `rival_follow` of the gap down to
                  its reservation - half now, the rest with the next e-mail ("check the rest")
  grid            counter prices are rounded UP to its price grid (0.01 / 0.05 / 0.10 / 0.50)
  agreed          the buyer's best sheet is worth at least its next target -> it offers exactly that
  final offer     from reply `final_round` on, or when its room is used up; then it holds
  walk            pushing below a final offer -> walks with `p_walk_final`; patience (insulting
                  offers, no move, contradicted data, timeouts) runs out -> walks; per-round `hazard`;
                  three timeouts in a row -> the thread ends (arena rule)
"""

import math
import random
import re
from datetime import date

from arena_kit.cost import closing_terms, supplier_value

ID_RE = re.compile(r"\b(?:idx|quote|offer|sc|qn|po|cost|fc|news|doc|ctr|rfq|mtg|note|sup|part):[\w.:@#/-]*\w")
CHECKED = ("idx", "quote", "offer", "sc", "qn", "po", "cost", "fc", "news", "doc", "ctr")
LAST_DATA_MONTH = "2026-09"
KIND_WORDS = {
    "index_change": "index change",
    "should_cost": "should cost",
    "price_history": "price history",
    "quality": "scorecard",
    "volume_change": "volume change",
    "news": "news",
    "notice": "notice period",
    "contract": "contract terms",
    "rival_quote": "competitor quote",
}
LABELS = {
    "unit_price": "Unit price (EUR)",
    "payment_days": "Payment terms (days net)",
    "lead_time_days": "Lead time (days)",
    "volume_per_year": "Volume per year (pcs)",
    "contract_months": "Contract term (months)",
    "effective_date": "Price valid from",
    "index_clause": "Index clause",
    "incoterm": "Incoterm",
    "tooling_eur": "Tooling (EUR)",
    "ppm_commitment": "Quality commitment (ppm)",
    "chargeback_eur_per_complaint": "Chargeback per complaint (EUR)",
}
ENDED = {"walked_away", "no_bid"}


def _months(a, b):
    ya, ma = map(int, a.split("-")[:2])
    yb, mb = map(int, b.split("-")[:2])
    return (yb - ya) * 12 + (mb - ma)


def _fmt(field, v):
    if v is None:
        return "none"
    if field == "index_clause":
        return f"{v['series']}, {round(v['material_share'] * 100)}% material, deadband {v['deadband_pct']} %, base {v['base_month']}"
    if isinstance(v, float) or field in ("unit_price", "tooling_eur", "chargeback_eur_per_complaint"):
        return f"{float(v):.2f}"
    return str(v)


def quote_text(title, stated, standard, fixed):
    """A quote document as text, in the labels `arena_kit.docs.quote_terms` parses."""
    lines = [title, "Offered terms"]
    lines += [f"{LABELS[k]} {_fmt(k, v)}" for k, v in stated.items() if k in LABELS]
    lines.append("Our standard terms (apply to everything not stated above)")
    lines += [f"{LABELS[k]} {_fmt(k, v)}" for k, v in standard.items() if k in LABELS and k not in stated and k not in fixed]
    lines.append("Terms fixed by your enquiry")
    lines += [f"{LABELS[k]} {_fmt(k, v)}" for k, v in fixed.items() if k in LABELS]
    return "\n".join(lines)


class Session:
    """What the suppliers of one case share: the data facts, every offer made, cited ids."""

    def __init__(self, case, facts):
        self.case, self.facts = case, facts
        self.case_facts = case.get("facts") or {}
        self.offers = {}  # offer_id -> (supplier_id, terms)
        self.used = set()

    def fact(self, ref):
        if ref in self.case_facts:
            return self.case_facts[ref]
        if ref in self.facts:
            return self.facts[ref]
        if ref in self.offers:
            sid, terms = self.offers[ref]
            return {"supplier": sid, "unit_price": terms.get("unit_price"), "part": (self.case.get("parts") or [None])[0], "_offer": terms}
        return None


class SimSupplier:
    def __init__(self, case, sid, hp, session, seed):
        self.case, self.sid, self.hp, self.s = case, sid, hp, session
        self.key = sid.split(":", 1)[1]
        self.seed = seed
        self.std = dict(hp["standard"])
        self.fixed = dict(case.get("fixed_terms") or {})
        self.neg = list(case["negotiable"])
        self.p_ref = float(hp["opening"]["unit_price"])
        self.round = 0  # buyer messages received (timeouts included)
        self.replies = 0  # e-mails with a decision (not timeouts)
        self.n_msg = 0
        self.status = "open"
        self.closed = None
        self.timeouts_in_row = 0
        self.patience = hp["patience"]
        self.unlocked = {}  # claim type -> count
        self.vb_prev = None
        self.pending_rival = 0.0
        self.final_value = None
        self.rfq = len(case["suppliers"]) > 1
        self.walk_model = hp.get("walk_model", 1)  # 1 = the rules of stress/cases (v1), 2 = recalibrated (cases_v2)
        self.nomove_streak = 0
        self.history = []  # what it did, for calibration and debugging
        self.v_open = self.value(self.full(hp["opening"]))
        self.r_base = hp["r_base"] * self.v_open
        self.r_min = self.r_base - sum(hp["levers"].values()) * self.v_open
        self.r_eff = self.r_base
        self.target = self.v_open
        self.standing = self.full(hp["opening"], keep_stated=True)
        self.offer_id = None

    # ---------------------------------------------------------------- value ---------------------
    def full(self, terms, keep_stated=False):
        """Terms with every negotiable field (gaps from the standard terms)."""
        if keep_stated:
            return dict(terms)
        out = {f: terms.get(f, self.std.get(f, self.fixed.get(f))) for f in self.neg}
        return out

    def _closing(self, terms):
        return closing_terms(self.case, terms, {**self.std, **self.fixed})

    def cash_extra(self, t):
        """EUR per unit a deal's non-price terms bring (+) or cost (-) it, beyond supplier_value."""
        hp, p, e = self.hp, self.p_ref, 0.0
        if "lead_time_days" in self.neg and t.get("lead_time_days") is not None:
            faster = (self.std.get("lead_time_days") or t["lead_time_days"]) - t["lead_time_days"]
            if faster > 0:
                e -= hp["lt_cost"] * faster * p
        if "volume_per_year" in self.neg and self.std.get("volume_per_year"):
            e += hp["vol_elast"] * (t["volume_per_year"] - self.std["volume_per_year"]) / self.std["volume_per_year"] * p
        if "ppm_commitment" in self.neg and self.std.get("ppm_commitment"):
            sp, tp = self.std["ppm_commitment"], t.get("ppm_commitment") or self.std["ppm_commitment"]
            if tp < sp:
                e -= hp["ppm_cost"] * (sp - tp) / sp * p
        return e

    def security(self, t):
        """Decision-only value of contract length and an index clause (security, not cash)."""
        hp, p, e = self.hp, self.p_ref, 0.0
        if "contract_months" in self.neg:
            e += hp["contract_bonus"] * ((t.get("contract_months") or 0) - (self.std.get("contract_months") or 12)) / 12 * p
        if "index_clause" in self.neg and t.get("index_clause"):
            e += (hp["ix_base"] - hp["ix_slope"] * float(t["index_clause"].get("deadband_pct", 0))) * p
        return e

    def cash_value(self, terms):
        t = self._closing(terms)
        sup = {"standard": self.std, "interest_rate": self.hp["rate"], "usual_rate": self.hp.get("usual_rate", self.hp["rate"]),
               "ppm": self.hp["ppm_real"], "extra": self.cash_extra(t)}
        return supplier_value(self.case, terms, sup)

    def value(self, terms):
        return self.cash_value(terms) + self.security(self._closing(terms))

    def price_for(self, terms, target):
        """The price at which `terms` are worth `target` to it, rounded UP to its grid."""
        a = self.value({**terms, "unit_price": 1.0}) - self.value({**terms, "unit_price": 0.0})
        b = self.value({**terms, "unit_price": 0.0})
        p = (target - b) / a if a > 0 else self.p_ref
        g = self.hp["grid"]
        p = math.ceil(round(p / g, 6)) * g
        return round(max(p, g), 2)

    def full_cost(self):
        return self.hp["full_cost_frac"] * self.v_open

    def relationship_supplier(self, terms):
        """The supplier dict `arena_kit.cost.total_cost` needs for the relationship term."""
        t = self._closing(terms)
        return {"standard": self.std, "interest_rate": self.hp["rate"], "usual_rate": self.hp.get("usual_rate", self.hp["rate"]),
                "ppm": self.hp["ppm_real"], "full_cost": self.full_cost(), "extra": self.cash_extra(t)}

    # ---------------------------------------------------------------- terms ---------------------
    def admissible(self, terms):
        """Its answer keeps the buyer's terms where it can live with them (vetoes otherwise)."""
        t = dict(terms)
        maxpd = self.hp.get("max_payment_days")
        if "payment_days" in t and maxpd is not None and t["payment_days"] is not None and t["payment_days"] > maxpd:
            opts = [o for o in (self.case.get("term_options") or {}).get("payment_days", []) if o <= maxpd]
            t["payment_days"] = max(opts) if opts else self.std.get("payment_days")
        return t

    # ---------------------------------------------------------------- claims --------------------
    def check_claims(self, msg):
        """Claims the arena reads from the e-mail: at most 3, typed, with results."""
        body = msg.get("body") or ""
        ids = list(dict.fromkeys(list(msg.get("refs") or []) + ID_RE.findall(body)))
        ids = [i for i in ids if i.split(":", 1)[0] in CHECKED]
        claims, seen = [], set()
        idx = [i for i in ids if i.startswith("idx:")]
        pos = [i for i in ids if i.startswith("po:")]
        docs = [i for i in ids if i.startswith("doc:")]
        ctrs = [i for i in ids if i.startswith("ctr:")]
        for i in ids:
            if i in seen:
                continue
            kind = i.split(":", 1)[0]
            if kind == "idx":
                series = i.split(":", 1)[1].split("@")[0]
                pair = [j for j in idx if j.split(":", 1)[1].split("@")[0] == series and j not in seen][:2]
                seen.update(pair)
                claims.append(("index_change", pair))
            elif kind == "po":
                f = self.s.fact(i)
                part = f.get("part") if f else None
                grp = [j for j in pos if j not in seen and (self.s.fact(j) or {}).get("part") == part][:8] if f else [i]
                seen.update(grp or [i])
                claims.append(("price_history", grp or [i]))
            elif kind in ("doc", "ctr"):
                if kind == "doc" and ctrs:
                    pair = [i, next(c for c in ctrs if c not in seen)] if any(c not in seen for c in ctrs) else [i]
                    seen.update(pair)
                    claims.append(("notice", pair))
                elif kind == "ctr" and docs and any(d not in seen for d in docs):
                    d = next(d for d in docs if d not in seen)
                    seen.update([i, d])
                    claims.append(("notice", [d, i]))
                elif kind == "ctr":
                    seen.add(i)
                    claims.append(("contract", [i]))
                else:
                    seen.add(i)  # a document alone is context, not a check
            else:
                seen.add(i)
                t = {"cost": "should_cost", "fc": "volume_change", "news": "news", "sc": "quality", "qn": "quality"}.get(kind)
                if kind in ("quote", "offer"):
                    f = self.s.fact(i)
                    t = "rival_quote" if (f and f.get("supplier") and f.get("supplier") != self.sid) else "price_history"
                claims.append((t, [i]))
        out = []
        for ctype, refs in claims[:3]:
            out.append((ctype, refs, self._result(ctype, refs, body)))
        return out

    def _sentence_numbers(self, body, ref):
        for sent in re.split(r"(?<=[.!?])\s+|\n", body):
            if ref in sent:
                return [float(x.replace(",", "")) for x in re.findall(r"[-+]?\d[\d,]*\.?\d*(?=\s*%)", sent)], sent
        return [], ""

    def _result(self, ctype, refs, body):
        facts = [self.s.fact(r) for r in refs]
        if any(f is None for f in facts):
            return "contradicted"
        dup_keys = [(self.sid, r) if r.split(":", 1)[0] in ("quote", "offer") else r for r in refs]
        if all(k in self.s.used for k in dup_keys):
            return "duplicate"
        for k in dup_keys:
            self.s.used.add(k)
        parts = set(self.case.get("parts") or [])
        if ctype == "index_change":
            if len(refs) < 2:
                return "irrelevant"
            a, b = sorted(facts, key=lambda f: f["month"])
            if _months(a["month"], b["month"]) > 12 or _months(b["month"], LAST_DATA_MONTH) > 12:
                return "irrelevant"
            change = (b["value"] / a["value"] - 1) * 100
            nums, _ = self._sentence_numbers(body, refs[0])
            if nums and not any(abs(n - change) <= 0.5 for n in nums):
                return "contradicted"
            if not any(abs(n - change) <= 0.5 for n in nums) and not nums:
                pass  # no figure: the data's own value is taken
            series = refs[0].split(":", 1)[1].split("@")[0]
            if series not in self.hp.get("drivers", [series]):
                return "irrelevant" if self.hp.get("strict_drivers") else "verified"
            return "verified"
        if ctype in ("price_history", "should_cost", "volume_change", "rival_quote"):
            if any(f.get("part") and f.get("part") not in parts for f in facts):
                return "irrelevant"
        if ctype in ("price_history", "quality", "news", "notice", "contract"):
            if any(f.get("supplier") and f.get("supplier") != self.sid for f in facts) and ctype != "price_history":
                return "irrelevant"
        if ctype == "news" and facts[0].get("supplier") is None:
            return "irrelevant"
        return "verified"

    # ---------------------------------------------------------------- messages ------------------
    def _rng(self, tag):
        return random.Random(f"{self.seed}:{self.sid}:{self.round}:{tag}")

    def _mail(self, status, sheets, lines, claim_results=(), attach_quote=False):
        self.n_msg += 1
        self.status = status
        out_sheets = []
        if status not in ENDED and sheets:
            self.offer_id = f"offer:{self.key}-{self.round}"
            main = sheets[0]
            self.standing = dict(main)
            self.s.offers[self.offer_id] = (self.sid, dict(main))
            out_sheets.append({"term_sheet_id": self.offer_id, "terms": dict(main)})
            for j, alt in enumerate(sheets[1:3]):
                aid = f"{self.offer_id}-{'abc'[j]}"
                self.s.offers[aid] = (self.sid, dict(alt))
                out_sheets.append({"term_sheet_id": aid, "terms": dict(alt)})
        atts = []
        if attach_quote and out_sheets:
            name = f"quote-{self.offer_id.replace(':', '-')}.pdf"
            atts.append({"attachment_id": f"att:{self.key}-{self.round}-quote", "name": name, "type": "pdf", "content_b64": None,
                         "text": quote_text(f"Quote {self.offer_id}", out_sheets[0]["terms"], self.std, self.fixed)})
        stated = out_sheets[0]["terms"] if out_sheets else {}
        return {
            "thread_id": f"thread:{self.case['case_id'][5:]}:{self.key}",
            "message_id": f"msg:{self.key}-{self.round}-{self.n_msg}",
            "in_reply_to": None,
            "from": f"sales@{self.key}",
            "from_name": f"Sales, supplier {self.key}",
            "to": "Hollerau Pumpenwerke GmbH",
            "subject": f"Re: {self.case.get('title', '')}",
            "body": "Guten Tag,\n\n" + "\n".join(x for x in lines if x) + "\n\nBest regards\nSales",
            "refs": [],
            "action": None,
            "term_sheets": out_sheets,
            "status": status,
            "signals": {"reply_delay_days": 1 + self.round % 3, "validity_days": 30},
            "claim_results": [{"index": i, "result": r} for i, r in enumerate(claim_results)],
            "missing_fields": sorted(set(self.neg) - set(stated)) if out_sheets else [],
            "attachments": atts,
        }

    def _terms_line(self, t):
        bits = [f"a price of EUR {t['unit_price']:.2f} per unit"]
        if "payment_days" in t:
            bits.append(f"payment {t['payment_days']} days net")
        if "lead_time_days" in t:
            bits.append(f"lead time {t['lead_time_days']} days")
        if "volume_per_year" in t:
            bits.append(f"{t['volume_per_year']} pcs a year")
        if "contract_months" in t:
            bits.append(f"a contract term of {t['contract_months']} months")
        if "effective_date" in t:
            bits.append(f"valid from {t['effective_date']}")
        if "index_clause" in t:
            bits.append("an index clause on " + t["index_clause"]["series"] if t["index_clause"] else "no index clause")
        if "ppm_commitment" in t:
            bits.append(f"a quality commitment of {t['ppm_commitment']} ppm")
        if "chargeback_eur_per_complaint" in t:
            bits.append(f"a chargeback of EUR {float(t['chargeback_eur_per_complaint'] or 0):.2f} per complaint")
        if "tooling_eur" in t:
            bits.append(f"tooling EUR {float(t['tooling_eur'] or 0):.2f}")
        return "Our terms: " + ", ".join(bits) + "."

    def opening_message(self):
        hp = self.hp
        lines = ["Thank you for your enquiry. Please find our quote below.", self._terms_line({**hp["opening"]})]
        if hp.get("remark"):
            lines.append(hp["remark"])
        lines.append(f"Our standard payment term is {self.std.get('payment_days')} days net.")
        msg = self._mail("open", [dict(hp["opening"])], lines, attach_quote=True)
        self.target = self.v_open
        return msg

    def timeout(self):
        """The buyer missed its 60 s: the offer stands under a new id; patience drops; three in a row end it."""
        self.round += 1
        self.timeouts_in_row += 1
        self.patience -= 1
        self.history.append({"round": self.round, "kind": "timeout"})
        if self.timeouts_in_row >= 3 or self.round >= self.case.get("round_limit", 10):
            self.closed = "timeout"
            return self._mail("walked_away", [], ["We did not hear from you; we close this enquiry."])
        return self._mail(self.status, [dict(self.standing)], ["We have not heard from you; our offer stands."])

    def walk(self, why, claim_results=()):
        self.closed = "walked_away"
        self.history.append({"round": self.round, "kind": "walk", "why": why})
        return self._mail("walked_away", [], [why, "We must therefore respectfully withdraw from this negotiation."], claim_results)

    def respond(self, msg):
        """Answer one buyer e-mail (already validated by the harness)."""
        hp = self.hp
        self.round += 1
        self.timeouts_in_row = 0
        rng = self._rng("walk")
        sheets = [self.admissible(self.full(ts["terms"])) for ts in (msg.get("term_sheets") or [])]
        claims = self.check_claims(msg)
        results = [r for _, _, r in claims]
        lines = []
        # --- data: levers and trust
        d_lever, new_kinds, rival_vals = 0.0, [], []
        for ctype, refs, res in claims:
            word = KIND_WORDS.get(ctype, "data")
            if res == "verified":
                if ctype == "rival_quote":
                    f = self.s.fact(refs[0])
                    terms = {k: v for k, v in (f.get("_offer") or f).items() if k in self.neg and v is not None and k != "unit_price"}
                    rp = f.get("unit_price")
                    if rp:
                        rv = self.value(self.full({**terms, "unit_price": rp}))
                        rival_vals.append(rv)
                lever = hp["levers"].get(ctype, 0.0)
                n = self.unlocked.get(ctype, 0)
                gain = lever if n == 0 else lever * hp["lever_repeat"] ** n
                self.unlocked[ctype] = n + 1
                if gain > 0:
                    d_lever += gain * self.v_open
                    new_kinds.append(ctype)
                    lines.append(f"We checked the {word} data you cited; it holds and we took it into account.")
                else:
                    lines.append(f"We checked the {word} data you cited; it holds, but it does not change our calculation.")
            elif res == "contradicted":
                if self.walk_model == 1:
                    self.patience -= 1
                self.r_eff = min(self.v_open, self.r_eff + hp["trust_penalty"] * self.v_open)
                lines.append(f"The {word} figures you cite do not match our records.")
            elif res == "irrelevant":
                lines.append(f"The {word} data you cite does not concern us.")
        d_lever = min(d_lever, max(0.0, self.r_eff - self.r_min))
        self.r_eff -= d_lever
        # --- rival pressure: half now, the rest next time
        rival_step = self.pending_rival
        self.pending_rival = 0.0
        if rival_vals:
            rv = min(rival_vals)
            goal = max(self.r_eff, rv * (1 + hp["rival_premium"]))
            gap = max(0.0, self.target - goal) * hp["rival_follow"]
            if gap > 0:
                rival_step += gap / 2
                self.pending_rival = gap / 2
                lines.append("You show a much lower rival quote. We move part of the way now and check the rest.")
        # --- the buyer's best sheet for it
        vb, best = None, None
        for t in sheets:
            v = self.value(t)
            if vb is None or v > vb:
                vb, best = v, t
        step_b = None if (vb is None or self.vb_prev is None) else vb - self.vb_prev
        # --- walk rules
        if self.status == "final_offer":
            if vb is not None and vb >= self.final_value - 1e-9:
                return self._agree(best, lines, results)
            if self.walk_model == 1:
                if vb is not None and rng.random() < hp["p_walk_final"]:
                    return self.walk("We already gave you our final offer; we cannot go further.", results)
            elif vb is not None:  # walk_stats.json: pushes past a final offer
                gap = 1 - vb / self.final_value
                u = rng.random()
                if self.rfq:
                    # RFQ: 34/34 no-sheet pushes and 4/4 pushes 0.06-2.8 % below -> no walk; the 2 pushes 6.5 % and 13.2 %
                    # below (one game) -> walked. Walk chance ramps from 0 at `rfq_gap0` to `p_walk_final_rfq` at `rfq_gap1`
                    ramp = min(1.0, max(0.0, (gap - hp["rfq_gap0"]) / (hp["rfq_gap1"] - hp["rfq_gap0"])))
                    if u < hp["p_walk_final_rfq"] * ramp:
                        return self.walk("Your figure is far below our final offer; we close this enquiry.", results)
                elif gap <= hp["small_gap"]:  # single, within ~1.6 %: agreed 3, walked 1, repeated 1
                    if u < hp["p_agree_small"]:
                        return self._agree(best, lines, results)
                    if u < hp["p_agree_small"] + hp["p_walk_small"]:
                        return self.walk("We already gave you our final offer; we cannot go further.", results)
                elif u < hp["p_walk_final"]:  # single, further below: 4/4 walked
                    return self.walk("We already gave you our final offer; we cannot go further.", results)
            self.replies += 1
            lines.append("Our final offer stands.")
            self.history.append({"round": self.round, "kind": "final_hold", "target": self.target / self.v_open})
            return self._mail("final_offer", [dict(self.standing)], lines + [self._terms_line(self.standing)], results, attach_quote=True)
        no_move = self.replies >= 1 and (step_b is not None and step_b <= 1e-9) and not new_kinds and not rival_vals
        if self.walk_model == 1:
            insult = vb is not None and vb < self.r_min * (1 - hp["insult"])
            slow = (self.replies >= 3 and step_b is not None and vb is not None and not new_kinds and not rival_vals
                    and step_b < hp.get("min_move", 0.0) * max(0.0, self.target - vb))
            if insult or no_move or slow:
                self.patience -= 1
            if self.patience <= 0:
                return self.walk("We are too far apart and see no movement.", results)
            if self.replies >= 2 and hp["hazard"] > 0 and rng.random() < hp["hazard"]:
                return self.walk("We need to plan our capacity and close this enquiry now.", results)
        else:
            # walk_stats.json: insulting offers (0 walks in 253), no-move (2 in 93, never on a 2nd/3rd no-move) and
            # contradicted data (0 in 3) did not make real suppliers walk; 7 walks from open threads in 466 threads, all at
            # reply 3-4 -> a per-reply hazard from the 3rd reply on (single 4/541, RFQ 3/71 replies at risk)
            self.nomove_streak = self.nomove_streak + 1 if no_move else 0
            if self.replies >= 2 and rng.random() < hp["hazard"]:
                return self.walk("We need to plan our capacity and close this enquiry now.", results)
        # --- concession in value space
        room = max(0.0, self.target - self.r_eff)
        if self.replies == 0:
            conc = hp["first_frac"] * room
        elif step_b is None:
            conc = 0.0
        else:
            conc = min(hp["cap"] * self.v_open, hp["recip"] * max(0.0, step_b))
        conc += hp["fact_pass"] * d_lever + rival_step
        new_target = max(self.r_eff, self.target - conc)
        self.replies += 1
        if vb is not None:
            self.vb_prev = vb if self.vb_prev is None else max(self.vb_prev, vb)
        if vb is not None and vb >= new_target - 1e-9:
            return self._agree(best, lines, results)
        terms = best if best is not None else self.full(self.standing)
        price = self.price_for(terms, new_target)
        main = {**terms, "unit_price": price}
        if self.standing.get("unit_price") is not None and all(main.get(k) == self.standing.get(k) for k in self.neg if k != "unit_price"):
            main["unit_price"] = min(price, self.standing["unit_price"])  # never dearer on the same terms
        self.target = self.value(main)
        out = [main]
        if hp["alt_std"] and best is not None:
            std_terms = self.full({})
            if any(std_terms.get(k) != main.get(k) for k in self.neg if k != "unit_price"):
                out.append({**std_terms, "unit_price": self.price_for(std_terms, self.target)})
        final = self.replies >= hp["final_round"] or (self.target - self.r_eff) < 0.002 * self.v_open
        if self.walk_model == 2 and not final and self.nomove_streak >= 2:
            # no-move streak 2 -> final_offer 10/17, streak 3 -> 6/6 (single supplier)
            final = self.nomove_streak >= 3 or self._rng("nomove").random() < hp["p_final_nomove2"]
        status = "final_offer" if final else "open"
        if final:
            self.final_value = self.target
            lines.append("This is our final offer.")
        lines.append(("We have reviewed your offer and can adjust our quote as follows. " if conc > 0 else "We keep our price. ") + self._terms_line(main))
        lines += self._hints()
        self.history.append({"round": self.round, "kind": status, "target": self.target / self.v_open, "conc": conc / self.v_open,
                             "step_b": None if step_b is None else step_b / self.v_open, "levers": d_lever / self.v_open})
        return self._mail(status, out, lines, results, attach_quote=final)

    def _agree(self, terms, lines, results):
        self.replies += 1
        self.target = self.value(terms)
        self.history.append({"round": self.round, "kind": "agreed", "target": self.target / self.v_open})
        lines = lines + ["We can accept your terms and await your order.", self._terms_line(terms)]
        return self._mail("agreed", [dict(terms)], lines, results, attach_quote=True)

    def _hints(self):
        hp, out = self.hp, []
        if hp["rate"] >= 0.09 and "payment_days" in self.neg:
            out.append("Faster payment is welcome; we can reflect it in the price.")
        if hp["vol_elast"] >= 0.08 and "volume_per_year" in self.neg:
            out.append("A binding higher volume would help us and can improve the price.")
        if hp["contract_bonus"] >= 0.004 and "contract_months" in self.neg:
            out.append("A longer commitment gives us planning security.")
        out.append(f"Our standard payment term is {self.std.get('payment_days')} days net.")
        return out


def best_package_cost(case, sup, total_cost, must_haves_ok, combos, prices=24):
    """C_best for one supplier: the cheapest C over every allowed combination of the non-price terms,
    at any price from its absolute floor (all levers applied, `r_min`) up, keeping the must-haves.
    The relationship term is priced with the supplier's hidden full cost and cash rate."""
    best = (math.inf, None)
    for combo in combos:
        terms = sup.full({**combo, "unit_price": sup.p_ref})
        terms = {k: v for k, v in terms.items()}
        a = sup.value({**terms, "unit_price": 1.0}) - sup.value({**terms, "unit_price": 0.0})
        b = sup.value({**terms, "unit_price": 0.0})
        if a <= 0:
            continue
        floor = math.ceil(((sup.r_min - b) / a) * 100 - 1e-6) / 100
        top = max(floor, (sup.v_open - b) / a)  # up to the price that is worth its opening value
        n = max(prices, 2)
        cand = [floor + (top - floor) * i / (n - 1) for i in range(n)]
        for p in cand:
            t = {**terms, "unit_price": round(p, 2)}
            if not must_haves_ok(case, t, sup.std):
                break
            c = total_cost(case, t, sup.std, sup.relationship_supplier(t))
            if c < best[0]:
                best = (c, t)
    return best
