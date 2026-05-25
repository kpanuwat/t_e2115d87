Title: Runbook — Profile Propagation Canary Rollout

Scope
-----
Runbook for canary rollout of profile propagation feature (hermes update --propagate) following SOUL best-practices: small, observable, reversible.

Prerequisites
-------------
- PR #1 merged into main
- CI green on PR (pytest + smoke)
- Monitoring hooks in place (propagation.log, metrics)
- A test tenant/group of 2-5 profiles labeled `canary` (local dirs under ~/.hermes/profiles/canary-*)

Canary plan
-----------
1) Dry-run on canary targets
   - Command (dry-run):
     python -m src.hermes.cli_update --source-old /path/to/old.json --source-new /path/to/new.json --propagate --propagate-dry-run --targets ~/.hermes/profiles/canary-1 ~/.hermes/profiles/canary-2
   - Verify diffs and propagation summaries.
2) Apply to canary (manual confirmation required)
   - Command: same as above + --yes (and without --propagate-dry-run)
   - Monitor propagation.log for successes and failures.
3) Observe for 24 hours (recommended 24–72h)
   - Metrics: propagation.attempts, propagation.success, propagation.failures, propagation.latency
   - Alerts: failure_rate > 5% for 5m
4) If stable, expand to next batch (10–50 profiles) and repeat observation window.
5) Full rollout: enable feature flag globally and monitor for 72h.

Rollback steps
--------------
- If failures exceed threshold: run reverse apply from snapshot or restore profile config from changelog snapshot: (1) collect propagation.log entries, (2) restore config.json from previous snapshot saved by propagation module, or (3) run hermes profile import from exported snapshot.
- Emergency: set propagation.enabled=false in ~/.hermes/config.yaml and notify ops.

Post-deploy
-----------
- Record rollout notes in CHANGELOG.md and kanban task comments.
- Add pager/runbook link to on-call runbook and update alerts.

Safety & approvals
------------------
- Require human approval before each apply step in canary (use --yes explicitly).
- Ensure propagation.dry-run is available in automation for scheduled checks.

