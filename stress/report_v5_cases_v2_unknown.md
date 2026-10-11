# Stress report `v5_cases_v2_unknown`

NOIDEA_EXPERIMENTS=`hidden` - 190 cases, offline simulator (stress/sim_supplier.py).

## Overall

| Overall | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 190 | 0.560 | 0.623 | 0.000 | 8% | 12% | 5% | 3% | 0 | 0 | 3.32 |

## By case type

| type | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bundling | 20 | 0.721 | 0.690 | 0.530 | 15% | 15% | 15% | 0% | 0 | 0 | 4.35 |
| capacity | 20 | 0.905 | 0.938 | 0.757 | 0% | 0% | 0% | 0% | 0 | 0 | 2.05 |
| price_increase | 40 | 0.517 | 0.561 | 0.000 | 2% | 0% | 0% | 2% | 0 | 0 | 3.33 |
| quality | 20 | 0.558 | 0.554 | 0.177 | 40% | 20% | 20% | 20% | 0 | 0 | 4.55 |
| raw_material | 30 | 0.418 | 0.348 | 0.000 | 3% | 3% | 3% | 0% | 0 | 0 | 3.9 |
| renewal | 40 | 0.625 | 0.704 | 0.000 | 5% | 5% | 5% | 0% | 0 | 0 | 2.17 |
| rfq | 20 | 0.228 | 0.204 | 0.000 | 0% | 65% | 0% | 0% | 0 | 0 | 3.75 |

## By template

| template | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case:P01 | 10 | 0.481 | 0.503 | 0.057 | 10% | 0% | 0% | 10% | 0 | 0 | 2.9 |
| case:P02 | 10 | 0.547 | 0.551 | 0.000 | 0% | 0% | 0% | 0% | 0 | 0 | 3 |
| case:P03 | 10 | 0.767 | 0.857 | 0.000 | 10% | 10% | 10% | 0% | 0 | 0 | 2.2 |
| case:P04 | 10 | 0.404 | 0.344 | 0.043 | 0% | 0% | 0% | 0% | 0 | 0 | 1.8 |
| case:P05 | 10 | 0.439 | 0.466 | 0.232 | 0% | 80% | 0% | 0% | 0 | 0 | 4.7 |
| case:P06 | 10 | 0.018 | 0.000 | 0.000 | 0% | 50% | 0% | 0% | 0 | 0 | 2.8 |
| case:P07 | 10 | 0.707 | 0.690 | 0.571 | 0% | 0% | 0% | 0% | 0 | 0 | 4.4 |
| case:P08 | 10 | 0.275 | 0.221 | 0.000 | 10% | 10% | 10% | 0% | 0 | 0 | 3.7 |
| case:P09 | 10 | 0.867 | 0.857 | 0.757 | 0% | 0% | 0% | 0% | 0 | 0 | 1.7 |
| case:P10 | 10 | 0.944 | 0.952 | 0.898 | 0% | 0% | 0% | 0% | 0 | 0 | 2.4 |
| case:P11 | 10 | 0.577 | 0.558 | 0.177 | 0% | 0% | 0% | 0% | 0 | 0 | 5.2 |
| case:P12 | 10 | 0.538 | 0.430 | 0.263 | 80% | 40% | 40% | 40% | 0 | 0 | 3.9 |
| case:P13 | 10 | 0.526 | 0.602 | 0.051 | 0% | 0% | 0% | 0% | 0 | 0 | 3.8 |
| case:P14 | 10 | 0.755 | 0.824 | 0.000 | 10% | 10% | 10% | 0% | 0 | 0 | 2.2 |
| case:P15 | 10 | 0.735 | 0.689 | 0.530 | 30% | 30% | 30% | 0% | 0 | 0 | 4.3 |
| case:P16 | 10 | 0.608 | 0.679 | 0.151 | 0% | 0% | 0% | 0% | 0 | 0 | 3.3 |
| case:P17 | 10 | 0.514 | 0.598 | 0.040 | 0% | 0% | 0% | 0% | 0 | 0 | 3.6 |
| case:P18 | 10 | 0.372 | 0.278 | 0.149 | 0% | 0% | 0% | 0% | 0 | 0 | 4.7 |
| case:P19 | 10 | 0.574 | 0.593 | 0.265 | 0% | 0% | 0% | 0% | 0 | 0 | 2.5 |

## By supplier archetype

| archetype | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| boulware | 17 | 0.319 | 0.265 | 0.000 | 12% | 35% | 12% | 0% | 0 | 0 | 3.12 |
| cash_short | 24 | 0.507 | 0.544 | 0.000 | 0% | 8% | 0% | 0% | 0 | 0 | 3.58 |
| conceder | 21 | 0.622 | 0.671 | 0.000 | 0% | 5% | 0% | 0% | 0 | 0 | 3.24 |
| data_driven | 22 | 0.381 | 0.287 | 0.000 | 14% | 23% | 14% | 0% | 0 | 0 | 2.95 |
| mirror | 84 | 0.568 | 0.588 | 0.000 | 7% | 17% | 5% | 2% | 0 | 0 | 3.65 |
| monopolist | 20 | 0.608 | 0.814 | 0.000 | 15% | 20% | 0% | 15% | 0 | 0 | 2.55 |
| walker | 22 | 0.574 | 0.672 | 0.000 | 4% | 14% | 4% | 0% | 0 | 0 | 3.45 |

## 10 worst cases

| case | template | type | score | archetypes | what went wrong |
|---|---|---|---|---|---|
| case:ST012 | case:P02 | price_increase | 0.000 | 990012=conceder | deal with sup:990012 (conceder) at r1, status agreed; price 347.09 vs best package 365.45; deal value +5.0% over the supplier's absolute floor; C_deal >= C_open; relationship charge 203939 |
| case:ST022 | case:P03 | renewal | 0.000 | 990022=walker | no deal - every supplier walked: sup:990022 walked at r4 |
| case:ST051 | case:P06 | rfq | 0.000 | 990051=monopolist, 991051=monopolist | deal with sup:990051 (monopolist) at r2, status final_offer; price 254.1 vs best package 232.79; deal value +0.9% over the supplier's absolute floor; C_deal >= C_open; sup:991051 walked at r2 (after final_offer) |
| case:ST052 | case:P06 | rfq | 0.000 | 990052=cash_short, 991052=monopolist | deal with sup:991052 (monopolist) at r2, status final_offer; price 241.5 vs best package 219.93; deal value +2.6% over the supplier's absolute floor; C_deal >= C_open |
| case:ST053 | case:P06 | rfq | 0.000 | 990053=walker, 991053=mirror | deal with sup:990053 (walker) at r3, status final_offer; price 253.45 vs best package 266.99; deal value +2.7% over the supplier's absolute floor; C_deal >= C_open; relationship charge 232964 |
| case:ST054 | case:P06 | rfq | 0.000 | 990054=boulware, 991054=boulware | deal with sup:991054 (boulware) at r3, status final_offer; price 238.0 vs best package 203.74; deal value +11.2% over the supplier's absolute floor; C_deal >= C_open; sup:990054 walked at r3 (after final_offer) |
| case:ST055 | case:P06 | rfq | 0.000 | 990055=walker, 991055=boulware | deal with sup:991055 (boulware) at r2, status final_offer; price 224.6 vs best package 209.03; deal value +14.1% over the supplier's absolute floor; C_deal >= C_open |
| case:ST056 | case:P06 | rfq | 0.000 | 990056=data_driven, 991056=mirror | deal with sup:991056 (mirror) at r3, status final_offer; price 267.9 vs best package 240.14; deal value +0.0% over the supplier's absolute floor; C_deal >= C_open; sup:990056 walked at r2 (after final_offer) |
| case:ST057 | case:P06 | rfq | 0.000 | 990057=monopolist, 991057=cash_short | deal with sup:991057 (cash_short) at r5, status final_offer; price 235.35 vs best package 207.57; deal value +7.6% over the supplier's absolute floor; C_deal >= C_open; relationship charge 2740; sup:990057 walked at r2 (after final_offer) |
| case:ST059 | case:P06 | rfq | 0.000 | 990059=mirror, 991059=monopolist | deal with sup:991059 (monopolist) at r3, status final_offer; price 243.86 vs best package 211.77; deal value +1.7% over the supplier's absolute floor; C_deal >= C_open; sup:990059 walked at r3 (after final_offer) |
