# Weekend plan — QuantumEffect

Deadline: Sunday Oct 11 (exact time on the schedule page; plan to submit by **Sunday 2 PM**).
Rule of the weekend: **stop adding features Saturday 10 PM.** Sunday is video, writeup, blog, submit.

## Thursday night (tonight)
- [ ] Both: Builder Center student verification · Rishikesh accepts the team invite with his own account
- [ ] Pratham: AWS account (ap-south-1), Bedrock Claude Haiku 4.5 playground once, AWS + SAM CLI
- [ ] Pratham: create GitHub repo `neeru`, push this code, **commit often all weekend** (history must match event dates)
- [ ] Pratham: `pytest`, then `sam build && sam deploy --guided`, seed, set webhook → `/start` works in Telegram
- [ ] Rishikesh: run `python scripts/local_demo.py`, click through every screen, list what feels confusing
- [ ] Rishikesh: verify all 16 coordinates in `data/hotspots.json` on Google Maps (drop the pin exactly on the dip/underpass)

## Friday — make the core loop real
- [ ] Pratham: first real photo through Telegram → agent verdict in CloudWatch logs; tune the system prompt on 10+ photos (flooded, dry, screenshot, meme, indoor, night)
- [ ] Pratham: check Haiku latency; if > 20 s, cut `nearby_reports` or raise memory
- [ ] Rishikesh: Kannada proofread (bot + web), deploy web to Amplify, test on 3 phones (Android Chrome, iPhone Safari, low-end)
- [ ] Rishikesh: collect 15–20 test photos (your own; news photos only for testing, never in the video without credit)
- [ ] Both: subscribe your own Telegram accounts to 2–3 spots; run storm replay; confirm alerts arrive and SNS email works

## Saturday — polish what judges see
- [ ] Usability pass with 2 people outside the team (hand them the bot with zero explanation, watch, fix)
- [ ] Add 4–6 more real hotspots you personally know (your area, BMSCE side)
- [ ] Stretch only if everything above is solid: "/route" check between two locations, or a WhatsApp link
- [ ] Record raw demo footage in the evening while it still works; **feature freeze 10 PM**

## Sunday — ship
- [ ] Edit video (follow `docs/DEMO_SCRIPT.md`), upload, test signed-out
- [ ] Writeup from `docs/WRITEUP.md`, fill "What fought back" honestly
- [ ] Blog from `docs/BLOG_OUTLINE.md`, publish on Builder Center
- [ ] Repo: README links, screenshots, public visibility · submit · double-check every link
