# alphaXiv 公開與受驗證 API 研究

- 研究日期：2026-08-13
- 目標：確認 alphaXiv 是否提供公開 API、受驗證 API，以及哪些介面適合本專案使用。
- 結論可信度：官方 MCP 介面為高；REST 介面的可用性為高，但其穩定性與允許用途僅為中等。

## 摘要

alphaXiv 正式提供一套有文件的 MCP API。

官方 MCP 端點是 `https://api.alphaxiv.org/mcp/v1`，支援 OAuth 2.1 與 API Key Bearer 驗證。

alphaXiv 也在 `https://api.alphaxiv.org` 提供 JSON REST API。

部分 REST 讀取端點不需要驗證，另一些使用者、個人書庫、資料夾及助理端點則需要登入工作階段或 API Key。

目前沒有找到獨立的「私人 API 產品」或合作夥伴 API。

所謂私人 API 實際上是同一個 REST 主機下，只有通過驗證的帳號才能存取的路由。

登入後的 `Settings → MCP/API` 頁面明確允許使用 API Key 存取使用者的個人書庫與論文。

生產環境沒有公開的 REST OpenAPI 文件，但 alphaXiv 的開發環境公開了一份包含內部與管理端點的 OpenAPI 規格。

因此，本專案應優先採用官方 MCP API，並只在 MCP 無法滿足需求時使用少量、經驗證的 REST 端點。

## 名詞定義

本文件使用以下分類，避免混淆「公開」與「私人」的意思。

| 分類 | 定義 |
| --- | --- |
| 官方公開介面 | alphaXiv 主動提供文件，並預期第三方程式使用的介面。 |
| 無驗證 REST | 不提供 Cookie 或 Bearer Token 仍可取得成功回應的 REST 端點。 |
| 受驗證 REST | 必須以 API Key 或登入工作階段存取的 REST 端點。 |
| Web 內部 REST | alphaXiv 網站前端使用，但沒有消費者文件或穩定性承諾的端點。 |
| 管理端點 | OpenAPI 中出現的 admin、批次工作、資料匯入、指標或維運端點。 |

## 研究方法

本次研究採用以下方法。

1. 檢查 alphaXiv 官方網站、MCP 文件、設定頁面、服務條款及公開問題追蹤器。
2. 在已登入的瀏覽器工作階段中觀察網站實際發出的網路請求。
3. 在不攜帶驗證資料的情況下，直接探測只讀 REST 端點的 HTTP 狀態。
4. 探測常見的 OpenAPI、Swagger、Redoc 與 API 文件路徑。
5. 下載並分析 `api-dev.alphaxiv.org` 公開的 OpenAPI 規格。
6. 檢查第三方 SDK，作為端點發現與實作風險的輔助證據。

本次研究沒有建立或刪除 API Key，也沒有執行遠端寫入操作。

## 官方 MCP API

### 基本資料

| 項目 | 值 |
| --- | --- |
| 文件 | `https://www.alphaxiv.org/docs/mcp` |
| 端點 | `https://api.alphaxiv.org/mcp/v1` |
| 協定 | Model Context Protocol v1.0.0 |
| 傳輸 | Streamable HTTP |
| 請求 | `POST` |
| 伺服器事件串流 | `GET` |
| 結束工作階段 | `DELETE` |
| 互動式驗證 | OAuth 2.1 |
| 非互動式驗證 | `Authorization: Bearer <key>` |

OAuth 模式會讓相容的 MCP 用戶端開啟瀏覽器完成登入，之後由用戶端處理 Token 更新。

非互動式腳本、CI 或無頭代理程式可以在 `Settings → MCP/API` 建立 API Key。

### 官方工具

官方文件列出 11 個 MCP 工具。

#### 研究工具

| 工具 | 用途 |
| --- | --- |
| `discover_papers` | 以關鍵字和語意問題發現及排序論文。 |
| `get_paper_content` | 取得 AI 中間報告或完整論文文字。 |
| `answer_pdf_queries` | 從 PDF 取出與問題相關的頁面內容。 |
| `read_files_from_github_repository` | 讀取論文所連結 GitHub 儲存庫的檔案。 |

這些研究工具會呼叫 alphaXiv 的 AI 模型，並計入 Assistant 配額。

#### 個人書庫工具

| 工具 | 用途 |
| --- | --- |
| `list_library` | 列出資料夾及其論文。 |
| `save_papers_to_folder` | 將論文加入資料夾。 |
| `remove_papers_from_folder` | 從資料夾移除論文。 |
| `move_papers_between_folders` | 在資料夾間移動論文。 |
| `create_folder` | 建立自訂資料夾。 |
| `rename_folder` | 重新命名自訂資料夾。 |
| `delete_folder` | 刪除資料夾及其中的成員關係。 |

### MCP 限制

官方文件說明瀏覽器內直接使用的 MCP 整合不受支援，因為 CORS 只允許第一方來源。

Claude Code、Claude Desktop、Cursor、VS Code、Zed，以及透過 `mcp-remote` 的本機橋接器屬於官方列出的支援方式。

MCP 是目前最清楚、最有文件且風險最低的第三方整合介面。

## REST API

### 主機與驗證

主要 REST 主機是 `https://api.alphaxiv.org`。

登入後的 `Settings → MCP/API` 頁面顯示以下說明：

> Connect MCP clients to `https://api.alphaxiv.org/mcp/v1` or access your library and papers over the API by sending an `Authorization: Bearer {key}` header.

這段文字是目前最直接的官方證據，證明 API Key 不只可用於 MCP，也預期用於個人書庫和論文 API。

Web 前端也會使用 alphaXiv 登入工作階段 Cookie 存取相同 REST 主機。

CLI 不應擷取或長期保存瀏覽器 Cookie，除非官方 API Key 無法完成已獲允許的功能。

### 已驗證的無驗證端點

以下端點在沒有 Cookie 與 Bearer Token 的情況下回傳 `HTTP 200`。

| 方法 | 路徑 | 用途 | 實際回應形狀 |
| --- | --- | --- | --- |
| `GET` | `/search/v2/paper/fast?q=...&includePrivate=false` | 快速搜尋公開論文。 | JSON 陣列。 |
| `GET` | `/papers/v3/legacy/{arxiv_id}` | 取得論文中繼資料與留言。 | 包含 `paper` 與 `comments` 的物件。 |
| `GET` | `/papers/v3/feed?...` | 取得首頁論文動態。 | 包含 `page` 與 `papers` 的物件。 |
| `GET` | `/events/v1` | 取得公開活動。 | JSON 陣列。 |

已驗證的公開論文查詢範例：

```bash
curl 'https://api.alphaxiv.org/search/v2/paper/fast?q=transformer&includePrivate=false'

curl 'https://api.alphaxiv.org/papers/v3/legacy/1706.03762'
```

這些端點可公開呼叫不代表 alphaXiv 已承諾其長期相容性。

### 已驗證的受驗證端點

以下端點在沒有驗證資料時回傳 `HTTP 401`。

| 方法 | 路徑 | 用途 | 建議狀態 |
| --- | --- | --- | --- |
| `GET` | `/users/v3` | 目前使用者與偏好設定。 | Web 內部端點，除非功能必要，否則不要依賴。 |
| `GET` | `/folders/v3` | 使用者資料夾與個人書庫。 | 與設定頁面的「library」用途一致。 |
| `GET` | `/assistant/v2?variant=homepage` | 使用者的 Assistant 工作階段。 | 不建議直接整合。 |

已登入的 alphaXiv 網頁可以成功呼叫這些端點。

API Key 的預期用法如下：

```bash
curl \
  -H "Authorization: Bearer $ALPHAXIV_API_KEY" \
  'https://api.alphaxiv.org/folders/v3'
```

本次研究沒有使用或顯示任何完整 API Key。

### 私人論文能力

開發環境 OpenAPI 顯示快速搜尋具有 `includePrivate` 參數，並包含私人論文上傳與中繼資料端點。

例如規格中出現 `/v2/papers/private` 與 `/v2/papers/private/{paperId}/metadata` 類型的路由。

這些路由沒有消費者文件，而且未在本次研究中測試。

除非 alphaXiv 提供進一步文件或書面許可，本專案不應實作私人論文上傳與修改功能。

## OpenAPI 文件調查

### 生產環境

以下生產路徑在研究時均回傳 `HTTP 404`。

- `https://api.alphaxiv.org/openapi.json`
- `https://api.alphaxiv.org/swagger.json`
- `https://api.alphaxiv.org/docs`
- `https://api.alphaxiv.org/api-docs`
- `https://api.alphaxiv.org/redoc`

`https://api.alphaxiv.org/` 只回傳簡短 HTML，不是 API 索引。

### 開發環境

以下開發環境文件可公開存取。

- API Reference：`https://api-dev.alphaxiv.org/`
- OpenAPI JSON：`https://api-dev.alphaxiv.org/api.json`

研究時下載的規格具有以下特徵。

| 項目 | 值 |
| --- | --- |
| OpenAPI 版本 | 3.0.0 |
| 路徑數 | 281 |
| 操作數 | 299 |
| `GET` 操作 | 123 |
| `POST` 操作 | 140 |
| `PATCH` 操作 | 14 |
| `PUT` 操作 | 4 |
| `DELETE` 操作 | 18 |

該規格包含公開讀取、使用者資料、助理、資料夾、MCP、帳務、管理、批次工作、指標和資料匯入端點。

每個操作的描述還包含伺服器端原始檔案路徑。

全域安全設定將 Bearer API Key 與匿名存取都標示為可選，因此無法單靠 OpenAPI 自動判斷每個端點是否需要驗證。

規格內含大量 admin 與維運操作，顯示它是整個後端的生成式參考，而不是經過篩選的第三方 API 產品文件。

本專案可以將此規格用於研究資料形狀，但不得自動產生並公開全部 API，也不得呼叫管理或批次工作端點。

## CORS 與速率限制

REST 回應只宣告允許 `https://www.alphaxiv.org` 作為跨來源瀏覽器 Origin。

這不會阻止 CLI 或伺服器端 HTTP 用戶端，但會阻止任意第三方網頁直接呼叫 API。

REST 回應帶有 `RateLimit` 標頭，但 alphaXiv 沒有發布消費者 REST 速率限制政策。

不應將研究時觀察到的標頭數字當作保證配額。

MCP 研究工具另有 Assistant 配額，這與 HTTP `RateLimit` 標頭不是同一個限制。

## 使用條款與允許用途

alphaXiv 的服務條款在研究時顯示最後修訂日期為 2026-04-17。

條款禁止資料探勘、robots、scraping，以及類似的資料收集或擷取方法。

條款也限制未經明確授權的商業使用。

目前設定頁面明確允許以 API Key 存取個人書庫與論文，因此個人用途的正常 API 操作和大規模資料抓取必須分開看待。

本專案不應加入全站爬取、規避封鎖、批量鏡像語料庫或未授權商業再利用功能。

若產品要支援商業使用、大量資料匯出或重新提供 alphaXiv 內容，應先取得 alphaXiv 的書面授權。

本節是技術風險評估，不是法律意見。

## 官方問題追蹤器中的歷史證據

alphaXiv 的公開 GitHub 問題追蹤器提供了 API 政策演變的額外脈絡。

| Issue | 日期 | 證據 |
| --- | --- | --- |
| [#66](https://github.com/alphaXiv/feedback/issues/66) | 2025-11 至 2026-01 | 官方確認正在開發 MCP，之後表示將發布文件。 |
| [#225](https://github.com/alphaXiv/feedback/issues/225) | 2026-03 | 官方表示 API Key 當時不允許作為個人聊天後端或重建現有網站功能。 |
| [#239](https://github.com/alphaXiv/feedback/issues/239) | 2026-03 至 2026-07 | 使用者要求 MCP 非互動式 API Key 驗證，官方在 2026-07-24 表示功能已上線。 |
| [#322](https://github.com/alphaXiv/feedback/issues/322) | 2026-07 | 官方指向 MCP 文件，並確認已加入個人書庫管理能力。 |

Issue #225 發生在目前自助 API Key 與完整 MCP 文件推出之前。

不過，現行文件仍沒有授權第三方直接使用 `/assistant/v2/chat` 重建 Assistant 體驗。

因此應把直接 Assistant REST 整合視為高風險，並改用官方 MCP 研究工具。

## 第三方 SDK

第三方專案 [`petroslamb/alphaxiv-py`](https://github.com/petroslamb/alphaxiv-py) 實作了 alphaXiv Python SDK 與 CLI。

它涵蓋搜尋、動態、論文、完整文字、摘要、留言、資料夾與 Assistant 等 REST 功能。

該專案不是 alphaXiv 官方 SDK，也不能代表端點穩定性或允許用途。

它在 2026-07-02 的 API inventory 中表示沒有找到 OpenAPI，但目前 `api-dev.alphaxiv.org/api.json` 已可公開存取。

這項差異本身說明 alphaXiv 的 API 表面仍在快速變動。

## 對本專案的建議

### 建議的架構

1. 以官方 MCP API 作為搜尋、論文理解、PDF 問答、程式碼閱讀及個人書庫管理的主要後端。
2. 以 API Key Bearer 驗證作為 CLI 的主要非互動式驗證方式。
3. 只為 MCP 未涵蓋的確定性讀取功能加入 REST，例如快速搜尋、動態和論文中繼資料。
4. 將 REST 呼叫集中在獨立的相容層，避免端點變更散布到整個 CLI。
5. 為每個 REST 端點建立小型線上 contract test，驗證狀態碼與最低必要欄位。
6. 為遠端寫入加入明確確認，並限制在官方 MCP 個人書庫工具或設定頁面明確允許的用途。

### 不建議實作

- 不要從瀏覽器擷取完整工作階段 Cookie 作為預設登入流程。
- 不要依賴 `/assistant/v2/chat` 重建 alphaXiv Assistant。
- 不要呼叫 OpenAPI 中的 admin、kickoff、process、ingest、metrics 或維運端點。
- 不要將開發 OpenAPI 當作穩定生產合約。
- 不要加入全站論文抓取或語料庫鏡像功能。
- 不要在沒有書面授權時提供商業資料再發布能力。

### 建議的第一階段功能

| CLI 功能 | 建議介面 |
| --- | --- |
| 連線與登入 | MCP OAuth 2.1 或 API Key。 |
| 發現論文 | MCP `discover_papers`。 |
| 讀取論文 | MCP `get_paper_content`。 |
| PDF 精準問答 | MCP `answer_pdf_queries`。 |
| 讀取相關程式碼 | MCP `read_files_from_github_repository`。 |
| 管理個人書庫 | MCP library tools。 |
| 快速關鍵字搜尋 | 必要時使用 `/search/v2/paper/fast`。 |
| 取得首頁動態 | 必要時使用 `/papers/v3/feed`。 |
| 取得原始論文中繼資料 | 必要時使用 `/papers/v3/legacy/{arxiv_id}`。 |

## 尚未確認的事項

- alphaXiv 是否會發布經過篩選的正式 REST API 文件。
- REST API 是否有版本淘汰、相容性或服務等級政策。
- API Key 對所有論文與個人書庫 REST 端點的精確權限範圍。
- API Key 是否正式允許直接使用 Assistant REST 讀取端點。
- 私人論文上傳與修改 API 是否預期開放給一般第三方用戶端。
- REST 的正式速率限制、批量操作限制及商業授權流程。

## 主要來源

### 官方來源

- [alphaXiv MCP Server Documentation](https://www.alphaxiv.org/docs/mcp)
- [alphaXiv MCP/API Settings](https://www.alphaxiv.org/settings/api-keys)，需要登入。
- [alphaXiv Terms of Service](https://www.alphaxiv.org/terms)
- [alphaXiv API Host](https://api.alphaxiv.org/)
- [alphaXiv Development API Reference](https://api-dev.alphaxiv.org/)
- [alphaXiv Development OpenAPI](https://api-dev.alphaxiv.org/api.json)
- [alphaXiv Feedback Issue #66](https://github.com/alphaXiv/feedback/issues/66)
- [alphaXiv Feedback Issue #225](https://github.com/alphaXiv/feedback/issues/225)
- [alphaXiv Feedback Issue #239](https://github.com/alphaXiv/feedback/issues/239)
- [alphaXiv Feedback Issue #322](https://github.com/alphaXiv/feedback/issues/322)

### 輔助來源

- [petroslamb/alphaxiv-py](https://github.com/petroslamb/alphaxiv-py)
- [petroslamb/alphaxiv-py API inventory](https://github.com/petroslamb/alphaxiv-py/blob/main/docs/api-inventory.md)
