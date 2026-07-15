# Soft, unsourced assumptions -- kept in one file so they're easy to find
# and revisit. Published rate cards live next to the adapter that uses them.

CACHE_DISCOUNT = 0.15  # cached tokens cost 15% of a fresh input token; proxied off the price discount, not a measured compute saving

CHATGPT_TIER_PROFILE = {
    # ChatGPT bills per message, not per token. Assumed (input, output) tokens
    # per message, borrowed from Jegham et al.'s short/medium/long buckets.
    # Weakest link in the pipeline -- calibrate against a real transcript sample.
    "instant": (100, 300),
    "thinking": (1000, 1000),
    "pro": (10000, 1500),
}

BEDROCK_INPUT_OUTPUT_RATIO = 3.0
# Bedrock spend-only exports have no token split; assumes input = ratio * output.
# Unsourced placeholder -- replace once CloudWatch gives real token counts.
