"""Compile workspace bundle from engine projection.

Wrapper over engine.projections.workspace.project_workspace for offline sample data.
"""
import argparse, json, sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

from engine.projections.workspace import project_workspace

p = argparse.ArgumentParser()
p.add_argument("--exports", type=Path, default=repo / "design_pack/sample_data")
p.add_argument("--output", type=Path, default=repo / "web/src/workspace/data.generated.json")
a = p.parse_args()

ids = ['c05_research_medium','c04_writing_short','c03_coding_short','c07_research_short','c20_coding_short','c27_creative_short','c30_creative_short','c10_research_short','c16_research_short','c17_research_short']
names = ['AI creativity · paper research','Human–AI interaction design','Interactive portfolio','Co-creation research','Figma migration','Jellyfish motion study','Language-learning videos','Project contribution','Co-creative panel','Datafied Society']

chats, warnings = [], []
for cid, title in zip(ids, names):
    export_file = a.exports / f"{cid}.json"
    cdir = repo / "data/chats" / cid
    dlg_path = cdir / "dialogue.json" if (cdir / "dialogue.json").exists() else repo / "data/corpus" / cid / "dialogue.json"
    dlg = json.loads(dlg_path.read_text(encoding="utf-8"))

    if (cdir / "state.json").exists() and (cdir / "ledger.jsonl").exists():
        st = json.loads((cdir / "state.json").read_text(encoding="utf-8"))
        ledger = [json.loads(line) for line in (cdir / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        summary = json.loads(export_file.read_text(encoding="utf-8")).get("dialogue_summary", "") if export_file.exists() else ""
    elif export_file.exists():
        d = json.loads(export_file.read_text(encoding="utf-8"))
        st = {"outcomes": d["step_1_outcomes"], "requirements": d["step_2_requirements"], "slots": d["step_2_slots"], "operations_log": d["step_3_operations_log"], "actions": d["step_3_all_actions"]}
        ledger = [r for pp in d["step_4_pairs"] for r in pp["ledger_rows"]]
        summary = d.get("dialogue_summary", "")
    else:
        warnings.append(f"{cid}: data not found; omitted")
        continue

    bundle = project_workspace(
        dialogue=dlg,
        state=st,
        ledger=ledger,
        source_meta={"title": title},
        meta={"category": cid.split("_")[1].title()},
        chat_id=cid,
        summary=summary,
    )
    chats.append(bundle)

a.output.write_text(json.dumps({"chats": chats, "links": [], "warnings": warnings}, ensure_ascii=False, separators=(",", ":")))
print(f"Compiled {len(chats)} chats; {sum(c['totalPairs'] for c in chats)} pairs; {a.output.stat().st_size} bytes; Warnings: {warnings}")
