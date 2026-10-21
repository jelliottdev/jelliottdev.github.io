# LP1 column balance with within-section shuffles

## Question and prior knowledge

Does the fixed 464-word, sixteen-column arrangement still have unusually low column-mean variance when the null preserves each section's word-length distribution and occupied slots? The unrestricted baseline is already known: integer score 128256, 54 of 49,999 shuffles at or below it, corrected lower-tail estimate 0.0011. The arrangement and baseline were selected through prior exploration. This follow-up does not correct that original selection and is not independent confirmation.

Freeze this variant before generating its constrained shuffles. Preserve the baseline's archived rune input, token rules, section order (Warning, Welcome, first koan, second koan), headings, interrupting F and row-major layout. There are 45, 124, 208 and 87 words in the sections, totaling 464 words and 1796 runes. Sixteen columns each contain 29 words. Section boundaries do not reset the column assignment.

## Null procedure and statistic

Use Python random.Random with seed 330146, 49,999 trials and one generator instance for the entire run. For each trial, take a fresh copy of each original section's lengths, shuffle it with random.shuffle in the stated section order, then concatenate the four shuffled sections. Do not shuffle the section order, move words across sections, reset the column index, or choose a new seed after seeing the result. The baseline and variant use the same seed number but different random-consumption patterns; their individual trials are not paired rearrangements.

For column sums S_j, k=16 and fixed total T=1796, retain the exact integer statistic Q=sum_j(k*S_j-T)^2. The observed Q is unchanged. Count every simulated Q <= observed, including ties; report (count+1)/(49999+1) and the fixed threshold 0.05. Save every null score, not just the tail. No alternative widths, section orders or thresholds are scanned.

Also calculate the exact expected column-mean variance under this constrained model. For section s with N_s lengths, mean mu_s, population variance sigma_s^2 and n_sj fixed slots in column j, the contribution has mean n_sj*mu_s and variance n_sj*(N_s-n_sj)*sigma_s^2/(N_s-1). A singleton section has zero contribution variance. Independent section permutations make column-sum variances additive. Thus E[Q] sums k^2*Var(S_j)+(k*E[S_j]-T)^2 over columns. Divide by k^3*29^2 to convert to column-mean variance, and compare observed variance to this expectation. Preserve all fractions exactly. Do not reuse the unrestricted expectation for the constrained ratio.

## Verification and presentation

The frozen word ledger, submitted vector, baseline plan and all original text files are hashed inputs. The checker must independently scan the original text, respecting the same declared token rules, and verify every section and word length. Reconstruct all 49,999 permutations using explicit index swaps rather than importing the producer, and independently accumulate their column sums and integer scores. Python's pseudorandom primitive remains shared and must be disclosed.

Check the expected score independently through position-pair second moments: same-section distinct positions use ((sum x)^2-sum x^2)/(N*(N-1)); different sections use the product of their means. Exhaustive small section-permutation fixtures must cover repeated lengths, unequal section sizes, boundaries cutting across rows, singleton sections and constant lengths. Check the complete saved tail count and plus-one estimate.

Present baseline and variant beside one another in the existing word-length-balance family. Retain the unchanged observed arrangement and show exactly what the constrained null preserves. The comparison is sensitivity to a model assumption, not two independent discoveries. Neither null preserves sentence syntax or coherent prose. No result establishes deliberate design, a grille, a carrier text or a decryption. Human review remains separate from computational verification.
