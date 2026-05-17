# Cron setup — agent instructions

To install the self-improving compound cron audit pipeline, your OpenClaw agent needs to
create three cron jobs. The full job definitions (names, schedules, payloads, tool
allowlists) live in `scripts/setup-cron.json`.

## Prerequisites

- This skill must be installed (the agent can find the `setup-cron.json` under the skill root).
- The agent must have access to the `cron` tool (default in OpenClaw).
- The user must confirm cron creation — creating persistent background jobs is a
  side-effect that warrants explicit opt-in.

## Steps for the agent

1. **Read `scripts/setup-cron.json`** to load the three job definitions.
   The file lives at the skill root. If the skill is installed via ClawHub, the path is:
   `~/.openclaw/workspace/skills/self-improving-compound/scripts/setup-cron.json`

2. **Edit the paths inside each job's `payload.message`:**
   - Replace `/path/to/skills/self-improving-compound` with the actual skill install path.
   - Replace `/path/to/workspace` with the user's workspace root
     (usually `~/.openclaw/workspace` or project root).
   The JSON uses placeholder paths so it is generic; the agent must resolve them
   at install time.

3. **Optionally configure `delivery` for each job:**
   - The JSON ships with `bestEffort: true` (no specific channel).
   - The agent should ask or infer the correct delivery target
     (e.g., Telegram DM, Feishu DM) and set `delivery.channel` + `delivery.to`.

4. **Use the `cron add` tool three times**, once per job entry. Example for the
   Light Check job:

   ```json
   {
     "action": "add",
     "job": {
       "name": "Self-Improving Light Check",
       "schedule": { "kind": "cron", "expr": "0 8-22/2 * * *", "tz": "Asia/Shanghai" },
       "sessionTarget": "isolated",
       "payload": {
         "kind": "agentTurn",
         "message": "Run a lightweight self-improving check…",
         "timeoutSeconds": 180,
         "toolsAllow": ["read", "exec", "sessions_list", "sessions_history"]
       },
       "delivery": { "mode": "announce", "channel": "telegram", "to": "6243021106", "bestEffort": true }
     }
   }
   ```

5. **Verify** with `cron list` that all three jobs show `enabled: true` and
   have a `nextRunAtMs`.

## Timezone

All schedules use `Asia/Shanghai`. If the user is in a different timezone, the
agent should adjust `schedule.tz` before creating the jobs. The cron expressions
(`0 8-22/2 * * *` etc.) are wall-clock time in the specified timezone.

## Idempotency

Running the setup more than once should not create duplicate jobs. The agent
should check `cron list` first; if a job with the same `name` already exists,
skip creation or update it.
