# Demo video — 3:00 max, YouTube (public or unlisted)

Judges only see this video. Every claim must be **shown**, and AWS must be **on screen**.
Record the screen at 1080p, phone via scrcpy / QuickTime mirroring. Voice-over recorded separately, calm and clear.
Check the link in a signed-out browser before submitting.

| Time | Screen | Say (roughly) |
|---|---|---|
| **0:00–0:20** | Real photo/video of a flooded Bengaluru underpass (your own, or a news clip with credit). Then the Neeru map. | "Every monsoon, the same underpasses in Bengaluru fill up. Riders on two-wheelers find out when they're already in the water. Neeru tells them three hours earlier." |
| **0:20–0:45** | Telegram bot: `/start` → pick **ಕನ್ನಡ** → share location → list of nearby spots with 🔴/🟠/🟢 → tap **🔔 ಎಚ್ಚರಿಸಿ**. | "No app to install. In Kannada or English, share your location and see the risk at the spots on your route for the next three hours. Tap Alert me." |
| **0:45–1:25** | Send a **real photo** of a waterlogged road (take one, or a wet road you staged safely) → share location → "checking…" → verdict with depth + advice. Cut to the web map: the spot changes colour; open it and show the photo. | "Anyone can report. An AI agent built with the Strands Agents SDK on Amazon Bedrock checks it: is this a real street photo, how deep is the water, does live rainfall back it up, do other reports agree. Only confident verdicts touch the map." |
| **1:25–1:50** | Web Report tab: show the **agent steps** chips (`get_rainfall_here → nearby_reports → submit_verdict`). Then the hotspot detail: "Floods at about N mm… learns from citizen photos". | "The risk model is simple and explainable: rain on the ground, rain on the way, how fast this spot drains. When a citizen shows a flood the model didn't expect, that spot's threshold drops. The map gets smarter with every photo." |
| **1:50–2:15** | Admin: start **storm replay** (banner visible). Phone buzzes: 🔴 alert in Telegram. Ops tab: dispatch list, #1 underpass. SNS email arriving. | "Here's a storm replay over Bellandur, clearly labelled as a demo. Subscribers get warned before the spot turns red, and ward engineers get a dispatch list: where to send pumps first." |
| **2:15–2:45** | Architecture diagram (README mermaid, exported). Then **AWS console**, 3 quick cuts: Lambda functions list, DynamoDB items with risk, CloudWatch log of the agent's tool calls. | "Strands Agents and Bedrock for verification. Lambda, API Gateway, DynamoDB, S3, EventBridge every fifteen minutes, SNS for alerts, Amplify for the web app. All deployed with SAM, all serverless, pay per request." |
| **2:45–3:00** | Map zoomed out, logo, live URL, bot handle. | "Neeru. Know before you ride into it. Built for Bengaluru, and any city can bring its own hotspots." |

**Before recording:** clear test reports you don't want shown, make sure the map isn't all red, and
run storm replay only for the replay segment. Never present replayed rain as real.
