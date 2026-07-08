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
