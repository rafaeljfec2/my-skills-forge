# Upstream lock

Observed sources used by this migration.

## agent-skills (Tech Leads Club catalog)

- Repository: `https://github.com/tech-leads-club/agent-skills.git`
- Observed commit: `d41f62b` (`d41f62b chore(release): publish`)
- Catalog path: `packages/skills-catalog/skills/`
- Local checkout at migration time may be ahead of the lock; copied
  skill content was taken from the local tree and provenance records
  the concrete source path. The lock pin remains `d41f62b` as the
  audited upstream reference from the migration plan.

## Local skill folders

- User Cursor skills: `/mnt/c/Users/rafae/.cursor/skills` (symlink target of `~/.cursor/skills`)
- STFlow Cursor skills: `/home/rafael/dev-rafael/connexto-stt-flow/.cursor/skills`
- STFlow Claude skills: `/home/rafael/dev-rafael/connexto-stt-flow/.claude/skills`
- FlowDeploy Cursor skills: `/home/rafael/dev-rafael/connexto-vps-deploy-paas/.cursor/skills`
- Axiom PR skill: `/home/rafael/dev-rafael/connexto-axiom-agents/core/skills/pr-creator-ado`
- Job Search skills: `/home/rafael/dev-rafael/connexto-job-search`
- SDD protocol references: `/mnt/c/Users/rafae/.cursor/rules/sdd-development-protocol-references`
