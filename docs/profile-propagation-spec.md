Title: Automatic Profile Propagation — Requirements
Date: 2026-05-24
Author: architect (draft)

Summary
-------
This document defines the scope, UX, authorization, and failure modes for an automatic "profile propagation" feature of `hermes update`. When enabled, an update to one Hermes profile can optionally apply selected configuration changes to other profiles.

Goals
-----
- Produce a clear, implementable CLI + config UX for propagation.
- Define which target profiles qualify for propagation.
- Define authorization rules and conflict resolution policy.
- Provide two example flows and a decision about default behavior.
- Provide interview questions for the requestor/PO to finalize open decisions.

Decision (current draft)
------------------------
- Conservative default: propagation is OFF by default.
  Rationale: updates can be surprising and affect other people/automations. Make propagation explicit.

Scope: which profiles are targeted
---------------------------------
Possible scopes (spec chooses one as default and allows flags):
- all: every profile under ~/.hermes/profiles/* (risky)
- linked: profiles explicitly linked to the source profile via `hermes profile link` or config key (recommended)
- same-owner: profiles whose recorded owner matches the invoking user (useful on multi-user machines)

Draft choice: linked (safer than `all`, less surprising than `same-owner`).

Propagation semantics
---------------------
- Propagate only the config keys changed in the source update (diff apply), not a wholesale profile overwrite unless `--clone-all` used.
- By default, non-destructive keys only: model.provider, model.default, agent.max_turns, tools enable/disable, simple yaml keys. Keys that are explicitly sensitive or unique (auth tokens, .env secrets, profile name, credentials, ssh keys, pairing tokens) are never propagated.
- Propagation can be recursive (A → B → C) only if `--propagate-recursive` is passed. Recursive propagation is OFF by default to avoid accidental blast radius.

Conflict resolution
-------------------
When a target profile has local changes that differ from the incoming update:
- Default policy: latest-wins for non-sensitive keys (apply, and record the change in the target profile's changelog).
- Optional interactive policy: `--prompt-on-conflict` (opens an interactive diff+choice: [apply, skip, abort]) — requires interactive TTY or gateway approval flow.
- For non-interactive runs, a `--abort-on-conflict` flag causes the whole propagation to abort with a non-zero exit and no partial changes.

CLI UX (flags)
---------------
New flags on `hermes update` (examples):
- --propagate / --no-propagate  (bool)
- --propagate-scope=linked|all|same-owner  (default: linked)
- --propagate-recursive  (bool, default: false)
- --propagate-dry-run  (bool)  (dry-run: show the diff that WOULD be applied)
- --prompt-on-conflict / --abort-on-conflict  (conflict policy)
- --propagate-level=keys|full  (keys = only changed keys; full = overwrite profile)

Default CLI behavior examples are below.

Config file keys
----------------
Under `~/.hermes/config.yaml` (or per-profile config):

propagation:
  enabled: false            # default behavior (global default)
  default_scope: "linked" # linked | all | same-owner
  recursive_by_default: false
  conflict_policy: "latest-wins"  # latest-wins | abort | prompt
  excluded_keys:
    - ".env"
    - "auth"
    - "credentials"

Per-profile override in ~/.hermes/profiles/<name>/config.yaml:

propagation:
  enabled: true
  scope: null   # null uses global default; otherwise linked|all|same-owner
  allow_overwrite_keys: ["display.skin", "agent.max_turns"]

Environment variables (optional):
- HERMES_PROPAGATE=true|false  (cli-env override)

Authorization model
-------------------
Principles:
- Only the invoking user (unix owner) or an account with explicit pairing/permission may propagate updates to a profile.
- Profiles have an owner metadata field (`owner_email` or `owner_userid`) set on profile creation or import.

Rules:
- If the invoker's identity == target_profile.owner → permitted.
- If target_profile has a `pairing` entry that includes the invoker → permitted.
- Otherwise, operation is blocked; `hermes update --propagate` returns 403-like error with instruction to `hermes pairing request <profile>` or to ask the owner to approve.

Surface permission errors clearly: show which profile(s) were skipped and why, and provide an actionable command for requesting permission.

Audit & logging
---------------
- Every propagated change gets a changelog entry in target profile: ~/.hermes/profiles/<name>/propagation.log with timestamp, origin_profile, keys_changed, user, outcome (applied/skipped/conflict).
- `hermes profile show <name>` should display last propagated-from info and a link to the log tail.

Dry-run and confirmation step
-----------------------------
- `--propagate-dry-run` prints a machine-readable diff (JSON + human summary) and exits with 0; no changes applied.
- For non-interactive flows, `--propagate` without `--yes` should *not* prompt; requiring `--yes` for non-interactive destructive operations is recommended. Interactive tools (CLI TTY) can prompt when `--prompt-on-conflict` is set.

Examples
--------
1) Propagate explicit ON (invoker chooses to propagate):

# User updates profile 'alice' and wants to propagate to linked profiles
hermes profile use alice
hermes update --propagate --propagate-scope=linked --propagate-dry-run
# Review diff, then:
hermes update --propagate --propagate-scope=linked --yes

Expected outcome: diffs applied to linked profiles; propagation.log updated; any permission-denied targets reported and skipped.

2) Propagate explicitly OFF (explicitly prevent propagation):

# Update without propagation
hermes profile use bob
hermes update --no-propagate

Expected outcome: only 'bob' updated, no changes to any other profiles.

Failure modes
-------------
- Partial application (network/power failure mid-propagation): use changelog entries and idempotent diffs. Implementation should apply changes per-target atomically (write temp file + rename) and record success before moving to next target.
- Conflicts resolved silently (latest-wins) may surprise users — mitigation: email / comment notification and changelog records.
- Permission errors: should be non-fatal for other targets; return non-zero if all targets failed.

Migration notes
---------------
- Existing setups have no propagation keys. Add `propagation:` section to global config via `hermes config migrate` with default settings (enabled: false).
- For users who previously used scripts to copy configs between profiles, recommend switching to explicit `hermes update --propagate --propagate-scope=linked` workflows; provide a migration helper `hermes profile snapshot --export /tmp/p.json && hermes profile import --target other --apply-snapshot /tmp/p.json` for one-off clones.

Open questions / Interview checklist
-----------------------------------
(These must be answered by the product owner or requestor; record timestamps of answers in this task thread.)
1. Which default scope should be chosen for first release? (linked | all | same-owner)
2. Is default propagation ON or OFF? (draft: OFF)
3. Should recursive propagation be allowed by default? (draft: OFF)
4. Preferred conflict policy (latest-wins | prompt | abort)? (draft: latest-wins with prompt option)
5. Which exact config keys must be excluded from propagation? Any extra secrets or provider-specific tokens?
6. What is acceptable audit retention and where should logs be stored? (local only vs. central audit server)
7. Integration needs: should the gateway send propagation notifications to profile owners (email/DM)?
8. UX: Should `hermes update` prompt by default when invoked from an interactive TTY and propagation is enabled? (draft: require `--yes` for destructive ops)

Acceptance criteria checklist (self-check)
-----------------------------------------
- [x] Requirements doc draft created (this file)
- [x] Two example command flows included
- [x] Decision about default behavior recorded (default: OFF)
- [ ] Stakeholder review & sign-off pending — requesting review via kanban comment and blocking for sign-off

Next steps
----------
1. Send this draft to the requestor/PO with the interview checklist (timestamp answers in the task comment).
2. After answers, update the spec and implement `hermes config migrate` entry + CLI flags.
3. Add unit tests covering: (a) propagate-dry-run shows correct diffs, (b) permission denied targets are reported and skipped, (c) propagation.log entries recorded.

Files produced by this run
-------------------------
- /home/pk/.hermes/kanban/workspaces/t_e2115d87/docs/profile-propagation-spec.md


