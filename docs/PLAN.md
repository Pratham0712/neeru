# Weekend plan — solo (Pratham)

Deadline: Sunday Oct 11 (exact time on the schedule page; submissions open 8 AM, plan to submit by **Sunday 2 PM**).
Rule of the weekend: **stop adding features Saturday 10 PM.** Sunday is video, writeup, blog, submit.

## Friday (today)
- [x] Code on GitHub from the project root, 68 tests passing, local demo running
- [ ] Builder Center student verification (needed for the Amazon fast-track) · cancel the pending teammate invite
- [ ] AWS: IAM user + `aws configure`, Bedrock Haiku 4.5 answers in the playground, copy inference profile ID
- [ ] Telegram bot from @BotFather
- [ ] `sam build` → `sam deploy --guided` → seed → webhook → `/admin/refresh` → `/start` works in Telegram
- [ ] Real photo through the bot → verdict; check CloudWatch logs show the agent's tool calls
- [ ] Web app on Amplify; open it on your phone

## Saturday morning — make it real
- [ ] Check all 16 coordinates in `data/hotspots.json` on Google Maps (pin on the dip/underpass), re-seed
- [ ] Add 3–5 spots you personally know (your area, BMSCE / Basavanagudi side)
- [ ] Test the verifier with 10+ photos: flooded, dry, screenshot, meme, indoor, night. Tune the prompt if needed
- [ ] Safe Route: try 5 real trips (e.g. HSR → Hebbal, Koramangala → Whitefield) with storm replay on and off
- [ ] Ops Copilot: generate a briefing during storm replay; check it names only real spots

## Saturday afternoon — make it usable
- [ ] Hand the bot and web app to 2 friends with zero explanation; fix whatever confuses them
- [ ] Ask a Kannada-speaking friend to read the bot + web text (`src/neeru/i18n.py`, `web/app.js`)
- [ ] Open the CloudWatch dashboard (stack output `DashboardUrl`); make sure graphs have data

## Saturday evening
- [ ] Record all demo footage (follow `docs/DEMO_SCRIPT.md`) while everything works
- [ ] **Feature freeze 10 PM**

## Sunday — ship
- [ ] Edit video (< 3:00), upload to YouTube (public/unlisted), test the link signed-out
- [ ] Writeup from `docs/WRITEUP.md` — fill "What fought back" honestly
- [ ] Blog on AWS Builder Center from `docs/BLOG_OUTLINE.md` (top 5 blogs win AirPods)
- [ ] README: add live URL, bot handle, 3 screenshots · repo public · submit · re-check every link
