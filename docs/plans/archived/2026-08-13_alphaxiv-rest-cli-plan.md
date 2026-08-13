# alphaXiv 靜態 OpenAPI REST CLI 實作計畫

## 目標

以 Python、Typer、HTTPX 與 `pydantic.BaseModel` 實作 `alphaxiv` CLI 的基礎與唯讀 REST 功能。

`https://api-dev.alphaxiv.org/api.json` 作為開發期契約來源，但所有正式 request 都以人工審核的靜態 Python 方法實作。

正式 CLI 不在執行期下載 OpenAPI、不動態產生 request，也不接受任意 HTTP method、URL 或 path。

## 背景

目前 `src/alphaxiv/cli.py` 只有 Typer Hello World，測試也只有佔位案例。

`pyproject.toml` 已依賴 Typer，但尚未依賴 Pydantic 或 HTTPX。

API 研究與實測結果位於 `docs/research/alphaxiv-api.md`。

實測顯示多個公開 REST 端點應匿名呼叫，加入 `Authorization` 後反而會回傳 `403`。

本計畫先完成穩定的 CLI、模型、輸出、錯誤與靜態 REST 邊界，後續 MCP 與 Skill 由 `docs/plans/2026-08-13_alphaxiv-mcp-skill-plan.md` 接續。

## 架構

```text
src/alphaxiv/
├── cli.py
├── commands/
│   ├── events.py
│   ├── feed.py
│   ├── paper.py
│   ├── researchers.py
│   └── search.py
├── clients/
│   └── public_rest.py
├── contracts/
│   └── rest.py
├── models/
│   ├── common.py
│   ├── events.py
│   ├── feed.py
│   ├── paper.py
│   ├── researchers.py
│   └── search.py
├── errors.py
└── output.py

scripts/
└── check_openapi_contract.py

tests/
├── clients/
├── fixtures/
│   ├── api/
│   └── openapi/alphaxiv-rest-subset.json
└── test_cli.py
```

`PublicRestClient` 永遠不加入 `Authorization`、Cookie 或其他登入資訊。

每個公開 client method 對應一個固定 HTTP method、固定 path template，以及固定的 Pydantic 輸入與輸出模型。

內部可以共用私有 `_request()`，但套件不得公開可接受任意 method、URL 或 path 的 request 方法。

設定、參數、API 回應、穩定 JSON 輸出及錯誤封套都以 `pydantic.BaseModel` 定義。

外部 API 回應模型允許未知欄位，以容忍 alphaXiv 增加欄位。

CLI 輸入與本專案輸出模型禁止未知欄位，以維持明確合約。

## OpenAPI 策略

開發 OpenAPI 只用來確認路徑、HTTP 方法、參數名稱、必要性與回應 schema。

`src/alphaxiv/contracts/rest.py` 以不可變的 Pydantic model 實例記錄經審核端點的 method、path template、驗證模式、必要參數與用途。

第一階段靜態實作下列唯讀端點。

| 群組 | 端點 |
| --- | --- |
| 搜尋 | `/search/v2/paper/fast`、`/search/v2/paper/full-text`、`/v1/search/paper`、`/v1/search/closest-topic` |
| 組織 | `/organizations/v2/search`、`/organizations/v2/top` |
| 研究者 | `/researchers/v1`、`/researchers/v1/search` |
| 活動 | `/events/v1` |
| 論文動態 | `/papers/v3/feed`、`/papers/v3/icml-topics` |
| 論文核心 | `/papers/v3/legacy/{unresolved}`、`/papers/v3/{unresolved}`、`/papers/v3/{id}/preview` |
| 論文內容 | `/papers/v3/{paperVersion}/full-text`、`/papers/v3/{paperVersion}/overview/{language}`、`/papers/v3/{paperVersion}/overview/status` |
| 論文留言與相似項目 | `/papers/v3/legacy/{group}/comments`、`/papers/v3/{id}/similar-papers` |
| 論文群組關聯 | `/papers/v3/{unresolved}/metrics`、`/papers/v3/{paperGroupId}/figures`、`/papers/v3/{paperGroupId}/extras`、`/papers/v3/{paperGroupId}/implementations`、`/papers/v3/{paperGroupId}/autoresearch-implementations` |
| 論文版本分析 | `/papers/v3/{paperVersion}/ai-detection`、`/papers/v3/{paperVersion}/model-links` |

需要 paper group、paper version 或 universal ID 的方法先以論文核心回應建立 `ResolvedPaperIdentifiers`，再把具體型別的識別碼交給固定方法。

完整 OpenAPI 不提交至儲存庫。

測試 fixture 只保留白名單操作的最小 schema，並移除內部原始檔路徑與無關 component。

`scripts/check_openapi_contract.py` 只下載 schema 並報告 method、path、必要參數與 schema reference 的 drift。

該腳本不得產生或覆寫 Python 原始碼，也不得呼叫 schema 內描述的 API 操作。

OpenAPI drift check 必須由明確命令啟動，不能在一般 CLI 啟動或離線單元測試中自動連線。

## CLI 命令

| 命令 | 固定後端行為 |
| --- | --- |
| `alphaxiv search papers QUERY` | 快速搜尋公開論文。 |
| `alphaxiv search full-text QUERY` | 搜尋論文全文。 |
| `alphaxiv search topics QUERY` | 取得最接近的主題。 |
| `alphaxiv search organizations QUERY` | 搜尋組織。 |
| `alphaxiv researchers list` | 列出受限數量的研究者。 |
| `alphaxiv researchers search QUERY` | 搜尋研究者。 |
| `alphaxiv events list` | 列出活動。 |
| `alphaxiv feed list` | 依排序、期間與限制取得論文動態。 |
| `alphaxiv feed topics` | 列出 ICML 主題群組。 |
| `alphaxiv paper show ID` | 解析並顯示論文中繼資料。 |
| `alphaxiv paper preview ID` | 顯示精簡論文資料。 |
| `alphaxiv paper text ID` | 取得已存在的完整文字。 |
| `alphaxiv paper overview ID` | 取得已存在的 overview 或狀態，不觸發生成。 |
| `alphaxiv paper related ID --kind KIND` | 取得一種明確列舉的關聯資料。 |

搜尋、清單、動態與相似論文命令都要有保守預設上限與硬性最大上限。

`paper related --kind` 使用靜態 Enum，不接受任意 path。

所有唯讀命令提供 `--json`，並由 Pydantic model 產生穩定 JSON。

人類輸出使用 Typer/Rich，stdout 只放結果，stderr 只放診斷與錯誤。

## 非目標

- 不實作 MCP、Agent Skill 或個人書庫寫入。
- 不實作受驗證帳號、Assistant、帳務、通知、偏好設定或管理端點。
- 不實作 OpenAPI code generation 或執行期 schema 解析。
- 不實作任意 request、全站抓取、語料庫鏡像或無上限匯出。
- 不實作會觸發 overview 生成、翻譯、索引或其他遠端工作的端點。
- 不發布 PyPI 套件。

## 風險

- REST 沒有穩定性承諾，因此模型必須容忍新增欄位，並以 drift check 監控必要契約。
- 相同識別碼在 group、version 與 legacy 路由的意義不同，因此解析結果要以明確 Pydantic model 保存各類 ID。
- 部分成功回應可能很大，因此 CLI 要限制清單數量，並避免在預設人類輸出中完整傾印全文。
- 開發 schema 可能與生產部署不同，因此 drift 只作提示，不能自動修改正式契約。

## 計畫

- [x] 在 `tests/test_cli.py` 先定義根命令、REST 子命令、`--help`、`--json`、stdout、stderr 與 exit code 合約；`uv run --python 3.12 pytest tests/test_cli.py -q` 以 4 個缺少命令的失敗確認 red state。
- [x] 使用 `uv add pydantic httpx` 加入直接依賴並更新 `pyproject.toml` 與 `uv.lock`；`uv tree --depth 1` 確認 Typer 0.27.1、Pydantic 2.13.4 與 HTTPX 0.28.1 為直接依賴。
- [x] 在 `src/alphaxiv/models/` 建立 `BaseModel` 設定、搜尋、組織、研究者、活動、動態、論文與錯誤模型；`uv run --python 3.12 pytest tests/test_models.py -q` 以 5 個案例驗證 alias、未知欄位策略、必要欄位、固定主機及 JSON 序列化。
- [x] 在 `src/alphaxiv/errors.py` 與 `src/alphaxiv/output.py` 實作輸入錯誤、找不到資源、速率限制、遠端錯誤、網路錯誤、exit code、Rich 輸出與 JSON 封套；`uv run --python 3.12 pytest tests/test_output.py -q` 以 9 個案例確認錯誤映射、訊息清理、stdout/stderr 與無 traceback。
- [x] 從 `api-dev.alphaxiv.org/api.json` 擷取 26 個白名單操作至 `tests/fixtures/openapi/alphaxiv-rest-subset.json`；`jq empty` 通過，且內容掃描確認不含管理、寫入、批次、資料匯入、內部原始檔路徑或無關 schema。
- [x] 在 `src/alphaxiv/contracts/rest.py` 以不可變 `BaseModel` 契約靜態定義 26 個白名單 endpoint；`uv run --python 3.12 pytest tests/test_rest_contracts.py -q` 以 4 個案例確認 GET-only、固定生產主機、匿名模式、placeholder 與最小 OpenAPI fixture 一致。
- [x] 先在 `tests/clients/test_public_rest.py` 以 `httpx.MockTransport` 建立 red state，再實作 header、query encoding、逾時、狀態碼、20 MiB 回應上限與回應驗證；測試證明連續 request 都沒有 `Authorization` 或 Cookie，且拒絕含敏感預設 Header 的注入 client。
- [x] 依搜尋、組織、研究者、活動、動態、論文核心、論文內容與論文關聯群組加入 26 個固定 client method 與最小 API fixture；離線 client suite 涵蓋所有固定路由及共用成功與錯誤路徑，另以匿名唯讀探測確認 26 個方法皆能解析生產回應。
- [x] 建立固定下載 URL、5 MiB 上限且只報告 drift 的 `scripts/check_openapi_contract.py`；4 個離線案例驗證缺少路由、新增必要參數與回應 schema drift，線上執行確認 26 個靜態 endpoint 全部相容。
- [x] 將 `src/alphaxiv/cli.py` 改為只負責根 Typer app、`--debug` 與子 app 註冊，並在 `src/alphaxiv/commands/` 實作 14 個固定 REST 命令；`uv run --python 3.12 pytest tests/test_cli.py tests/test_cli_commands.py -q` 以 42 個案例驗證 Help、人類輸出、JSON、靜態 related dispatch、識別碼解析及上限檢查。
- [x] 建立 `tests/e2e/test_live_rest_readonly.py`，未 opt in 時 2 案例略過，`ALPHAXIV_LIVE=1 uv run --python 3.12 pytest tests/e2e/test_live_rest_readonly.py -q` 以 2 個匿名唯讀案例通過；線上測試發現並修正 gzip 回應被重複解碼的 lifecycle 錯誤，且加入回歸測試。
- [x] 更新 `README.md` 與套件描述，記錄 uv 安裝、靜態 REST 命令、JSON 模式、匿名驗證語意、上限、live tests 與 OpenAPI drift check；實際執行 `--help`、有限搜尋及動態 JSON 範例，並修正 Rich 換行破壞長 JSON 的問題及加入回歸測試。
- [x] 在 Python 3.12 執行 `uv lock --check`、Ruff lint/format、`ty check` 及完整 coverage 測試；最終結果為 104 passed、2 個需 opt in 的 live tests skipped，所有靜態檢查通過。
- [x] 使用 `uv build --no-sources` 建立 wheel 與 sdist，內容清單確認不含 `.env`、完整 OpenAPI、API fixture、coverage 或暫存檔；在全新隔離 uv 環境從 wheel 執行 `alphaxiv --help` 與有限匿名搜尋均通過。

## 完成檢查

- [x] 所有跨越 commands、clients 與 output 邊界的正式資料都由 `pydantic.BaseModel` 驗證；raw JSON 只存在於私有傳輸與立即驗證路徑。
- [x] 每個 REST 功能都有固定 client method、靜態契約、Pydantic 輸入輸出模型、離線 fixture 測試及匿名生產解析證據。
- [x] 正式 CLI 不下載 OpenAPI、不動態產生 request，也不提供任意 method、URL、path 或 MCP tool 入口。
- [x] 所有 REST request 都不含 `Authorization`、Cookie 或其他登入資訊；連續 cookie、敏感注入 client 與 redirect client 都有拒絕測試。
- [x] OpenAPI drift checker 只報告差異，不產生程式碼，也不呼叫規格中的 API 操作；遠端 26 個 endpoint 檢查通過。
- [x] 所有清單與大型資料命令都有預設上限、最大上限、20 MiB 傳輸上限或預設摘要輸出及相應測試。
- [x] Python 3.12 的 lock、lint、format、型別檢查、104 個離線測試、2 個 live tests 與 build 全部通過。
- [x] wheel、sdist、Git diff 與測試輸出均不包含 `.env`、API Key、Cookie、完整內部 OpenAPI 或個人 alphaXiv 資料。
- [x] `docs/research/alphaxiv-api.md` 已記錄 26 個靜態匿名 REST endpoint 與 drift checker 邊界。
