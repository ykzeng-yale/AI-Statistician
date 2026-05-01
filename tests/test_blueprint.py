from pathlib import Path

from statlean_agent.blueprint import blueprint_status, load_blueprint, render_blueprint_status, validate_blueprint


def test_real_blueprint_selects_next_unfinished_milestone() -> None:
    blueprint = load_blueprint(Path("config/statlean_blueprint.json"))

    assert validate_blueprint(blueprint) == ()
    status = blueprint_status(blueprint)

    assert status["valid"] is True
    assert status["current_phase"]["id"] == "P8"
    assert status["current_milestone"]["id"] == "P8.M1"
    assert "continue" in render_blueprint_status(blueprint)
    assert any("held-out" in action.lower() for action in status["next_actions"])


def test_blueprint_validation_rejects_duplicate_ids_and_bad_status() -> None:
    blueprint = {
        "id": "bad",
        "target": "bad target",
        "phases": [
            {
                "id": "P0",
                "status": "done",
                "milestones": [{"id": "P0.M1", "status": "done"}],
            },
            {
                "id": "P0",
                "status": "unknown",
                "milestones": [{"id": "P0.M1", "status": "pending"}],
            },
        ],
    }

    errors = validate_blueprint(blueprint)

    assert "duplicate phase id `P0`" in errors
    assert "phase `P0` has invalid status `unknown`" in errors
    assert "duplicate milestone id `P0.M1`" in errors
