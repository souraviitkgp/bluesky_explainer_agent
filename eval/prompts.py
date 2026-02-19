"""Eval judge prompts. Placeholders: post_text, expected (golden only), agent_explanation."""

JUDGE_GOLDEN = """You are an eval judge. Given the original post, the expected (reference) explanation, and the agent's explanation, score the agent's explanation from 1 to 5.
5 = matches intent and key content; 1 = wrong or irrelevant.
Respond with a JSON object: "score" (integer 1-5), "reasoning" (one short sentence).

Post:
{post_text}

Expected (reference):
{expected}

Agent explanation:
{agent_explanation}
"""

JUDGE_RELEVANCE = """You are an eval judge. Given the original post and the agent's explanation, score how relevant and accurate the explanation is (1-5).
5 = clearly explains the post; 1 = irrelevant or wrong.
Respond with a JSON object: "score" (integer 1-5), "reasoning" (one short sentence).

Post:
{post_text}

Agent explanation:
{agent_explanation}
"""
