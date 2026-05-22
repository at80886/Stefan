# 00_HEAD

## Project Goal

Build a desktop application for visual simulation of the one-dimensional Stefan problem.
The application should help users configure physical parameters, run a numerical phase-change simulation, and inspect the moving solid-liquid interface over time.

## Technical Constraints

- Frontend stack: PyQt6.
- Release platform: Windows.
- Development software: VSCode.
- Environment: conda virtual environment `py39`, installed under `D:\Anaconda`.
- Use UTF-8 for reading and writing all project documents.
- Avoid unnecessary large dependencies. Prefer the Python standard library and small, well-maintained packages already justified by the task.

## Core Functions

- Provide a PyQt6 desktop interface for configuring a one-dimensional Stefan problem.
- Support input of geometry, material properties, thermal parameters, initial conditions, boundary conditions, time step, and simulation duration.
- Implement a reliable baseline numerical solver before adding advanced models.
- Visualize temperature distribution along the one-dimensional domain.
- Visualize the phase interface position as it evolves over time.
- Provide start, pause, reset, and rerun controls for simulations.
- Show key numerical outputs, including current time, interface position, and stability or convergence status where applicable.
- Support saving or exporting simulation results in a simple tabular format.
- Keep the architecture modular: UI, solver, data model, plotting, and export logic should remain separable.
- Maintain module-level technical documentation and useful comments as the code evolves.

## Development Rules

- You are using Codex based on GPT-5.5. You run as a code agent in the Codex CLI on the user's computer. You and the user share the same workspace and collaborate to achieve the user's goals.
- You may be using a messy Git working tree. Never revert changes you have not made unless explicitly requested by the user, as these changes were made by the user.
- Except for this document, all other documents are in Chinese and should be read using UTF-8 format.
- Documents starting with a number are task documents. Unless otherwise specified, always adhere to the requirements of the task documents.
- Each commit or phase summary must specify which files were modified, what was implemented, and how it was verified.
- Any questions encountered during development should first be recorded in `OPEN_QUESTIONS.md`. Do not act rashly; wait for user confirmation.
- Communicate in a concise and respectful manner, focusing on the current task. Always prioritize actionable guidance, clearly explaining assumptions, environmental prerequisites, and subsequent steps.
- Unless explicitly requested, avoid lengthy explanations of the work.
- Maintain technical documentation and comments for each module promptly.
- When creating task documentation, proceed in small steps, one task at a time, keeping it concise and limiting it to 50 lines or less.
- Task documents should only describe what needs to be done and the intended effect; they should not describe implementation methods, acceptance criteria, or unrelated content.
- Avoid introducing unnecessary large dependencies.
- Prioritize ensuring functionality before gradually adding content.
- The main thread is only allowed to execute UI operations; the UI thread only initiates tasks, receives status, and updates the interface.
- Establish a unified exception management system; errors should be logizable, promptable, and recoverable.

## Working Principles

- Prefer small, verifiable implementation steps.
- Preserve user-created files and changes.
- Keep UI behavior practical and testable before polishing visual details.
- Record unresolved assumptions and blocking decisions in `OPEN_QUESTIONS.md`.
- Verify each phase with the most appropriate available method, such as unit tests, manual application launch, solver sanity checks, or export inspection.

## Remote Synchronization

- Remote repository: `https://github.com/at80886/Stefan.git`.
- Do not perform any Git operations unless explicitly requested by the user.
