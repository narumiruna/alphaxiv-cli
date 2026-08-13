# alphaXiv MCP CLI 與 Agent Skill 實作計畫

## 目標

在靜態 REST CLI 基礎上，以 Python、Typer、官方 MCP Python SDK 與 `pydantic.BaseModel` 實作 alphaXiv 研究及個人書庫命令。

在 `skills/using-alphaxiv-cli/` 建立 Agent Skill，讓 Agent 能選擇正確命令、優先使用 JSON 輸出，並在任何遠端寫入前取得具體授權。

所有 MCP tool 名稱與參數模型都以靜態 Python 程式碼定義，不在執行期動態暴露或呼叫任意 tool。

## 背景

本計畫依賴 `docs/plans/archived/2026-08-13_alphaxiv-rest-cli-plan.md` 完成的 CLI、Pydantic、輸出、錯誤與測試基礎。

官方 MCP 端點是 `https://api.alphaxiv.org/mcp/v1`，並接受 `ALPHAXIV_API_KEY` Bearer 驗證。

實測已確認 `initialize`、`tools/list` 與唯讀 `list_library` 可使用 API Key。

研究工具會消耗 Assistant 配額，個人書庫工具可能修改遠端資料，因此測試與 Skill 都需要明確的安全邊界。

## 假設

REST CLI 計畫已完成且品質檢查通過後，才開始執行本計畫。

第一階段只支援 `ALPHAXIV_API_KEY`，不支援互動式 OAuth 或瀏覽器 Cookie。

Skill 以原始碼形式放在 `skills/`，不在本階段實作自動安裝至其他 Agent 框架。

## 架構

```text
src/alphaxiv/
├── commands/
│   ├── auth.py
│   ├── library.py
│   └── research.py
├── clients/
│   └── mcp.py
├── contracts/
│   └── mcp.py
└── models/
    ├── library.py
    └── mcp.py

skills/using-alphaxiv-cli/
├── SKILL.md
└── references/
    ├── command-map.md
    └── workflows.md
```

`McpClient` 集中處理 Streamable HTTP 工作階段、Bearer Header、協定錯誤與文字內容解析。

`src/alphaxiv/contracts/mcp.py` 以 Enum、Literal 與不可變 Pydantic model 靜態定義允許的 11 個官方 tool。

每個公開 client method 對應一個固定 tool name 與固定 `BaseModel` arguments。

內部可以共用私有 `_call_tool()`，但套件與 CLI 不提供接受任意 tool name 或任意 arguments 的公開入口。

研究工具回傳無結構文字時，使用 `McpTextResult` 保存文字、錯誤狀態及必要中繼資料，不假裝能解析不存在的穩定 schema。

個人書庫 JSON 回傳以寬鬆外部模型解析，但 CLI 的穩定輸出以嚴格模型重新封裝。

## 驗證與安全

CLI 只從 `ALPHAXIV_API_KEY` 環境變數讀取金鑰。

CLI 不接受 `--api-key`，也不輸出完整金鑰、原始 Header 或 MCP 驗證回應。

`auth status` 只回報環境變數是否存在、MCP 是否可初始化，以及官方 tool 清單是否符合靜態契約。

研究命令會消耗配額，因此 Help、離線測試與預設品質檢查不得呼叫真實研究 tool。

個人書庫的 save、remove、move、create、rename 與 delete 都需要 `--yes`。

提供 `--yes` 只代表略過 CLI 二次提示，不代表 Agent 已取得授權。

Agent Skill 必須先取得使用者對具體 tool、資料夾與論文的明確授權，才能執行帶有 `--yes` 的命令。

## MCP 命令

| 命令 | 靜態 MCP tool | 遠端影響 |
| --- | --- | --- |
| `alphaxiv auth status` | `initialize`、`tools/list` | 唯讀。 |
| `alphaxiv research discover QUESTION --keyword KEYWORD` | `discover_papers` | 唯讀，但消耗 Assistant 配額。 |
| `alphaxiv paper content PAPER [--full-text]` | `get_paper_content` | 唯讀，但可能消耗 Assistant 配額。 |
| `alphaxiv paper query PAPER --query QUESTION` | `answer_pdf_queries` | 唯讀，但消耗 Assistant 配額。 |
| `alphaxiv paper code REPOSITORY PATH` | `read_files_from_github_repository` | 唯讀，但消耗 Assistant 配額。 |
| `alphaxiv library list` | `list_library` | 唯讀。 |
| `alphaxiv library save FOLDER PAPER... --yes` | `save_papers_to_folder` | 寫入個人書庫。 |
| `alphaxiv library remove FOLDER PAPER... --yes` | `remove_papers_from_folder` | 寫入個人書庫。 |
| `alphaxiv library move SOURCE TARGET PAPER... --yes` | `move_papers_between_folders` | 寫入個人書庫。 |
| `alphaxiv library folder create NAME --yes` | `create_folder` | 建立遠端資料夾。 |
| `alphaxiv library folder rename FOLDER NAME --yes` | `rename_folder` | 修改遠端資料夾。 |
| `alphaxiv library folder delete FOLDER --yes` | `delete_folder` | 刪除資料夾及其中的成員關係。 |

`discover_papers` 的 keywords、question、difficulty、日期與排序使用明確 options 和 Pydantic 驗證，不由 CLI 自行猜測或擴寫。

`answer_pdf_queries` 支援重複 `--query`，並一次送出同一篇論文的所有問題。

`library list` 預設不載入資料夾內論文，只有明確 `--include-papers` 才要求額外內容。

所有讀取命令提供 `--json`，所有寫入命令提供可供 Agent 判讀的穩定結果封套。

## Agent Skill

Skill 名稱為 `using-alphaxiv-cli`。

`SKILL.md` frontmatter 的 `name` 必須和目錄名稱完全一致。

`description` 必須涵蓋使用 alphaXiv CLI 進行論文發現、閱讀、PDF 問答、程式碼探索及個人書庫管理的觸發情境。

`SKILL.md` 只放共通工作流程、驗證方式、JSON 輸出偏好、配額提醒、寫入授權與停止條件。

`references/command-map.md` 記錄使用者需求、CLI 命令、後端、驗證需求、配額、遠端影響及主要失敗處理。

`references/workflows.md` 記錄文獻回顧、單篇論文研究、PDF 證據擷取、程式碼查核及個人書庫整理流程。

Skill 只能使用正式 CLI 命令，不能直接呼叫 MCP endpoint、REST endpoint 或未公開的 Python client 方法。

Skill 遇到缺少 API Key、配額不足、`403`、未知 tool、使用者未授權寫入或破壞性目標不明確時必須停止並回報。

Skill 文件遵守一句一行，且不重複 `docs/research/alphaxiv-api.md` 的背景研究。

## 非目標

- 不實作 Assistant REST、帳號、帳務、通知或管理 API。
- 不提供任意 MCP tool name、任意 JSON arguments 或通用 MCP proxy 命令。
- 不在一般測試中消耗 Assistant 配額或修改真實個人書庫。
- 不支援瀏覽器 Cookie、互動式 OAuth 或遠端 API Key 管理。
- 不實作 Skill 自動安裝、發布或套件登錄。
- 不發布 PyPI 套件。

## 風險

- 官方 MCP tool schema 可能變更，因此靜態契約需要 `tools/list` drift check。
- MCP 研究結果可能是大型文字，因此輸出層要支援 stdout 串流或明確檔案輸出，而不能截斷 JSON。
- 研究 tool 會消耗配額，因此 live test 必須另外 opt in。
- 資料夾刪除會移除成員關係，因此 CLI 和 Skill 都要顯示具體目標並要求確認。
- API Key 只應送往生產 MCP endpoint，因此 client 不接受任意 base URL。

## 計畫

- [x] 重新檢查已封存 REST CLI 計畫與目前 CLI registry；完成清單無未勾選項目，根 Help 顯示 5 個既有 app，`uv run --python 3.12 pytest tests/test_cli.py tests/test_cli_commands.py -q` 以 45 個案例通過，且 lock、Ruff 與 ty 均通過。
- [x] 先以 `tests/clients/test_mcp.py` 定義缺少金鑰、固定 Bearer Header、初始化、工作階段清理、`tools/list`、工具錯誤及文字內容解析；focused run 在收集時因 `alphaxiv.clients.mcp` 尚不存在而失敗，確認 production boundary 的預期 red state。
- [x] 使用 `uv add mcp` 更新 `pyproject.toml` 與 `uv.lock`；`uv tree --depth 1` 確認官方 `mcp` 2.0.0 為可重現的直接依賴，既有 HTTPX、Pydantic 與 Typer 仍是直接依賴。
- [x] 在 `src/alphaxiv/contracts/mcp.py` 以不可變 `BaseModel`、Enum 與固定 mapping 定義 11 個允許 tool、6 個寫入分類、4 個配額分類及各自 arguments model；`tests/test_mcp_contracts.py` 確認完整 surface 且 public client 沒有任意 tool、request 或 endpoint 入口。
- [x] 在 `src/alphaxiv/models/mcp.py` 與 `library.py` 建立有界研究輸入、文字結果、寬鬆遠端資料夾與論文成員關係，以及嚴格穩定輸出模型；`tests/test_mcp_models.py` 驗證 alias、日期、必要欄位、遠端上限、未知欄位策略、JSON 與敏感欄位排除。
- [x] 以可注入假 session 完成 async `McpClient` lifecycle、`initialize`、`list_tools`、四個研究方法及七個個人書庫方法，production transport 接上官方 MCP SDK 2.0.0、固定 HTTPS endpoint、不跟隨 redirect 的 Bearer client 與固定 HEAD auth preflight；15 個 focused client tests 證明每個公開方法只 dispatch 一個固定 tool、failure 時清理 lifecycle、plain-text write result 不造成誤判重試，且巢狀敏感欄位會移除。
- [x] 在 `check_mcp_tools()` 建立純報告式 `tools/list` drift check，比較 11 個遠端名稱、必要 arguments 與完整 argument names；3 個離線案例涵蓋 missing、unknown 與 schema drift，匿名值不輸出的實際 API Key 連線亦回報 11 tools compatible，且 registry 維持不可變。
- [x] 在 `src/alphaxiv/commands/auth.py` 實作 `auth status` 並註冊根 app；5 個 CLI tests 確認 Help 不需金鑰、缺少金鑰為 input error、驗證失敗為 permission error、drift 有獨立 code、成功回傳穩定狀態，所有輸出均不含金鑰值。
- [x] 在 `src/alphaxiv/commands/research.py` 與現有 paper app 實作 discover、content、query 與 code；10 個 `CliRunner`/假 client tests 驗證離線 Help、Pydantic 日期與 URL 輸入、重複 keyword/query、ID 正規化、單次固定 dispatch、完整文字、JSON 及穩定配額錯誤。
- [x] 在 `src/alphaxiv/commands/library.py` 實作預設不載入 papers 的 list，以及 save、remove、move、folder create、rename、delete；20 個 CLI tests 證明 7 個 Help 離線、6 個 write 缺少 `--yes` 時零 client call，確認後只初始化並呼叫一次預期固定方法與 Pydantic arguments。
- [x] 建立 `tests/e2e/test_live_mcp_readonly.py`，只有同時設定 `ALPHAXIV_LIVE=1` 與 `ALPHAXIV_API_KEY` 才執行 initialize、tools/list 與預設不載入 papers 的 `library list`；default run skipped，明確 readonly opt-in run 以 1 個案例通過且不呼叫研究 tool。
- [x] 建立獨立 `tests/e2e/test_live_mcp_research.py`，只有 `ALPHAXIV_LIVE_RESEARCH=1` 與金鑰同時存在才執行一個已知論文 content 案例，並先輸出配額警告；預設驗證確認案例 skipped，本次未在缺少明確配額 opt-in 時消耗 Assistant quota。
- [x] 建立 `skills/using-alphaxiv-cli/SKILL.md`、command map 與 5 類 workflows；內容只使用正式 CLI，偏好 JSON，逐項記錄驗證、Assistant 配額、讀寫分類、具體寫入授權、`--yes`、delete memberships 警告及缺 key、403、drift、quota、unknown tool 停止條件。
- [x] 在 `tests/test_skill.py` 以 5 個案例驗證目錄/frontmatter 名稱、description、必要 references、相對連結、一句一行、CLI-only 安全詞與 command map 中所有命令均存在於實際 Typer registry。
- [x] 更新 `README.md` 與 `docs/research/alphaxiv-api.md`，記錄 environment-only API Key、固定 MCP 命令、配額、`--json`、具體遠端寫入確認、live opt-ins 與 source Skill；實際執行 auth/library/research Help 及 readonly `auth status --json`，未消耗研究配額或寫入遠端。
- [x] 在 Python 3.12 執行 lock check、Ruff lint/format、ty 及完整 coverage suite；最終為 170 passed、4 個 opt-in live tests skipped，並另以 3 個 readonly REST/MCP live tests 通過，且 hardening regression 涵蓋 control inputs、auth status、plain-text write result、nested secret redaction 與 session lifecycle。
- [x] 使用 `uv build --no-sources` 建立 43 KB wheel 與 30 KB sdist，內容清單不含 `.env`、tests/e2e、fixtures、coverage 或 live response；從新路徑 wheel 建立隔離 uv 環境後，`auth status --help` 與 `library list --help` 均通過。

## 完成檢查

- [x] MCP endpoint、11 個 tool name 與各自 arguments 都由靜態程式碼決定，CLI 與 public client 不提供任意 MCP 呼叫入口。
- [x] 所有跨越 commands、MCP client 與 output 邊界的正式輸入、狀態、文字、書庫與 mutation 資料都由 `pydantic.BaseModel` 驗證。
- [x] `tools/list` drift check 只建立嚴格 report，不動態註冊 tool 或產生 request 程式碼，且 live check 與 11 tools 相容。
- [x] 一般測試與預設 live test 不消耗 Assistant 研究配額，也不修改遠端個人書庫；research live test 維持獨立雙條件 opt-in。
- [x] 6 個個人書庫寫入命令在缺少 `--yes` 時都於建立 client 前失敗，參數化測試證明 MCP call count 為零。
- [x] Skill 對每個遠端寫入都要求使用者針對具體 command、folder 與 papers 明確授權，delete 另提示 memberships 影響。
- [x] `skills/using-alphaxiv-cli/SKILL.md` 的 trigger、正式命令、references、JSON 偏好、配額與停止條件均由 5 個 skill tests 與實際 CLI registry 核對。
- [x] Python 3.12 的 lock、lint、format、型別檢查、170 個預設 tests、3 個 readonly live tests 與 build 全部通過。
- [x] wheel、sdist、Git diff 與測試輸出掃描均不包含 `.env`、真實 API Key、Cookie 值、MCP 驗證回應或個人 alphaXiv 資料。
- [x] `README.md` 與 `docs/research/alphaxiv-api.md` 已反映最終 MCP、REST、驗證、配額、寫入確認與 Skill 邊界。
