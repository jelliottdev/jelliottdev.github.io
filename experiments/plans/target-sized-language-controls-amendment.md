# Boundary amendment for exact-token language controls

The first implementation stopped at the planned assertion that all three representations preserve identical token boundaries. That assertion is false for the inherited tokenizer: lowercasing capital dotted I (U+0130) produces i followed by a combining dot. The raw-letter mode treats that mark as a separator; the folded modes remove it. The all-source diagnostic found three affected sentences across the sixteen translation files. The original plan remains unchanged as a record of the assumption.

No complete control report was produced. Some distances were computed in memory before the assertion stopped execution, but no scores were printed or inspected. The diagnosis inspected tokenization differences only. This amendment is made after that input inspection and before inspecting follow-up scores.

Keep the baseline tokenizer and all existing corpus files unchanged. Partition each representation's token stream independently into complete 2,896-token blocks, using the original offset-zero, no-wrap rule. Save each block's sentence/token endpoints. Record total token counts by representation and explicitly state whether their endpoint ledgers agree within each language. Do not assert agreement where it is false. The folded and GP-grouped modes should still agree because grouping does not change their already-folded word boundaries; verify that narrower invariant.

All other planned scoring, tie handling, complete-block inclusion, remainder reporting and interpretation limits remain unchanged. This preserves comparability with the existing experiments while making the inherited normalization behavior visible. A revised Unicode tokenizer would require a separately declared variant and reruns of the affected baselines.
