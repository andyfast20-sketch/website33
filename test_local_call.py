"""Local integration harness for the telephone agent."""
from __future__ import annotations

import asyncio

from agent.app import AgentApp


def main():  # pragma: no cover - manual integration
    app = AgentApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()
