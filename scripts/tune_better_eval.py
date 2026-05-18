from __future__ import annotations

import argparse
import csv
import contextlib
import io
import json
import os
import random
import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

for extra_path in (ROOT / ".vendor", ROOT / "src"):
    extra_path_str = str(extra_path)
    if extra_path.exists() and extra_path_str not in sys.path:
        sys.path.insert(0, extra_path_str)

try:
    import optuna
except ImportError as exc:
    raise SystemExit(
        "Optuna is not available. Install it into .vendor first, "
        "for example: python -m pip install 'optuna>=4,<5' -t .vendor"
    ) from exc

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from core.agents import multiAgents
from core.controller import pacman

USER_BASELINE_WEIGHTS = {
    "food_closeness_reward": 10.0,
    "remaining_food_penalty": 4.0,
    "scared_ghost_reward": 200.0,
    "dangerous_ghost_collision_penalty": 500.0,
    "dangerous_ghost_distance_penalty": 2.0,
    "remaining_capsule_penalty": 20.0
}


def parse_seed_list(value: str) -> list[int]:
    seeds = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        seeds.append(int(part))
    if not seeds:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return seeds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tune betterEvaluationFunction weights with Optuna."
    )
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--layout", default="smallClassic")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--ghosts", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--seeds",
        type=parse_seed_list,
        default=parse_seed_list("0,1,2,3,4,5,6,7,8,9"),
    )
    parser.add_argument(
        "--validation-seeds",
        type=parse_seed_list,
        default=parse_seed_list("0,1,2,3,4,5,6,7,8,9"),
    )
    parser.add_argument("--study-name", default="better-eval")
    parser.add_argument(
        "--storage",
        default="",
    )
    parser.add_argument(
        "--result-json",
        default=str(ROOT / "artifacts" / "optuna" / "better_eval_best.json"),
    )
    parser.add_argument(
        "--trials-csv",
        default=str(ROOT / "artifacts" / "optuna" / "better_eval_trials.csv"),
    )
    parser.add_argument(
        "--trials-json",
        default=str(ROOT / "artifacts" / "optuna" / "better_eval_trials.json"),
    )
    parser.add_argument(
        "--games-csv",
        default=str(ROOT / "artifacts" / "optuna" / "better_eval_games.csv"),
    )
    parser.add_argument(
        "--plots-dir",
        default=str(ROOT / "artifacts" / "optuna" / "plots"),
    )
    parser.add_argument("--sampler-seed", type=int, default=20260513)
    return parser


def build_game_argv(args: argparse.Namespace) -> list[str]:
    agent_args = f"evalFn=better,depth={args.depth}"
    return [
        "-p", "ExpectimaxAgent",
        "-a", agent_args,
        "-l", args.layout,
        "-g", "RandomGhost",
        "-k", str(args.ghosts),
        "-q",
        "-n", "1",
        "--timeout", str(args.timeout),
    ]


def run_single_game(game_argv: list[str], seed: int) -> dict[str, object]:
    random.seed(seed)
    run_args = pacman.readCommand(game_argv)
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        games = pacman.runGames(**run_args)

    game = games[0]
    final_state = game.state
    return {
        "seed": seed,
        "score": float(final_state.getScore()),
        "win": bool(final_state.isWin()),
        "move_count": len(game.moveHistory),
        "remaining_food": len(final_state.getFood().asList()),
        "remaining_capsules": len(final_state.getCapsules()),
    }


def evaluate_weights(
    weights: dict[str, float],
    args: argparse.Namespace,
    seeds: list[int],
) -> dict[str, object]:
    multiAgents.set_better_eval_weights(weights)
    game_argv = build_game_argv(args)

    scores: list[float] = []
    game_results: list[dict[str, object]] = []
    wins = 0

    for step, seed in enumerate(seeds, start=1):
        result = run_single_game(game_argv, seed)
        score = float(result["score"])
        win = bool(result["win"])
        scores.append(score)
        wins += int(win)
        game_results.append(result)

    mean_score = sum(scores) / len(scores)
    metrics = {
        "mean_score": mean_score,
        "win_rate": wins / len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
        "scores": scores,
        "played_seeds": [item["seed"] for item in game_results],
        "completed_games": len(game_results),
        "game_results": game_results,
    }

    return metrics


def suggest_weights(trial: optuna.trial.Trial) -> dict[str, float]:
    return {
        "food_closeness_reward": trial.suggest_float("food_closeness_reward", 1.0, 40.0),
        "remaining_food_penalty": trial.suggest_float("remaining_food_penalty", 0.5, 12.0),
        "scared_ghost_reward": trial.suggest_float("scared_ghost_reward", 100.0, 700.0),
        "dangerous_ghost_collision_penalty": trial.suggest_float(
            "dangerous_ghost_collision_penalty", 100.0, 1200.0
        ),
        "dangerous_ghost_distance_penalty": trial.suggest_float(
            "dangerous_ghost_distance_penalty", 0.1, 20.0, log=True
        ),
        "remaining_capsule_penalty": trial.suggest_float(
            "remaining_capsule_penalty", 0.0, 60.0
        )
    }


def ensure_parent(path_str: str) -> None:
    if not path_str:
        return

    if path_str.startswith("sqlite:///"):
        db_path = Path(path_str.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return

    Path(path_str).parent.mkdir(parents=True, exist_ok=True)


def collect_trial_rows(study: optuna.study.Study) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for trial in study.trials:
        row: dict[str, object] = {
            "trial": trial.number,
            "state": str(trial.state),
            "objective_value": "" if trial.value is None else float(trial.value),
            "mean_score": trial.user_attrs.get("mean_score", ""),
            "win_rate": trial.user_attrs.get("win_rate", ""),
            "min_score": trial.user_attrs.get("min_score", ""),
            "max_score": trial.user_attrs.get("max_score", ""),
            "played_seeds": json.dumps(trial.user_attrs.get("played_seeds", [])),
            "game_results": json.dumps(trial.user_attrs.get("game_results", [])),
        }
        for name in multiAgents.BETTER_EVAL_DEFAULT_WEIGHTS:
            row[name] = trial.params.get(name, "")
        rows.append(row)

    return rows


def write_trials_csv(rows: list[dict[str, object]], csv_path: str) -> None:
    ensure_parent(csv_path)
    fieldnames = [
        "trial",
        "state",
        "objective_value",
        "mean_score",
        "win_rate",
        "min_score",
        "max_score",
        "played_seeds",
        "game_results",
        *multiAgents.BETTER_EVAL_DEFAULT_WEIGHTS.keys(),
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def flatten_trial_game_rows(trial_details: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for trial in trial_details:
        metrics = trial.get("metrics", {})
        params = trial.get("params", {})
        game_results = metrics.get("game_results", [])

        for game in game_results:
            row = {
                "trial": trial["trial"],
                "state": trial["state"],
                "objective_value": trial["objective_value"],
                "seed": game.get("seed"),
                "game_score": game.get("score"),
                "win": game.get("win"),
                "move_count": game.get("move_count"),
                "remaining_food": game.get("remaining_food"),
                "remaining_capsules": game.get("remaining_capsules"),
            }
            for name in multiAgents.BETTER_EVAL_DEFAULT_WEIGHTS:
                row[name] = params.get(name, "")
            rows.append(row)

    return rows


def write_games_csv(rows: list[dict[str, object]], csv_path: str) -> None:
    ensure_parent(csv_path)
    fieldnames = [
        "trial",
        "state",
        "objective_value",
        "seed",
        "game_score",
        "win",
        "move_count",
        "remaining_food",
        "remaining_capsules",
        *multiAgents.BETTER_EVAL_DEFAULT_WEIGHTS.keys(),
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def collect_trial_details(study: optuna.study.Study) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []

    for trial in study.trials:
        details.append({
            "trial": trial.number,
            "state": str(trial.state),
            "objective_value": None if trial.value is None else float(trial.value),
            "params": {
                key: float(value)
                for key, value in trial.params.items()
            },
            "metrics": dict(trial.user_attrs),
            "intermediate_values": {
                str(step): float(value)
                for step, value in trial.intermediate_values.items()
            },
        })

    return details


def write_trials_json(
    study: optuna.study.Study,
    trial_details: list[dict[str, object]],
    json_path: str,
    args: argparse.Namespace,
) -> None:
    ensure_parent(json_path)
    payload = {
        "study_name": study.study_name,
        "direction": "maximize",
        "layout": args.layout,
        "depth": args.depth,
        "ghosts": args.ghosts,
        "timeout": args.timeout,
        "search_seeds": args.seeds,
        "validation_seeds": args.validation_seeds,
        "trial_count": len(trial_details),
        "trials": trial_details,
    }
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def write_trial_outputs(
    study: optuna.study.Study,
    args: argparse.Namespace,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    trial_rows = collect_trial_rows(study)
    trial_details = collect_trial_details(study)
    game_rows = flatten_trial_game_rows(trial_details)
    write_trials_csv(trial_rows, args.trials_csv)
    write_trials_json(study, trial_details, args.trials_json, args)
    write_games_csv(game_rows, args.games_csv)
    return trial_rows, trial_details, game_rows


def compare_weight_sets(
    optimized_weights: dict[str, float],
    baseline_weights: dict[str, float],
    args: argparse.Namespace,
) -> dict[str, object]:
    optimized_metrics = evaluate_weights(optimized_weights, args, args.validation_seeds)
    baseline_metrics = evaluate_weights(baseline_weights, args, args.validation_seeds)

    per_seed = []
    for optimized_game, baseline_game in zip(
        optimized_metrics["game_results"],
        baseline_metrics["game_results"],
    ):
        per_seed.append({
            "seed": optimized_game["seed"],
            "optimized_score": optimized_game["score"],
            "baseline_score": baseline_game["score"],
            "score_delta": optimized_game["score"] - baseline_game["score"],
            "optimized_win": optimized_game["win"],
            "baseline_win": baseline_game["win"],
            "optimized_move_count": optimized_game["move_count"],
            "baseline_move_count": baseline_game["move_count"],
        })

    return {
        "baseline_weights": baseline_weights,
        "optimized_weights": optimized_weights,
        "baseline_validation": baseline_metrics,
        "optimized_validation": optimized_metrics,
        "mean_score_delta": (
            optimized_metrics["mean_score"] - baseline_metrics["mean_score"]
        ),
        "win_rate_delta": (
            optimized_metrics["win_rate"] - baseline_metrics["win_rate"]
        ),
        "per_seed": per_seed,
    }


def plot_history(rows: list[dict[str, object]], plots_dir: str) -> list[str]:
    if plt is None:
        return []

    Path(plots_dir).mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []

    complete_rows = [
        row for row in rows
        if row["state"] == "TrialState.COMPLETE" and row["mean_score"] != ""
    ]
    if not complete_rows:
        return saved_paths

    trials = [int(row["trial"]) for row in complete_rows]
    mean_scores = [float(row["mean_score"]) for row in complete_rows]

    best_so_far: list[float] = []
    current_best = float("-inf")
    for score in mean_scores:
        current_best = max(current_best, score)
        best_so_far.append(current_best)

    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    ax.plot(trials, mean_scores, marker="o", linewidth=1.5, label="Mean score")
    ax.plot(trials, best_so_far, linewidth=2, linestyle="--", label="Best so far")
    ax.set_title("Optimization History")
    ax.set_xlabel("Trial")
    ax.set_ylabel("Mean score")
    ax.grid(True, alpha=0.3)
    ax.legend()
    history_path = str(Path(plots_dir) / "optimization_history.png")
    fig.savefig(history_path, dpi=160)
    plt.close(fig)
    saved_paths.append(history_path)

    return saved_paths


def plot_parameter_game_scores(game_rows: list[dict[str, object]], plots_dir: str) -> list[str]:
    if plt is None:
        return []

    complete_rows = [
        row for row in game_rows
        if row["state"] == "TrialState.COMPLETE" and row["game_score"] is not None
    ]
    if not complete_rows:
        return []

    Path(plots_dir).mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []
    parameter_names = list(multiAgents.BETTER_EVAL_DEFAULT_WEIGHTS.keys())
    column_count = 3
    row_count = math.ceil(len(parameter_names) / column_count)

    fig, axes = plt.subplots(
        row_count,
        column_count,
        figsize=(15, 4.5 * row_count),
        constrained_layout=True,
    )
    flat_axes = list(axes.flat) if hasattr(axes, "flat") else [axes]

    for ax, parameter_name in zip(flat_axes, parameter_names):
        points = sorted(
            (
                float(row[parameter_name]),
                float(row["game_score"]),
            )
            for row in complete_rows
            if row[parameter_name] != ""
        )
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]

        ax.scatter(x_values, y_values, alpha=0.7, s=26, color="tab:blue")
        ax.set_title(parameter_name)
        ax.set_xlabel("Parameter value")
        ax.set_ylabel("Game score")
        ax.grid(True, alpha=0.25)

    for ax in flat_axes[len(parameter_names):]:
        ax.set_visible(False)

    score_plot_path = str(Path(plots_dir) / "parameter_vs_game_score.png")
    fig.savefig(score_plot_path, dpi=160)
    plt.close(fig)
    saved_paths.append(score_plot_path)

    return saved_paths


def plot_optimized_vs_baseline(
    comparison: dict[str, object],
    plots_dir: str,
) -> list[str]:
    if plt is None:
        return []

    Path(plots_dir).mkdir(parents=True, exist_ok=True)
    per_seed = comparison["per_seed"]
    if not per_seed:
        return []

    seeds = [item["seed"] for item in per_seed]
    optimized_scores = [item["optimized_score"] for item in per_seed]
    baseline_scores = [item["baseline_score"] for item in per_seed]

    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ax.plot(seeds, optimized_scores, marker="o", linewidth=2, label="Optimized")
    ax.plot(seeds, baseline_scores, marker="s", linewidth=2, label="Baseline")
    ax.set_title("Optimized vs Baseline by Seed")
    ax.set_xlabel("Seed")
    ax.set_ylabel("Game score")
    ax.grid(True, alpha=0.3)
    ax.legend()

    compare_plot_path = str(Path(plots_dir) / "optimized_vs_baseline.png")
    fig.savefig(compare_plot_path, dpi=160)
    plt.close(fig)

    return [compare_plot_path]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    Path(args.result_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.plots_dir).mkdir(parents=True, exist_ok=True)

    ensure_parent(args.storage)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=args.sampler_seed)
    study_kwargs = {
        "study_name": args.study_name,
        "direction": "maximize",
        "sampler": sampler,
    }
    if args.storage:
        study_kwargs["storage"] = args.storage
        study_kwargs["load_if_exists"] = True

    study = optuna.create_study(**study_kwargs)

    if len(study.trials) == 0:
        study.enqueue_trial(multiAgents.get_better_eval_weights())

    def objective(trial: optuna.trial.Trial) -> float:
        weights = suggest_weights(trial)
        metrics = evaluate_weights(weights, args, args.seeds)
        for name, value in metrics.items():
            if name in {"scores", "game_results", "played_seeds"}:
                trial.set_user_attr(name, value)
            else:
                trial.set_user_attr(name, float(value))
        return float(metrics["mean_score"])

    trial_outputs_written = False

    def save_trial_outputs_callback(
        callback_study: optuna.study.Study,
        _trial: optuna.trial.FrozenTrial,
    ) -> None:
        nonlocal trial_outputs_written
        write_trial_outputs(callback_study, args)
        trial_outputs_written = True

    try:
        study.optimize(
            objective,
            n_trials=args.trials,
            callbacks=[save_trial_outputs_callback],
        )
        trial_rows, _, game_rows = write_trial_outputs(study, args)
        trial_outputs_written = True

        best_params = {
            key: float(value)
            for key, value in study.best_trial.params.items()
        }
        comparison = compare_weight_sets(best_params, USER_BASELINE_WEIGHTS, args)
        validation = comparison["optimized_validation"]
        payload = {
            "study_name": study.study_name,
            "search_seeds": args.seeds,
            "validation_seeds": args.validation_seeds,
            "best_trial_number": study.best_trial.number,
            "best_mean_score": float(study.best_value),
            "best_params": best_params,
            "validation": validation,
            "baseline_comparison": comparison,
        }

        Path(args.result_json).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        plot_paths = []
        plot_paths.extend(plot_history(trial_rows, args.plots_dir))
        plot_paths.extend(plot_parameter_game_scores(game_rows, args.plots_dir))
        plot_paths.extend(plot_optimized_vs_baseline(comparison, args.plots_dir))

        print("Best trial:", study.best_trial.number)
        print("Search mean score:", f"{study.best_value:.2f}")
        print("Validation mean score:", f"{validation['mean_score']:.2f}")
        print("Validation win rate:", f"{validation['win_rate']:.2%}")
        print("Baseline validation mean score:", f"{comparison['baseline_validation']['mean_score']:.2f}")
        print("Mean score delta:", f"{comparison['mean_score_delta']:.2f}")
        print("Best params:")
        print(json.dumps(best_params, indent=2))
        print("Saved:", args.result_json)
        print("Trials CSV:", args.trials_csv)
        print("Trials JSON:", args.trials_json)
        print("Games CSV:", args.games_csv)
        if plot_paths:
            print("Plots:")
            for plot_path in plot_paths:
                print(plot_path)
        elif plt is None:
            print("Plots: matplotlib is not installed, so no PNG charts were generated.")
        return 0
    finally:
        if not trial_outputs_written and study.trials:
            try:
                write_trial_outputs(study, args)
                print(
                    "Saved partial trial outputs before exit:",
                    args.trials_csv,
                    args.trials_json,
                    args.games_csv,
                    file=sys.stderr,
                )
            except Exception as exc:
                print(f"Failed to save partial trial outputs: {exc}", file=sys.stderr)
        multiAgents.set_better_eval_weights(multiAgents.BETTER_EVAL_DEFAULT_WEIGHTS)


if __name__ == "__main__":
    raise SystemExit(main())
