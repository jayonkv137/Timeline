"""P2.S3 tests: Steps 1a → 1b → 1c per pair (§9.1).

Uses a MOCKED LLM client — zero API cost, deterministic.

Test plan from the preamble:
 - Happy path across 2 pairs proving accumulation + summary loop
 - Bad turn-id format → raises PipelineError
 - Wrong pair number in action id → raises PipelineError
 - Invalid role → raises PipelineError
 - Incomplete action_to_outcome → raises PipelineError
 - Duplicate outcome ids → raises PipelineError
 - Incomplete outcome→intention → raises PipelineError
 - Duplicate intention mapping → raises PipelineError
 - Unknown outcome in intention mapping → raises PipelineError
 - Unknown parent outcome → raises PipelineError
 - Formatting helpers produce spec-shaped keys
 - action_sort_key: U before A within a pair, pair ordering
"""
import json
from dataclasses import dataclass

import pytest

from engine.pipeline import (
    ACTION_ID_RE,
    PipelineError,
    action_sort_key,
    format_actions_block,
    format_dialogue_block,
    format_outcomes_list,
    run_level1,
    step_1a,
    step_1b,
    step_1c,
    format_prior_requirements,
    format_prior_slots,
    step_2,
    run_level2,
    format_action_list_for_step3,
    step_3_for_req,
    run_level3,
)
from engine.state import State




# ---------------------------------------------------------------- mock LLM

class MockLLMClient:
    """Returns pre-programmed JSON responses keyed by step label prefix."""

    def __init__(self, responses):
        self._responses = responses  # {prefix: dict}
        self.calls = []

    def call_json(self, step, model, prompt):
        self.calls.append((step, model, prompt))
        for prefix, response in self._responses.items():
            if step.startswith(prefix):
                return response
        raise RuntimeError(f"MockLLMClient: no response for step {step!r}")


@dataclass(frozen=True)
class MockConfig:
    model_fast: str = "mock-fast"
    model_main: str = "mock-main"
    model_step2: str = "mock-main"
    model_step3: str = "mock-main"
    step3_batch_size: int = 3




# ------------------------------------------------------------- test data

PAIR1_STEP1A_RESPONSE = {
    "actions": [
        {
            "turn id": "U(1,1)",
            "action type": "Request",
            "action text": "User asks AI to build a website.",
            "role": "SHAPER",
            "evidence quote": "Can you build me a website?",
        },
        {
            "turn id": "U(1,2)",
            "action type": "Constrain",
            "action text": "User specifies it must be responsive.",
            "role": "SHAPER",
            "evidence quote": "It needs to be responsive.",
        },
        {
            "turn id": "A(1,1)",
            "action type": "Accept",
            "action text": "AI agrees to build the website.",
            "role": "EXECUTOR",
            "evidence quote": "Sure, I'll build a responsive website.",
        },
    ]
}

PAIR1_STEP1B_RESPONSE = {
    "dialogue summary": "User and AI are collaborating on building a responsive website.",
    "outcomes": [
        {
            "outcome id": "outcome 1",
            "outcome": "Responsive website",
            "turn id": "U(1,1)",
            "parent outcome id": None,
            "child outcome ids": [],
            "related outcome ids": [],
            "confidence": 0.95,
        },
    ],
    "action to outcome": {
        "U(1,1)": "outcome 1",
        "U(1,2)": "outcome 1",
        "A(1,1)": "outcome 1",
    },
}

PAIR1_STEP1C_RESPONSE = {
    "intentions": [
        {"intention id": "I1", "intention": "Build a website"},
    ],
    "outcome to intention": [
        {"outcome id": "outcome 1", "intention id": "I1"},
    ],
}

# Pair 2: accumulates on top of pair 1

PAIR2_STEP1A_RESPONSE = {
    "actions": [
        {
            "turn id": "U(2,1)",
            "action type": "Request",
            "action text": "User asks for a dark mode.",
            "role": "SHAPER",
            "evidence quote": "Add dark mode please.",
        },
        {
            "turn id": "A(2,1)",
            "action type": "Implement",
            "action text": "AI implements dark mode toggle.",
            "role": "EXECUTOR",
            "evidence quote": "I've added a dark mode toggle.",
        },
    ]
}

PAIR2_STEP1B_RESPONSE = {
    "dialogue summary": "User and AI are building a responsive website with dark mode support.",
    "outcomes": [
        {
            "outcome id": "outcome 1",
            "outcome": "Responsive website with dark mode",
            "turn id": "U(1,1)",
            "parent outcome id": None,
            "child outcome ids": ["outcome 2"],
            "related outcome ids": [],
            "confidence": 0.95,
        },
        {
            "outcome id": "outcome 2",
            "outcome": "Dark mode feature",
            "turn id": "U(2,1)",
            "parent outcome id": "outcome 1",
            "child outcome ids": [],
            "related outcome ids": [],
            "confidence": 0.9,
        },
    ],
    "action to outcome": {
        "U(1,1)": "outcome 1",
        "U(1,2)": "outcome 1",
        "A(1,1)": "outcome 1",
        "U(2,1)": "outcome 2",
        "A(2,1)": "outcome 2",
    },
}

PAIR2_STEP1C_RESPONSE = {
    "intentions": [
        {"intention id": "I1", "intention": "Build a website"},
    ],
    "outcome to intention": [
        {"outcome id": "outcome 1", "intention id": "I1"},
        {"outcome id": "outcome 2", "intention id": "I1"},
    ],
}


# ------------------------------------------------------------ formatting

def test_format_dialogue_block():
    block = format_dialogue_block(3, "Hello", "Hi there")
    assert "PAIR 3" in block
    assert "pair 3" in block
    assert "Hello" in block
    assert "Hi there" in block


def test_format_actions_block_spec_keys():
    actions = [{"id": "U(1,1)", "type": "Request", "text": "asks",
                "role": "SHAPER", "evidence_quote": "q"}]
    block = format_actions_block(actions)
    parsed = json.loads(block)
    assert "turn id" in parsed[0]
    assert "action type" in parsed[0]
    assert "evidence quote" in parsed[0]
    # schema-shaped keys should NOT be in the output
    assert "id" not in parsed[0]
    assert "evidence_quote" not in parsed[0]


def test_format_outcomes_list():
    outcomes = [{"id": "outcome 1", "text": "the thing"}]
    block = format_outcomes_list(outcomes)
    parsed = json.loads(block)
    assert parsed[0]["outcome id"] == "outcome 1"
    assert parsed[0]["outcome"] == "the thing"


# ------------------------------------------------------------ sort key

def test_action_sort_key_u_before_a():
    assert action_sort_key("U(1,1)") < action_sort_key("A(1,1)")


def test_action_sort_key_pair_order():
    assert action_sort_key("A(1,5)") < action_sort_key("U(2,1)")


def test_action_sort_key_seq_order():
    assert action_sort_key("U(1,1)") < action_sort_key("U(1,2)")


def test_action_sort_key_malformed():
    with pytest.raises(PipelineError, match="malformed"):
        action_sort_key("X(1,1)")
    with pytest.raises(PipelineError, match="malformed"):
        action_sort_key("1")


# -------------------------------------------------------- Step 1a tests

def test_step_1a_happy(tmp_path):
    state = State()
    config = MockConfig()
    client = MockLLMClient({"1a": PAIR1_STEP1A_RESPONSE})
    new_actions = step_1a(client, config, state, 1, "Can you build me a website?", "Sure")
    assert len(new_actions) == 3
    assert len(state.actions) == 3
    assert state.get_action("U(1,1)")["role"] == "SHAPER"
    assert state.get_action("A(1,1)")["role"] == "EXECUTOR"
    # verify spec→schema key translation happened
    assert "id" in state.actions[0]
    assert "evidence_quote" in state.actions[0]


def test_step_1a_bad_turn_id_format():
    state = State()
    client = MockLLMClient({"1a": {
        "actions": [{"turn id": "user-1", "action type": "Ask",
                     "action text": "x", "role": "SHAPER", "evidence quote": "q"}]
    }})
    with pytest.raises(PipelineError, match="violates U\\(x,y\\)/A\\(x,y\\)"):
        step_1a(client, MockConfig(), state, 1, "hi", "hello")


def test_step_1a_wrong_pair_number():
    state = State()
    client = MockLLMClient({"1a": {
        "actions": [{"turn id": "U(2,1)", "action type": "Ask",
                     "action text": "x", "role": "SHAPER", "evidence quote": "q"}]
    }})
    with pytest.raises(PipelineError, match="claims pair 2.*pair 1"):
        step_1a(client, MockConfig(), state, 1, "hi", "hello")


def test_step_1a_invalid_role():
    state = State()
    client = MockLLMClient({"1a": {
        "actions": [{"turn id": "U(1,1)", "action type": "Ask",
                     "action text": "x", "role": "BOSS", "evidence quote": "q"}]
    }})
    with pytest.raises(PipelineError, match="invalid role"):
        step_1a(client, MockConfig(), state, 1, "hi", "hello")


def test_step_1a_empty_actions():
    state = State()
    client = MockLLMClient({"1a": {"actions": []}})
    with pytest.raises(PipelineError, match="non-empty list"):
        step_1a(client, MockConfig(), state, 1, "hi", "hello")


def test_step_1a_missing_key():
    state = State()
    client = MockLLMClient({"1a": {
        "actions": [{"turn id": "U(1,1)", "action type": "Ask",
                     "action text": "x", "role": "SHAPER"}]  # missing evidence quote
    }})
    with pytest.raises(PipelineError, match="missing key.*evidence quote"):
        step_1a(client, MockConfig(), state, 1, "hi", "hello")


def test_step_1a_no_partial_append_on_error():
    """If validation fails mid-batch, no actions should be appended to state."""
    state = State()
    client = MockLLMClient({"1a": {
        "actions": [
            {"turn id": "U(1,1)", "action type": "Ask",
             "action text": "x", "role": "SHAPER", "evidence quote": "q"},
            {"turn id": "badid", "action type": "Ask",
             "action text": "y", "role": "SHAPER", "evidence quote": "q"},
        ]
    }})
    with pytest.raises(PipelineError):
        step_1a(client, MockConfig(), state, 1, "hi", "hello")
    assert len(state.actions) == 0  # no partial append


# -------------------------------------------------------- Step 1b tests

def _state_with_pair1_actions():
    state = State()
    for a in PAIR1_STEP1A_RESPONSE["actions"]:
        state.add_action({
            "id": a["turn id"], "type": a["action type"],
            "text": a["action text"], "role": a["role"],
            "evidence_quote": a["evidence quote"],
        })
    state.run["dialogue_summary"] = ""
    return state


def test_step_1b_happy():
    state = _state_with_pair1_actions()
    client = MockLLMClient({"1b": PAIR1_STEP1B_RESPONSE})
    outcomes = step_1b(client, MockConfig(), state, 1)
    assert len(outcomes) == 1
    assert outcomes[0]["id"] == "outcome 1"
    assert state.outcomes == outcomes
    assert state.run["dialogue_summary"] == \
        "User and AI are collaborating on building a responsive website."
    assert state.run["action_to_outcome"]["U(1,1)"] == "outcome 1"


def test_step_1b_incomplete_action_to_outcome():
    state = _state_with_pair1_actions()
    bad_response = dict(PAIR1_STEP1B_RESPONSE)
    bad_response["action to outcome"] = {"U(1,1)": "outcome 1"}  # missing U(1,2), A(1,1)
    bad_response["outcomes"] = list(PAIR1_STEP1B_RESPONSE["outcomes"])
    bad_response["dialogue summary"] = "x"
    client = MockLLMClient({"1b": bad_response})
    with pytest.raises(PipelineError, match="action_to_outcome incomplete"):
        step_1b(client, MockConfig(), state, 1)


def test_step_1b_unknown_outcome_in_mapping():
    state = _state_with_pair1_actions()
    bad_response = {
        "dialogue summary": "x",
        "outcomes": list(PAIR1_STEP1B_RESPONSE["outcomes"]),
        "action to outcome": {
            "U(1,1)": "outcome 1",
            "U(1,2)": "outcome 99",  # unknown outcome
            "A(1,1)": "outcome 1",
        },
    }
    client = MockLLMClient({"1b": bad_response})
    with pytest.raises(PipelineError, match="unknown outcome.*outcome 99"):
        step_1b(client, MockConfig(), state, 1)


def test_step_1b_duplicate_outcome_ids():
    state = _state_with_pair1_actions()
    bad_response = {
        "dialogue summary": "x",
        "outcomes": [
            {"outcome id": "outcome 1", "outcome": "first", "turn id": "U(1,1)",
             "parent outcome id": None, "child outcome ids": [], "related outcome ids": []},
            {"outcome id": "outcome 1", "outcome": "dupe", "turn id": "U(1,2)",
             "parent outcome id": None, "child outcome ids": [], "related outcome ids": []},
        ],
        "action to outcome": {
            "U(1,1)": "outcome 1",
            "U(1,2)": "outcome 1",
            "A(1,1)": "outcome 1",
        },
    }
    client = MockLLMClient({"1b": bad_response})
    with pytest.raises(PipelineError, match="duplicate outcome ids"):
        step_1b(client, MockConfig(), state, 1)


def test_step_1b_unknown_parent():
    state = _state_with_pair1_actions()
    bad_response = {
        "dialogue summary": "x",
        "outcomes": [
            {"outcome id": "outcome 1", "outcome": "thing", "turn id": "U(1,1)",
             "parent outcome id": "outcome 99",  # unknown parent
             "child outcome ids": [], "related outcome ids": []},
        ],
        "action to outcome": {
            "U(1,1)": "outcome 1",
            "U(1,2)": "outcome 1",
            "A(1,1)": "outcome 1",
        },
    }
    client = MockLLMClient({"1b": bad_response})
    with pytest.raises(PipelineError, match="unknown parent"):
        step_1b(client, MockConfig(), state, 1)


def test_step_1b_parent_children_bidirectional():
    """Children are rebuilt from parent pointers — verifying bidirectional consistency."""
    state = _state_with_pair1_actions()
    # Response with parent-child relationship
    response = {
        "dialogue summary": "x",
        "outcomes": [
            {"outcome id": "outcome 1", "outcome": "parent thing", "turn id": "U(1,1)",
             "parent outcome id": None, "child outcome ids": [],
             "related outcome ids": []},
            {"outcome id": "outcome 2", "outcome": "child thing", "turn id": "U(1,2)",
             "parent outcome id": "outcome 1", "child outcome ids": [],
             "related outcome ids": []},
        ],
        "action to outcome": {
            "U(1,1)": "outcome 1",
            "U(1,2)": "outcome 2",
            "A(1,1)": "outcome 1",
        },
    }
    client = MockLLMClient({"1b": response})
    outcomes = step_1b(client, MockConfig(), state, 1)
    parent = next(o for o in outcomes if o["id"] == "outcome 1")
    child = next(o for o in outcomes if o["id"] == "outcome 2")
    assert "outcome 2" in parent["children"]
    assert child["parent"] == "outcome 1"


# -------------------------------------------------------- Step 1c tests

def _state_with_pair1_outcomes():
    state = _state_with_pair1_actions()
    state.outcomes = [{
        "id": "outcome 1", "text": "Responsive website",
        "turn_id": "U(1,1)", "parent": None, "children": [], "related": [],
    }]
    state.run["action_to_outcome"] = {"U(1,1)": "outcome 1",
                                       "U(1,2)": "outcome 1",
                                       "A(1,1)": "outcome 1"}
    state.run["dialogue_summary"] = "Building a website."
    return state


def test_step_1c_happy():
    state = _state_with_pair1_outcomes()
    client = MockLLMClient({"1c": PAIR1_STEP1C_RESPONSE})
    intentions = step_1c(client, MockConfig(), state, 1)
    assert len(intentions) == 1
    assert intentions[0]["intention_id"] == "I1"
    assert intentions[0]["outcome_ids"] == ["outcome 1"]
    assert state.run["outcome_to_intention"]["outcome 1"] == "I1"


def test_step_1c_incomplete_mapping():
    state = _state_with_pair1_outcomes()
    # Add a second outcome but don't map it
    state.outcomes.append({
        "id": "outcome 2", "text": "Second thing",
        "turn_id": "U(1,2)", "parent": None, "children": [], "related": [],
    })
    response = {
        "intentions": [{"intention id": "I1", "intention": "Build a website"}],
        "outcome to intention": [
            {"outcome id": "outcome 1", "intention id": "I1"},
            # outcome 2 is missing
        ],
    }
    client = MockLLMClient({"1c": response})
    with pytest.raises(PipelineError, match="outcomes left unmapped.*outcome 2"):
        step_1c(client, MockConfig(), state, 1)


def test_step_1c_duplicate_outcome_mapping():
    state = _state_with_pair1_outcomes()
    response = {
        "intentions": [{"intention id": "I1", "intention": "Build a website"}],
        "outcome to intention": [
            {"outcome id": "outcome 1", "intention id": "I1"},
            {"outcome id": "outcome 1", "intention id": "I1"},  # duplicate
        ],
    }
    client = MockLLMClient({"1c": response})
    with pytest.raises(PipelineError, match="mapped more than once"):
        step_1c(client, MockConfig(), state, 1)


def test_step_1c_unknown_outcome():
    state = _state_with_pair1_outcomes()
    response = {
        "intentions": [{"intention id": "I1", "intention": "Build a website"}],
        "outcome to intention": [
            {"outcome id": "outcome 1", "intention id": "I1"},
            {"outcome id": "outcome 99", "intention id": "I1"},  # unknown
        ],
    }
    client = MockLLMClient({"1c": response})
    with pytest.raises(PipelineError, match="unknown outcome id.*outcome 99"):
        step_1c(client, MockConfig(), state, 1)


def test_step_1c_unknown_intention():
    state = _state_with_pair1_outcomes()
    response = {
        "intentions": [{"intention id": "I1", "intention": "Build a website"}],
        "outcome to intention": [
            {"outcome id": "outcome 1", "intention id": "I99"},  # unknown
        ],
    }
    client = MockLLMClient({"1c": response})
    with pytest.raises(PipelineError, match="unknown intention id.*I99"):
        step_1c(client, MockConfig(), state, 1)


def test_step_1c_duplicate_intention_ids():
    state = _state_with_pair1_outcomes()
    response = {
        "intentions": [
            {"intention id": "I1", "intention": "first"},
            {"intention id": "I1", "intention": "dupe"},  # duplicate
        ],
        "outcome to intention": [
            {"outcome id": "outcome 1", "intention id": "I1"},
        ],
    }
    client = MockLLMClient({"1c": response})
    with pytest.raises(PipelineError, match="duplicate intention ids"):
        step_1c(client, MockConfig(), state, 1)


# ----------------------------------------------- run_level1 integration

def test_run_level1_two_pairs():
    """Happy path across 2 pairs proving accumulation + summary loop."""
    config = MockConfig()
    state = State()

    # Pair 1
    pair1_client = MockLLMClient({
        "1a:pair1": PAIR1_STEP1A_RESPONSE,
        "1b:pair1": PAIR1_STEP1B_RESPONSE,
        "1c:pair1": PAIR1_STEP1C_RESPONSE,
    })
    new_actions_1 = run_level1(
        pair1_client, config, state, 1,
        "Can you build me a website? It needs to be responsive.",
        "Sure, I'll build a responsive website.",
    )
    assert len(new_actions_1) == 3
    assert len(state.actions) == 3
    assert len(state.outcomes) == 1
    assert state.run["dialogue_summary"] == \
        "User and AI are collaborating on building a responsive website."
    assert len(pair1_client.calls) == 3  # exactly 3 LLM calls per pair

    # Pair 2 — accumulates on pair 1
    pair2_client = MockLLMClient({
        "1a:pair2": PAIR2_STEP1A_RESPONSE,
        "1b:pair2": PAIR2_STEP1B_RESPONSE,
        "1c:pair2": PAIR2_STEP1C_RESPONSE,
    })
    new_actions_2 = run_level1(
        pair2_client, config, state, 2,
        "Add dark mode please.",
        "I've added a dark mode toggle.",
    )
    assert len(new_actions_2) == 2
    assert len(state.actions) == 5  # 3 + 2 accumulated

    # Outcome tree re-emitted: should be fully replaced per §4.7
    assert len(state.outcomes) == 2
    assert state.outcomes[0]["id"] == "outcome 1"
    assert state.outcomes[1]["id"] == "outcome 2"
    assert "outcome 2" in state.outcomes[0]["children"]  # bidirectional

    # Summary loop: updated for pair 2
    assert "dark mode" in state.run["dialogue_summary"]

    # action_to_outcome: all 5 actions mapped
    assert len(state.run["action_to_outcome"]) == 5

    # Intentions: both outcomes mapped
    assert state.run["outcome_to_intention"]["outcome 1"] == "I1"
    assert state.run["outcome_to_intention"]["outcome 2"] == "I1"

    # Models used: step 1a = model_fast, steps 1b/1c = model_main
    assert pair2_client.calls[0][1] == "mock-fast"   # 1a
    assert pair2_client.calls[1][1] == "mock-main"   # 1b
    assert pair2_client.calls[2][1] == "mock-main"   # 1c


def test_run_level1_1b_gets_summary_from_prior_pair():
    """The SELF-REFERENCE loop: 1b receives the dialogue_summary from the prior
    pair's 1b call, not an empty string on pair 2."""
    config = MockConfig()
    state = State()

    # Pair 1
    run_level1(
        MockLLMClient({
            "1a:pair1": PAIR1_STEP1A_RESPONSE,
            "1b:pair1": PAIR1_STEP1B_RESPONSE,
            "1c:pair1": PAIR1_STEP1C_RESPONSE,
        }),
        config, state, 1, "hi", "hello",
    )
    assert state.run["dialogue_summary"] != ""

    # Pair 2 — capture the prompt sent to 1b
    pair2_client = MockLLMClient({
        "1a:pair2": PAIR2_STEP1A_RESPONSE,
        "1b:pair2": PAIR2_STEP1B_RESPONSE,
        "1c:pair2": PAIR2_STEP1C_RESPONSE,
    })
    run_level1(pair2_client, config, state, 2, "more", "ok")

    # Find the 1b call's prompt
    step1b_call = [c for c in pair2_client.calls if c[0].startswith("1b")]
    assert len(step1b_call) == 1
    prompt_text = step1b_call[0][2]
    # The prior summary should appear in the prompt
    assert "responsive website" in prompt_text


def test_run_level1_1b_gets_all_actions_accumulated():
    """The ACCUMULATE input: 1b on pair 2 receives actions from both pairs."""
    config = MockConfig()
    state = State()

    # Pair 1
    run_level1(
        MockLLMClient({
            "1a:pair1": PAIR1_STEP1A_RESPONSE,
            "1b:pair1": PAIR1_STEP1B_RESPONSE,
            "1c:pair1": PAIR1_STEP1C_RESPONSE,
        }),
        config, state, 1, "hi", "hello",
    )

    # Pair 2
    pair2_client = MockLLMClient({
        "1a:pair2": PAIR2_STEP1A_RESPONSE,
        "1b:pair2": PAIR2_STEP1B_RESPONSE,
        "1c:pair2": PAIR2_STEP1C_RESPONSE,
    })
    run_level1(pair2_client, config, state, 2, "more", "ok")

    # The 1b prompt should contain pair 1's action ids
    step1b_prompt = [c[2] for c in pair2_client.calls if c[0].startswith("1b")][0]
    assert "U(1,1)" in step1b_prompt
    assert "U(1,2)" in step1b_prompt
    assert "A(1,1)" in step1b_prompt
    # And pair 2's new actions
    assert "U(2,1)" in step1b_prompt
    assert "A(2,1)" in step1b_prompt


def test_run_level1_outcome_tree_replaced_not_merged():
    """§4.7: the full outcome tree is re-emitted each call — STATE's outcome
    list is replaced, not merged. Verified by having pair 2 return different
    outcome text from pair 1."""
    config = MockConfig()
    state = State()

    # Pair 1
    run_level1(
        MockLLMClient({
            "1a:pair1": PAIR1_STEP1A_RESPONSE,
            "1b:pair1": PAIR1_STEP1B_RESPONSE,
            "1c:pair1": PAIR1_STEP1C_RESPONSE,
        }),
        config, state, 1, "hi", "hello",
    )
    assert state.outcomes[0]["text"] == "Responsive website"

    # Pair 2 — outcome 1's text is now different (re-emitted)
    run_level1(
        MockLLMClient({
            "1a:pair2": PAIR2_STEP1A_RESPONSE,
            "1b:pair2": PAIR2_STEP1B_RESPONSE,
            "1c:pair2": PAIR2_STEP1C_RESPONSE,
        }),
        config, state, 2, "more", "ok",
    )
    assert state.outcomes[0]["text"] == "Responsive website with dark mode"


# -------------------------------------------------------- Step 2 formatting

def test_format_prior_requirements_and_slots():
    reqs = [
        {
            "req_id": "req 1", "outcome_id": "outcome 1",
            "text": "must exist", "type": "constraint", "status": "active",
            "creation_action_ids": ["U(1,1)"], "contributing_action_ids": [],
            "implementation_action_ids": [], "revise_action_ids": [],
            "related_to": [], "explicit_or_implicit": "explicit",
            "rationale": "r", "created_at_pair": 1
        },
        {
            "req_id": "req 2", "outcome_id": "outcome 1",
            "text": "should be fast", "type": "preference", "status": "revised",
            "creation_action_ids": ["U(1,2)"], "contributing_action_ids": [],
            "implementation_action_ids": [], "revise_action_ids": [],
            "related_to": [], "explicit_or_implicit": "explicit",
            "rationale": "r", "created_at_pair": 1
        }
    ]
    formatted_reqs = format_prior_requirements(reqs)
    parsed_reqs = json.loads(formatted_reqs)
    assert len(parsed_reqs) == 1  # Only the active one is formatted
    assert parsed_reqs[0]["req id"] == "req 1"
    assert parsed_reqs[0]["fields"]["text"] == "must exist"

    slots = [
        {
            "slot_id": "slot 1", "outcome_id": "outcome 1",
            "text": "maybe fast", "type": "preference", "origin": "AI",
            "status": "open", "creation_action_ids": ["A(1,1)"],
            "contributing_action_ids": [], "resolved_into": None
        },
        {
            "slot_id": "slot 2", "outcome_id": "outcome 1",
            "text": "maybe slow", "type": "preference", "origin": "AI",
            "status": "resolved", "creation_action_ids": ["A(1,2)"],
            "contributing_action_ids": [], "resolved_into": "req 1"
        }
    ]
    formatted_slots = format_prior_slots(slots)
    parsed_slots = json.loads(formatted_slots)
    assert len(parsed_slots) == 1  # Only the open one is formatted
    assert parsed_slots[0]["slot id"] == "slot 1"
    assert parsed_slots[0]["origin"] == "AI"


# -------------------------------------------------------- Step 2 test helpers

def _setup_step2_state():
    state = State()
    state.add_action({"id": "U(1,1)", "type": "Ask", "text": "asks", "role": "SHAPER", "evidence_quote": "q"})
    state.add_action({"id": "A(1,1)", "type": "Draft", "text": "drafts", "role": "EXECUTOR", "evidence_quote": "q"})
    state.add_action({"id": "U(1,2)", "type": "Refine", "text": "refines", "role": "SHAPER", "evidence_quote": "q"})
    state.outcomes = [{
        "id": "outcome 1", "text": "Responsive website",
        "turn_id": "U(1,1)", "parent": None, "children": [], "related": [],
    }]
    state.run["action_to_outcome"] = {
        "U(1,1)": "outcome 1",
        "A(1,1)": "outcome 1",
        "U(1,2)": "outcome 1",
    }
    return state


# -------------------------------------------------------- Step 2 tests

def test_step_2_happy_path(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    config = MockConfig(model_step2="mock-step2")
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    response = {
        "requirement ops": [{
            "op": "create",
            "req id": "req 1",
            "bound outcome id": "outcome 1",
            "fields": {"text": "site must be mobile-friendly", "type": "constraint"},
            "creation action ids": ["U(1,1)"],
            "contributing action ids": ["U(1,2)"],
            "explicit or implicit": "explicit",
            "rationale": "explicitly requested"
        }],
        "open_slot ops": [{
            "op": "open_slot",
            "slot id": "slot 1",
            "bound outcome id": "outcome 1",
            "fields": {"text": "what styling library to use", "type": "preference"},
            "origin": "AI",
            "creation action ids": ["A(1,1)"],
            "contributing action ids": [],
            "explicit or implicit": "explicit",
            "rationale": "AI asked which framework"
        }]
    }

    client = MockLLMClient({"2:outcome 1": response})
    
    new_reqs = step_2(client, config, state, ledger_writer, 1, "outcome 1")
    
    # Verify new requirement in state
    assert len(new_reqs) == 1
    assert state.requirements[0]["req_id"] == "req 1"
    assert state.requirements[0]["status"] == "active"
    assert state.requirements[0]["created_at_pair"] == 1
    
    # Verify new slot in state
    assert len(state.slots) == 1
    assert state.slots[0]["slot_id"] == "slot 1"
    assert state.slots[0]["status"] == "open"
    assert state.run["slot_opened_at_pair"]["outcome 1||slot 1"] == 1

    # Verify operations log
    ops = state.operations_log
    assert len(ops) == 2
    assert ops[0]["op"] == "create"
    assert ops[0]["target_id"] == "req 1"
    assert ops[1]["op"] == "open_slot"
    assert ops[1]["target_id"] == "slot 1"

    # Verify ledger row
    rows = ledger_writer.rows
    assert len(rows) == 1
    assert rows[0]["req_id"] == "req 1"
    assert rows[0]["score"] == 5.0
    assert rows[0]["kind"] == "creation"
    assert rows[0]["speaker"] == "U"
    assert rows[0]["role"] == "SHAPER"


def test_step_2_revise_op(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    # Add pre-existing requirement
    state.requirements.append({
        "outcome_id": "outcome 1", "req_id": "req 1",
        "text": "original text", "type": "constraint", "status": "active",
        "creation_action_ids": ["U(1,1)"], "contributing_action_ids": [],
        "implementation_action_ids": [], "revise_action_ids": [],
        "related_to": [], "explicit_or_implicit": "explicit",
        "rationale": "r", "created_at_pair": 1
    })
    
    config = MockConfig()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    response = {
        "requirement ops": [{
            "op": "revise",
            "req id": "req 2",
            "bound outcome id": "outcome 1",
            "fields": {"text": "revised text", "type": "constraint"},
            "creation action ids": ["U(1,2)"],
            "contributing action ids": [],
            "related to": ["req 1"],
            "explicit or implicit": "explicit",
            "rationale": "updated"
        }]
    }

    client = MockLLMClient({"2:outcome 1": response})
    step_2(client, config, state, ledger_writer, 2, "outcome 1")

    # req 1 should be revised
    req1 = state.find_requirement("outcome 1", "req 1")
    assert req1["status"] == "revised"

    # req 2 should be active
    req2 = state.find_requirement("outcome 1", "req 2")
    assert req2["status"] == "active"
    assert req2["related_to"] == ["req 1"]

    # check revise operation in log
    assert any(o["op"] == "revise" and o["target_id"] == "req 1" for o in state.operations_log)


def test_step_2_delete_op(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    state.requirements.append({
        "outcome_id": "outcome 1", "req_id": "req 1",
        "text": "original text", "type": "constraint", "status": "active",
        "creation_action_ids": ["U(1,1)"], "contributing_action_ids": [],
        "implementation_action_ids": [], "revise_action_ids": [],
        "related_to": [], "explicit_or_implicit": "explicit",
        "rationale": "r", "created_at_pair": 1
    })
    
    config = MockConfig()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    response = {
        "requirement ops": [{
            "op": "delete",
            "req id": "req 1",
            "bound outcome id": "outcome 1"
        }]
    }

    client = MockLLMClient({"2:outcome 1": response})
    step_2(client, config, state, ledger_writer, 2, "outcome 1")

    # req 1 should be deleted
    req1 = state.find_requirement("outcome 1", "req 1")
    assert req1["status"] == "deleted"
    assert any(o["op"] == "delete" and o["target_id"] == "req 1" for o in state.operations_log)


def test_step_2_resolve_op(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    state.slots.append({
        "slot_id": "slot 1", "outcome_id": "outcome 1",
        "text": "maybe fast", "type": "preference", "origin": "AI",
        "status": "open", "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [], "resolved_into": None
    })
    
    config = MockConfig()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    response = {
        "requirement ops": [{
            "op": "create",
            "req id": "req 1",
            "bound outcome id": "outcome 1",
            "fields": {"text": "resolved requirement text", "type": "preference"},
            "creation action ids": ["U(1,2)"],
            "contributing action ids": [],
            "related to": ["slot 1"],
            "explicit or implicit": "explicit",
            "rationale": "resolved slot 1"
        }],
        "open_slot ops": [{
            "op": "resolve",
            "slot id": "slot 1",
            "bound outcome id": "outcome 1"
        }]
    }

    client = MockLLMClient({"2:outcome 1": response})
    step_2(client, config, state, ledger_writer, 2, "outcome 1")

    # slot 1 should be resolved into req 1
    slot = state.find_slot("outcome 1", "slot 1")
    assert slot["status"] == "resolved"
    assert slot["resolved_into"] == "req 1"
    assert any(o["op"] == "resolve" and o["target_id"] == "slot 1" for o in state.operations_log)


def test_step_2_abandon_op(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    state.slots.append({
        "slot_id": "slot 1", "outcome_id": "outcome 1",
        "text": "maybe fast", "type": "preference", "origin": "AI",
        "status": "open", "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [], "resolved_into": None
    })
    
    config = MockConfig()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    response = {
        "open_slot ops": [{
            "op": "abandon",
            "slot id": "slot 1",
            "bound outcome id": "outcome 1"
        }]
    }

    client = MockLLMClient({"2:outcome 1": response})
    step_2(client, config, state, ledger_writer, 2, "outcome 1")

    # slot 1 should be abandoned
    slot = state.find_slot("outcome 1", "slot 1")
    assert slot["status"] == "abandoned"
    assert any(o["op"] == "abandon" and o["target_id"] == "slot 1" for o in state.operations_log)


def test_run_level2_abandonment_sweep(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    state.slots.append({
        "slot_id": "slot 1", "outcome_id": "outcome 1",
        "text": "maybe fast", "type": "preference", "origin": "AI",
        "status": "open", "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [], "resolved_into": None
    })
    # Slot was opened at pair 1
    state.run["slot_opened_at_pair"]["outcome 1||slot 1"] = 1
    
    config = MockConfig()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    # Pair 2 - not abandoned
    run_level2(MockLLMClient({}), config, state, ledger_writer, 2, [])
    assert state.find_slot("outcome 1", "slot 1")["status"] == "open"

    # Pair 3 - not abandoned
    run_level2(MockLLMClient({}), config, state, ledger_writer, 3, [])
    assert state.find_slot("outcome 1", "slot 1")["status"] == "open"

    # Pair 4 - 3 consecutive pairs passed (4 - 1 = 3) -> ABANDONED
    run_level2(MockLLMClient({}), config, state, ledger_writer, 4, [])
    assert state.find_slot("outcome 1", "slot 1")["status"] == "abandoned"
    assert any(o["op"] == "abandon" and o["target_id"] == "slot 1" for o in state.operations_log)


def test_step_2_validation_failures(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step2_state()
    config = MockConfig()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")

    # Case 1: Bound outcome ID mismatch
    client1 = MockLLMClient({"2:outcome 1": {
        "requirement ops": [{
            "op": "create", "req id": "req 1",
            "bound outcome id": "outcome 99",  # mismatch
            "fields": {"text": "t", "type": "constraint"},
            "creation action ids": ["U(1,1)"], "contributing action ids": [],
            "explicit or implicit": "explicit", "rationale": "r"
        }]
    }})
    with pytest.raises(PipelineError, match="bound outcome id.*match"):
        step_2(client1, config, state, ledger_writer, 1, "outcome 1")

    # Case 2: Invalid requirement type
    client2 = MockLLMClient({"2:outcome 1": {
        "requirement ops": [{
            "op": "create", "req id": "req 1", "bound outcome id": "outcome 1",
            "fields": {"text": "t", "type": "BOGUS"},  # invalid type
            "creation action ids": ["U(1,1)"], "contributing action ids": [],
            "explicit or implicit": "explicit", "rationale": "r"
        }]
    }})
    with pytest.raises(PipelineError, match="invalid requirement type"):
        step_2(client2, config, state, ledger_writer, 1, "outcome 1")

    # Case 3: Unknown action ID
    client3 = MockLLMClient({"2:outcome 1": {
        "requirement ops": [{
            "op": "create", "req id": "req 1", "bound outcome id": "outcome 1",
            "fields": {"text": "t", "type": "constraint"},
            "creation action ids": ["U(9,9)"],  # unknown action
            "contributing action ids": [],
            "explicit or implicit": "explicit", "rationale": "r"
        }]
    }})
    with pytest.raises(PipelineError, match="unknown creation action id"):
        step_2(client3, config, state, ledger_writer, 1, "outcome 1")

    # Case 4: Action ID bound to a different outcome
    state.add_action({"id": "U(1,3)", "type": "Ask", "text": "asks", "role": "SHAPER", "evidence_quote": "q"})
    state.run["action_to_outcome"]["U(1,3)"] = "outcome 99"  # different outcome
    client4 = MockLLMClient({"2:outcome 1": {
        "requirement ops": [{
            "op": "create", "req id": "req 1", "bound outcome id": "outcome 1",
            "fields": {"text": "t", "type": "constraint"},
            "creation action ids": ["U(1,3)"],  # bound to outcome 99
            "contributing action ids": [],
            "explicit or implicit": "explicit", "rationale": "r"
        }]
    }})
    with pytest.raises(PipelineError, match="not bound to outcome"):
        step_2(client4, config, state, ledger_writer, 1, "outcome 1")

    # Case 5: Disjointness violation (same action in both active req and open slot)
    client5 = MockLLMClient({"2:outcome 1": {
        "requirement ops": [{
            "op": "create", "req id": "req 1", "bound outcome id": "outcome 1",
            "fields": {"text": "t", "type": "constraint"},
            "creation action ids": ["U(1,1)"], "contributing action ids": [],
            "explicit or implicit": "explicit", "rationale": "r"
        }],
        "open_slot ops": [{
            "op": "open_slot", "slot id": "slot 1", "bound outcome id": "outcome 1",
            "fields": {"text": "t", "type": "constraint"}, "origin": "AI",
            "creation action ids": ["U(1,1)"],  # same action
            "contributing action ids": [],
            "explicit or implicit": "explicit", "rationale": "r"
        }]
    }})
    with pytest.raises(PipelineError, match="action/slot action overlap"):
        step_2(client5, config, state, ledger_writer, 1, "outcome 1")


# -------------------------------------------------------- Step 3 formatting

def test_format_action_list_for_step3():
    assert format_action_list_for_step3([]) == ""
    
    actions = [
        {"id": "U(1,1)", "type": "Ask", "role": "SHAPER", "text": "asks", "evidence_quote": "why"}
    ]
    formatted = format_action_list_for_step3(actions)
    assert formatted == 'U(1,1) | Ask | SHAPER | asks | evidence: "why"'


# -------------------------------------------------------- Step 3 tests

def _setup_step3_state():
    state = State()
    state.add_action({"id": "U(1,1)", "type": "Ask", "text": "asks for feature", "role": "SHAPER", "evidence_quote": "need X"})
    state.add_action({"id": "A(1,1)", "type": "Draft", "text": "drafts X", "role": "EXECUTOR", "evidence_quote": "here is X"})
    state.add_action({"id": "U(2,1)", "type": "Ask", "text": "asks for Y", "role": "SHAPER", "evidence_quote": "need Y"})
    state.add_action({"id": "A(2,1)", "type": "Draft", "text": "drafts Y", "role": "EXECUTOR", "evidence_quote": "here is Y"})
    
    state.outcomes = [{
        "id": "outcome 1", "text": "Responsive website",
        "turn_id": "U(1,1)", "parent": None, "children": [], "related": [],
    }]
    
    state.run["action_to_outcome"] = {
        "U(1,1)": "outcome 1",
        "A(1,1)": "outcome 1",
        "U(2,1)": "outcome 1",
        "A(2,1)": "outcome 1",
    }
    return state


def test_step_3_trigger_a_directly_created(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step3_state()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")
    config = MockConfig(step3_batch_size=3)

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "X must be fast",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "explicit_or_implicit": "explicit",
        "rationale": "r",
        "created_at_pair": 1
    }
    state.requirements.append(req)

    # Preceding action is U(1,1)
    # Subsequent action is U(2,1), A(2,1)
    preceding_response = {
        "preceding labels": [{
            "index": 0, "action id": "U(1,1)",
            "relationship type": "IMPLICIT CONNECTION", "relationship score": 2,
            "explanation": "asks for feature leads to speed req", "contribution role": "SHAPER"
        }]
    }

    subsequent_response = {
        "subsequent labels": [
            {
                "index": 0, "action id": "U(2,1)",
                "relationship type": "NO CONNECTION", "relationship score": None,
                "explanation": "unrelated", "contribution role": "SHAPER"
            },
            {
                "index": 1, "action id": "A(2,1)",
                "relationship type": "IMPLEMENTS", "relationship score": 5,
                "explanation": "drafts Y implements req 1", "contribution role": "EXECUTOR"
            }
        ]
    }

    client = MockLLMClient({
        "3:req 1:preceding:batch0": preceding_response,
        "3:req 1:subsequent:batch0": subsequent_response
    })

    step_3_for_req(client, config, state, ledger_writer, 1, req, is_trigger_b=False)

    # Check preceding log and ledger rows
    rows = ledger_writer.rows
    assert len(rows) == 2  # U(1,1) implicit (2), A(2,1) implements (5). U(2,1) is NO CONNECTION -> no row.
    
    assert rows[0]["action_id"] == "U(1,1)"
    assert rows[0]["score"] == 2.0
    assert rows[0]["kind"] == "labeled"

    assert rows[1]["action_id"] == "A(2,1)"
    assert rows[1]["score"] == 5.0
    assert rows[1]["kind"] == "labeled"

    # Check that labeled list contains creation ID and labeled IDs
    labeled_list = state.run["labeled_action_ids"]["outcome 1||req 1"]
    assert "A(1,1)" in labeled_list  # creation
    assert "U(1,1)" in labeled_list  # preceding
    assert "U(2,1)" in labeled_list  # subsequent (even though NO CONNECTION)
    assert "A(2,1)" in labeled_list  # subsequent


def test_step_3_trigger_a_resolved_from_slot(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step3_state()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")
    config = MockConfig(step3_batch_size=3)

    state.slots.append({
        "slot_id": "slot 1", "outcome_id": "outcome 1",
        "text": "maybe fast", "type": "preference", "origin": "AI",
        "status": "resolved", "creation_action_ids": ["U(1,1)"],
        "contributing_action_ids": [], "resolved_into": "req 1"
    })

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "X must be fast",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": ["slot 1"],
        "explicit_or_implicit": "explicit",
        "rationale": "r",
        "created_at_pair": 1
    }
    state.requirements.append(req)

    slot_origin_response = {
        "slot origin labels": [{
            "index": 0, "action id": "U(1,1)",
            "relationship type": "IMPLICIT CONNECTION", "relationship score": 3,
            "explanation": "slot origin", "contribution role": "SHAPER"
        }]
    }

    # Since U(1,1) is slot origin, it's excluded from preceding block.
    # Therefore preceding block has 0 actions, so no preceding batch is executed.
    client = MockLLMClient({
        "3:req 1:slot_origin:batch0": slot_origin_response,
        "3:req 1:subsequent:batch0": {"subsequent labels": [
            {"index": 0, "action id": "U(2,1)", "relationship type": "NO CONNECTION", "relationship score": None, "explanation": "x", "contribution role": "SHAPER"},
            {"index": 1, "action id": "A(2,1)", "relationship type": "NO CONNECTION", "relationship score": None, "explanation": "x", "contribution role": "AI"}
        ]}
    })


    step_3_for_req(client, config, state, ledger_writer, 1, req, is_trigger_b=False)

    rows = ledger_writer.rows
    assert len(rows) == 1
    assert rows[0]["action_id"] == "U(1,1)"
    assert rows[0]["score"] == 3.0
    assert rows[0]["kind"] == "slot-origin"


def test_step_3_trigger_b_incremental(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step3_state()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")
    config = MockConfig(step3_batch_size=3)

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "X must be fast",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "explicit_or_implicit": "explicit",
        "rationale": "r",
        "created_at_pair": 1
    }
    state.requirements.append(req)
    
    # Pre-populate labeled list for Trigger B
    state.run["labeled_action_ids"]["outcome 1||req 1"] = ["A(1,1)", "U(1,1)"]

    # Current pair is 2. New actions are U(2,1) and A(2,1).
    response = {
        "subsequent labels": [
            {
                "index": 0, "action id": "U(2,1)",
                "relationship type": "IMPLEMENTS", "relationship score": 4,
                "explanation": "implements", "contribution role": "SHAPER"
            },
            {
                "index": 1, "action id": "A(2,1)",
                "relationship type": "REVISES", "relationship score": 5,
                "explanation": "revises", "contribution role": "AI"
            }
        ]
    }

    client = MockLLMClient({
        "3:req 1:subsequent:batch0": response
    })

    step_3_for_req(client, config, state, ledger_writer, 2, req, is_trigger_b=True)

    rows = ledger_writer.rows
    assert len(rows) == 2
    assert rows[0]["action_id"] == "U(2,1)"
    assert rows[0]["kind"] == "labeled"
    assert rows[1]["action_id"] == "A(2,1)"
    assert rows[1]["kind"] == "labeled"

    # Verify A(2,1) is appended to revise_action_ids
    assert "A(2,1)" in req["revise_action_ids"]
    assert "U(2,1)" not in req["revise_action_ids"]


def test_step_3_batching(tmp_path):
    from engine.artifacts import LedgerWriter
    state = _setup_step3_state()
    ledger_writer = LedgerWriter(tmp_path / "ledger.jsonl")
    # Batch size = 2.
    # Preceding actions has 1: U(1,1)
    # Subsequent actions has 3: U(1,1) is preceding, but A(1,1), U(2,1), A(2,1) are subsequent.
    # Wait, creation is A(1,1), so subsequent is U(2,1) and A(2,1). Length of subsequent is 2.
    # Let's add more subsequent actions to force multiple batches:
    state.add_action({"id": "U(2,2)", "type": "Ask", "text": "asks again", "role": "SHAPER", "evidence_quote": "q"})
    state.run["action_to_outcome"]["U(2,2)"] = "outcome 1"
    
    # Now subsequent actions has: U(2,1), A(2,1), U(2,2) (length 3).
    # Since batch size = 2, it should split subsequent actions into 2 batches.
    config = MockConfig(step3_batch_size=2)

    req = {
        "outcome_id": "outcome 1",
        "req_id": "req 1",
        "text": "X must be fast",
        "type": "constraint",
        "status": "active",
        "creation_action_ids": ["A(1,1)"],
        "contributing_action_ids": [],
        "implementation_action_ids": [],
        "revise_action_ids": [],
        "related_to": [],
        "explicit_or_implicit": "explicit",
        "rationale": "r",
        "created_at_pair": 1
    }
    state.requirements.append(req)

    client = MockLLMClient({
        "3:req 1:preceding:batch0": {"preceding labels": [{"index": 0, "action id": "U(1,1)", "relationship type": "IMPLICIT CONNECTION", "relationship score": 2, "explanation": "x", "contribution role": "SHAPER"}]},
        "3:req 1:subsequent:batch0": {"subsequent labels": [
            {"index": 0, "action id": "U(2,1)", "relationship type": "NO CONNECTION", "relationship score": None, "explanation": "x", "contribution role": "SHAPER"},
            {"index": 1, "action id": "A(2,1)", "relationship type": "NO CONNECTION", "relationship score": None, "explanation": "x", "contribution role": "AI"}
        ]},
        "3:req 1:subsequent:batch1": {"subsequent labels": [
            {"index": 0, "action id": "U(2,2)", "relationship type": "NO CONNECTION", "relationship score": None, "explanation": "x", "contribution role": "SHAPER"}
        ]}
    })

    step_3_for_req(client, config, state, ledger_writer, 2, req, is_trigger_b=False)

    # Verify that the client was called for batch0 and batch1 of subsequent
    assert any(c[0] == "3:req 1:subsequent:batch0" for c in client.calls)
    assert any(c[0] == "3:req 1:subsequent:batch1" for c in client.calls)

