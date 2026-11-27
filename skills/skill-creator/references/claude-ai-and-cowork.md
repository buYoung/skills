# Claude.ai and Cowork

The core workflow is the same in Claude.ai and Cowork (draft → test → review → improve → repeat). What changes is which mechanics the environment supports.

Claude.ai is merging chat and Cowork into one conversation, and the change is rolling out in stages, so two accounts can see different capabilities. Cowork describes sub-agent coordination as Claude splitting its own work into parallel tasks. Baseline runs and blind comparison need something narrower: a separate agent whose prompt and context you control, which doesn't see the conversation you used to write the skill. Check whether you can start one. If you can, follow the main workflow in SKILL.md. If you can't, use the fallbacks below.

Cowork sessions don't read `~/.claude/skills/` on the user's machine. They load the skills enabled for the user's claude.ai account, synced at session start. A skill you edit inside a session is therefore not the copy Claude.ai or Cowork loads until the user enables the new version for their account; in Claude.ai, skills also need code execution turned on (in Settings > Capabilities on Free, Pro, Max, and Ultra plans; by the organization's owner on Team and Enterprise).

## Without independent agents

**Post-draft refinement**: Follow the "independent agents are unavailable" rule in [post-draft-refinement.md](post-draft-refinement.md). Don't present candidates you wrote one after another as independent.

**Running test cases**: For each test case, read the skill's SKILL.md, then follow its instructions to accomplish the test prompt yourself. Do them one at a time. This is less rigorous than independent agents (you wrote the skill and you're also running it, so you have full context), but it's a useful sanity check — and the human review step compensates. Skip the baseline runs — just use the skill to complete the task as requested.

**Benchmarking**: Skip the quantitative benchmarking — it relies on baseline comparisons, which aren't meaningful without independent runs. Focus on qualitative feedback from the user.

**Blind comparison**: Requires independent agents. Skip it.

**The iteration loop**: Same as before — improve the skill, rerun the test cases, ask for feedback. You can still organize results into iteration directories on the filesystem if you have one.

## Reviewing results

If the user can't open a viewer served from your environment (for example, your session runs on a remote server), don't start the server. Write a standalone file with `generate_review.py <workspace>/iteration-N --static <output_path>` and tell the user where it is, or present results directly in the conversation: for each test case, show the prompt and the output. If the output is a file the user needs to see (like a .docx or .xlsx), save it to the filesystem and tell them where it is so they can download and inspect it. Ask for feedback inline: "How does this look? Anything you'd change?"

With a static viewer, the "Submit All Reviews" button downloads `feedback.json` instead of saving it to the workspace. Read it from where it was downloaded (you may have to request access first) and copy it into the workspace for the next iteration.

## Description optimization

`run_loop.py` and `run_eval.py` call `claude -p`, a Claude Code CLI command, in a subprocess. They work only where the `claude` command is installed and signed in. Check with `claude auth status` before offering this step (it exits with 0 when signed in and 1 when not), and skip the step if the command isn't there or isn't signed in. Even when it is, save it until you've fully finished making the skill and the user agrees it's in good shape.

## Packaging

`package_skill.py` needs Python, PyYAML (for `quick_validate.py`), and a filesystem. You can run it and the user can download the resulting `.skill` file, a ZIP archive of the skill folder. Claude.ai's skill upload under Customize > Skills takes a ZIP of the skill folder.

## Updating an existing skill

The user might be asking you to update an existing skill, not create a new one. In this case:
- **Preserve the original name.** Note the skill's directory name and `name` frontmatter field -- use them unchanged. E.g., if the installed skill is `research-helper`, output `research-helper.skill` (not `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the output directory -- direct writes may fail due to permissions.

## Cowork

- If you can start independent agents, the main workflow (spawn test cases in parallel, run baselines, grade, etc.) works. If you run into severe problems with timeouts, it's OK to run the test prompts in series rather than parallel.
- Cowork runs the session in the cloud, on Anthropic's servers. Claude Desktop has a built-in browser for Claude's web tasks, but a viewer server started inside the session listens on the session's own `localhost`, which the user's browser may not reach. Generate the viewer with `--static <output_path>` and give the user the file, as described in "Reviewing results" above.
- For whatever reason, the Cowork setup seems to disincline Claude from generating the eval viewer after running the tests, so just to reiterate: whether you're in Cowork or in Claude Code, after running tests, you should always generate the eval viewer for the human to look at examples before revising the skill yourself and trying to make corrections, using `generate_review.py` (not writing your own boutique html code). Sorry in advance but I'm gonna go all caps here: GENERATE THE EVAL VIEWER *BEFORE* evaluating inputs yourself. You want to get them in front of the human ASAP!
