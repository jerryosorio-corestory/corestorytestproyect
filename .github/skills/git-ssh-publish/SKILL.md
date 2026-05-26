---
name: git-ssh-publish
description: 'Publish this repo to GitHub over SSH using the jerryosorio-corestory account. Use when configuring origin, verifying SSH access, or pushing local changes to git@github.com:jerryosorio-corestory/corestorytestproyect.git.'
argument-hint: 'Provide the branch, commit scope, and whether to verify SSH before pushing.'
user-invocable: true
---

# Git SSH Publish Workflow

Use this skill when you need to publish changes to GitHub from this workspace using SSH.

## Default Remote
- `origin` should point to `git@github.com:jerryosorio-corestory/corestorytestproyect.git`.
- Prefer SSH for fetch and push operations.

## Procedure
1. Check the current branch and remote configuration.
2. If needed, set `origin` to the SSH URL above.
3. Verify SSH access with `ssh -T git@github.com` when authentication is uncertain.
4. Review the diff and commit the intended changes.
5. Push the current branch to `origin` using SSH.
6. Confirm the push succeeded and report the branch, remote, and commit reference.

## Safety Rules
- Do not change the GitHub account unless explicitly requested.
- Do not rewrite history unless the user asks for it.
- Do not force push by default.
- Do not publish unreviewed changes.

## Output Checklist
1. Remote URL confirmed or updated.
2. SSH access verified when relevant.
3. Commit or push status reported.
4. Any blocking auth or branch issues explained clearly.
