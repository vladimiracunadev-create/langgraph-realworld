from src.graph import build_shortlist, load_inputs, schedule_interviews, score_one


def test_flow_produces_shortlist_and_schedule():
    state = load_inputs({"events": []})

    # Score all candidates one by one
    while True:
        out = score_one(state)
        if not out:
            break
        state.update(out)
        # accumulate scored list
        if "scored" in out:
            state["scored"] = (state.get("scored") or []) + out["scored"]
        if "events" in out:
            state["events"] = (state.get("events") or []) + out["events"]

    out_short = build_shortlist(state)
    state.update(out_short)

    assert "shortlist" in state
    assert isinstance(state["shortlist"], list)

    out_sched = schedule_interviews(state)
    state.update(out_sched)

    assert state.get("done") is True
    assert isinstance(state.get("scheduled"), list)


def test_shortlist_respects_min_score_top_n():
    state = load_inputs({"events": []})

    # Inject minimal scored data
    state["job"]["min_score"] = 60
    state["job"]["top_n"] = 2
    state["scored"] = [
        {"candidate_id": "a", "score": 95},
        {"candidate_id": "b", "score": 80},
        {"candidate_id": "c", "score": 50},
    ]

    out = build_shortlist(state)
    assert len(out["shortlist"]) == 2
    assert out["shortlist"][0]["candidate_id"] == "a"
