# Blog post outline (AWS Builder Center — top 5 blogs win AirPods)

Write it yourself, in your own voice, on Saturday night or Sunday morning. Judges for the blog prize want
*what fought back*, not a feature list. Aim for 900–1,300 words, 3–5 screenshots, one diagram, one code snippet.
Publish on AWS Builder Center and link it in the submission.

**Title ideas**
- "Know before you ride into it: building a flood-alert agent for Bengaluru's underpasses in 72 hours"
- "Teaching an AI agent to tell ankle-deep from tyre-deep"

**Sections**
1. **The underpass at the end of my street** — a real moment: a flooded road you or a friend rode into. Why city-wide alerts don't help a rider.
2. **One question, three hours** — why we scoped to "will this spot flood in the next 3 hours" instead of "predict floods".
3. **The risk model on one napkin** — rain still on the road + rain on the way vs. a threshold. Include the worked example from `risk.py`. Why explainable beat a black-box model for this weekend.
4. **The verifier agent** — Strands Agents SDK, the SOP-style system prompt, the three tools, why `submit_verdict` as a tool gives reliable structured output. Snippet: the `@tool` definition.
5. **What fought back** — your real list. Candidates: Telegram retries on slow webhooks (de-dupe by `update_id`); Bedrock model access in Mumbai; depth categories riders understand; getting real hotspot coordinates; Kannada text that sounds natural.
6. **A map that learns** — threshold calibration from citizen photos; why that matters more than a better forecast.
7. **Architecture and cost** — the diagram; everything serverless, pay-per-request.
8. **What's next** — WhatsApp, route checks, a pilot with ward engineers.
