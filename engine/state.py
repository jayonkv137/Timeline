"""In-memory pipeline STATE ↔ state.json.

The persisted shape is EXACTLY state.schema.json (actions, outcomes,
intentions, requirements, slots, operations_log — additionalProperties
false). The pipeline also needs cross-pair working data that the state
schema has no home for (action→outcome mapping from Step 1b, the rolling
dialogue summary, Trigger-B's per-requirement labeled-action tracking,
slot age counters for the 3-pair abandonment sweep). That lives in
`self.run` and is persisted separately to `<out>/run/pipeline_state.json`
— an internal, non-contract file under run/ (gitignored), see
SPEC_QUESTIONS.md Q3.
"""
import json
from pathlib import Path

from engine.artifacts import validate_artifact, write_json_artifact


def _empty_run_state():
    return {
        # Step 1b outputs consumed by Step 2's FILTER:
        "action_to_outcome": {},          # action_id -> outcome_id
        "dialogue_summary": "",           # SELF-REFERENCE loop input
        "outcome_to_intention": {},       # outcome_id -> intention_id (R-SIDE)
        # Trigger B bookkeeping: (outcome_id, req_id) -> [action_id, ...]
        # stored with a "outcome_id||req_id" string key for JSON round-trip
        "labeled_action_ids": {},
        # slot ageing for the 3-pair abandonment sweep:
        # "outcome_id||slot_id" -> pair the slot was opened at
        "slot_opened_at_pair": {},
        "last_completed_pair": 0,         # for --resume
    }


class State:
    def __init__(self):
        self.actions = []
        self.outcomes = []
        self.intentions = []
        self.requirements = []
        self.slots = []
        self.operations_log = []
        self.run = _empty_run_state()
        self._actions_by_id = {}

    # ---- lookups the pipeline steps need -------------------------------

    def get_action(self, action_id):
        return self._actions_by_id[action_id]

    def has_action(self, action_id):
        return action_id in self._actions_by_id

    def add_action(self, action):
        if action["id"] in self._actions_by_id:
            raise ValueError(f"duplicate action id: {action['id']}")
        self.actions.append(action)
        self._actions_by_id[action["id"]] = action

    def actions_for_outcome(self, outcome_id):
        a2o = self.run["action_to_outcome"]
        return [a for a in self.actions if a2o.get(a["id"]) == outcome_id]

    def get_outcome(self, outcome_id):
        for o in self.outcomes:
            if o["id"] == outcome_id:
                return o
        raise KeyError(f"unknown outcome id: {outcome_id}")

    def requirements_for_outcome(self, outcome_id):
        return [r for r in self.requirements if r["outcome_id"] == outcome_id]

    def find_requirement(self, outcome_id, req_id):
        for r in self.requirements:
            if r["outcome_id"] == outcome_id and r["req_id"] == req_id:
                return r
        return None

    def slots_for_outcome(self, outcome_id, status=None):
        found = [s for s in self.slots if s["outcome_id"] == outcome_id]
        if status is not None:
            found = [s for s in found if s["status"] == status]
        return found

    def find_slot(self, outcome_id, slot_id):
        for s in self.slots:
            if s["outcome_id"] == outcome_id and s["slot_id"] == slot_id:
                return s
        return None

    def log_operation(self, pair, outcome_id, op, target_id, target_type):
        self.operations_log.append({
            "pair": pair,
            "outcome_id": outcome_id,
            "op": op,
            "target_id": target_id,
            "target_type": target_type,
        })

    # ---- persistence ----------------------------------------------------

    def to_dict(self):
        return {
            "actions": self.actions,
            "outcomes": self.outcomes,
            "intentions": self.intentions,
            "requirements": self.requirements,
            "slots": self.slots,
            "operations_log": self.operations_log,
        }

    def save(self, out_dir):
        """Write <out>/state.json (schema-validated, raises on failure) and
        <out>/run/pipeline_state.json (internal working data).
        """
        out_dir = Path(out_dir)
        write_json_artifact(out_dir / "state.json", self.to_dict(), "state")
        run_path = out_dir / "run" / "pipeline_state.json"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        with open(run_path, "w") as f:
            json.dump(self.run, f, indent=2, ensure_ascii=False)
            f.write("\n")

    @classmethod
    def load(cls, out_dir):
        """Rebuild STATE from <out>/state.json (validated on read) plus
        <out>/run/pipeline_state.json if present (fresh run-state otherwise).
        """
        out_dir = Path(out_dir)
        with open(out_dir / "state.json") as f:
            data = validate_artifact(json.load(f), "state")
        state = cls()
        for action in data["actions"]:
            state.add_action(action)
        state.outcomes = data["outcomes"]
        state.intentions = data["intentions"]
        state.requirements = data["requirements"]
        state.slots = data["slots"]
        state.operations_log = data["operations_log"]
        run_path = out_dir / "run" / "pipeline_state.json"
        if run_path.exists():
            with open(run_path) as f:
                loaded = json.load(f)
            run = _empty_run_state()
            run.update(loaded)
            state.run = run
        return state
