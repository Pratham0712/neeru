# Submission writeup (paste into the form; edit to your own words)

**Project:** Neeru (ನೀರು) — know before you ride into it
**Track:** Heat and Water (monsoon waterlogging, floods)
**Team:** QuantumEffect — Pratham Patil, Rishikesh Bulagouda
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
- **Ward engineers:** a dispatch list ranked by risk × road importance × verified reports, and SNS alerts.

The risk model is deliberately explainable: rain still on the road (decayed by each spot's drainage) plus
rain forecast for the next 3 hours, against a per-spot flood threshold. Verified photos can override the
forecast for local cloudbursts, and they recalibrate the threshold, so the map improves with use.

## Where AWS fits
| Service | Role |
|---|---|
| Strands Agents SDK (AWS open source) | Verifier agent: tools for rainfall, nearby reports, structured verdict |
| Amazon Bedrock (Claude Haiku 4.5) | Vision + reasoning for photo verification, replies in Kannada/English |
| AWS Lambda | API, Telegram webhook, 15-minute risk refresh |
| Amazon API Gateway (HTTP API) | Public API + bot webhook, throttled |
| Amazon DynamoDB | Hotspots, reports, subscriptions, bot sessions (TTL) |
| Amazon S3 | Citizen photos (private, presigned links, 30-day expiry) |
| Amazon EventBridge | Schedules the refresh every 15 minutes |
| Amazon SNS | Red alerts to ops email/SMS |
| AWS Amplify Hosting | Web app |
| AWS SAM | Infrastructure as code, one-command deploy |

## What fought back
<!-- Fill this in honestly as you go: e.g. Telegram retrying slow webhooks (fixed by de-duplicating update_ids),
     Bedrock model access, picking depth categories a rider understands, finding real hotspot coordinates. -->

## Limitations and next steps
Seed hotspots are approximate and thresholds are starting guesses that citizen reports correct. Open-Meteo is a
global model, so citizen photos matter most for very local storms. Next: WhatsApp channel, route-level checks
("is my commute safe?"), and sharing the dispatch list with BBMP ward engineers for a pilot.

## AI tools used
Claude (Anthropic) was used to help scaffold the code, tests and documentation. All code was reviewed, run and
deployed by the team.
