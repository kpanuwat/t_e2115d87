Title: Implementation Plan — Profile Propagation

Summary
-------
Concrete implementation plan for profile propagation feature for `hermes update` (linked scope, default OFF) following SOUL principles: reliability, tests, small increments, observability, reversible rollouts.

Scope
-----
- Implement diff-based propagation of changed keys to linked profiles only by default.
- Exclude sensitive keys (.env, auth, credentials).
- Default behavior: propagation OFF; explicit via --propagate.

Phased work (small increments)
-----------------------------
1) Design & Tests (this PR)
   - Add design doc and unit test skeletons for propagation logic.
   - Provide CLI flag parsing tests for --propagate, --propagate-scope, --propagate-dry-run.
2) Implement core library
   - Add hermes.propagation module: diff extractor, safe-apply (tempfile+rename), excluded keys filter, permission checks.
   - Ensure idempotency tokens and per-target atomic write semantics.
3) CLI integration
   - Wire into `hermes update` command: dry-run, prompt-on-conflict, abort-on-conflict flags.
   - Add per-profile config overrides.
4) Tests & CI
   - Unit tests for diff application, permission checks, conflict policies.
   - Integration test harness (in-memory profiles store) to run end-to-end.
5) Docs & changelog
   - Update docs, CLI help, and add migration helper.
6) Rollout
   - Feature flag behind config (propagation.enabled=false default).
   - Canary rollout to one profile group, monitor propagation.log and metrics.

Pre-deploy checklist (SOUL)
--------------------------
- [x] Tests added (skeleton)
- [x] Design doc added
- [ ] Implementation module added and covered by unit tests
- [ ] CI integration and smoke test added
- [ ] Monitoring + propagation.log entries implemented
- [ ] Rollout plan and runbook created

Observability
-------------
- propagation.log per target profile (~/.hermes/profiles/<name>/propagation.log)
- metrics: propagation.attempts, propagation.success, propagation.failures, propagation.latency
- alerts: propagation.failure_rate > 5% for 5m

Rollback & Safety
-----------------
- Atomic apply per-profile (write temp + rename)
- Write changelog entry before marking success
- Provide --propagate-dry-run for safe inspection
- Provide --abort-on-conflict to avoid partial application in non-interactive runs

Files to produce in this PR
--------------------------
- docs/implementation-plan.md (this file)
- tests/test_propagation.py (skeleton)
- CHANGELOG.md entry

Next actions
------------
- Create a feature branch if not present (we already are on openspec/... branch)
- Implement hermes.propagation core module and unit tests
- Open PR for review

