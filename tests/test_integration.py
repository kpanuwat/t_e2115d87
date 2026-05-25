import json
import subprocess
from pathlib import Path


def run_cli(old_path, new_path, targets, yes=False, dry_run=False):
    cmd = ["python3", "-m", "src.hermes.cli_update", "--source-old", str(old_path), "--source-new", str(new_path), "--propagate"]
    if dry_run:
        cmd.append("--propagate-dry-run")
    if yes:
        cmd.append("--yes")
    cmd += ["--targets"] + [str(t) for t in targets]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res


def test_integration_propagate(tmp_path):
    # prepare old/new
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    old.write_text(json.dumps({"model": {"default": "gpt-4"}, "agent": {"max_turns": 3}, "auth": "old-secret"}))
    new.write_text(json.dumps({"model": {"default": "gpt-4o"}, "agent": {"max_turns": 5}, "auth": "new-secret"}))

    # create two profile dirs
    p1 = tmp_path / "profiles" / "p1"
    p2 = tmp_path / "profiles" / "p2"
    p1.mkdir(parents=True)
    p2.mkdir(parents=True)
    (p1 / "config.json").write_text(json.dumps({"model": {"default": "gpt-4"}, "agent": {"max_turns": 3}}))
    (p2 / "config.json").write_text(json.dumps({"model": {"default": "gpt-4"}, "agent": {"max_turns": 3}}))

    # dry-run
    r = run_cli(old, new, [p1, p2], dry_run=True)
    assert r.returncode == 0
    assert 'dry-run' in r.stdout

    # apply
    r = run_cli(old, new, [p1, p2], yes=True)
    assert r.returncode == 0
    assert 'applied' in r.stdout

    # check propagation logs
    for p in [p1, p2]:
        log = p / 'propagation.log'
        assert log.exists()
        lines = log.read_text().strip().splitlines()
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry['outcome'] == 'applied'

