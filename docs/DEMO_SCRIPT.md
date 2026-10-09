# Demo video — 3:00 max, YouTube (public or unlisted)

Judges only see this video. Every claim must be **shown**, and AWS must be **on screen**.
Record the screen at 1080p; show the phone via scrcpy (Android) or a phone-sized browser window.
Record the voice-over separately, calm and clear. Check the link in a signed-out browser before submitting.

| Time | Screen | Say (roughly) |
|---|---|---|
| **0:00–0:15** | A real photo of a flooded Bengaluru underpass (your own, or a news photo with credit on screen). Cut to the Neeru map. | "Every monsoon, the same underpasses in Bengaluru fill up, and riders on two-wheelers find out when they're already in the water. Neeru tells them before they leave." |
| **0:15–0:45** | Storm replay on (banner visible). Tap **🧭 Safe route** → tap HSR Layout → tap Hebbal. The grey dashed fastest route goes through a red spot; the blue route goes around it; the verdict card reads "+N min, avoids Silk Board". | "Where are you going? Neeru takes the fastest route and its alternatives, checks every one against live flood risk, and tells you the safer way and what it costs you: seven minutes, instead of a stalled engine at Silk Board." |
| **0:45–1:15** | Telegram: send a **real photo** of a wet road → share location → verdict in Kannada with depth and advice → tap **🔔 Alert me**. Cut to the web map: the spot changed colour; open it to show the photo. | "Anyone can report. An AI agent built with the Strands Agents SDK on Amazon Bedrock checks the photo: is it a real street, how deep is the water, does live rainfall back it up, do other people agree. Only confident verdicts change the map. And it answers in Kannada." |
| **1:15–1:35** | Web Report tab: the **agent steps** chips. Then a hotspot detail: the rain chart and "floods at about N mm… learns from citizen photos". | "The risk model is simple and explainable: rain still on the road, rain on the way, how fast this spot drains. When a citizen shows a flood the model didn't expect, that spot's threshold drops. The map gets smarter with every photo." |
| **1:35–2:05** | Ops tab: dispatch list → **🤖 Get dispatch briefing**. Show the headline, the actions (Pump / Divert / Close) with reasons, the Kannada summary, and the tool-call trace. Phone buzzes: 🔴 Telegram alert. SNS email arrives. | "For ward engineers, a second agent, the Ops Copilot, reads the dispatch list and citizen reports and writes the briefing: where the pumps go, which underpass to close, and why, in English and Kannada for the ward WhatsApp group. It can only name spots that are really in the data." |
| **2:05–2:40** | Architecture diagram (README). Then **AWS console**, quick cuts: Lambda functions → **CloudWatch dashboard** (spots at risk, reports, agent latency) → **X-Ray trace map** → DynamoDB items. | "Two Strands agents on Bedrock. Lambda, API Gateway, DynamoDB, S3, EventBridge every 15 minutes, SNS alerts, Amplify for the web, and production observability: X-Ray traces, custom metrics and a dashboard. All serverless, all in one SAM template." |
| **2:40–3:00** | Map zoomed out, logo, live URL, bot handle. | "Neeru. Know before you ride into it. Built for Bengaluru, and any city can bring its own hotspots." |

**Before recording**
- Clear test reports you don't want shown. Start storm replay only for the segments that need it, and keep the banner visible.
- **Never present replayed rain as real rain.** Say "storm replay" out loud once.
- Run the copilot once before recording so the first take isn't waiting on a cold start.
