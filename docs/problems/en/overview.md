# Multi-Agent Search Problem

**Due:** 06/05/2026 (dd-mm-yyyy)

## Table of Contents

* [Q1 - Reflex Agent](q1.md)
* [Q2 - Minimax](q2.md)
* [Q3 - Alpha-Beta Pruning](q3.md)
* [Q4 - Expectimax](q4.md)
* [Q5 - Evaluation Function](q5.md)
* [Q6 - AI Usage Reflection and Collaborators](q6.md)

---

## Introduction

In this project, you will design agents for the classic version of Pacman, including ghosts. Along the way, you will implement both minimax and expectimax search and try your hand at evaluation function design.

The code base has not changed much from the previous project, but please start with a fresh installation, rather than intermingling files from project 1.

As in project 1, this project includes an autograder for you to grade your answers on your machine. This can be run on all questions with the command:
```bash
python autograder.py
```
It can be run for one particular question, such as q2, by:
```bash
python autograder.py -q q2
```
It can be run for one particular test by commands of the form:
```bash
python autograder.py -t test_cases/q2/0-small-tree
```
By default, the autograder displays graphics with the `-t` option, but doesn't with the `-q` option. You can force graphics by using the `--graphics` flag, or force no graphics by using the `--no-graphics` flag.

See the autograder tutorial in Project 0 for more information about using the autograder.

## Three Working Modes

This repository now supports three parallel ways of working:

1. `Legacy-compatible mode`: use the root-level files such as `pacman.py`, `autograder.py`, and `multiAgents.py`.
2. `Refactored native mode`: work directly with the current layout under `src/core` and `tests`.
3. `Taskfile mode`: use the `Taskfile.yml` targets to run the launcher and tests consistently across environments (CI uses the same targets).

### Option 1: Legacy-compatible mode

This is the best fit if you want the original Berkeley-style commands in the assignment docs to keep working as written.

Run the game from the repository root:
```bash
python -m src.core.controller.pacman
python -m src.core.controller.pacman -p ReflexAgent -l testClassic
```

Run the autograder from the repository root:
```bash
python -m autograder
python -m autograder -q q2 --no-graphics
```

If you follow the original assignment wording, the file you will usually edit is:
```bash
multiAgents.py
```

### Option 2: Refactored native mode

This is the better fit if you want to work directly against the current repository structure.

Run Pacman from the refactored package layout:
```bash
python -m src.core.controller.pacman -p ReflexAgent -l testClassic
```

Run the autograder against the refactored layout:
```bash
python -m autograder -q q2 --no-graphics
```

If you work directly in the canonical refactored source tree, the file you will usually edit is:
```bash
src/core/agents/multiAgents.py
```

### Option 3: Taskfile mode

Taskfile provides a convenient single entry point for running the launcher and tests. Examples:

```bash
task run:pacman
task test
task test:fast
task test:q2
```

TaskFILE respects `PYTHON_BIN` and is configured to prefer `uv run` when available, falling back to the plain Python interpreter.

The code for this project contains the following files, available as a zip archive.

**Files you'll edit:**
* `multiAgents.py`: Where all of your multi-agent search agents will reside.

**Files you might want to look at:**
* `pacman.py`: The main file that runs Pacman games. This file also describes a Pacman `GameState` type, which you will use extensively in this project.
* `game.py`: The logic behind how the Pacman world works. This file describes several supporting types like `AgentState`, `Agent`, `Direction`, and `Grid`.
* `util.py`: Useful data structures for implementing search algorithms. You don't need to use these for this project, but may find other functions defined here to be useful.

**Supporting files you can ignore:**
* `graphicsDisplay.py`: Graphics for Pacman
* `graphicsUtils.py`: Support for Pacman graphics
* `textDisplay.py`: ASCII graphics for Pacman
* `ghostAgents.py`: Agents to control ghosts
* `keyboardAgents.py`: Keyboard interfaces to control Pacman
* `layout.py`: Code for reading layout files and storing their contents
* `autograder.py`: Project autograder
* `testParser.py`: Parses autograder test and solution files
* `testClasses.py`: General autograding test classes
* `test_cases/`: Directory containing the test cases for each question
* `multiagentTestClasses.py`: Project 3 specific autograding test classes

**Files to Edit and Submit:** You will fill in portions of `multiAgents.py` during the assignment. Once you have completed the assignment, you will submit these files to Gradescope (for instance, you can upload all `.py` files in the folder). Please do not change the other files in this distribution.

**Evaluation:** Your code will be autograded for technical correctness. Please do not change the names of any provided functions or classes within the code, or you will wreak havoc on the autograder. However, the correctness of your implementation - not the autograder's judgements - will be the final judge of your score. If necessary, we will review and grade assignments individually to ensure that you receive due credit for your work.

**Academic Dishonesty:** We will be checking your code against other submissions in the class for logical redundancy. If you copy someone else's code and submit it with minor changes, we will know. These cheat detectors are quite hard to fool, so please don't try. We trust you all to submit your own work only; please don't let us down. If you do, we will pursue the strongest consequences available to us.

**Getting Help:** You are not alone! If you find yourself stuck on something, contact the course staff for help. Office hours, section, and the discussion forum are there for your support; please use them. If you can't make our office hours, let us know and we will schedule more. We want these projects to be rewarding and instructional, not frustrating and demoralizing. But, we don't know when or how to help unless you ask.

**Discussion:** Please be careful not to post spoilers.

---

## Welcome to Multi-Agent Pacman

First, play a game of classic Pacman by running the following command:
```bash
python -m src.core.controller.pacman
```
and using the arrow keys to move. Now, run the provided `ReflexAgent` in `multiAgents.py`
```bash
python -m src.core.controller.pacman -p ReflexAgent
```
Note that it plays quite poorly even on simple layouts:
```bash
python -m src.core.controller.pacman -p ReflexAgent -l testClassic
```
Inspect its code (in `multiAgents.py`) and make sure you understand what it's doing.

---

## Submission

In order to submit your project upload the Python files you edited. For instance, use Gradescope's upload on all `.py` files in the project folder. Remember to tag your partners on Gradescope as a part of your submission.
