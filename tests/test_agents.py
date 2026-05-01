from statlean_agent.agents import AGENT_REGISTRY, get_agent, writable_agents


def test_registry_has_more_than_ten_agents() -> None:
    assert len(AGENT_REGISTRY) >= 12


def test_agent_keys_are_unique() -> None:
    keys = [agent.key for agent in AGENT_REGISTRY]
    assert len(keys) == len(set(keys))


def test_get_agent() -> None:
    assert get_agent("formalization").name == "Formalization Agent"


def test_writable_agents_have_owned_paths() -> None:
    for agent in writable_agents():
        assert agent.owns

