# Design Spec: Four New Nextcloud App Integrations

**Date:** 2026-04-14
**Status:** Draft
**Apps:** WeekPlanner, Agora, IntraVox, Analytics

## Context

The nextcloud-mcp-server currently supports 10 Nextcloud apps (Notes, Calendar, Contacts, Files/WebDAV, Deck, Cookbook, Tables, Sharing, News, Collectives). This spec adds support for 4 additional apps that the user regularly uses: WeekPlanner, Agora, IntraVox, and Analytics.

All 4 are standard Nextcloud apps installed from the app store. Each exposes REST API endpoints that follow Nextcloud conventions. The goal is full MCP tool coverage enabling an AI assistant to create, read, update, and manage resources in each app.

## Implementation Order

Sequential, one app at a time: **WeekPlanner -> Agora -> IntraVox -> Analytics**

Rationale: WeekPlanner is smallest (proves the pattern), Agora is the user's stated priority, IntraVox introduces OCS+internal mixed routing, Analytics is largest and benefits from all patterns being established.

## Architecture (All Apps)

Each app follows the existing 3-layer pattern:

```
client/{app}.py          -> BaseNextcloudClient subclass, raw HTTP, returns dict/list[dict]
models/{app}.py          -> Pydantic BaseModel (data) + BaseResponse (responses)
server/{app}.py          -> configure_{app}_tools(mcp), @mcp.tool() + @require_scopes + @instrument_tool
```

Registration points (2 existing files modified):
- `client/__init__.py` -> `self.{app} = {App}Client(self._client, username)`
- `server/__init__.py` -> `AVAILABLE_APPS["{app}"] = configure_{app}_tools`

Shared conventions:
- `app_name` class attribute for metrics/tracing
- `API_BASE` constant for endpoint prefix
- Scopes: `{app}.read` / `{app}.write` (auto-discovered by `discover_all_scopes`)
- Tool naming: `nc_{app}_{action}`
- ToolAnnotations per ADR-017: all `openWorldHint=True`
- Error handling: catch `HTTPStatusError`/`RequestError`, raise `McpError`

---

## App 1: WeekPlanner

### Overview
Weekly task planner. Tasks organized by day of week. Stores entire weeks as JSON blobs keyed by (user, year, week). No per-task API endpoints.

### API Surface
Base: `/apps/weekplanner`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/week/{year}/{week}` | Get week data (days -> tasks) |
| PUT | `/week/{year}/{week}` | Save week data (body: `{days: {...}}`) |
| GET | `/custom-columns` | Get custom columns + recurring tasks |
| PUT | `/custom-columns` | Save custom columns config |

### Data Model
```
Task: { id: str, title: str, done: bool, notes: str,
        recurrence: ''|'daily'|'weekly'|'monthly',
        color: ''|'red'|'orange'|'yellow'|'green'|'blue'|'purple' }

WeekData: { days: { monday: Task[], tuesday: Task[], ..., sunday: Task[] } }

CustomColumn: { id: str, title: str, tasks: Task[] }
RecurringTaskDefinition: { id, title, notes, recurrence, startDate, endDate, dayOfWeek, dayOfMonth, exceptionDates }
```

### Design Decision: Read-Modify-Write
Per-task tools (add, update, complete, move, delete) perform GET -> modify JSON -> PUT internally. The `updatedAt` timestamp from GET is checked against the current state before PUT to detect concurrent modifications. If stale, the tool raises an error.

### MCP Tools (8)

| Tool | Annotations | Scope |
|------|-------------|-------|
| `nc_weekplanner_get_week` | readOnly, openWorld | weekplanner.read |
| `nc_weekplanner_add_task` | openWorld | weekplanner.write |
| `nc_weekplanner_update_task` | openWorld | weekplanner.write |
| `nc_weekplanner_complete_task` | openWorld | weekplanner.write |
| `nc_weekplanner_move_task` | openWorld | weekplanner.write |
| `nc_weekplanner_delete_task` | destructive, idempotent, openWorld | weekplanner.write |
| `nc_weekplanner_get_custom_columns` | readOnly, openWorld | weekplanner.read |
| `nc_weekplanner_update_custom_columns` | openWorld | weekplanner.write |

### Client Methods
- `get_week(year: int, week: int) -> dict`
- `put_week(year: int, week: int, days: dict) -> dict`
- `get_custom_columns() -> dict`
- `put_custom_columns(columns: list[dict], recurring_tasks: list[dict]) -> dict`

### Response Models
- `WeekPlannerTask(BaseModel)` — individual task
- `GetWeekResponse(BaseResponse)` — results: dict[str, list[WeekPlannerTask]], updated_at: int
- `UpdateWeekResponse(BaseResponse)` — status message, updated_at
- `GetCustomColumnsResponse(BaseResponse)` — columns, recurring_tasks, updated_at
- `UpdateCustomColumnsResponse(BaseResponse)` — status message, updated_at

---

## App 2: Agora

### Overview
Participatory democracy app. Inquiries (proposals, debates, petitions, projects, etc.) organized into families. Supports comments, suggestions, and voting (supports).

### API Surface
Base: `/apps/agora/api/v1.0`

**Inquiries:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agora` | List all inquiries |
| GET | `/inquiry/{id}` | Get inquiry by ID |
| POST | `/inquiry` | Create inquiry (`{type, title, description}`) |
| PUT | `/inquiry/{id}` | Update inquiry |
| DELETE | `/inquiry/{id}` | Delete inquiry |
| POST | `/inquiry/{id}/clone` | Clone inquiry |
| POST | `/inquiry/{id}/trash` | Toggle trash |
| PUT | `/inquiry/{id}/close` | Close inquiry |
| PUT | `/inquiry/{id}/reopen` | Reopen inquiry |
| GET | `/enum/inquiry` | List valid inquiry types |

**Comments:** GET `/inquiry/{id}/comments`, POST `/comment`, DELETE `/comment/{id}`
**Suggestions:** GET `/inquiry/{id}/suggestions`, POST `/suggestion`, DELETE `/suggestion/{id}`
**Supports:** GET `/inquiry/{id}/supports`, PUT `/support/{id}`, DELETE `/support/{id}`

### Inquiry Types
proposal, debate, project, petition, official_response, suggestion, grievance

### MCP Tools (16)

| Tool | Annotations | Scope |
|------|-------------|-------|
| `nc_agora_list_inquiries` | readOnly, openWorld | agora.read |
| `nc_agora_get_inquiry` | readOnly, openWorld | agora.read |
| `nc_agora_create_inquiry` | openWorld | agora.write |
| `nc_agora_update_inquiry` | openWorld | agora.write |
| `nc_agora_delete_inquiry` | destructive, idempotent, openWorld | agora.write |
| `nc_agora_clone_inquiry` | openWorld | agora.write |
| `nc_agora_trash_inquiry` | openWorld | agora.write |
| `nc_agora_close_inquiry` | openWorld | agora.write |
| `nc_agora_reopen_inquiry` | openWorld | agora.write |
| `nc_agora_list_comments` | readOnly, openWorld | agora.read |
| `nc_agora_create_comment` | openWorld | agora.write |
| `nc_agora_delete_comment` | destructive, idempotent, openWorld | agora.write |
| `nc_agora_list_suggestions` | readOnly, openWorld | agora.read |
| `nc_agora_create_suggestion` | openWorld | agora.write |
| `nc_agora_list_supports` | readOnly, openWorld | agora.read |
| `nc_agora_get_inquiry_types` | readOnly, openWorld | agora.read |

### Client Methods
- Inquiry: `list_inquiries()`, `get_inquiry(id)`, `create_inquiry(type, title, description?)`, `update_inquiry(id, **fields)`, `delete_inquiry(id)`
- Actions: `clone_inquiry(id)`, `trash_inquiry(id)`, `close_inquiry(id)`, `reopen_inquiry(id)`
- Comments: `get_comments(inquiry_id)`, `create_comment(inquiry_id, message)`, `delete_comment(comment_id)`
- Suggestions: `get_suggestions(inquiry_id)`, `create_suggestion(inquiry_id, message)`, `delete_suggestion(id)`
- Supports: `get_supports(inquiry_id)`
- Enum: `get_inquiry_types()`

### Response Models
- `AgoraInquiry(BaseModel)` — id, title, description, type, access, owner, created, etc.
- `AgoraComment(BaseModel)` — id, inquiryId, userId, message, timestamp
- `AgoraSuggestion(BaseModel)` — id, inquiryId, message
- `AgoraSupport(BaseModel)` — id, inquiryId, userId, status
- Response wrappers: `ListInquiriesResponse`, `GetInquiryResponse`, `CreateInquiryResponse`, etc.

---

## App 3: IntraVox

### Overview
Intranet page builder (SharePoint-style). Pages stored as JSON with drag-and-drop widget layouts. Uses GroupFolders for storage and permissions.

### API Surface
**OCS routes** (Basic Auth): `/ocs/v2.php/apps/intravox/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pages` | List all pages |
| POST | `/pages` | Create page |
| GET | `/pages/{id}` | Get page content |
| PUT | `/pages/{id}` | Update page |
| DELETE | `/pages/{id}` | Delete page |
| GET | `/pages/{pageId}/media` | List page media |
| POST | `/pages/{pageId}/media` | Upload media |
| GET | `/pages/{pageId}/media/{filename}` | Get media file |

**Internal routes** (selective): `/apps/intravox/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pages/tree` | Get page tree structure |
| GET | `/search` | Search pages by query |
| GET | `/pages/{id}/breadcrumb` | Get breadcrumb navigation |
| GET | `/navigation` | Get navigation structure |
| GET | `/pages/{pageId}/comments` | Get page comments |
| POST | `/pages/{pageId}/comments` | Create comment |
| PUT | `/comments/{commentId}` | Update comment |
| DELETE | `/comments/{commentId}` | Delete comment |

### Design Decision: OCS + Selective Internal
OCS routes for core pages/media CRUD (explicitly designed for Basic Auth). Internal routes for search, comments, navigation, page tree (high-value features that likely work with Basic Auth based on how Nextcloud AppFramework handles auth).

### OCS Response Handling
OCS endpoints return wrapped responses: `response.json()["ocs"]["data"]`. The client will have a helper method `_make_ocs_request()` that handles the header injection and response unwrapping, following the pattern in the existing `SharingClient`.

### MCP Tools (15)

| Tool | Annotations | Scope |
|------|-------------|-------|
| `nc_intravox_list_pages` | readOnly, openWorld | intravox.read |
| `nc_intravox_get_page` | readOnly, openWorld | intravox.read |
| `nc_intravox_create_page` | openWorld | intravox.write |
| `nc_intravox_update_page` | openWorld | intravox.write |
| `nc_intravox_delete_page` | destructive, idempotent, openWorld | intravox.write |
| `nc_intravox_search_pages` | readOnly, openWorld | intravox.read |
| `nc_intravox_get_page_tree` | readOnly, openWorld | intravox.read |
| `nc_intravox_get_navigation` | readOnly, openWorld | intravox.read |
| `nc_intravox_get_breadcrumb` | readOnly, openWorld | intravox.read |
| `nc_intravox_list_media` | readOnly, openWorld | intravox.read |
| `nc_intravox_upload_media` | openWorld | intravox.write |
| `nc_intravox_get_comments` | readOnly, openWorld | intravox.read |
| `nc_intravox_create_comment` | openWorld | intravox.write |
| `nc_intravox_update_comment` | openWorld | intravox.write |
| `nc_intravox_delete_comment` | destructive, idempotent, openWorld | intravox.write |

### Client Methods
- OCS pages: `list_pages()`, `get_page(id)`, `create_page(title, language, layout?)`, `update_page(id, data)`, `delete_page(id)`
- OCS media: `list_media(page_id)`, `upload_media(page_id, filename, content)`, `get_media(page_id, filename)`
- Internal: `search_pages(query)`, `get_page_tree()`, `get_navigation()`, `get_breadcrumb(page_id)`
- Comments: `get_comments(page_id)`, `create_comment(page_id, message)`, `update_comment(comment_id, message)`, `delete_comment(comment_id)`

---

## App 4: Analytics

### Overview
Data analytics and visualization. Reports visualize data from datasets. Panoramas are dashboards containing multiple reports. Supports scheduled data loads from various sources.

### API Surface
**Internal routes:** `/apps/analytics`

**Reports:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/report` | List all reports |
| POST | `/report` | Create report |
| GET | `/report/{id}` | Get report details |
| PUT | `/report/{id}` | Update report |
| DELETE | `/report/{id}` | Delete report |
| POST | `/report/copy` | Copy a report |
| GET | `/report/export/{id}` | Export report |

**Datasets:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dataset` | List all datasets |
| POST | `/dataset` | Create dataset |
| GET | `/dataset/{id}` | Get dataset details |
| PUT | `/dataset/{id}` | Update dataset |
| DELETE | `/dataset/{id}` | Delete dataset |

**Panoramas:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/panorama` | List all panoramas |
| POST | `/panorama` | Create panorama |
| GET | `/panorama/{id}` | Get panorama details |
| PUT | `/panorama/{id}` | Update panorama |
| DELETE | `/panorama/{id}` | Delete panorama |

**Data Operations (v3 API):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/3.0/data/{reportId}` | Get data records |
| POST | `/api/3.0/data/{datasetId}/add` | Add data records |
| POST | `/api/3.0/data/{datasetId}/delete` | Delete data records |

**Dataloads:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dataload` | List dataloads |
| POST | `/dataload` | Create dataload |
| PUT | `/dataload/{id}` | Update dataload |
| DELETE | `/dataload/{id}` | Delete dataload |
| POST | `/dataload/execute` | Execute a dataload |

**Datasources:** GET `/datasource` (list types)

### MCP Tools (22)

| Tool | Annotations | Scope |
|------|-------------|-------|
| `nc_analytics_list_reports` | readOnly, openWorld | analytics.read |
| `nc_analytics_get_report` | readOnly, openWorld | analytics.read |
| `nc_analytics_create_report` | openWorld | analytics.write |
| `nc_analytics_update_report` | openWorld | analytics.write |
| `nc_analytics_delete_report` | destructive, idempotent, openWorld | analytics.write |
| `nc_analytics_copy_report` | openWorld | analytics.write |
| `nc_analytics_list_datasets` | readOnly, openWorld | analytics.read |
| `nc_analytics_get_dataset` | readOnly, openWorld | analytics.read |
| `nc_analytics_create_dataset` | openWorld | analytics.write |
| `nc_analytics_update_dataset` | openWorld | analytics.write |
| `nc_analytics_delete_dataset` | destructive, idempotent, openWorld | analytics.write |
| `nc_analytics_list_panoramas` | readOnly, openWorld | analytics.read |
| `nc_analytics_get_panorama` | readOnly, openWorld | analytics.read |
| `nc_analytics_create_panorama` | openWorld | analytics.write |
| `nc_analytics_update_panorama` | openWorld | analytics.write |
| `nc_analytics_delete_panorama` | destructive, idempotent, openWorld | analytics.write |
| `nc_analytics_get_data` | readOnly, openWorld | analytics.read |
| `nc_analytics_add_data` | openWorld | analytics.write |
| `nc_analytics_delete_data` | destructive, openWorld | analytics.write |
| `nc_analytics_list_datasources` | readOnly, openWorld | analytics.read |
| `nc_analytics_list_dataloads` | readOnly, openWorld | analytics.read |
| `nc_analytics_execute_dataload` | openWorld | analytics.write |

---

## Testing Strategy

### Per-App Test Files

| File | Marker | Purpose |
|------|--------|---------|
| `tests/client/{app}/test_{app}_api.py` | `@pytest.mark.unit` | Mocked HTTP response parsing |
| `tests/client/{app}/__init__.py` | — | Package init |

### Mock Helpers
Added to `tests/client/conftest.py`:
- `create_mock_{app}_{entity}_response(...)` for each entity type
- Uses existing `create_mock_response()` base helper

### Integration Tests
Deferred — require the apps installed on the test Nextcloud Docker instance. Test files created with `@pytest.mark.integration` marker but initially skipped. Can be enabled when Docker environment is extended.

### What We Test (Unit)
- Correct API endpoint URLs called
- Correct HTTP methods used
- Request parameters/body passed correctly
- Response JSON parsed correctly into expected format
- Error responses (404, 409, 422) handled properly

---

## Files Created/Modified

### New Files (per app, x4)
- `nextcloud_mcp_server/client/{app}.py`
- `nextcloud_mcp_server/models/{app}.py`
- `nextcloud_mcp_server/server/{app}.py`
- `tests/client/{app}/__init__.py`
- `tests/client/{app}/test_{app}_api.py`

### Modified Files (once)
- `nextcloud_mcp_server/client/__init__.py` — add 4 client imports + instantiation
- `nextcloud_mcp_server/server/__init__.py` — add 4 configure imports + AVAILABLE_APPS entries

### Total
- ~20 new files
- 2 modified files
- ~61 new MCP tools (8 + 16 + 15 + 22)
