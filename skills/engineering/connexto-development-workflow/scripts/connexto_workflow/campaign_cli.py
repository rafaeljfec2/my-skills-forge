"""Command line for the sequential campaign checkpoint."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from connexto_workflow.campaign import (
    campaign_commit,
    init_campaign,
    load_campaign,
    merge_pull_request,
    open_pull_request,
    open_sprint,
    reconcile,
    reconcile_plan,
    record_review,
)
from connexto_workflow.engine import Engine
from connexto_workflow.errors import WorkflowError


def register_campaign_commands(
    sub: Any,
    actor: Callable[[argparse.ArgumentParser], None],
) -> None:
    campaign_init = sub.add_parser("campaign-init")
    campaign_init.add_argument("--repo", type=Path, required=True)
    campaign_init.add_argument("--campaign-id", required=True)
    campaign_init.add_argument("--plan", type=Path, required=True)
    campaign_init.add_argument("--integration-branch", required=True)
    campaign_init.add_argument("--release-branch", default="main")
    campaign_init.add_argument("--protect-branch", action="append", default=[])

    campaign_status = sub.add_parser("campaign-status")
    campaign_status.add_argument("--repo", type=Path, required=True)
    campaign_status.add_argument("--campaign-id", required=True)

    campaign_sprint = sub.add_parser("campaign-open-sprint")
    campaign_sprint.add_argument("--repo", type=Path, required=True)
    campaign_sprint.add_argument("--campaign-id", required=True)
    campaign_sprint.add_argument("--sprint", required=True)

    campaign_bind = sub.add_parser("campaign-bind-branch")
    actor(campaign_bind)
    campaign_bind.add_argument("--branch", required=True)

    campaign_review = sub.add_parser("campaign-record-review")
    campaign_review.add_argument("--repo", type=Path, required=True)
    campaign_review.add_argument("--campaign-id", required=True)
    campaign_review.add_argument("--stage", required=True)
    campaign_review.add_argument("--verdict", required=True)
    campaign_review.add_argument("--actor", required=True)
    campaign_review.add_argument("--session", required=True)
    campaign_review.add_argument("--findings", type=Path)

    campaign_commit_parser = sub.add_parser("campaign-commit")
    campaign_commit_parser.add_argument("--repo", type=Path, required=True)
    campaign_commit_parser.add_argument("--campaign-id", required=True)
    campaign_commit_parser.add_argument("--message", required=True)
    campaign_commit_parser.add_argument("--path", action="append", required=True)

    campaign_pr = sub.add_parser("campaign-open-pr")
    campaign_pr.add_argument("--repo", type=Path, required=True)
    campaign_pr.add_argument("--campaign-id", required=True)
    campaign_pr.add_argument("--title", required=True)
    campaign_pr.add_argument("--body", required=True)
    campaign_pr.add_argument("--gh-bin", default="gh")

    campaign_merge = sub.add_parser("campaign-merge")
    campaign_merge.add_argument("--repo", type=Path, required=True)
    campaign_merge.add_argument("--campaign-id", required=True)
    campaign_merge.add_argument("--gh-bin", default="gh")

    campaign_reconcile = sub.add_parser("campaign-reconcile")
    campaign_reconcile.add_argument("--repo", type=Path, required=True)
    campaign_reconcile.add_argument("--campaign-id", required=True)
    campaign_reconcile.add_argument("--gh-bin")

    campaign_plan = sub.add_parser("campaign-reconcile-plan")
    campaign_plan.add_argument("--repo", type=Path, required=True)
    campaign_plan.add_argument("--campaign-id", required=True)
    campaign_plan.add_argument("--plan", type=Path, required=True)
    campaign_plan.add_argument("--dry-run", action="store_true")


def dispatch_campaign(args: argparse.Namespace) -> int:
    repo = args.repo
    if args.command == "campaign-init":
        state = init_campaign(
            repo,
            campaign_id=args.campaign_id,
            plan_text=args.plan.read_text(encoding="utf-8"),
            integration_branch=args.integration_branch,
            release_branch=args.release_branch,
            protect_branches=list(args.protect_branch),
        )
    elif args.command == "campaign-status":
        state = load_campaign(repo, args.campaign_id)
    elif args.command == "campaign-open-sprint":
        state = open_sprint(repo, args.campaign_id, args.sprint)
    elif args.command == "campaign-bind-branch":
        engine = Engine(repo, args.run)
        engine.bind_work_branch(args.role, args.actor, args.branch)
        print(json.dumps(engine.status_view(), indent=2))
        return 0
    elif args.command == "campaign-record-review":
        findings = None
        if args.findings is not None:
            loaded = json.loads(args.findings.read_text(encoding="utf-8"))
            if not isinstance(loaded, list):
                raise WorkflowError("findings file must be a JSON list")
            findings = loaded
        state = record_review(
            repo,
            args.campaign_id,
            stage=args.stage,
            verdict=args.verdict,
            actor_id=args.actor,
            session_id=args.session,
            findings=findings,
        )
    elif args.command == "campaign-commit":
        state = campaign_commit(
            repo,
            args.campaign_id,
            message=args.message,
            paths=list(args.path),
        )
    elif args.command == "campaign-open-pr":
        state = open_pull_request(
            repo,
            args.campaign_id,
            title=args.title,
            body=args.body,
            gh_bin=args.gh_bin,
        )
    elif args.command == "campaign-merge":
        state = merge_pull_request(repo, args.campaign_id, gh_bin=args.gh_bin)
    elif args.command == "campaign-reconcile":
        state = reconcile(repo, args.campaign_id, gh_bin=args.gh_bin)
    elif args.command == "campaign-reconcile-plan":
        state = reconcile_plan(
            repo,
            args.campaign_id,
            args.plan.read_text(encoding="utf-8"),
            dry_run=bool(args.dry_run),
        )
    else:
        raise WorkflowError(f"unknown command: {args.command}")
    print(json.dumps(state, indent=2))
    return 0
