# LP1 section-order selection: frozen comparison

## Question and prior knowledge

For the same 464-word object and sixteen-column statistic, how unusual is the flattest arrangement after considering all 24 orders of its four sections? This follows the unrestricted and within-section fixed-order controls. Their results (54 and 88 lower-tail trials out of 49,999) are already known. No section-order enumeration or order-selected null scores have yet been calculated for this variant.

Use the same archived tokenization, four sections, word lengths and section boundaries as `lp1-word-length-balance`. Preserve the word order within each section when evaluating the observed arrangements. Each order fills the 29-by-16 table continuously without resetting columns at a section boundary. The only newly searched choice is the order of the four intact sections. Do not test additional widths, reversals or deletions.

## Search and null

Enumerate all permutations of section IDs in the baseline order: Warning, Welcome, first koan, second koan. For each, calculate Q=sum_j(16*S_j-1796)^2. Record all 24 observed scores and every minimizing order, preserving ties. The selected statistic is the minimum Q across the complete search.

For each of 49,999 null trials, shuffle fresh original length lists within their own four sections using one Python random.Random instance seeded with 330146. Shuffle sections in baseline order before trying arrangements. Then enumerate the same 24 section orders and retain the minimum Q and every minimizing order. This uses the same within-section permutations as the completed fixed-order variant, allowing an exact replay check of its baseline-order score sequence. Do not redraw lengths separately for each order.

Count null minima <= the observed minimum, ties included. Report the plus-one estimate (count+1)/50000 and compare it with the declared threshold 0.05. This accounts for choosing among these 24 orders under this null; it does not adjust for the original exploration that selected the word object, width, statistic or other hypotheses. It is not a general probability of coincidence or design.

## Duplicate arrangements and storage

A cyclic rotation of the full 464-length sequence permutes the sixteen column sums because 464 is divisible by 16. Rotating an order of four intact sections is one such cyclic rotation; it therefore leaves Q unchanged. The 24 orders partition into six cyclic-order classes, each with four members. This is an exact invariance, not independence of the six remaining scores. Other accidental score ties must remain visible.

Store the 24 orders, their six class representatives and membership map, all observed scores, and each trial's six class scores. Store its minimum and all minimizing order indices as well. This compact format retains every order's score through an explicit map, rather than silently reporting only six of the 24 searches. The primary producer may evaluate representatives after verifying the class identity. The checker must independently evaluate all 24 orders for every trial and check the expansion.

## Inputs and verification

Hash the original baseline plan, word ledger, submitted length vector, all original text files, and the completed within-section report and receipt. Check the current constrained report against its receipt. Independently reconstruct the source lengths and section IDs before simulation.

Before manuscript evaluation, exhaust small fixtures whose total length is divisible by the column count, including unequal section lengths and repeated values. Verify cyclic-order partitioning and score invariance. Include a fixture whose length is not divisible by the column count to demonstrate why the stated divisibility assumption matters; do not apply the reduced search to it.

The independent checker must not import the producer. Reconstruct within-section permutations through explicit index swaps, enumerate all 24 orders and accumulate column sums separately. Check every trial against the saved fixed-order score from `lp1-section-balance`. Verify every minimum, tie list and the complete tail count. The Python pseudorandom primitive is shared. No new simulation seed or threshold may be chosen after inspecting outputs.

## Presentation

Publish as a variant in the existing LP1 column-balance family. Show all six cyclic classes with their four section orders, plus the observed scores. Compare the observed minimum to the order-selected null distribution. Clearly distinguish the original fixed order from searching orders and distinguish duplicate configurations from independent evidence. Retain all output data and a reproducible bundle. Do not relabel the earlier fixed-order p-values as though they already accounted for this order search. Human review remains pending.
