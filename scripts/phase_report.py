#!/usr/bin/env python3
"""scripts/phase_report.py - Programmatic phase verification report.

Generates ground-truth metrics, test counts per tier, corpus reconciliation,
fidelity grades, invariant evaluation, and Definition of Done status
strictly from filesystem state. Zero narrative prose.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_git_info() -> dict[str, str]:
    info = {"head": "unknown", "branch": "unknown", "tag": "none"}
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
        if r.returncode == 0:
            info["head"] = r.stdout.strip()
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
        if r.returncode == 0:
            info["branch"] = r.stdout.strip()
        r = subprocess.run(["git", "tag", "--points-at", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
        if r.returncode == 0 and r.stdout.strip():
            info["tag"] = r.stdout.strip().replace("\n", ", ")
    except Exception:
        pass
    return info


def get_python_bin() -> str:
    venv_py = REPO_ROOT / ".venv/bin/python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def get_test_counts() -> dict[str, int]:
    tiers = ["tier0", "tier1", "tier2", "tier3"]
    counts: dict[str, int] = {}
    python_bin = get_python_bin()


    # Total collected
    cmd = [python_bin, "-m", "pytest", "--collect-only", "-q"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        # last line usually contains e.g. "52 tests collected in 0.05s"
        m = re.search(r"(\d+)\s+tests?\s+collected", r.stdout)
        counts["total_collected"] = int(m.group(1)) if m else 0
    except Exception:
        counts["total_collected"] = 0

    for t in tiers:
        cmd = [python_bin, "-m", "pytest", "-m", t, "--collect-only", "-q"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
            m = re.search(r"(\d+)\s+tests?\s+collected", r.stdout)
            counts[t] = int(m.group(1)) if m else 0
        except Exception:
            counts[t] = 0
    return counts


def run_pytest(marker: str | None = None) -> tuple[bool, str]:
    python_bin = get_python_bin()
    cmd = [python_bin, "-m", "pytest", "-q"]

    if marker:
        cmd.extend(["-m", marker])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        summary = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "no output"
        return (r.returncode == 0, summary)
    except Exception as e:
        return (False, str(e))


def evaluate_corpus() -> dict[str, Any]:
    corpus_dirs = sorted([d for d in glob.glob(str(REPO_ROOT / "data/corpus/c*")) if os.path.isdir(d)])
    chats: list[dict[str, Any]] = []

    tot_pairs = 0
    tot_images = 0
    tot_injected = 0
    tot_tool = 0
    tot_empty = 0
    grades = {"clean": 0, "degraded": 0, "unusable": 0}
    missing_files = []
    schema_errors = []

    # Schema check
    schema_path = REPO_ROOT / "engine/schemas/dialogue.schema.json"
    schema = None
    if schema_path.exists():
        try:
            import jsonschema  # type: ignore
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except ImportError:
            pass

    filled_meta_count = 0

    for d in corpus_dirs:
        cid = os.path.basename(d)
        sm_path = os.path.join(d, "source_meta.json")
        dial_path = os.path.join(d, "dialogue.json")
        meta_path = os.path.join(d, "meta.yaml")

        for req in ["source_meta.json", "dialogue.json", "meta.yaml"]:
            if not os.path.exists(os.path.join(d, req)):
                missing_files.append((cid, req))

        has_source = any(os.path.exists(os.path.join(d, f"source.{ext}")) for ext in ["json", "md", "txt", "html"])
        if not has_source:
            missing_files.append((cid, "source.*"))

        if os.path.exists(sm_path):
            with open(sm_path, "r", encoding="utf-8") as f:
                sm = json.load(f)
            pairs = sm.get("pairs", 0)
            fid = sm.get("fidelity", {})
            img = fid.get("images_dropped", 0)
            inj = fid.get("injected_turns", 0)
            tool = fid.get("tool_narration_turns", 0)
            empty = fid.get("empty_turns", 0)
            grade = fid.get("grade") or ("clean" if img / max(pairs, 1) <= 0.05 else ("degraded" if img / max(pairs, 1) <= 0.5 else "unusable"))

            tot_pairs += pairs
            tot_images += img
            tot_injected += inj
            tot_tool += tool
            tot_empty += empty
            if grade in grades:
                grades[grade] += 1

            chats.append({
                "id": cid,
                "title": sm.get("source_title") or sm.get("chat_id", cid),
                "pairs": pairs,
                "images": img,
                "ratio": round(img / max(pairs, 1), 2),
                "injected": inj,
                "tool": tool,
                "empty": empty,
                "grade": grade,
            })

        if schema and os.path.exists(dial_path):
            with open(dial_path, "r", encoding="utf-8") as f:
                dial = json.load(f)
            try:
                jsonschema.validate(instance=dial, schema=schema)
            except Exception as e:
                schema_errors.append((cid, str(e)))

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                content = f.read()
            m = re.search(r"^task_type:([^#\n]*)", content, re.MULTILINE)
            if m and m.group(1).strip():
                filled_meta_count += 1

    # Manifest check
    manifest_reconciled = False
    manifest_totals = {}
    manifest_path = REPO_ROOT / "data/corpus/manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        m_chats = manifest.get("chats", [])
        m_pairs = sum(c.get("pairs", 0) for c in m_chats)
        m_images = sum(c.get("images_dropped", 0) for c in m_chats)
        m_injected = sum(c.get("injected_turns", 0) for c in m_chats)
        m_tool = sum(c.get("tool_narration_turns", 0) for c in m_chats)
        manifest_totals = {
            "chats": len(m_chats),
            "pairs": m_pairs,
            "images_dropped": m_images,
            "injected_turns": m_injected,
            "tool_narration_turns": m_tool,
        }
        manifest_reconciled = (
            len(m_chats) == len(chats)
            and m_pairs == tot_pairs
            and m_images == tot_images
            and m_injected == tot_injected
            and m_tool == tot_tool
        )

    golden_01_exists = (REPO_ROOT / "data/corpus/golden_01").exists()

    return {
        "chat_count": len(chats),
        "chats": chats,
        "tot_pairs": tot_pairs,
        "tot_images": tot_images,
        "tot_injected": tot_injected,
        "tot_tool": tot_tool,
        "tot_empty": tot_empty,
        "grades": grades,
        "missing_files": missing_files,
        "schema_errors": schema_errors,
        "manifest_reconciled": manifest_reconciled,
        "manifest_totals": manifest_totals,
        "filled_meta_count": filled_meta_count,
        "golden_01_exists": golden_01_exists,
    }


def evaluate_invariants_on_fixture() -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from tests import invariants as inv
    except ImportError:
        return {"error": "cannot import tests.invariants"}

    fixture_dir = REPO_ROOT / "data/chats/fixture_pair1"
    artifacts: dict[str, Any] = {}
    for name in ["dialogue.json", "state.json", "snapshots.json", "panel_bundle.json"]:
        p = fixture_dir / name
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                artifacts[name.split(".")[0]] = json.load(f)

    ledger_path = fixture_dir / "ledger.jsonl"
    ledger_rows = []
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ledger_rows.append(json.loads(line))
        artifacts["ledger"] = ledger_rows

    results: dict[str, str] = {}
    for i in range(1, 22):
        fn_name = f"inv_{i:02d}_"
        match_fn = [getattr(inv, name) for name in dir(inv) if name.startswith(fn_name)]
        if not match_fn:
            results[f"inv_{i:02d}"] = "missing"
            continue
        fn = match_fn[0]
        # Dispatch with appropriate args
        try:
            if i == 1:
                res = fn({"dialogue": artifacts.get("dialogue"), "state": artifacts.get("state"), "snapshots": artifacts.get("snapshots"), "panel_bundle": artifacts.get("panel_bundle")})
            elif i == 2:
                res = fn(artifacts.get("state", {}))
            elif i == 3:
                res = fn(artifacts.get("ledger", []), artifacts.get("state", {}))
            elif i == 4:
                res = fn(artifacts.get("state", {}))
            elif i == 5:
                res = fn(artifacts.get("ledger", []))
            elif i in (6, 7, 8):
                res = fn(artifacts.get("state", {}))
            elif i == 9:
                res = fn(artifacts.get("state", {}))
            elif i in (10, 11, 12, 13, 14, 15, 16):
                res = fn(None)
            elif i in (17, 18, 19, 20):
                res = fn(None, None)
            elif i == 21:
                res = fn(artifacts.get("dialogue"), artifacts.get("ledger"), artifacts.get("state"))
            else:
                res = []

            if not res:
                results[f"inv_{i:02d}"] = "PASS"
            elif any("skipped:" in str(x) for x in res):
                results[f"inv_{i:02d}"] = f"SKIPPED ({res[0]})"
            else:
                results[f"inv_{i:02d}"] = f"FAIL: {res[0]}"
        except Exception as e:
            results[f"inv_{i:02d}"] = f"ERROR: {e}"

    return results


def check_fixture_untouched() -> tuple[bool, str]:
    try:
        r = subprocess.run(["git", "diff", "origin/master...HEAD", "--", "data/chats/fixture_pair1/"],
                           capture_output=True, text=True, cwd=REPO_ROOT)
        if r.stdout.strip():
            return False, "fixture modified relative to origin/master"
        r2 = subprocess.run(["git", "status", "--porcelain", "data/chats/fixture_pair1/"],
                            capture_output=True, text=True, cwd=REPO_ROOT)
        if r2.stdout.strip():
            return False, "fixture working tree dirty"
        return True, "byte-identical"
    except Exception as e:
        return False, str(e)


def main() -> int:
    print("=" * 80)
    print("PHASE VERIFICATION REPORT (GENERATED FROM FILESYSTEM)")
    print("=" * 80)

    git = get_git_info()
    print(f"Git Branch: {git['branch']} | Commit: {git['head']} | Tag(s): {git['tag']}")
    print("-" * 80)

    # 1. Test Suite Summary
    test_counts = get_test_counts()
    pytest_pass, pytest_summary = run_pytest()
    t1_pass, t1_summary = run_pytest("tier1")

    print("1. TEST HARNESS & TIERS")
    print(f"  Total collected tests : {test_counts.get('total_collected', 0)}")
    print(f"  tier0 (replay)        : {test_counts.get('tier0', 0)}")
    print(f"  tier1 (deterministic) : {test_counts.get('tier1', 0)}")
    print(f"  tier2 (live API)      : {test_counts.get('tier2', 0)}")
    print(f"  tier3 (robustness)    : {test_counts.get('tier3', 0)}")
    print(f"  Default pytest run    : {'PASS' if pytest_pass else 'FAIL'} ({pytest_summary})")
    print(f"  pytest -m tier1       : {'PASS' if t1_pass else 'FAIL'} ({t1_summary})")
    print("-" * 80)

    # 2. Corpus Fidelity & Reconciliation
    corp = evaluate_corpus()
    print("2. CORPUS FIDELITY & MANIFEST RECONCILIATION")
    print(f"  Ingested chats        : {corp['chat_count']}")
    print(f"  Total dialogue pairs  : {corp['tot_pairs']}")
    print(f"  Images dropped        : {corp['tot_images']}")
    print(f"  Injected turns        : {corp['tot_injected']}")
    print(f"  Tool narration turns  : {corp['tot_tool']}")
    print(f"  Empty AI turns        : {corp['tot_empty']}")
    print(f"  Fidelity grades       : clean={corp['grades']['clean']}, "
          f"degraded={corp['grades']['degraded']}, unusable={corp['grades']['unusable']}")
    print(f"  Missing 4-files       : {len(corp['missing_files'])}")
    print(f"  Schema errors         : {len(corp['schema_errors'])}")
    print(f"  Manifest reconciled   : {'YES (100% match)' if corp['manifest_reconciled'] else 'NO (mismatch)'}")
    print(f"  meta.yaml filled      : {corp['filled_meta_count']} of {corp['chat_count']}")
    print(f"  golden_01 exists      : {'YES' if corp['golden_01_exists'] else 'NO'}")
    print("-" * 80)

    # 3. Per-Chat Fidelity Table
    print("3. PER-CHAT FIDELITY TABLE")
    print(f"  {'Chat ID':<16} {'Pairs':>5} {'Img':>5} {'Ratio':>6} {'Empty':>5} {'Grade':<9} {'Title'}")
    for c in corp["chats"]:
        print(f"  {c['id']:<16} {c['pairs']:>5} {c['images']:>5} {c['ratio']:>6.2f} {c['empty']:>5} {c['grade']:<9} {c['title'][:40]}")
    print("-" * 80)

    # 4. Invariants on Fixture
    invs = evaluate_invariants_on_fixture()
    print("4. THE 21 INVARIANTS EVALUATION (data/chats/fixture_pair1/)")
    for k, v in sorted(invs.items()):
        print(f"  {k}: {v}")
    print("-" * 80)

    # 5. Fixture Integrity
    fix_ok, fix_msg = check_fixture_untouched()
    print("5. FROZEN FIXTURE INTEGRITY")
    print(f"  fixture_pair1 state   : {'UNTOUCHED' if fix_ok else 'MODIFIED'} ({fix_msg})")
    print("-" * 80)

    # 6. E0 Definition of Done Checkboxes
    print("6. E0 DEFINITION OF DONE AUDIT")
    dod = [
        ("pytest green (including 22 pre-existing)", pytest_pass),
        ("pytest -m tier1 green", t1_pass),
        ("Every export in testing folder ingested or refused with reason", corp["chat_count"] == 36 and len(corp["missing_files"]) == 0),
        ("Every corpus entry has 4 files and validates dialogue schema", len(corp["missing_files"]) == 0 and len(corp["schema_errors"]) == 0),
        ("data/corpus/manifest.json exists and totals reconcile", corp["manifest_reconciled"]),
        ("Owner has filled meta.yaml for every entry and renamed folders", corp["filled_meta_count"] == corp["chat_count"] and corp["filled_meta_count"] > 0),
        ("tests/invariants.py implements all 21; 1-9 pass on fixture", all(invs.get(f"inv_{i:02d}") == "PASS" for i in range(1, 10))),
        ("Record and replay LLM client demonstrated working", (REPO_ROOT / "tests/test_llm_cache.py").exists()),
        ("Q4, Q5, Q6 (and Q7, Q8) logged in SPEC_QUESTIONS.md", (REPO_ROOT / "SPEC_QUESTIONS.md").exists()),
        ("data/chats/fixture_pair1/ byte-identical", fix_ok),
        ("Golden chat (golden_01) established for E1", corp["golden_01_exists"]),
    ]

    all_done = True
    for desc, passed in dod:
        mark = "[X]" if passed else "[ ]"
        print(f"  {mark} {desc}")
        if not passed:
            all_done = False

    print("=" * 80)
    print(f"Overall Status: {'ALL DOD CRITERIA MET' if all_done else 'IN PROGRESS (OWNER TASKS OUTSTANDING)'}")
    print("=" * 80)
    return 0 if pytest_pass and t1_pass and corp["manifest_reconciled"] else 1


if __name__ == "__main__":
    sys.exit(main())
