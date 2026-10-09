# Submission writeup (paste into the form; edit to your own words)

**Project:** Neeru (ನೀರು) — know before you ride into it
**Track:** Heat and Water (monsoon waterlogging, floods)
**Team:** QuantumEffect — Pratham Patil (solo)
**Live app:** <Amplify URL> · **Bot:** @<bot_username> · **Repo:** <GitHub URL> · **Video:** <YouTube URL>

## The problem
Bengaluru's underpasses and low junctions flood in heavy rain, often in under an hour. Two-wheeler riders,
including thousands of delivery partners, find out when they are already in the water: stalled engines,
falls, people stranded. Official alerts are city-wide ("heavy rain expected") and never say *which road*.

## What we built
- **Riders:** a Telegram bot in English and Kannada, plus a mobile web map. Share a location to see the
  flood risk at nearby spots for the next 3 hours; subscribe to a spot to be warned before it turns red.
- **Citizens:** send a photo of a waterlogged road. A verifier agent (Strands Agents SDK on Amazon Bedrock)
  checks that it is a real street photo, estimates depth in rider terms (ankle / tyre-hub / knee), compares
  it with live rainfall and nearby reports, and only then updates the map. Reports far from known spots
  add new spots.
- **Safe Route:** tap a start and a destination. Neeru checks the fastest route and its alternatives against live
  flood risk and recommends the safest one, saying exactly which flooded spot it avoids and how many minutes it costs.
- **Ward engineers:** a dispatch list ranked by risk × road importance × verified reports, SNS alerts, and an
  **Ops Copilot**, a second Strands agent that writes a dispatch briefing (pump here, divert there, and why) in
  English and Kannada. It is constrained so it can only name spots and actions that exist in the data.

The risk model is deliberately explainable: rain still on the road (decayed by each spot's drainage) plus
rain forecast for the next 3 hours, against a per-spot flood threshold. Verified photos can override the
forecast for local cloudbursts, and they recalibrate the threshold, so the map improves with use.

## Where AWS fits
| Service | Role |
|---|---|
| Strands Agents SDK (AWS open source) | Two agents: the photo verifier (rainfall, nearby reports, structured verdict) and the Ops Copilot (dispatch list, spot reports, structured briefing) |
| Amazon Bedrock (Claude Haiku 4.5) | Vision + reasoning for photo verification, replies in Kannada/English |
| AWS Lambda | API, Telegram webhook, 15-minute risk refresh |
| Amazon API Gateway (HTTP API) | Public API + bot webhook, throttled |
| Amazon DynamoDB | Hotspots, reports, subscriptions, bot sessions (TTL) |
| Amazon S3 | Citizen photos (private, presigned links, 30-day expiry) |
| Amazon EventBridge | Schedules the refresh every 15 minutes |
| Amazon SNS | Red alerts to ops email/SMS |
| AWS Amplify Hosting | Web app |
| Amazon CloudWatch + AWS X-Ray | Custom metrics (EMF), dashboard, alarm on bot errors, tracing on every function |
| AWS SAM | Infrastructure as code, one-command deploy |

## What fought back
<!-- Fill this in honestly as you go: e.g. Telegram retrying slow webhooks (fixed by de-duplicating update_ids),
     Bedrock model access, picking depth categories a rider understands, finding real hotspot coordinates. -->

## Limitations and next steps
Seed hotspots are approximate and thresholds are starting guesses that citizen reports correct. Open-Meteo is a
global model, so citizen photos matter most for very local storms. Safe Route uses the public OSRM server with car routing; production would self-host OSRM with a two-wheeler profile.
Next: a WhatsApp channel, Safe Route inside the bot, and a pilot with BBMP ward engineers using the Ops Copilot briefing.

## AI tools used
Claude (Anthropic) was used to help scaffold the code, tests and documentation. All code was reviewed, run and
deployed by me.
