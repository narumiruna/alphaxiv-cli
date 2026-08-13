# alphaXiv CLI Command Map

Run authenticated commands only after `alphaxiv auth status --json` succeeds.

Prefer `--json` for agent-readable output.

| User need | CLI command | Backend | Authentication | Quota | Remote effect | Primary failure handling |
| --- | --- | --- | --- | --- | --- | --- |
| Check MCP access | `alphaxiv auth status --json` | MCP initialize and tools/list | API key required | None | Read only | Stop on missing key, permission failure, or tool drift. |
| Discover papers | `alphaxiv research discover QUESTION --keyword KEYWORD --json` | `discover_papers` | API key required | Assistant | Read only | Stop on quota exhaustion and do not invent keywords. |
| Read paper content | `alphaxiv paper content PAPER --json` | `get_paper_content` | API key required | Assistant | Read only | Stop on quota exhaustion or an unsupported paper URL. |
| Read full extracted text | `alphaxiv paper content PAPER --full-text --json` | `get_paper_content` | API key required | Assistant | Read only | Stop on quota exhaustion or an unsupported paper URL. |
| Ask PDF questions | `alphaxiv paper query PAPER --query QUESTION --json` | `answer_pdf_queries` | API key required | Assistant | Read only | Batch all questions for one paper and stop on quota exhaustion. |
| Inspect linked code | `alphaxiv paper code REPOSITORY PATH --json` | `read_files_from_github_repository` | API key required | Assistant | Read only | Require an HTTPS GitHub repository and stop on inaccessible files. |
| List folders | `alphaxiv library list --json` | `list_library` | API key required | None | Read only | Stop on authentication failure and use returned folder IDs. |
| List folder papers | `alphaxiv library list --include-papers --json` | `list_library` | API key required | None | Read only | Request paper loading only when needed. |
| Save papers | `alphaxiv library save FOLDER PAPER... --yes --json` | `save_papers_to_folder` | API key required | None | Writes memberships | Require authorization for the exact folder and papers. |
| Remove papers | `alphaxiv library remove FOLDER PAPER... --yes --json` | `remove_papers_from_folder` | API key required | None | Removes memberships | Require authorization for the exact folder and papers. |
| Move papers | `alphaxiv library move SOURCE TARGET PAPER... --yes --json` | `move_papers_between_folders` | API key required | None | Moves memberships | Require authorization for both folders and every paper. |
| Create folder | `alphaxiv library folder create NAME --yes --json` | `create_folder` | API key required | None | Creates a folder | Require authorization for the exact name and optional parent. |
| Rename folder | `alphaxiv library folder rename FOLDER NAME --yes --json` | `rename_folder` | API key required | None | Renames a folder | Require authorization for the exact folder ID and new name. |
| Delete folder | `alphaxiv library folder delete FOLDER --yes --json` | `delete_folder` | API key required | None | Deletes folder memberships | Require destructive authorization for the exact folder ID. |

Never use `--yes` until the user has authorized the exact write described in the final command.

Stop rather than retry when the response reports a missing key, `403`, tool drift, quota exhaustion, or an unknown tool.
