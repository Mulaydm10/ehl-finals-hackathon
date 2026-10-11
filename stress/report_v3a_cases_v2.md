# Stress report `v3a_cases_v2`

NOIDEA_EXPERIMENTS=`hidden` - 190 cases, offline simulator (stress/sim_supplier.py).

## Overall

| Overall | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 190 | 0.633 | 0.681 | 0.000 | 6% | 8% | 4% | 2% | 0 | 0 | 2.96 |

## By case type

| type | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bundling | 20 | 0.757 | 0.727 | 0.530 | 15% | 10% | 10% | 5% | 0 | 0 | 4.05 |
| capacity | 20 | 0.926 | 0.953 | 0.772 | 0% | 0% | 0% | 0% | 0 | 0 | 2 |
| price_increase | 40 | 0.610 | 0.623 | 0.040 | 2% | 2% | 2% | 0% | 0 | 0 | 2.58 |
| quality | 20 | 0.645 | 0.612 | 0.308 | 25% | 10% | 10% | 15% | 0 | 0 | 4.25 |
| raw_material | 30 | 0.571 | 0.608 | 0.000 | 3% | 3% | 3% | 0% | 0 | 0 | 3.77 |
| renewal | 40 | 0.693 | 0.796 | 0.121 | 0% | 0% | 0% | 0% | 0 | 0 | 1.75 |
| rfq | 20 | 0.226 | 0.199 | 0.000 | 5% | 50% | 5% | 0% | 0 | 0 | 3.55 |

## By template

| template | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case:P01 | 10 | 0.684 | 0.804 | 0.057 | 10% | 10% | 10% | 0% | 0 | 0 | 2.7 |
| case:P02 | 10 | 0.687 | 0.744 | 0.242 | 0% | 0% | 0% | 0% | 0 | 0 | 2.3 |
| case:P03 | 10 | 0.849 | 0.845 | 0.767 | 0% | 0% | 0% | 0% | 0 | 0 | 1.2 |
| case:P04 | 10 | 0.501 | 0.344 | 0.121 | 0% | 0% | 0% | 0% | 0 | 0 | 1.7 |
| case:P05 | 10 | 0.436 | 0.466 | 0.232 | 0% | 50% | 0% | 0% | 0 | 0 | 4.3 |
| case:P06 | 10 | 0.017 | 0.000 | 0.000 | 10% | 50% | 10% | 0% | 0 | 0 | 2.8 |
| case:P07 | 10 | 0.772 | 0.779 | 0.674 | 0% | 0% | 0% | 0% | 0 | 0 | 3.8 |
| case:P08 | 10 | 0.494 | 0.526 | 0.000 | 10% | 10% | 10% | 0% | 0 | 0 | 3.7 |
| case:P09 | 10 | 0.891 | 0.897 | 0.772 | 0% | 0% | 0% | 0% | 0 | 0 | 1.7 |
| case:P10 | 10 | 0.960 | 0.965 | 0.898 | 0% | 0% | 0% | 0% | 0 | 0 | 2.3 |
| case:P11 | 10 | 0.718 | 0.739 | 0.547 | 0% | 0% | 0% | 0% | 0 | 0 | 5.2 |
| case:P12 | 10 | 0.573 | 0.464 | 0.308 | 50% | 20% | 20% | 30% | 0 | 0 | 3.3 |
| case:P13 | 10 | 0.574 | 0.609 | 0.189 | 0% | 0% | 0% | 0% | 0 | 0 | 3.5 |
| case:P14 | 10 | 0.843 | 0.859 | 0.724 | 0% | 0% | 0% | 0% | 0 | 0 | 1.5 |
| case:P15 | 10 | 0.743 | 0.705 | 0.530 | 30% | 20% | 20% | 10% | 0 | 0 | 4.3 |
| case:P16 | 10 | 0.691 | 0.736 | 0.285 | 0% | 0% | 0% | 0% | 0 | 0 | 2.9 |
| case:P17 | 10 | 0.496 | 0.528 | 0.040 | 0% | 0% | 0% | 0% | 0 | 0 | 1.8 |
| case:P18 | 10 | 0.526 | 0.575 | 0.294 | 0% | 0% | 0% | 0% | 0 | 0 | 4.7 |
| case:P19 | 10 | 0.578 | 0.593 | 0.265 | 0% | 0% | 0% | 0% | 0 | 0 | 2.6 |

## By supplier archetype

| archetype | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| boulware | 17 | 0.346 | 0.306 | 0.000 | 12% | 29% | 12% | 0% | 0 | 0 | 3.06 |
| cash_short | 24 | 0.549 | 0.560 | 0.000 | 0% | 8% | 0% | 0% | 0 | 0 | 3.21 |
| conceder | 21 | 0.724 | 0.828 | 0.000 | 0% | 0% | 0% | 0% | 0 | 0 | 2.24 |
| data_driven | 22 | 0.540 | 0.621 | 0.000 | 9% | 14% | 4% | 4% | 0 | 0 | 2.27 |
| mirror | 84 | 0.634 | 0.648 | 0.000 | 5% | 11% | 4% | 1% | 0 | 0 | 3.39 |
| monopolist | 20 | 0.598 | 0.826 | 0.000 | 20% | 25% | 10% | 10% | 0 | 0 | 2.6 |
| walker | 22 | 0.636 | 0.774 | 0.000 | 0% | 9% | 0% | 0% | 0 | 0 | 3.23 |

## 10 worst cases

| case | template | type | score | archetypes | what went wrong |
|---|---|---|---|---|---|
| case:ST051 | case:P06 | rfq | 0.000 | 70120=monopolist, 70150=monopolist | deal with sup:70120 (monopolist) at r2, status final_offer; price 254.1 vs best package 232.79; deal value +0.9% over the supplier's absolute floor; C_deal >= C_open; sup:70150 walked at r2 (after final_offer) |
| case:ST052 | case:P06 | rfq | 0.000 | 70120=cash_short, 70150=monopolist | deal with sup:70150 (monopolist) at r2, status final_offer; price 249.0 vs best package 219.93; deal value +2.4% over the supplier's absolute floor; C_deal >= C_open |
| case:ST053 | case:P06 | rfq | 0.000 | 70120=walker, 70150=mirror | deal with sup:70120 (walker) at r3, status final_offer; price 250.8 vs best package 266.99; deal value +2.7% over the supplier's absolute floor; C_deal >= C_open; relationship charge 232980 |
| case:ST054 | case:P06 | rfq | 0.000 | 70120=boulware, 70150=boulware | deal with sup:70150 (boulware) at r3, status final_offer; price 238.5 vs best package 203.74; deal value +11.5% over the supplier's absolute floor; C_deal >= C_open; sup:70120 walked at r3 (after final_offer) |
| case:ST055 | case:P06 | rfq | 0.000 | 70120=walker, 70150=boulware | deal with sup:70150 (boulware) at r2, status final_offer; price 224.5 vs best package 209.03; deal value +14.1% over the supplier's absolute floor; C_deal >= C_open |
| case:ST056 | case:P06 | rfq | 0.000 | 70120=data_driven, 70150=mirror | deal with sup:70150 (mirror) at r3, status final_offer; price 267.9 vs best package 240.14; deal value +0.0% over the supplier's absolute floor; C_deal >= C_open; sup:70120 walked at r2 (after final_offer) |
| case:ST057 | case:P06 | rfq | 0.000 | 70120=monopolist, 70150=cash_short | deal with sup:70150 (cash_short) at r5, status final_offer; price 235.35 vs best package 207.57; deal value +7.6% over the supplier's absolute floor; C_deal >= C_open; relationship charge 2740; sup:70120 walked at r2 (after final_offer) |
| case:ST059 | case:P06 | rfq | 0.000 | 70120=mirror, 70150=monopolist | no deal - every supplier walked: sup:70120 walked at r3 (after final_offer); sup:70150 walked at r3 |
| case:ST060 | case:P06 | rfq | 0.000 | 70120=conceder, 70150=walker | deal with sup:70120 (conceder) at r1, status final_offer; price 264.84 vs best package 245.92; deal value +1.5% over the supplier's absolute floor; C_deal >= C_open; relationship charge 74193 |
| case:ST080 | case:P08 | raw_material | 0.000 | 70710=data_driven | no deal - every supplier walked: sup:70710 walked at r5 |
