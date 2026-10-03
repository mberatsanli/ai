"""Reads agent-team.json, the one file that holds what is project-specific about the merge gate and
local CI. Shared by scripts/merge-gate and scripts/local-ci. See scripts/README.md for every field.

The file lives at the root of the repo. AGENT_TEAM_CONFIG points at another file, for tests.
Unknown keys are refused, so a typo can't silently turn a rule off. Keys that start with "$" are
ignored, so the file can carry a "$comment".
"""

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any, Optional

CONFIG_FILENAME = "agent-team.json"
CONFIG_PATH_ENV = "AGENT_TEAM_CONFIG"

DEFAULT_REVIEW_MARKER = "REVIEW:"
# CI takes a few minutes; polling every 15 s keeps gh well inside GitHub's rate limit.
DEFAULT_POLL_INTERVAL_SECONDS = 15
DEFAULT_CI_TIMEOUT_MINUTES = 30


class ConfigError(Exception):
    """agent-team.json is missing or wrong. The message says which file and what to fix."""


@dataclass(frozen=True)
class Job:
    name: str
    command: str
    needs_docker: bool
    # Paths in the worktree to keep next to the job's log, like test traces. The worktree goes away.
    artifacts: tuple[str, ...]


@dataclass(frozen=True)
class LocalCi:
    setup: Optional[str]
    env: dict[str, str]
    unset_env: tuple[str, ...]
    jobs: tuple[Job, ...]


@dataclass(frozen=True)
class Config:
    required_checks: tuple[str, ...]
    review_marker: str
    carry_over_lock_files: frozenset[str]
    poll_interval_ms: int
    ci_timeout_ms: int
    local_ci_on_update: bool
    local_ci: Optional[LocalCi]


def load_config() -> Config:
    path = find_config_path()
    try:
        with open(path, encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError:
        raise ConfigError(f"{path} not found: copy templates/agent-team.json from the agent-team skill")
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path} is not valid JSON: {error}")
    try:
        return parse_config(raw)
    except ConfigError as error:
        raise ConfigError(f"{path}: {error}")


def find_config_path() -> str:
    override = os.environ.get(CONFIG_PATH_ENV)
    if override:
        return override
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ConfigError(f"not inside a git repo, so there is no {CONFIG_FILENAME} to read")
    return os.path.join(result.stdout.strip(), CONFIG_FILENAME)


def parse_config(raw: Any) -> Config:
    root = Section(raw, "")
    root.allow_only("requiredChecks", "reviewMarker", "carryOverLockFiles", "mergeGate", "localCi")
    gate = Section(root.get("mergeGate", {}), "mergeGate")
    gate.allow_only("pollIntervalSeconds", "ciTimeoutMinutes", "localCiOnUpdate")
    local_ci = root.get("localCi", None)
    return Config(
        required_checks=tuple(root.string_list("requiredChecks", required=True)),
        review_marker=root.string("reviewMarker", DEFAULT_REVIEW_MARKER),
        carry_over_lock_files=frozenset(root.string_list("carryOverLockFiles")),
        poll_interval_ms=gate.positive_number("pollIntervalSeconds", DEFAULT_POLL_INTERVAL_SECONDS)
        * 1000,
        ci_timeout_ms=gate.positive_number("ciTimeoutMinutes", DEFAULT_CI_TIMEOUT_MINUTES) * 60_000,
        local_ci_on_update=gate.boolean("localCiOnUpdate", False),
        local_ci=None if local_ci is None else parse_local_ci(Section(local_ci, "localCi")),
    )


def parse_local_ci(section: "Section") -> LocalCi:
    section.allow_only("setup", "env", "unsetEnv", "jobs")
    env = section.get("env", {})
    if not isinstance(env, dict) or not all(isinstance(value, str) for value in env.values()):
        raise ConfigError("localCi.env must be an object of strings")
    jobs = section.get("jobs", None)
    if not isinstance(jobs, list) or not jobs:
        raise ConfigError("localCi.jobs must be a non-empty list")
    parsed_jobs = tuple(parse_job(Section(job, f"localCi.jobs[{index}]")) for index, job in enumerate(jobs))
    names = [job.name for job in parsed_jobs]
    if len(set(names)) != len(names):
        raise ConfigError("localCi.jobs has two jobs with the same name")
    setup = section.get("setup", None)
    if setup is not None and (not isinstance(setup, str) or not setup):
        raise ConfigError("localCi.setup must be a command")
    return LocalCi(
        setup=setup,
        env=dict(env),
        unset_env=tuple(section.string_list("unsetEnv")),
        jobs=parsed_jobs,
    )


def parse_job(section: "Section") -> Job:
    section.allow_only("name", "command", "needsDocker", "artifacts")
    return Job(
        name=section.string("name", None),
        command=section.string("command", None),
        needs_docker=section.boolean("needsDocker", False),
        artifacts=tuple(section.string_list("artifacts")),
    )


class Section:
    """One JSON object of the config, with typed reads that name the field when it is wrong."""

    def __init__(self, raw: Any, where: str) -> None:
        if not isinstance(raw, dict):
            raise ConfigError(f"{where or 'the file'} must be a JSON object")
        self.raw = raw
        self.where = where

    def field(self, key: str) -> str:
        return f"{self.where}.{key}" if self.where else key

    def allow_only(self, *keys: str) -> None:
        unknown = sorted(key for key in self.raw if key not in keys and not key.startswith("$"))
        if unknown:
            raise ConfigError(f"unknown key {unknown[0]!r} in {self.where or 'the top level'}")

    def get(self, key: str, default: Any) -> Any:
        return self.raw.get(key, default)

    def string(self, key: str, default: Optional[str]) -> str:
        value = self.raw.get(key, default)
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{self.field(key)} must be a non-empty string")
        return value

    def string_list(self, key: str, required: bool = False) -> list[str]:
        value = self.raw.get(key, None if required else [])
        valid = isinstance(value, list) and all(isinstance(item, str) and item for item in value)
        if not valid or (required and not value):
            kind = "a non-empty list" if required else "a list"
            raise ConfigError(f"{self.field(key)} must be {kind} of strings")
        return value

    def boolean(self, key: str, default: bool) -> bool:
        value = self.raw.get(key, default)
        if not isinstance(value, bool):
            raise ConfigError(f"{self.field(key)} must be true or false")
        return value

    def positive_number(self, key: str, default: int) -> int:
        value = self.raw.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigError(f"{self.field(key)} must be a whole number above 0")
        return value
