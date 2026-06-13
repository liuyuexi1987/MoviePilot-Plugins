# 影巢「网页方式」搜索/解锁设计（绕过 OpenAPI）

- 日期：2026-06-13
- 插件：AgentResourceOfficer（ARO）
- 范围：仅影巢资源搜索/解锁，新增「网页方式」作为 OpenAPI 之外的可选路径
- 参考实现：DDSRem-Dev/MoviePilot-Plugins → `plugins.v2/p115strmhelper/helper/hdhive/browser.py`（GPL v3）

## 1. 背景与问题

影巢 OpenAPI 需官方授权，用户的 OpenAPI 一直未通过，导致 ARO 现有的影巢搜索/解锁（走 `/api/open/...`）不可用。

调研 DDSRem 的 P115StrmHelper 后确认：其「无 API」影巢能力本质是**浏览器自动化**——用账号密码/cookie 在影巢网页上登录、搜索、解锁，而非逆向 HTTP 接口。该仓库与本仓库均为 **GPL v3**，复刻合规（需注明来源）。

关键事实（已实测/读码确认）：
- MoviePilot 官方镜像自带 chromium 内核，并提供 `app.helper.browser.PlaywrightHelper`（内置 **cloakbrowser** 反检测 + **FlareSolverr** 绕 Cloudflare）。裸调 playwright 会撞版本不匹配，必须走 MP 封装。
- 影巢**登录是纯填表**（打开 `/login` → 填账密 → 提交 → 等待离开登录页），**不需要验证码**。那套依赖 `115server.ddsrem.com` 的空间验证码**只用于签到**，本设计不涉及。
- 整个方案在 **NAS 的 MoviePilot docker 容器内 headless 运行**，与用户个人电脑、是否开机无关。

## 2. 目标 / 非目标

### 目标
- ARO 内置「网页方式」影巢搜索 + 解锁，不依赖 OpenAPI 即可用。
- 基于 MP 官方 `PlaywrightHelper`（cloakbrowser），docker headless 运行。
- 登录支持：cookie 注入优先；失效时账号密码自动登录拿新 cookie 并持久化。
- 复用现有 `hdhive_checkin_username/password/cookie` 等配置，不让用户重复填。
- 搜索结果与解锁产出对齐 ARO 现有数据结构，下游转存流程不变。
- 新增配置项，让用户自由选择影巢资源方式（网页 / OpenAPI / 自动）。

### 非目标
- 不做签到、不做空间验证码求解（沿用 ARO 现有签到，不碰 `115server.ddsrem.com`）。
- 第一版不照搬 DDSRem 全部反检测/验证码代码，反检测与 CF 处理交给 MP cloakbrowser/FlareSolverr。
- 不改动 115/夸克转存逻辑、不改前端扫码弹窗、不改签到逻辑。

## 3. 架构

### 新增模块 `services/hdhive_browser.py`
精简复刻自 DDSRem `browser.py`，文件头注明来源与 GPL v3。对外暴露 `HDHiveBrowserService`：

| 方法 | 说明 |
|---|---|
| `login(cookie_str=None, username=None, password=None) -> (cookie_str, token) \| None` | 有 cookie 走 cookie；否则账密填表登录拿 cookie |
| `search(media_type, tmdb_id) -> List[Dict]` | 打开 `{base}/tmdb/{movie\|tv}/{tmdb_id}`，抓资源卡片 |
| `unlock(slug) -> Dict`（含 115 链接） | 打开资源页点「确定解锁」，抓 `115.com` 链接 |
| `is_ready() -> bool` | 已填账密或存在可用 cookie，且 playwright/cloakbrowser 后端可用 |

内部：
- 浏览器上下文统一通过 `app.helper.browser.PlaywrightHelper`（cloakbrowser context）获取，failsafe 到 playwright。
- cookie 持久化到插件数据目录 `hdhive_browser_cookies.json`；JWT `exp` 过期判断；失效自动重登（`auto_login` 开关控制）。
- 资源卡片解析、解锁 DOM 操作的选择器/JS 复刻自 DDSRem（`_scrape_resource_cards_js` / unlock 流程），按影巢实际页面适配。

### 接入点 `__init__.py`
现有影巢搜索/解锁经 `_ensure_hdhive_service()`（返回 `HDHiveOpenApiService`）。新增按 `hdhive_resource_mode` 路由：
- 在搜索/解锁的调用处，根据模式选择 `HDHiveOpenApiService`（openapi）或 `HDHiveBrowserService`（browser），`auto` 时网页优先、OpenAPI 兜底。
- 两条路径返回结构归一（标题/分辨率/大小/解锁积分/slug/115链接），下游无感知。

## 4. 配置项

### 新增
- `hdhive_resource_mode`：枚举 `browser` / `openapi` / `auto`，默认 `browser`（用户 OpenAPI 未通过）。前端在「影巢资源」卡片加一个下拉（VSelect）。

### 复用（不新增）
- `hdhive_checkin_username` / `hdhive_checkin_password` / `hdhive_checkin_cookie`：网页登录凭据。
- `hdhive_checkin_auto_login`：是否允许 cookie 失效后账密自动重登。
- `hdhive_base_url`（默认 `https://hdhive.com`）、`hdhive_default_path`、`hdhive_max_unlock_points`、`hdhive_candidate_page_size`、`hdhive_timeout`。

> 前端「影巢资源」卡片副标题补一句方式说明；登录凭据沿用「影巢签到」卡片已有字段，不重复加输入框。

## 5. 数据流

**搜索**：关键词 → TMDB 候选（现有 `resolve_candidates_by_keyword`）→ `HDHiveBrowserService.search(type, tmdb_id)` → 资源卡片 → 归一结构 → 现有展示/排序（`resource_sort_key`、积分上限过滤）。

**解锁**：用户/智能体选定 slug → `HDHiveBrowserService.unlock(slug)` → 115 链接 → **交 ARO 现有转存流程**（115/夸克），行为与 OpenAPI 解锁一致。

## 6. 登录与会话管理

1. 优先用 cookie：现有 `hdhive_checkin_cookie` 或持久化文件中的 cookie，注入上下文。
2. 打开目标页若被重定向到 `/login` 或 token 过期 → 判定 cookie 失效。
3. 若 `auto_login` 开且已填账密 → 账密填表登录拿新 cookie → 写回持久化文件（并可回填运行时）。
4. 仍失败 → 抛出明确错误，提示用户检查账密或手动更新 cookie。

## 7. 错误处理

- 浏览器后端不可用（无 cloakbrowser 且 playwright 版本不匹配）→ 明确报错 + 指引。
- Cloudflare 拦截 → 依赖 cloakbrowser/FlareSolverr；仍失败 → 报错并建议手动提供有效 cookie。
- 登录失败 / 账密错误 → 明确错误信息，不静默。
- 页面结构变更导致抓取为空 → 记录日志、返回空列表，不崩溃。
- 解锁未拿到 115 链接 → 报错并提示积分/资源状态。
- 单次操作设超时与浏览器关闭兜底，避免句柄泄漏占内存。

## 8. 许可与归属

- 本仓库与 DDSRem-Dev/MoviePilot-Plugins 均为 **GPL v3**，复刻兼容。
- `services/hdhive_browser.py` 文件头注明：改编自 DDSRem-Dev/MoviePilot-Plugins（p115strmhelper），原作者、原仓库链接、GPL v3。

## 9. 测试与验收

- `python3 -m py_compile AgentResourceOfficer/__init__.py services/hdhive_browser.py` 通过。
- 单元：cookie 字符串解析、JWT `exp` 过期判断、资源卡片解析（用保存的 HTML 片段 mock）。
- 集成（需有效影巢账号）：在本机 `moviepilot-v2` 容器内实跑一次搜索 + 解锁，确认拿到资源列表与 115 链接。
- 前端：`npm run build` 通过，「影巢资源」卡片出现方式下拉，字段无缺失。
- 同步到 `plugins/`、`plugins.v2/`，部署容器内置 + `/config` 两处。

## 10. 风险

- **内存**：每次搜索/解锁开 headless 浏览器，吃几百 MB；低配 NAS 需并发/超时控制。
- **影巢改版**：选择器/页面结构变化会使抓取失效，需跟随维护。
- **CF 风控**：headless + 机房/家宽 IP 偶发被拦；有 cloakbrowser/FlareSolverr 兜底但非 100%。
- **解锁消耗积分**：受 `hdhive_max_unlock_points` 上限保护。
- **GPL 传染**：复刻代码须保持 GPL，注明来源。

## 11. 分阶段实现

- **P1**：`HDHiveBrowserService`（cookie 注入）+ 搜索 + 解锁 + 接入 `__init__.py` + 新增 `hdhive_resource_mode` + 前端下拉。
- **P2**：账密自动登录 + cookie 持久化 + 失效重登。
- **P3**：`auto` 模式（网页优先、OpenAPI 兜底）打磨与错误提示完善。
