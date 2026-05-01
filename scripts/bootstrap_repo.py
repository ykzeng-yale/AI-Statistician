"""Bootstrap helper for local development."""

from statlean_agent.agents import AGENT_REGISTRY


def main() -> None:
    print(f"registered_agents={len(AGENT_REGISTRY)}")
    for agent in AGENT_REGISTRY:
        print(f"- {agent.key}: {agent.name}")


if __name__ == "__main__":
    main()

