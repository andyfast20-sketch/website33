# Version 100 (known-good voice)

This repo state is **Version 100** — a known-good baseline where callers can reliably hear the agent voice.

## What “Version 100” means
- The OpenAI Realtime message schema is aligned with the currently deployed model expectations.
- Speechmatics/telephony audio flow is working (no “silent agent” caused by schema errors).

## How to revert to Version 100
If anything breaks later, you can return to this exact working state:

- Switch your working tree to the tag:
  - `git checkout v100`

- Or create a branch from it (recommended if you plan to make fixes):
  - `git checkout -b hotfix-from-v100 v100`

## Important
If any future change might affect voice behavior (OpenAI schema, Vonage framing, TTS streaming, VAD/barge-in), treat `v100` as the rollback point.
