"""scripts/merge-gate, run as a command against a fake gh that answers with recorded GitHub data.

Each case reads one folder in fixtures/ (see fixtures/README.md) and checks the exit code, the output
and the commands that would have changed GitHub.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from typing import Optional

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MERGE_GATE = os.path.join(TESTS_DIR, "..", "templates", "scripts", "merge-gate")
FAKE_GH_DIR = os.path.join(TESTS_DIR, "fake-gh")
FAKE_LOCAL_CI = os.path.join(TESTS_DIR, "fake-local-ci", "local-ci")
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")
# The config of the project the fixtures were recorded on.
FIXTURES_CONFIG = os.path.join(TESTS_DIR, "agent-team.json")

# Fast enough that --update tests don't wait on real time, slow enough that the fake CI gets polled.
FAST_POLLING = {"MERGE_GATE_POLL_INTERVAL_MS": "1", "MERGE_GATE_CI_TIMEOUT_MS": "2000"}
LOCAL_CI_ON = {**FAST_POLLING, "AGENT_TEAM_LOCAL_CI": "1", "MERGE_GATE_LOCAL_CI": FAKE_LOCAL_CI}

USAGE = "Usage: scripts/merge-gate <PR> [--dry-run | --update | [--update] --rerun]"
REQUIRED_CHECKS = ["checks", "test-postgres", "pr-title", "dev-smoke"]

# The recorded heads the gate merges.
HEAD_68 = "ad7fa1c97b7e12a61ba1a26c0d1439109986ede3"
HEAD_69 = "e2b955023764af7f94c2460c57dc11368140644f"
HEAD_82 = "edb9829487ae290f039a7063b9839afa681c76e2"
HEAD_92 = "1b17d05c6db07d8d7cf3df7dc6b18ecc2010c2f7"
HEAD_125 = "9bef7ffd2cc61b1d879e00a4265c6805c97cbc36"
HEAD_171 = "80f967ac2f59343468feb4ac15862b4e30a1cc97"


def merge_command(pr: int, head_sha: str) -> str:
    return (
        f"gh pr merge {pr} --repo octo-org/octo-repo --squash --delete-branch "
        f"--match-head-commit {head_sha}"
    )


def update_command(pr: int) -> str:
    return f"gh pr update-branch {pr} --repo octo-org/octo-repo"


class GateRun:
    def __init__(self, exit_code: int, output: str, write_commands: list[str]) -> None:
        self.exit_code = exit_code
        self.output = output
        self.write_commands = write_commands


class MergeGateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.work_dir = tempfile.mkdtemp(prefix="merge-gate-")
        self.addCleanup(shutil.rmtree, self.work_dir, True)

    def run_gate(self, fixture: str, args: list[str], env: Optional[dict[str, str]] = None) -> GateRun:
        result = subprocess.run(
            [MERGE_GATE, *args],
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "AGENT_TEAM_CONFIG": FIXTURES_CONFIG,
                **(env or {}),
                "PATH": FAKE_GH_DIR + os.pathsep + os.environ.get("PATH", ""),
                "FAKE_GH_FIXTURE": os.path.join(FIXTURES_DIR, fixture),
                "FAKE_GH_WORK_DIR": self.work_dir,
            },
        )
        return GateRun(result.returncode, result.stdout + result.stderr, self.read_writes())

    def read_writes(self) -> list[str]:
        path = os.path.join(self.work_dir, "writes.log")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as file:
            return [line for line in file.read().split("\n") if line]

    def write_config(self, config: dict) -> str:
        path = os.path.join(self.work_dir, "agent-team.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(config, file)
        return path

    def assert_refused(self, run: GateRun, *reasons: str) -> None:
        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.write_commands, [])
        for reason in reasons:
            self.assertIn(reason, run.output)


class MergeTests(MergeGateTestCase):
    def test_squash_merges_a_pr_whose_checks_passed_and_whose_head_has_review_approved(self):
        run = self.run_gate("approved-on-head", ["68"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(68, HEAD_68)])
        self.assertIn("Merged PR #68", run.output)

    def test_prints_the_decision_without_merging_on_dry_run(self):
        run = self.run_gate("approved-on-head", ["68", "--dry-run"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [])
        self.assertIn("PR #68 can merge", run.output)
        self.assertIn("dry run", run.output)

    def test_refuses_an_already_merged_pr_even_on_dry_run(self):
        run = self.run_gate("already-merged", ["76", "--dry-run"])

        self.assert_refused(run, "the PR is already merged")
        self.assertNotIn("can merge", run.output)

    def test_refuses_a_closed_pr(self):
        self.assert_refused(self.run_gate("closed-unmerged", ["68"]), "the PR is closed")

    def test_refuses_a_pr_whose_head_is_behind_main_and_says_how_to_update_it(self):
        run = self.run_gate("behind-main", ["68"])

        self.assert_refused(run, "the head is 2 commits behind main", "scripts/merge-gate 68 --update")

    def test_prints_every_reason_when_several_rules_fail(self):
        run = self.run_gate("checks-never-ran", ["67", "--dry-run"])

        self.assertIn("Refusing to merge PR #67:", run.output)
        self.assertEqual(len([line for line in run.output.split("\n") if line.startswith("  - ")]), 4)


class CarryOverTests(MergeGateTestCase):
    def test_carries_an_approval_over_when_only_merges_from_main_came_after_it(self):
        run = self.run_gate("carried-over", ["69"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(69, HEAD_69)])
        self.assertIn("approval carried over from 4bfcbfe: only main's changes were merged in", run.output)

    def test_carries_an_approval_over_a_merge_that_changed_only_a_configured_lock_file(self):
        run = self.run_gate("merge-changed-only-bun-lock", ["92"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(92, HEAD_92)])
        self.assertIn("approval carried over from 1c18ad3: only main's changes were merged in", run.output)

    def test_refuses_to_carry_an_approval_over_a_lock_file_change_when_the_lock_file_is_not_configured(self):
        config = self.write_config({"requiredChecks": REQUIRED_CHECKS})

        run = self.run_gate("merge-changed-only-bun-lock", ["92"], {"AGENT_TEAM_CONFIG": config})

        self.assert_refused(
            run,
            "the approval on 1c18ad3 can't carry over to 1b17d05: the merges after it changed bun.lock, "
            "which the PR changes",
        )

    def test_refuses_to_carry_an_approval_over_a_merge_that_changed_the_lock_file_and_another_pr_file(self):
        run = self.run_gate("merge-changed-bun-lock-and-pr-file", ["92"])

        self.assert_refused(
            run,
            "the approval on 1c18ad3 can't carry over to 1b17d05: the merges after it changed "
            "packages/http/package.json, which the PR changes",
        )

    def test_refuses_to_carry_an_approval_over_a_merge_that_swapped_where_a_renamed_file_came_from(self):
        run = self.run_gate("rename-source-swapped", ["69"])

        self.assert_refused(
            run,
            "the approval on 4bfcbfe can't carry over to e2b9550: the merges after it changed "
            "schema/api.def, which the PR changes",
        )

    def test_refuses_to_carry_an_approval_over_a_merge_that_changed_a_pr_files_mode(self):
        run = self.run_gate("mode-changed", ["69"])

        self.assert_refused(
            run,
            "the approval on 4bfcbfe can't carry over to e2b9550: the merges after it changed "
            "schema/scripts/generate.ts, which the PR changes",
        )

    def test_refuses_to_carry_an_approval_over_when_github_cant_list_the_whole_diff(self):
        run = self.run_gate("too-many-files", ["69"])

        self.assert_refused(
            run,
            "the approval on 4bfcbfe can't carry over to e2b9550: GitHub lists only part of the PR's "
            "diff at e2b9550, so the gate can't compare it",
        )

    def test_refuses_to_carry_an_approval_over_a_commit_the_author_pushed_after_it(self):
        run = self.run_gate("pushed-after-approval", ["82"])

        self.assert_refused(
            run,
            "the approval on 6051a70 can't carry over to edb9829: commit 096b783 is not a merge from main",
        )

    def test_refuses_to_carry_an_approval_over_a_merge_from_a_branch_other_than_main(self):
        run = self.run_gate("merged-other-branch", ["69"])

        self.assert_refused(
            run,
            "the approval on 4bfcbfe can't carry over to e2b9550: merge commit e2b9550 brings in "
            "8c724a6, which is not on main",
        )

    def test_refuses_when_the_approved_commit_is_no_longer_on_the_pr(self):
        run = self.run_gate("approved-commit-gone", ["69"])

        self.assert_refused(
            run, "the approval on 4bfcbfe can't carry over to e2b9550: 4bfcbfe is no longer on the PR"
        )


class ReviewTests(MergeGateTestCase):
    def test_refuses_when_changes_requested_came_after_the_approval(self):
        run = self.run_gate("changes-requested-after-approval", ["69"])

        self.assert_refused(run, "the newest REVIEW: review says 'REVIEW: CHANGES_REQUESTED'")

    def test_refuses_when_no_review_starts_with_the_marker(self):
        self.assert_refused(self.run_gate("no-review", ["69"]), "no review starts with 'REVIEW:'")

    def test_reads_the_review_marker_from_the_config(self):
        config = self.write_config(
            {"requiredChecks": REQUIRED_CHECKS, "reviewMarker": "VERDICT:"}
        )

        run = self.run_gate("approved-on-head", ["68"], {"AGENT_TEAM_CONFIG": config})

        self.assert_refused(run, "no review starts with 'VERDICT:'")


class CheckTests(MergeGateTestCase):
    def test_refuses_while_a_check_is_still_running(self):
        run = self.run_gate("checks-pending", ["69"])

        self.assert_refused(run, "check test-postgres has not finished (IN_PROGRESS)")

    def test_refuses_while_a_rerun_of_a_passed_check_is_queued(self):
        run = self.run_gate("check-requeued", ["68"])

        self.assert_refused(run, "check pr-title has not finished (QUEUED)")

    def test_refuses_when_a_check_failed(self):
        self.assert_refused(self.run_gate("check-failed", ["69"]), "check checks finished with FAILURE")

    def test_merges_when_dev_smoke_passed_next_to_the_other_required_checks(self):
        run = self.run_gate("dev-smoke-passed", ["125"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(125, HEAD_125)])

    def test_refuses_when_dev_smoke_failed(self):
        run = self.run_gate("dev-smoke-failed", ["125"])

        self.assert_refused(run, "check dev-smoke finished with FAILURE")

    def test_refuses_while_dev_smoke_is_still_running(self):
        run = self.run_gate("dev-smoke-pending", ["125"])

        self.assert_refused(run, "check dev-smoke has not finished (IN_PROGRESS)")

    def test_refuses_when_a_required_check_never_ran_even_with_the_other_checks_green(self):
        run = self.run_gate("dev-smoke-never-ran", ["125"])

        self.assert_refused(run, "check dev-smoke has not run on 9bef7ff")

    def test_reads_the_required_checks_from_the_config(self):
        config = self.write_config({"requiredChecks": ["checks", "test-postgres", "pr-title"]})

        run = self.run_gate("dev-smoke-never-ran", ["125"], {"AGENT_TEAM_CONFIG": config})

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(125, HEAD_125)])

    def test_refuses_when_required_checks_never_ran_on_the_head(self):
        run = self.run_gate("checks-never-ran", ["67"])

        self.assert_refused(
            run,
            "check checks has not run on b0164bf",
            "check test-postgres has not run on b0164bf",
            "check pr-title has not run on b0164bf",
            "check dev-smoke has not run on b0164bf",
        )


class CommitStatusTests(MergeGateTestCase):
    def test_merges_when_a_commit_status_passed_next_to_the_checks(self):
        run = self.run_gate("status-context-passed", ["68"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertIn("Merged PR #68", run.output)

    def test_refuses_while_a_commit_status_is_pending(self):
        run = self.run_gate("status-context-pending", ["68"])

        self.assert_refused(run, "check EasyCLA has not finished (PENDING)")

    def test_merges_when_a_commit_status_passed_after_the_actions_run_of_the_same_name_failed(self):
        run = self.run_gate("status-beats-failed-check", ["171", "--dry-run"])

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertIn("PR #171 can merge", run.output)

    def test_refuses_a_passed_commit_status_for_a_required_check_that_local_ci_didnt_post(self):
        run = self.run_gate("status-without-marker", ["171", "--dry-run"])

        self.assert_refused(
            run,
            "check checks passed in a commit status without the marker 'local-ci <host> 80f967a: ', "
            "so it doesn't count",
            "check checks finished with FAILURE",
        )
        self.assertNotIn("check test-postgres", run.output)

    def test_refuses_a_passed_commit_status_whose_local_ci_marker_names_another_head(self):
        run = self.run_gate("status-marker-other-head", ["171", "--dry-run"])

        self.assert_refused(
            run, "check checks passed in a commit status without the marker 'local-ci <host> 80f967a: '"
        )

    def test_refuses_when_a_commit_status_for_a_required_check_failed(self):
        run = self.run_gate("status-failed", ["171", "--dry-run"])

        self.assert_refused(run, "check checks finished with FAILURE")
        self.assertNotIn("check test-postgres", run.output)


class UpdateTests(MergeGateTestCase):
    def test_merges_main_in_waits_for_ci_on_the_new_head_and_merges(self):
        run = self.run_gate("update-then-merge", ["82", "--update"], FAST_POLLING)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(
            run.write_commands,
            [update_command(82), merge_command(82, HEAD_82)],
        )
        self.assertIn("approval carried over from 3468ba3: only main's changes were merged in", run.output)

    def test_with_local_ci_runs_it_on_the_new_head_instead_of_waiting_for_actions(self):
        run = self.run_gate("update-then-local-ci", ["82", "--update"], LOCAL_CI_ON)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(
            run.write_commands,
            [update_command(82), "local-ci 82", merge_command(82, HEAD_82)],
        )

    def test_with_local_ci_turned_on_in_the_config_runs_it_on_the_new_head(self):
        config = self.write_config(
            {
                "requiredChecks": REQUIRED_CHECKS,
                "carryOverLockFiles": ["bun.lock"],
                "mergeGate": {"localCiOnUpdate": True},
            }
        )
        env = {**FAST_POLLING, "AGENT_TEAM_CONFIG": config, "MERGE_GATE_LOCAL_CI": FAKE_LOCAL_CI}

        run = self.run_gate("update-then-local-ci", ["82", "--update"], env)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands[:2], [update_command(82), "local-ci 82"])

    def test_with_local_ci_turned_on_in_the_config_the_env_can_turn_it_off(self):
        config = self.write_config(
            {"requiredChecks": REQUIRED_CHECKS, "mergeGate": {"localCiOnUpdate": True}}
        )
        env = {
            **FAST_POLLING,
            "AGENT_TEAM_CONFIG": config,
            "AGENT_TEAM_LOCAL_CI": "0",
            "MERGE_GATE_LOCAL_CI": FAKE_LOCAL_CI,
        }

        run = self.run_gate("update-then-local-ci", ["82", "--update"], env)

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.write_commands, [update_command(82)])

    def test_with_local_ci_refuses_when_local_ci_could_not_run_the_jobs(self):
        env = {**LOCAL_CI_ON, "FAKE_LOCAL_CI_EXIT_CODE": "2"}

        run = self.run_gate("update-then-local-ci", ["82", "--update"], env)

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.write_commands, [update_command(82), "local-ci 82"])
        self.assertIn("stopped with exit code 2", run.output)

    def test_with_local_ci_runs_it_on_a_head_that_is_up_to_date_but_has_no_local_ci_results(self):
        run = self.run_gate("up-to-date-without-local-ci", ["171", "--update"], LOCAL_CI_ON)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(
            run.write_commands, ["local-ci 171", merge_command(171, HEAD_171)]
        )

    def test_with_local_ci_runs_it_again_on_a_head_whose_local_ci_run_errored_on_this_machine(self):
        run = self.run_gate("local-ci-errored", ["171", "--update"], LOCAL_CI_ON)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(
            run.write_commands, ["local-ci 171", merge_command(171, HEAD_171)]
        )

    def test_with_local_ci_doesnt_run_it_again_on_a_head_that_already_has_its_results(self):
        run = self.run_gate("status-beats-failed-check", ["171", "--update"], LOCAL_CI_ON)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(171, HEAD_171)])

    def test_rerun_runs_local_ci_again_on_a_head_whose_local_ci_run_failed(self):
        run = self.run_gate("status-failed", ["171", "--rerun"], LOCAL_CI_ON)

        self.assertEqual(run.write_commands[0], "local-ci 171", run.output)

    def test_rerun_also_takes_the_update_rerun_spelling(self):
        run = self.run_gate("status-failed", ["171", "--update", "--rerun"], LOCAL_CI_ON)

        self.assertEqual(run.write_commands[0], "local-ci 171", run.output)

    def test_rerun_refuses_to_start_without_local_ci(self):
        env = {**FAST_POLLING, "AGENT_TEAM_LOCAL_CI": "0", "MERGE_GATE_LOCAL_CI": FAKE_LOCAL_CI}

        run = self.run_gate("status-failed", ["171", "--rerun"], env)

        self.assertEqual(run.exit_code, 2, run.output)
        self.assertEqual(run.write_commands, [])
        self.assertIn("--rerun needs local CI", run.output)

    def test_without_local_ci_refuses_when_actions_failed_on_the_new_head(self):
        env = {**FAST_POLLING, "MERGE_GATE_LOCAL_CI": FAKE_LOCAL_CI}

        run = self.run_gate("update-then-local-ci", ["82", "--update"], env)

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.write_commands, [update_command(82)])
        self.assertIn("check checks finished with FAILURE", run.output)

    def test_refuses_when_ci_doesnt_finish_on_the_new_head_in_time(self):
        env = {"MERGE_GATE_POLL_INTERVAL_MS": "1", "MERGE_GATE_CI_TIMEOUT_MS": "50"}

        run = self.run_gate("update-ci-never-finishes", ["92", "--update"], env)

        self.assertEqual(run.exit_code, 1, run.output)
        self.assertEqual(run.write_commands, [update_command(92)])
        self.assertIn("CI did not finish on the new head within 50 ms", run.output)

    def test_merges_a_pr_that_is_up_to_date_without_updating_it(self):
        run = self.run_gate("approved-on-head", ["68", "--update"], FAST_POLLING)

        self.assertEqual(run.exit_code, 0, run.output)
        self.assertEqual(run.write_commands, [merge_command(68, HEAD_68)])


class FailureTests(MergeGateTestCase):
    def test_exits_with_one_line_and_no_traceback_when_gh_fails(self):
        run = self.run_gate("unknown-pr", ["99999"])

        self.assertEqual(run.exit_code, 2)
        self.assertEqual(run.write_commands, [])
        lines = run.output.rstrip().split("\n")
        self.assertEqual(len(lines), 1, run.output)
        self.assertIn("GraphQL: Could not resolve to a PullRequest with the number of 99999.", lines[0])

    def test_exits_with_one_line_when_gh_refuses_the_merge(self):
        run = self.run_gate("merge-refused", ["68"])

        self.assertEqual(run.exit_code, 2)
        lines = run.output.rstrip().split("\n")
        self.assertEqual(len(lines), 1, run.output)
        self.assertIn("Head branch was modified. Review and try the merge again.", lines[0])
        self.assertNotIn("Merged PR", run.output)

    def test_exits_with_usage_help_when_the_arguments_are_wrong(self):
        for args in [[], ["abc"], ["12", "--force"], ["12", "--dry-run", "--update"]]:
            with self.subTest(args=args):
                run = self.run_gate("approved-on-head", args)

                self.assertEqual(run.exit_code, 2)
                self.assertIn(USAGE, run.output)

    def test_exits_with_one_line_when_the_config_is_missing(self):
        missing = os.path.join(self.work_dir, "agent-team.json")

        run = self.run_gate("approved-on-head", ["68"], {"AGENT_TEAM_CONFIG": missing})

        self.assertEqual(run.exit_code, 2)
        self.assertEqual(run.write_commands, [])
        self.assertEqual(
            run.output.rstrip().split("\n"),
            [f"merge-gate: {missing} not found: copy templates/agent-team.json from the agent-team skill"],
        )

    def test_exits_with_one_line_naming_an_unknown_config_key(self):
        config = self.write_config({"requiredChecks": ["checks"], "requiredCheck": ["typo"]})

        run = self.run_gate("approved-on-head", ["68"], {"AGENT_TEAM_CONFIG": config})

        self.assertEqual(run.exit_code, 2)
        self.assertEqual(run.write_commands, [])
        self.assertIn("unknown key 'requiredCheck'", run.output)


if __name__ == "__main__":
    unittest.main()
