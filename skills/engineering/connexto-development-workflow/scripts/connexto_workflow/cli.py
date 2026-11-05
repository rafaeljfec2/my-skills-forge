"""Command line for one demand. The state file, not the terminal scrollback, is the checkpoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from connexto_workflow.config import load_config
from connexto_workflow.engine import Brief, Engine
from connexto_workflow.errors import WorkflowError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cdw")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-config")
    check.add_argument("--repo", type=Path, required=True)
    check.add_argument("--file", type=Path)

    init = sub.add_parser("init")
    _repo_run(init, run=False)
    init.add_argument("--demand-id", required=True)
    init.add_argument("--type", required=True)
    init.add_argument("--problem", required=True)
    init.add_argument("--outcome", required=True)
    init.add_argument("--scope", required=True)
    init.add_argument("--project", required=True)
    init.add_argument("--criterion", action="append", required=True)
    init.add_argument("--constraint", action="append", default=[])
    init.add_argument("--risk")

    status = sub.add_parser("status")
    _repo_run(status)

    transition = sub.add_parser("transition")
    _actor(transition)
    transition.add_argument("--to", required=True)
    transition.add_argument("--reason", required=True)

    put = sub.add_parser("put")
    _actor(put)
    put.add_argument("--artifact", required=True)
    put.add_argument("--file", type=Path, required=True)

    note = sub.add_parser("note")
    _actor(note)
    note.add_argument("--summary", required=True)

    hook = sub.add_parser("implement-hook")
    _actor(hook)

    dev = sub.add_parser("develop-task")
    _actor(dev)
    dev.add_argument("--session", required=True)

    develop = sub.add_parser("run-developer")
    _actor(develop)
    develop.add_argument("--session", required=True)

    report = sub.add_parser("develop-report")
    _actor(report)
    report.add_argument("--file", type=Path, required=True)

    judge = sub.add_parser("run-judge")
    _actor(judge)
    judge.add_argument("--session", required=True)

    sync = sub.add_parser("memory-sync")
    _actor(sync)

    validate = sub.add_parser("validate")
    _actor(validate)

    review = sub.add_parser("review")
    _actor(review)
    review.add_argument("--file", type=Path, required=True)

    deliver = sub.add_parser("deliver")
    _actor(deliver)
    deliver.add_argument("--file", type=Path, required=True)

    payload = sub.add_parser("memory-payload")
    _repo_run(payload)

    ack = sub.add_parser("memory-ack")
    _actor(ack)
    ack.add_argument("--page", required=True)

    skip = sub.add_parser("memory-skip")
    _actor(skip)
    skip.add_argument("--reason", required=True)

    approve = sub.add_parser("approve")
    _actor(approve)
    approve.add_argument("--action", required=True)

    protect = sub.add_parser("protect")
    _actor(protect)
    protect.add_argument("--action", required=True)

    block = sub.add_parser("block")
    _actor(block)
    block.add_argument("--dependency", required=True)

    unblock = sub.add_parser("unblock")
    _actor(unblock)

    fail = sub.add_parser("fail")
    _actor(fail)
    fail.add_argument("--detail", required=True)

    cancel = sub.add_parser("cancel")
    _actor(cancel)
    cancel.add_argument("--detail", required=True)

    commit = sub.add_parser("commit")
    _actor(commit)
    commit.add_argument("--message", required=True)
    commit.add_argument("--path", action="append", required=True)

    proof = sub.add_parser("proof")
    proof.add_argument("--dest", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        return _dispatch(args)
    except WorkflowError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "check-config":
        path = args.file or (args.repo / "connexto.project.json")
        config = load_config(path)
        print(json.dumps({"project": config.project.name, "language": config.project.language}))
        return 0
    if args.command == "proof":
        from connexto_workflow.proof import run_proof

        print(json.dumps(run_proof(args.dest), indent=2))
        return 0
    if args.command == "init":
        engine = Engine(args.repo, args.demand_id)
        engine.init_run(
            Brief(
                demand_id=args.demand_id,
                demand_type=args.type,
                problem=args.problem,
                desired_outcome=args.outcome,
                scope=args.scope,
                success_criteria=tuple(args.criterion),
                target_project=args.project,
                constraints=tuple(args.constraint),
                risk=args.risk,
            )
        )
        print(json.dumps(engine.status_view(), indent=2))
        return 0
    engine = Engine(args.repo, args.run)
    if args.command == "status":
        print(json.dumps(engine.status_view(), indent=2))
        return 0
    if args.command == "memory-payload":
        print(json.dumps(engine.memory_payload(), indent=2))
        return 0
    if args.command == "transition":
        engine.request_transition(args.to, args.role, args.actor, args.reason)
    elif args.command == "put":
        engine.put_artifact(args.role, args.actor, args.artifact, args.file.read_text(encoding="utf-8"))
    elif args.command == "note":
        engine.note_implementation(args.role, args.actor, args.summary)
    elif args.command == "develop-task":
        engine.materialize_developer_task(args.role, args.actor, args.session)
    elif args.command == "run-developer":
        engine.run_developer_backend(args.role, args.actor, args.session)
    elif args.command == "develop-report":
        payload = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowError("developer report file must be a JSON object")
        engine.submit_developer_report(args.role, args.actor, payload, args.session)
    elif args.command == "implement-hook":
        engine.run_implement_hook(args.role, args.actor)
    elif args.command == "validate":
        engine.run_validation(args.role, args.actor)
    elif args.command == "review":
        payload = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowError("review file must be a JSON object")
        engine.submit_review(args.role, args.actor, payload)
    elif args.command == "run-judge":
        engine.run_independent_judge(args.role, args.actor, args.session)
    elif args.command == "deliver":
        sections = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(sections, dict) or any(not isinstance(value, str) for value in sections.values()):
            raise WorkflowError("delivery file must be a JSON object of strings")
        engine.compose_delivery(args.role, args.actor, sections)
    elif args.command == "memory-ack":
        engine.ack_memory(args.role, args.actor, args.page)
    elif args.command == "memory-sync":
        engine.sync_memory(args.role, args.actor)
    elif args.command == "memory-skip":
        engine.skip_memory(args.role, args.actor, args.reason)
    elif args.command == "approve":
        engine.approve(args.role, args.actor, args.action)
    elif args.command == "protect":
        engine.request_protected(args.role, args.actor, args.action)
    elif args.command == "block":
        engine.block(args.role, args.actor, args.dependency)
    elif args.command == "unblock":
        engine.unblock(args.role, args.actor)
    elif args.command == "fail":
        engine.fail(args.role, args.actor, args.detail)
    elif args.command == "cancel":
        engine.cancel(args.role, args.actor, args.detail)
    elif args.command == "commit":
        engine.commit_work(args.role, args.actor, args.message, list(args.path))
    else:
        raise WorkflowError(f"unknown command: {args.command}")
    print(json.dumps(engine.status_view(), indent=2))
    return 0


def _repo_run(parser: argparse.ArgumentParser, run: bool = True) -> None:
    parser.add_argument("--repo", type=Path, required=True)
    if run:
        parser.add_argument("--run", required=True)


def _actor(parser: argparse.ArgumentParser) -> None:
    _repo_run(parser)
    parser.add_argument("--role", required=True)
    parser.add_argument("--actor", required=True)
