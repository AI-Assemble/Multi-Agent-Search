#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from .batch import _log_status, _run_game_batch, _status_details
from .colors import GREEN, _paint
from .fs import _preview_pythonpath
from .menu import _run_interactive_setup


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive launcher for Pacman")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--agent")
    parser.add_argument("--evalFn")
    parser.add_argument("--layout")
    parser.add_argument("--ghosts", type=int)
    parser.add_argument("--num-games", type=int)
    parser.add_argument("--parallel", type=int)
    parser.add_argument("--", dest="dashdash", nargs="*")
    args, extra = parser.parse_known_args()

    root = Path(__file__).resolve().parents[2]
    app_root = root / "src" / "core"

    provided_any = any(
        v is not None for v in [args.agent, args.evalFn, args.layout, args.ghosts, args.num_games, args.parallel]
    ) or bool(extra)
    parallel = args.parallel if args.parallel is not None else 1
    if parallel < 1:
        parallel = 1

    if provided_any:
        selected_agent = args.agent or "ReflexAgent"
        selected_layout = args.layout or "mediumClassic"
        selected_ghosts = args.ghosts if args.ghosts is not None else 2
        selected_games = args.num_games if args.num_games is not None else 1
        search_agents = {"MinimaxAgent", "AlphaBetaAgent", "ExpectimaxAgent"}
        selected_evalFn = args.evalFn or "score"
        extra_with_eval = extra
        if selected_agent in search_agents:
            agent_args = f"evalFn={selected_evalFn}"
            extra_with_eval = [*extra, "-a", agent_args]
        else:
            selected_evalFn = "unavailable"  # Mark as unavailable for non-search agents
        preview_pythonpath = _preview_pythonpath(app_root)
        _log_status(
            "Launcher Status",
            _status_details(
                root=root,
                app_root=app_root,
                selected_agent=selected_agent,
                selected_evalFn=selected_evalFn,
                selected_layout=selected_layout,
                selected_ghosts=selected_ghosts,
                selected_games=selected_games,
                extra=extra_with_eval,
                provided_any=provided_any,
                python_bin=args.python_bin,
                pythonpath=preview_pythonpath,
                parallel=parallel,
            ),
        )
        print(_paint("Running now...", GREEN))
        return _run_game_batch(
            root=root,
            app_root=app_root,
            python_bin=args.python_bin,
            selected_agent=selected_agent,
            selected_evalFn=selected_evalFn,
            selected_layout=selected_layout,
            selected_ghosts=selected_ghosts,
            total_games=selected_games,
            parallel=parallel,
            extra=extra_with_eval,
            provided_any=provided_any,
            wait_for_q_to_return=False,
        )

    prev_state = None
    while True:
        selected_agent, selected_evalFn, selected_layout, selected_ghosts, selected_games, selected_parallel = (
            _run_interactive_setup(root, parallel, initial_state=prev_state)
        )
        parallel = selected_parallel
        search_agents = {"MinimaxAgent", "AlphaBetaAgent", "ExpectimaxAgent"}
        extra_with_eval = extra
        if selected_agent in search_agents:
            agent_args = f"evalFn={selected_evalFn}"
            extra_with_eval = [*extra, "-a", agent_args]
        else:
            selected_evalFn = "unavailable"  # Mark as unavailable for non-search agents
        preview_pythonpath = _preview_pythonpath(app_root)
        _log_status(
            "Launcher Status",
            _status_details(
                root=root,
                app_root=app_root,
                selected_agent=selected_agent,
                selected_evalFn=selected_evalFn,
                selected_layout=selected_layout,
                selected_ghosts=selected_ghosts,
                selected_games=selected_games,
                extra=extra_with_eval,
                provided_any=provided_any,
                python_bin=args.python_bin,
                pythonpath=preview_pythonpath,
                parallel=selected_parallel,
            ),
        )
        print(_paint("Running now...", GREEN))
        _run_game_batch(
            root=root,
            app_root=app_root,
            python_bin=args.python_bin,
            selected_agent=selected_agent,
            selected_evalFn=selected_evalFn,
            selected_layout=selected_layout,
            selected_ghosts=selected_ghosts,
            total_games=selected_games,
            parallel=selected_parallel,
            extra=extra_with_eval,
            provided_any=provided_any,
            wait_for_q_to_return=True,
        )
        # Remember last selections for the next interactive run
        prev_state = {
            "agent": selected_agent,
            "evalFn": selected_evalFn if selected_evalFn != "unavailable" else None,
            "layout": selected_layout,
            "ghosts": selected_ghosts,
            "games": selected_games,
            "parallel": selected_parallel,
        }


if __name__ == "__main__":
    raise SystemExit(main())
