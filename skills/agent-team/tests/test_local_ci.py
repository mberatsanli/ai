"""scripts/local-ci, run as a command in a real git clone, with a fake gh and a fake Docker.

Each test pushes a PR head whose job scripts prove what local-ci gave them, then checks the exit code,
the output and the commit statuses that would have been posted.
"""

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from typing import Optional

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CI = os.path.join(TESTS_DIR, "..", "templates", "scripts", "local-ci")
FAKE_TOOLS_DIR = os.path.join(TESTS_DIR, "fake-local-ci-tools")

PR_NUMBER = "7"
PR_TITLE = "feat(ci): run CI locally"
JOB_NAMES = ["checks", "test-postgres", "dev-smoke", "pr-title", "e2e"]

CONFIG = {
    "requiredChecks": ["checks", "test-postgres", "dev-smoke", "pr-title"],
    "localCi": {
        "setup": "scripts/ci/setup.sh",
        "env": {"TURBO_FORCE": "true"},
        "unsetEnv": ["DATABASE_URL", "DATABASE_APP_URL"],
        "jobs": [
            {"name": "checks", "command": "scripts/ci/checks.sh"},
            {"name": "test-postgres", "command": "scripts/ci/test-postgres.sh", "needsDocker": True},
            {"name": "dev-smoke", "command": "scripts/ci/dev-smoke.sh"},
            {"name": "pr-title", "command": 'scripts/ci/pr-title.sh "$PR_TITLE"'},
            {"name": "e2e", "command": "scripts/ci/e2e.sh", "artifacts": ["e2e/test-results"]},
        ],
    },
}

# Each job script of the PR head proves what local-ci gave it, then passes or fails.
JOB_SCRIPTS = {
    "setup.sh": 'pwd -P > "$FAKE_WORK_DIR/setup"',
    "checks.sh": (
        'echo "checks CI=$CI DATABASE_URL=${DATABASE_URL:-unset} DATABASE_APP_URL=${DATABASE_APP_URL:-unset} '
        'TURBO_FORCE=${TURBO_FORCE:-unset} PR=$PR_NUMBER $PR_HEAD_SHA" > "$FAKE_WORK_DIR/checks"'
    ),
    "test-postgres.sh": 'echo "test-postgres ran" > "$FAKE_WORK_DIR/test-postgres"',
    "dev-smoke.sh": 'echo "dev-smoke started"\necho "the server never answered" >&2\nexit 1',
    "pr-title.sh": 'echo "$1" > "$FAKE_WORK_DIR/pr-title"',
    "e2e.sh": 'echo "e2e CI=$CI" > "$FAKE_WORK_DIR/e2e"',
}

# An e2e job that fails the way Playwright does: it leaves a trace and the stack's log behind.
FAILING_E2E_SCRIPT = "\n".join(
    [
        "mkdir -p e2e/test-results/smoke-signs-in",
        'echo "a trace" > e2e/test-results/smoke-signs-in/trace.zip',
        "echo \"the stack's log\" > e2e/test-results/stack.log",
        'echo "1 failed" >&2',
        "exit 1",
    ]
)

# A job whose machine broke: its database never got ready, which says nothing about the PR.
MACHINE_ERROR_SCRIPT = 'echo "Postgres did not get ready in 60 s" >&2\nexit 75'

# A job that says it started, then keeps running for longer than any test may take.
LONG_JOB_SCRIPT = 'touch "$FAKE_WORK_DIR/started"\nsleep 30\ntouch "$FAKE_WORK_DIR/outlived-local-ci"'

# Long enough for a run with fake jobs, far shorter than the 30 s a stopped job keeps running.
PROMPT_EXIT_SECONDS = 10


def git(cwd: str, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def context_and_state(status: str) -> str:
    """Each status line is "<sha> <context> <state> <description>"."""
    return " ".join(status.split(" ")[1:3])


def log_path_in(status: str) -> str:
    return status.rsplit("log: ", 1)[1]


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as file:
        return file.read()


class LocalCiRun:
    def __init__(self, exit_code: int, duration: float, output: str, statuses: list[str], docker: list[str]):
        self.exit_code = exit_code
        self.duration = duration
        self.output = output
        self.statuses = statuses
        self.docker_commands = docker

    def results(self) -> list[str]:
        """The context and state of every status after the pending ones."""
        return [context_and_state(status) for status in self.statuses[len(JOB_NAMES):]]


class LocalCiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.work_dir = tempfile.mkdtemp(prefix="local-ci-test-")
        self.addCleanup(shutil.rmtree, self.work_dir, True)
        origin = os.path.join(self.work_dir, "origin.git")
        self.checkout = os.path.join(self.work_dir, "checkout")
        git(self.work_dir, "init", "--quiet", "--bare", origin)
        git(self.work_dir, "clone", "--quiet", origin, self.checkout)
        self.write_config(CONFIG)
        self.push_pull_request_head(JOB_SCRIPTS)

    def write_config(self, config: dict) -> None:
        with open(os.path.join(self.checkout, "agent-team.json"), "w") as file:
            json.dump(config, file, indent=2)

    def push_pull_request_head(self, job_scripts: dict[str, str]) -> None:
        """Commits these job scripts and pushes them as the PR's head, like GitHub's refs/pull/<N>/head."""
        ci_dir = os.path.join(self.checkout, "scripts", "ci")
        os.makedirs(ci_dir, exist_ok=True)
        for name, body in job_scripts.items():
            script = os.path.join(ci_dir, name)
            with open(script, "w") as file:
                file.write(f"#!/bin/sh\nset -eu\n{body}\n")
            os.chmod(script, 0o755)
        git(self.checkout, "add", ".")
        author = ["-c", "user.name=Test", "-c", "user.email=test@example.com"]
        git(self.checkout, *author, "commit", "--quiet", "-m", "head")
        self.head_sha = git(self.checkout, "rev-parse", "HEAD")
        git(self.checkout, "push", "--quiet", "--force", "origin", f"HEAD:refs/pull/{PR_NUMBER}/head")

    def start_local_ci(self, args: list[str], env: dict[str, str]) -> subprocess.Popen:
        return subprocess.Popen(
            [LOCAL_CI, *args],
            cwd=self.checkout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={
                **os.environ,
                "DATABASE_URL": "postgres://someone:secret@example.com/production",
                "DATABASE_APP_URL": "postgres://app:secret@example.com/production",
                "PATH": FAKE_TOOLS_DIR + os.pathsep + os.environ.get("PATH", ""),
                "FAKE_WORK_DIR": self.work_dir,
                "FAKE_PR_HEAD_SHA": self.head_sha,
                "FAKE_PR_TITLE": PR_TITLE,
                **env,
            },
        )

    def run_local_ci(
        self, args: Optional[list[str]] = None, env: Optional[dict[str, str]] = None
    ) -> LocalCiRun:
        started = time.monotonic()
        process = self.start_local_ci([PR_NUMBER] if args is None else args, env or {})
        output, _ = process.communicate(timeout=60)
        return self.finished(process, output, started)

    def finished(self, process: subprocess.Popen, output: str, started: float) -> LocalCiRun:
        return LocalCiRun(
            process.returncode,
            time.monotonic() - started,
            output,
            self.read_lines("statuses.log"),
            self.read_lines("docker.log"),
        )

    def read_lines(self, name: str) -> list[str]:
        path = os.path.join(self.work_dir, name)
        return [line for line in read_file(path).split("\n") if line] if os.path.exists(path) else []

    def read_job_proof(self, job: str) -> str:
        return read_file(os.path.join(self.work_dir, job)).strip()

    def lock_dir(self) -> str:
        return os.path.join(self.checkout, ".git", "agent-team-local-ci.lock")

    def worktree_count(self) -> int:
        return len(git(self.checkout, "worktree", "list").split("\n"))


class StatusTests(LocalCiTestCase):
    def test_posts_every_job_as_pending_then_each_jobs_result_on_the_prs_head(self):
        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(
            [" ".join(status.split(" ")[:3]) for status in run.statuses],
            [f"{self.head_sha} {name} pending" for name in JOB_NAMES]
            + [
                f"{self.head_sha} checks success",
                f"{self.head_sha} test-postgres success",
                f"{self.head_sha} dev-smoke failure",
                f"{self.head_sha} pr-title success",
                f"{self.head_sha} e2e success",
            ],
        )

    def test_starts_every_description_with_a_marker_naming_local_ci_this_host_and_the_head(self):
        run = self.run_local_ci()

        for status in run.statuses:
            description = " ".join(status.split(" ")[3:])
            self.assertRegex(description, rf"^local-ci \S+ {self.head_sha[:7]}: ")

    def test_exits_with_0_when_every_job_passed(self):
        self.push_pull_request_head({**JOB_SCRIPTS, "dev-smoke.sh": "true"})

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(len([status for status in run.statuses if " success " in status]), 5)


class JobTests(LocalCiTestCase):
    def test_runs_each_job_like_ci_does_without_the_callers_unset_env(self):
        self.run_local_ci()

        self.assertEqual(
            self.read_job_proof("checks"),
            "checks CI=true DATABASE_URL=unset DATABASE_APP_URL=unset TURBO_FORCE=true "
            f"PR={PR_NUMBER} {self.head_sha}",
        )
        self.assertEqual(self.read_job_proof("pr-title"), PR_TITLE)
        self.assertEqual(self.read_job_proof("e2e"), "e2e CI=true")

    def test_runs_the_setup_in_the_heads_worktree_before_the_jobs(self):
        run = self.run_local_ci()

        logs_dir = os.path.dirname(log_path_in(run.statuses[-1]))
        self.assertEqual(self.read_job_proof("setup"), os.path.realpath(os.path.join(logs_dir, "head")))

    def test_marks_every_job_as_failed_when_the_setup_fails(self):
        self.push_pull_request_head({**JOB_SCRIPTS, "setup.sh": 'echo "lock file out of date" >&2\nexit 1'})

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.results(), [f"{name} failure" for name in JOB_NAMES])
        self.assertIn("lock file out of date", read_file(log_path_in(run.statuses[-1])))
        self.assertFalse(os.path.exists(os.path.join(self.work_dir, "checks")))

    def test_keeps_each_jobs_log_where_the_status_says_and_removes_the_worktree(self):
        run = self.run_local_ci()

        dev_smoke = next(status for status in run.statuses if " dev-smoke failure " in status)
        log = read_file(log_path_in(dev_smoke))
        self.assertIn("dev-smoke started", log)
        self.assertIn("the server never answered", log)
        self.assertEqual(self.worktree_count(), 1)

    def test_keeps_a_jobs_artifacts_where_its_log_says(self):
        self.push_pull_request_head({**JOB_SCRIPTS, "e2e.sh": FAILING_E2E_SCRIPT})

        run = self.run_local_ci()

        e2e = next(status for status in run.statuses if " e2e failure " in status)
        log = read_file(log_path_in(e2e))
        kept = next(line for line in log.split("\n") if line.startswith("Kept e2e/test-results: "))
        kept_dir = kept.split(": ", 1)[1]
        self.assertEqual(read_file(os.path.join(kept_dir, "smoke-signs-in", "trace.zip")), "a trace\n")
        self.assertEqual(read_file(os.path.join(kept_dir, "stack.log")), "the stack's log\n")

    def test_marks_a_job_as_errored_not_failed_when_it_exits_with_75(self):
        self.push_pull_request_head({**JOB_SCRIPTS, "test-postgres.sh": MACHINE_ERROR_SCRIPT})

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 2, run.output)
        self.assertEqual(
            run.results(),
            ["checks success", "test-postgres error", "dev-smoke failure", "pr-title success", "e2e success"],
        )
        errored = next(status for status in run.statuses if " test-postgres error " in status)
        self.assertIn("test-postgres: error", run.output)
        # A long log path can push the start of the reason out of GitHub's 140 characters; its end stays.
        self.assertTrue(errored.endswith("/test-postgres.log"), errored)
        self.assertLessEqual(len(errored.split(" ", 3)[3]), 140)
        self.assertIn("Postgres did not get ready in 60 s", read_file(log_path_in(errored)))


class StopTests(LocalCiTestCase):
    def assert_unfinished_jobs_errored(self, run: LocalCiRun, first_errored: str) -> None:
        self.assertEqual(run.exit_code, 2, run.output)
        index = JOB_NAMES.index(first_errored)
        self.assertEqual(
            run.results(),
            [f"{name} success" for name in JOB_NAMES[:index]]
            + [f"{name} error" for name in JOB_NAMES[index:]],
        )

    def test_on_a_signal_stops_the_running_job_at_once_and_marks_the_unfinished_jobs_as_errored(self):
        self.push_pull_request_head({**JOB_SCRIPTS, "test-postgres.sh": LONG_JOB_SCRIPT})
        for signal_number in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
            with self.subTest(signal=signal_number.name):
                self.reset_work_dir()
                started = time.monotonic()
                process = self.start_local_ci([PR_NUMBER], {})
                self.wait_for_file("started")

                process.send_signal(signal_number)
                output, _ = process.communicate(timeout=60)
                run = self.finished(process, output, started)

                self.assert_unfinished_jobs_errored(run, "test-postgres")
                self.assertLess(run.duration, PROMPT_EXIT_SECONDS)
                self.assertEqual(self.worktree_count(), 1)
                self.assertFalse(os.path.exists(self.lock_dir()))
                time.sleep(0.2)
                self.assertFalse(os.path.exists(os.path.join(self.work_dir, "outlived-local-ci")))

    def reset_work_dir(self) -> None:
        for name in ["started", "statuses.log", "status-posts", "docker.log"]:
            path = os.path.join(self.work_dir, name)
            if os.path.exists(path):
                os.remove(path)

    def wait_for_file(self, name: str) -> None:
        deadline = time.monotonic() + PROMPT_EXIT_SECONDS
        while not os.path.exists(os.path.join(self.work_dir, name)):
            self.assertLess(time.monotonic(), deadline, f"{name} never appeared")
            time.sleep(0.05)

    def test_marks_the_unfinished_jobs_as_errored_when_posting_a_status_fails(self):
        # The 6th status is checks' result, the first one after the five pending ones.
        run = self.run_local_ci(env={"FAKE_GH_FAILING_STATUS_POST": "6"})

        self.assert_unfinished_jobs_errored(run, "checks")

    def test_marks_every_job_as_errored_when_it_cant_check_the_head_out(self):
        self.head_sha = "0000000000000000000000000000000000000001"

        run = self.run_local_ci()

        self.assert_unfinished_jobs_errored(run, "checks")


class RefusalTests(LocalCiTestCase):
    def test_refuses_to_start_when_a_job_needs_docker_and_docker_isnt_running_and_posts_nothing(self):
        run = self.run_local_ci(env={"FAKE_DOCKER_DOWN": "1"})

        self.assertEqual(run.exit_code, 2)
        self.assertIn("Docker isn't running (start Docker Desktop or OrbStack)", run.output)
        self.assertEqual(run.statuses, [])
        self.assertFalse(os.path.exists(self.lock_dir()))

    def test_doesnt_need_docker_when_no_job_asks_for_it(self):
        jobs = [{**job, "needsDocker": False} for job in CONFIG["localCi"]["jobs"]]
        self.write_config({**CONFIG, "localCi": {**CONFIG["localCi"], "jobs": jobs}})
        self.push_pull_request_head(JOB_SCRIPTS)

        run = self.run_local_ci(env={"FAKE_DOCKER_DOWN": "1"})

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.docker_commands, [])

    def test_refuses_to_start_while_another_local_ci_holds_the_lock_and_posts_nothing(self):
        os.mkdir(self.lock_dir())
        with open(os.path.join(self.lock_dir(), "pid"), "w") as file:
            file.write(f"{os.getpid()}\n")

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 2)
        self.assertIn(f"another scripts/local-ci (pid {os.getpid()}) is running", run.output)
        self.assertEqual(run.statuses, [])
        self.assertTrue(os.path.exists(self.lock_dir()))

    def test_takes_over_a_lock_whose_local_ci_is_gone_and_releases_it_at_the_end(self):
        gone = subprocess.run(["sh", "-c", "echo $$"], capture_output=True, text=True).stdout.strip()
        os.mkdir(self.lock_dir())
        with open(os.path.join(self.lock_dir(), "pid"), "w") as file:
            file.write(f"{gone}\n")

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(len(run.statuses), 10)
        self.assertFalse(os.path.exists(self.lock_dir()))

    def test_refuses_to_run_from_a_dirty_working_tree_and_posts_nothing(self):
        with open(os.path.join(self.checkout, "scripts", "ci", "checks.sh"), "a") as file:
            file.write("# changed\n")

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 2)
        self.assertIn("uncommitted changes", run.output)
        self.assertEqual(run.statuses, [])

    def test_refuses_without_a_local_ci_section_in_the_config(self):
        self.write_config({"requiredChecks": ["checks"]})
        self.push_pull_request_head(JOB_SCRIPTS)

        run = self.run_local_ci()

        self.assertEqual(run.exit_code, 2)
        self.assertIn("agent-team.json has no localCi section", run.output)
        self.assertEqual(run.statuses, [])

    def test_exits_with_usage_help_when_the_pr_number_is_missing_or_not_a_number(self):
        for args in [[], ["abc"], ["7", "8"]]:
            with self.subTest(args=args):
                run = self.run_local_ci(args)

                self.assertEqual(run.exit_code, 2)
                self.assertIn("Usage: scripts/local-ci <PR>", run.output)
                self.assertEqual(run.statuses, [])


if __name__ == "__main__":
    unittest.main()
