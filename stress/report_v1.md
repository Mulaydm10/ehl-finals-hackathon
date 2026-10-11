# Stress report `v1`

NOIDEA_EXPERIMENTS=`hidden` - 190 cases, offline simulator (stress/sim_supplier.py).

## Overall

| Overall | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 190 | 0.595 | 0.670 | 0.000 | 13% | 13% | 8% | 5% | 0 | 0 | 2.83 |

## By case type

| type | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bundling | 20 | 0.707 | 0.716 | 0.149 | 25% | 10% | 10% | 15% | 0 | 0 | 3.85 |
| capacity | 20 | 0.926 | 0.953 | 0.772 | 0% | 0% | 0% | 0% | 0 | 0 | 2 |
| price_increase | 40 | 0.598 | 0.623 | 0.000 | 5% | 2% | 2% | 2% | 0 | 0 | 2.55 |
| quality | 20 | 0.589 | 0.575 | 0.000 | 40% | 10% | 10% | 30% | 0 | 0 | 3.8 |
| raw_material | 30 | 0.442 | 0.526 | 0.000 | 23% | 23% | 23% | 0% | 0 | 0 | 3.33 |
| renewal | 40 | 0.693 | 0.796 | 0.121 | 0% | 0% | 0% | 0% | 0 | 0 | 1.8 |
| rfq | 20 | 0.190 | 0.084 | 0.000 | 15% | 65% | 15% | 0% | 0 | 0 | 3.5 |

## By template

| template | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case:P01 | 10 | 0.684 | 0.804 | 0.057 | 10% | 0% | 0% | 10% | 0 | 0 | 2.6 |
| case:P02 | 10 | 0.687 | 0.744 | 0.242 | 0% | 0% | 0% | 0% | 0 | 0 | 2.3 |
| case:P03 | 10 | 0.849 | 0.845 | 0.767 | 0% | 0% | 0% | 0% | 0 | 0 | 1.2 |
| case:P04 | 10 | 0.501 | 0.344 | 0.121 | 0% | 0% | 0% | 0% | 0 | 0 | 1.9 |
| case:P05 | 10 | 0.363 | 0.385 | 0.000 | 10% | 60% | 10% | 0% | 0 | 0 | 3.9 |
| case:P06 | 10 | 0.017 | 0.000 | 0.000 | 20% | 70% | 20% | 0% | 0 | 0 | 3.1 |
| case:P07 | 10 | 0.694 | 0.725 | 0.149 | 10% | 10% | 10% | 0% | 0 | 0 | 3.7 |
| case:P08 | 10 | 0.386 | 0.437 | 0.000 | 30% | 30% | 30% | 0% | 0 | 0 | 3 |
| case:P09 | 10 | 0.891 | 0.897 | 0.772 | 0% | 0% | 0% | 0% | 0 | 0 | 1.7 |
| case:P10 | 10 | 0.960 | 0.965 | 0.898 | 0% | 0% | 0% | 0% | 0 | 0 | 2.3 |
| case:P11 | 10 | 0.634 | 0.654 | 0.000 | 10% | 10% | 10% | 0% | 0 | 0 | 4.9 |
| case:P12 | 10 | 0.545 | 0.464 | 0.182 | 70% | 10% | 10% | 60% | 0 | 0 | 2.7 |
| case:P13 | 10 | 0.525 | 0.609 | 0.000 | 10% | 10% | 10% | 0% | 0 | 0 | 3.5 |
| case:P14 | 10 | 0.843 | 0.859 | 0.724 | 0% | 0% | 0% | 0% | 0 | 0 | 1.5 |
| case:P15 | 10 | 0.720 | 0.705 | 0.303 | 40% | 10% | 10% | 30% | 0 | 0 | 4 |
| case:P16 | 10 | 0.553 | 0.695 | 0.000 | 20% | 20% | 20% | 0% | 0 | 0 | 2.8 |
| case:P17 | 10 | 0.496 | 0.528 | 0.040 | 0% | 0% | 0% | 0% | 0 | 0 | 1.8 |
| case:P18 | 10 | 0.386 | 0.373 | 0.000 | 20% | 20% | 20% | 0% | 0 | 0 | 4.2 |
| case:P19 | 10 | 0.578 | 0.593 | 0.265 | 0% | 0% | 0% | 0% | 0 | 0 | 2.6 |

## By supplier archetype

| archetype | n | mean | median | min | no-deal | any supplier walked | all walked | agent walked | crashes | broken must-have | rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| boulware | 17 | 0.313 | 0.265 | 0.000 | 24% | 35% | 12% | 12% | 0 | 0 | 2.76 |
| cash_short | 24 | 0.442 | 0.494 | 0.000 | 17% | 21% | 17% | 0% | 0 | 0 | 2.88 |
| conceder | 21 | 0.702 | 0.828 | 0.000 | 5% | 5% | 5% | 0% | 0 | 0 | 2.38 |
| data_driven | 22 | 0.560 | 0.651 | 0.000 | 14% | 14% | 9% | 4% | 0 | 0 | 2.27 |
| mirror | 84 | 0.623 | 0.648 | 0.000 | 8% | 11% | 2% | 6% | 0 | 0 | 3.35 |
| monopolist | 20 | 0.598 | 0.826 | 0.000 | 15% | 25% | 5% | 10% | 0 | 0 | 2.45 |
| walker | 22 | 0.460 | 0.519 | 0.000 | 23% | 41% | 23% | 0% | 0 | 0 | 2.68 |

## 10 worst cases

| case | template | type | score | archetypes | what went wrong |
|---|---|---|---|---|---|
| case:ST043 | case:P05 | rfq | 0.000 | 70210=mirror, 70240=conceder, 70250=mirror | no deal - every supplier walked: sup:70210 walked at r6; sup:70240 walked at r6 (after final_offer); sup:70250 walked at r5 (after final_offer) |
| case:ST051 | case:P06 | rfq | 0.000 | 70120=monopolist, 70150=monopolist | deal with sup:70120 (monopolist) at r2, status final_offer; price 254.1 vs best package 232.79; deal value +0.9% over the supplier's absolute floor; C_deal >= C_open; sup:70150 walked at r2 (after final_offer) |
| case:ST052 | case:P06 | rfq | 0.000 | 70120=cash_short, 70150=monopolist | deal with sup:70150 (monopolist) at r2, status final_offer; price 249.0 vs best package 219.93; deal value +2.4% over the supplier's absolute floor; C_deal >= C_open |
| case:ST053 | case:P06 | rfq | 0.000 | 70120=walker, 70150=mirror | deal with sup:70150 (mirror) at r7, status final_offer; price 260.36 vs best package 266.99; deal value +10.7% over the supplier's absolute floor; C_deal >= C_open; relationship charge 152581; sup:70120 walked at r4 |
| case:ST054 | case:P06 | rfq | 0.000 | 70120=boulware, 70150=boulware | no deal - every supplier walked: sup:70120 walked at r3 (after final_offer); sup:70150 walked at r3 |
| case:ST055 | case:P06 | rfq | 0.000 | 70120=walker, 70150=boulware | deal with sup:70150 (boulware) at r2, status final_offer; price 224.5 vs best package 209.03; deal value +14.1% over the supplier's absolute floor; C_deal >= C_open; sup:70120 walked at r2 |
| case:ST056 | case:P06 | rfq | 0.000 | 70120=data_driven, 70150=mirror | no deal - every supplier walked: sup:70120 walked at r2 (after final_offer); sup:70150 walked at r3 |
| case:ST057 | case:P06 | rfq | 0.000 | 70120=monopolist, 70150=cash_short | deal with sup:70150 (cash_short) at r5, status final_offer; price 235.35 vs best package 207.57; deal value +7.6% over the supplier's absolute floor; C_deal >= C_open; relationship charge 2740; sup:70120 walked at r2 (after final_offer) |
| case:ST059 | case:P06 | rfq | 0.000 | 70120=mirror, 70150=monopolist | deal with sup:70150 (monopolist) at r3, status final_offer; price 241.45 vs best package 211.77; deal value +1.7% over the supplier's absolute floor; C_deal >= C_open; sup:70120 walked at r3 (after final_offer) |
| case:ST060 | case:P06 | rfq | 0.000 | 70120=conceder, 70150=walker | deal with sup:70120 (conceder) at r1, status final_offer; price 264.84 vs best package 245.92; deal value +1.5% over the supplier's absolute floor; C_deal >= C_open; relationship charge 74193 |
