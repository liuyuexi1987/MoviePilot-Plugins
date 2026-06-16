# Changelog

## 当前主线

- 仓库已经从单一 AI Gateway 插件，收拢为 MoviePilot 资源与智能体插件套件。
- 当前发布前检查覆盖 2 个可本地安装插件：
  `AIRecognizerEnhancer`、`AgentResourceOfficer`。
- `AgentResourceOfficer` 已作为新资源主入口，负责影巢、盘搜、115、夸克、内置飞书入口和智能体 Tool 的统一路由。
- 旧插件 `FeishuCommandBridgeLong`、`HdhiveOpenApi`、`QuarkShareSaver` 已迁移到备份仓库，不再作为当前插件市场条目发布。
- `AIRecognizerEnhancer` 作为新识别增强线，逐步替代旧网关转发链路。
- 发布流程已补齐 `plugins/`、`plugins.v2/` 同步、元数据校验、语法检查、ZIP 打包和 GitHub Actions CI。

## 当前核心版本

- `AIRecognizerEnhancer`: `0.1.13`
- `AgentResourceOfficer`: `0.3.1`

## 近期基础设施更新

- `AgentResourceOfficer 0.3.1`：回退并固定 `p115client` 到 `0.0.8.5.1.1`，避免与 MoviePilot 当前环境和 115 插件依赖版本冲突。
- `AgentResourceOfficer 0.3.0`：精简 Agent/MCP 暴露工具集，仅保留 12 个业务能力工具，移除 ARO 自建计划、会话和自描述脚手架噪声；保留飞书与 HTTP 端点。
- `AIRecognizerEnhancer 0.1.13`：收紧失败样本持久化逻辑，修复清空失败样本与自动移除样本后的配置保存一致性。
- `AgentResourceOfficer 0.2.99`：修复飞书/助手 PT 搜索入口因可选 SubscribeHelper 路径变更导致整组 MoviePilot 搜索依赖被误判缺失的问题。
- `AgentResourceOfficer 0.2.98`：修复影巢网页登录 Cookie 只作为请求头注入导致详情页仍被重定向登录的问题，网页搜索/解锁会写入 Playwright context 后重新打开目标页。
- `AgentResourceOfficer 0.2.97`：将影巢网页搜索/解锁的浏览器动作最小超时提升到 60 秒，降低详情页加载较慢时误判无资源的概率。
- `AgentResourceOfficer 0.2.96`：修复影巢账号密码自动刷新 Cookie 读取过早导致保存为空的问题，登录后等待认证 Cookie 落盘并保存 refresh_token、hdh_uid 等完整网页认证字段。
- `AgentResourceOfficer 0.2.95`：影巢账号密码自动刷新 Cookie 的网页登录兜底改用 MoviePilot 官方 PlaywrightHelper/CloakBrowser，避免裸 Playwright 在容器内查找缺失 chromium_headless_shell。
- `AgentResourceOfficer 0.2.94`：影巢网页搜索/解锁在 Cookie 缺失或失效时复用已配置的影巢账号密码自动刷新 Cookie，并在刷新后自动重试一次资源查询或解锁。
- `AgentResourceOfficer 0.2.93`：修复影巢网页方式在 MoviePilot 异步插件请求中调用同步 PlaywrightHelper 导致 `Playwright Sync API inside the asyncio loop` 的端到端失败问题，浏览器动作改为在线程中执行。
- `AgentResourceOfficer 0.2.92`：重排 Vue 设置页信息架构并优化布局——按使用权重调整顺序为「基础设置 → MP/PT 策略 → 115 扫码 → 影巢资源 → 影巢签到 → 盘搜 → 飞书入口」，MP/PT 提到最前；影巢资源与签到拆成两张卡片，卡片标题加状态 chip 与副标题；短字段收窄并支持响应式一行多列、移除大段蓝色 Alert；顶部新增快速开始引导与主页文档链接；移除「完整配置 JSON」面板（全部字段已在表单中呈现）。Cookie/Token/Secret/Password 默认隐藏、单行、带查看/复制。
- `AgentResourceOfficer 0.2.91`：优化 Vue 设置页高级区视觉，将影巢、盘搜、MP/PT 改为统一卡片布局，影巢 Cookie 默认隐藏为单行输入并支持查看/复制。
- `AgentResourceOfficer 0.2.90`：补全 Vue 设置页高级配置，将影巢、盘搜、MP/PT 拆成三块，并恢复旧设置页中的影巢 OpenAPI、签到、积分上限、盘搜超时、MP 评分策略等字段。
- `AgentResourceOfficer 0.2.89`：修复 Vue 设置页扫码成功后关闭配置丢失的问题，新增设置页配置读取/保存接口，扫码成功自动持久化 115 Cookie，并防止旧空配置覆盖已保存 Cookie。
- `AgentResourceOfficer 0.2.88`：修复 115 扫码弹窗刷新二维码时重复请求和旧轮询互相抢状态导致一直转圈的问题，新增前端请求序号、并发锁和超时兜底。
- `AgentResourceOfficer 0.2.87`：修复 Vue 设置页 115 扫码弹窗请求被 apikey 鉴权拦截的问题，新增 bear 鉴权的设置页专用扫码接口。
- `AgentResourceOfficer 0.2.86`：切换为 Vue 自定义配置页，在 115 Cookie 行内提供 P115StrmHelper 同款扫码登录弹窗，不再跳转新网页。
- `AgentResourceOfficer 0.2.85`：修复 115 Cookie 旁扫码入口显示成灰色圆点的问题，改为明确的“扫码登录”按钮。
- `AgentResourceOfficer 0.2.84`：优化 115 扫码入口：参考 P115StrmHelper 将入口收敛到 Cookie 行二维码按钮，并保留独立扫码页兜底；受 MoviePilot 通用表单限制，真正内嵌弹窗需后续改自定义前端。
- `AgentResourceOfficer 0.2.83`：修复 MoviePilot 插件页卡死：状态页不再同步请求影巢外部接口，115 扫码生成与检查增加硬超时，并对齐 `p115client` 依赖版本，避免依赖冲突触发插件重载。
- `AgentResourceOfficer 0.2.82`：重做 115 扫码页为 P115StrmHelper 同款 `uid/time/sign` 流程；先选择扫码途径再生成二维码，重新生成不再依赖页面 session。
- `AgentResourceOfficer 0.2.81`：修复 115 扫码二维码页面「重新生成二维码」按钮会触发整页导航导致 MoviePilot 不可访问的问题，改为就地 fetch JSON 接口原位刷新二维码和会话。
- `AgentResourceOfficer 0.2.80`：收敛 115 扫码 UI；设置页不再内嵌大二维码，状态页只保留状态和扫码入口，并修复二维码过期后重新生成卡死的问题。
- `AgentResourceOfficer 0.2.79`：115 扫码设置页自动携带 MoviePilot API Token；内嵌二维码与登录状态轮询无需用户手动拼接 token。
- `AgentResourceOfficer 0.2.78`：115 扫码登录改为设置页内嵌二维码；扫码页自动创建短期会话并轮询状态，无需手填 API Token，扫码成功后自动保存 Cookie。
- `AgentResourceOfficer 0.2.77`：改进 115 扫码登录设置页 UX；替换纯文本 URL 为结构化可操作卡片（状态、路径、说明），扫码网页未授权时显示友好引导页。
- `AgentResourceOfficer 0.2.76`：新增 115 扫码登录原生网页；打开 `/p115/qrcode/page` 后自动生成二维码并轮询登录状态，成功后保存 115 Cookie，避免依赖外部智能体传图。
- `AgentResourceOfficer 0.2.75`：插件详情页新增 115 扫码登录原生卡片；直接在插件页面展示二维码 API 端点与扫码指引，无需通过外部智能体即可在 MoviePilot 内完成 115 App 扫码登录。
- `AgentResourceOfficer 0.2.74`：适配影巢 OpenAPI 新鉴权规则；业务接口支持用户级 Bearer Token 与 Refresh Token 自动续期，并保留签到网页兜底链路。
- `AgentResourceOfficer 0.2.73`：对齐并验证 `MoviePilot v2.11.4`；新增 `scripts/check-moviepilot-upstream-compat.py` 上游兼容检查，把最新已验证的 MoviePilot 版本暴露到 `assistant/selfcheck`，并纳入 `pre-release-check.sh` 发布前检查。
- `AgentResourceOfficer 0.2.72`：修复 PT 订阅下载保存路径；创建或复用订阅时同步写入 Agent影视助手 的 `PT 下载保存路径`，避免订阅刷新自动推下载时落回 MoviePilot/qB 默认目录。云盘 115/夸克转存默认目录不变，仍按各自网盘目录配置执行。
- `AgentResourceOfficer 0.2.71`：新增流媒体推荐能力；聚合 Netflix、Disney+、Apple TV+、Prime Video 四大平台，基于 TMDB discover 支持本月上新、近期热门电影/剧集等显式前缀推荐，结果页为只读列表，不扩张主线命令面。

- `AgentResourceOfficer 0.2.70`：最后一轮主线收口；取消标题级云盘转存/云盘搜索公开入口，统一保留前缀搜索与编号续接；补齐直链 115/夸克分享转存优先级，修复 PT 指定集/最新集筛选、下载路径透传、分页、旧别名拦截与外部智能体 Skill/命令文档同步。

- `AgentResourceOfficer 0.2.68`：收口云盘搜索/转存/影巢签到恢复链；固定“搜索/云盘搜索/转存/下载/更新检查”口径，补齐 `清空115转存目录`、`清空夸克转存目录`、插件页“立即影巢签到”、影巢 Cookie 一键刷新/签到修复 helper，以及主页/Skill 文档同步。

- `AgentResourceOfficer 0.2.67`：收口外部智能体入口细节；隐藏 `workbuddy_quickstart` 旧 recipe 展示名，为 `external-agent` / `commands` 增加 deprecated alias 语义，并统一首页、安装、外部接入、远程部署和 Skill 文档的当前状态区。
- `AgentResourceOfficer 0.2.66`：为 `request_templates` 增加 `entry_playbooks`，直接给出外部智能体、MP 内置智能体、飞书入口的 helper 命令、HTTP 端点、Tool 名称和推荐读取字段，进一步减少接入方的二次编排逻辑。
- `AgentResourceOfficer 0.2.65`：为 `request_templates` 与 helper 增加模板编排元数据，明确服务端/客户端角色、三类入口范式，以及推荐的 `startup -> decide -> route -> followup` 最小执行流。
- `AgentResourceOfficer 0.2.64`：把外部智能体执行契约与最小执行循环下沉到 `request_templates` 返回；新接入的智能体现在可以直接从模板元数据拿到 `startup -> decide -> route -> policy -> followup` 脚手架。
- `AgentResourceOfficer 0.2.63`：为 compact 顶层短命令增加执行语义字段：`command_policy`、`preferred_requires_confirmation`、`fallback_requires_confirmation`、`can_auto_run_preferred`；外部智能体现在可以机械判断“直接读”还是“先确认再写”。
- `AgentResourceOfficer 0.2.62`：把 `error_summary`、`followup_summary`、`score_summary.decision` 三层短命令继续上浮到 compact 主响应顶层；外部智能体现在只读 `preferred_command` / `compact_commands` 和 `command_source` 就能续跑。
- `AgentResourceOfficer 0.2.61`：为 compact 失败回执增加统一 `error_summary`；外部智能体现在可以直接读取失败标签、建议说明，以及 `preferred_command` / `compact_commands` 这样的最短恢复命令。
- `AgentResourceOfficer 0.2.60`：为 `score_summary.decision` 和 `followup_summary` 增加 `preferred_command`、`fallback_command` 与 `compact_commands`；`mp_recent_activity` 也补齐了 `followup_summary`，外部智能体可直接读取最短下一步命令。
- `AgentResourceOfficer 0.2.59`：新增统一 `跟进` 入口；有已执行计划时自动追执行后状态，有片名时直接查生命周期，否则退回最近活动，外部智能体只保留一个短入口也能续接。
- `AgentResourceOfficer 0.2.58`：压缩本地/PT 高跟踪入口；新增 `后续`、`状态`、`记录`、`入库`、`诊断`、`最近` 等短命令，并让推荐命令优先吐这套更省 token 的自然语言写法。
- `AgentResourceOfficer 0.2.57`：把写入动作后的追踪提示下沉为统一 `followup_summary`；执行计划、统一后续追踪和本地/PT 诊断现在都会返回稳定的后续标签、建议说明和推荐命令。
- `AgentResourceOfficer 0.2.56`：把评分后的确认提示下沉为统一 `decision` 摘要；`score_summary` 现在会稳定返回决策标签、建议说明和推荐命令，飞书、外部智能体和 MP 内置入口可以共用同一套下一步提示。
- `AgentResourceOfficer 0.2.55`：新增插件级智能体默认评分策略设置；可统一配置 `PT 最低做种数`、`建议确认分数线`、`自动入库分数线` 与 `默认自动化开关`，新会话默认偏好与 `scoring_policy` 公开数据现在统一读取这些值。
- `AgentResourceOfficer 0.2.54`：新增 `preferences_onboarding` 模板组、`评分策略` 自然语言只读入口与 helper 命令；补齐偏好/评分 smoke 覆盖，并修正能力摘要里的 `auto_ingest` 默认值。
- `AgentResourceOfficer 0.2.53`：新增本地/PT 入库诊断主线；补齐 `mp_ingest_status`、`mp_ingest_failures`、`mp_recent_activity`、`mp_local_diagnose`，并让生命周期/执行后追踪统一返回 `diagnosis_summary`。
- `AgentResourceOfficer 0.2.52`：调整 `recover` 优先级；当前会话最近一条计划已执行时，恢复入口会优先推荐 `query_execution_followup`，不再退回普通会话检查或新任务入口。
- `AgentResourceOfficer 0.2.51`：把 `execution_followup` 下沉为正式 request template 和 `followup` recipe，外部智能体可以用低 token 模板直接接到执行后只读追踪链。
- `AgentResourceOfficer 0.2.50`：补齐 `assistant/action` compact 协议，`query_execution_followup` 这类单动作返回现在也会带 `error_code`、`recommended_action` 和 `follow_up_hint`，外部智能体续接更稳定。
- `AgentResourceOfficer 0.2.49`：新增 `query_execution_followup` 统一只读入口，外部智能体可按最近已执行计划自动查询下载、订阅或入库后续状态，不必自己决定先查哪一个只读动作。
- `AgentResourceOfficer 0.2.48`：把 `recommended_action` 和 `follow_up_hint` 下沉到 `plan_execute` 的原始 data 与用户可读消息里，非 compact 调用和人工通道也能直接续接下一步。
- `AgentResourceOfficer 0.2.47`：在 `execute_plan` 的 compact 结果中补充 `recommended_action` 和 `follow_up_hint`，外部智能体执行计划后可直接读取建议下一步，不必再从模板列表里自己猜。
- `AgentResourceOfficer 0.2.46`：把 `execute_plan` 的 follow-up 样本加入 `assistant/selfcheck`，并纳入 live smoke 回归，后续即使没有真实写入执行，也能防止 PT 下载、订阅与云盘转存的后续动作模板回退。
- `AgentResourceOfficer 0.2.45`：执行 `plan_id` 成功后，会按 PT 下载、订阅或云盘转存 workflow 返回更明确的后续动作模板，方便外部智能体继续追踪状态，而不是只收到通用回执。
- `AgentResourceOfficer 0.2.44`：统一 `assistant/plan/execute` 的 compact 回执；失败态和执行态现在都会返回稳定的 `write_effect`、`error_code`、`result_summary` 与结果列表摘要，方便外部智能体续接。
- `AgentResourceOfficer 0.2.43`：调整 `recover` 优先级为业务续接优先于偏好初始化；已有 PT/云盘会话时，恢复入口会先推荐继续当前任务。
- `AgentResourceOfficer 0.2.42`：补齐 compact `session/recover` 协议里的 `action_templates`；外部智能体读取会话状态或恢复入口时，也能拿到完整的结构化下一步模板。
- `AgentResourceOfficer 0.2.41`：补齐 PT 只读会话的 `action_templates`；下载任务、站点、下载器、订阅列表等场景现在会给外部智能体正确的结构化下一步模板。
- `AgentResourceOfficer 0.2.40`：收紧 PT 只读会话的下一步建议；下载任务、站点、下载器、订阅列表等场景不再给出误导性的控制动作提示。
- `AgentResourceOfficer 0.2.39`：修复 workflow/tool 直调下的控制计划安全；空下载任务或空订阅列表时，不再为 `mp_download_control` / `mp_subscribe_control` 生成无效 `plan_id`。
- `AgentResourceOfficer 0.2.38`：修复空订阅列表下的订阅控制安全；自然语言编号必须命中当前会话列表，避免把“搜索订阅 1”误写成订阅 ID=1 的计划。
- `AgentResourceOfficer 0.2.37`：新增 `mp_pt_mainline` 与 `mp_recommendation` 请求模板 recipe，外部智能体可低 token 拉取 MP 原生 PT 主线与推荐主线模板，不再猜 workflow body。
- `AgentResourceOfficer 0.2.36`：优化评分展示文案；硬性阻断显示为“硬风险”，普通偏好未命中显示为“提醒”，避免智能体把软提醒误判为不可用。
- `AgentResourceOfficer 0.2.35`：修正 MP 推荐回退过滤；`热门电影`、`热门电视剧` 在回退到 `tmdb_trending` 时仍保留电影/电视剧类型，不再混入另一类结果。
- `AgentResourceOfficer 0.2.34`：修正 MP 原生搜索结果的下载提示；明确“下载资源 序号”会先生成下载计划，不会静默下载。
- `AgentResourceOfficer 0.2.33`：统一 MP 原生命令前缀解析；`下载历史蜘蛛侠`、`追踪蜘蛛侠`、`入库失败蜘蛛侠`、`暂停订阅1` 等无空格/冒号写法不再误落到资源搜索。
- `AgentResourceOfficer 0.2.32`：修复订阅列表自然语言解析；`订阅列表 蜘蛛侠`、`订阅列表：蜘蛛侠`、`订阅列表蜘蛛侠` 现在稳定走只读查询，不会被通用“订阅”写入计划覆盖。
- `AgentResourceOfficer 0.2.31`：收紧 compact 协议中的评分摘要返回；普通站点、下载器、任务诊断不再继承上一轮搜索的 `score_summary`，避免外部智能体误读上下文。
- `AgentResourceOfficer 0.2.30`：细化评分风险结构；`hard_risk_reasons` 表示真正阻断自动化的风险，`risk_reasons` 保留为确认前提醒，避免软提醒被误算为阻断。
- `AgentResourceOfficer 0.2.29`：收口 MP 原生 PT 主线；补齐做种/热度/字幕/站点等评分理由，下载/订阅/控制统一走 `plan_id` 确认链路，并强化 MP 原生推荐续接。
- `AgentResourceOfficer 0.2.28`：插件展示名统一改为 `Agent影视助手`，并同步仓库文档、Skill 文案和兼容插件引用。
- `AgentResourceOfficer 0.2.27`：优化盘搜和影巢资源列表的下一步提示；默认引导外部智能体先生成计划，再确认执行。
- `AgentResourceOfficer 0.2.26`：新增云盘写入计划入口；盘搜和影巢资源可用“计划选择 1”先生成 `plan_id`，再确认执行。
- `AgentResourceOfficer 0.2.25`：修复云盘会话最佳/详情选择安全；盘搜和影巢资源阶段的“最佳片源”只展示详情，不会误选最后一条执行。
- `AgentResourceOfficer 0.2.24`：补齐 PT 下载自动化闭环；仅在用户开启自动入库且评分达标、无硬风险时，下载选择和下载最佳才会直接提交。
- `AgentResourceOfficer 0.2.23`：新增偏好画像自然语言入口；可用“偏好”“保存偏好 ...”“重置偏好”查看、保存或重置智能体片源偏好。
- `AgentResourceOfficer 0.2.22`：新增计划确认自然语言入口；可用“执行计划”或“执行 plan-xxx”确认执行已生成的下载、订阅或控制计划。
- `AgentResourceOfficer 0.2.21`：新增“下载最佳”入口；在 MP 搜索会话中按最高评分 PT 候选生成下载计划，仍需用户确认 `plan_id` 后才会下载。
- `AgentResourceOfficer 0.2.20`：新增 MP 搜索最佳候选详情入口；智能体可用“最佳片源”或 `mp_search_best` 直接查看当前评分最高 PT 候选。
- `AgentResourceOfficer 0.2.19`：新增 MP 搜索结果详情入口；MP 搜索后“选择 1”会先展示 PT 详情、评分理由和风险，再由用户确认是否下载。
- `AgentResourceOfficer 0.2.18`：新增 MP 原生媒体识别详情入口；智能体可用“识别 片名”或 `mp_media_detail` 工作流确认 TMDB/Douban/IMDB 信息后再搜索、下载或订阅。
- `AgentResourceOfficer 0.2.17`：新增 MP 生命周期追踪聚合入口；智能体可用“追踪 片名”一次查看下载任务、下载历史和整理/入库历史。
- `AgentResourceOfficer 0.2.16`：新增 MP 下载历史查询，并按 hash 关联整理/入库状态；智能体可用“下载历史 片名”追踪资源是否已提交下载和是否落库。
- `AgentResourceOfficer 0.2.15`：新增 MP 整理/入库历史查询；智能体可用“入库历史”“入库失败 片名”判断下载后是否已落库，接口只返回脱敏摘要。
- `AgentResourceOfficer 0.2.14`：新增 MP 订阅列表查询与订阅控制计划；智能体可查看订阅规则，并对搜索、暂停、恢复、删除订阅生成 `plan_id` 后确认执行。
- `AgentResourceOfficer 0.2.13`：新增 MP 下载器与 PT 站点环境诊断入口；只返回启用状态、优先级、绑定下载器和 Cookie 是否存在，不暴露 Cookie 明文。
- `AgentResourceOfficer 0.2.12`：补齐 MP 原生下载任务查询与任务控制入口；智能体可查看下载中任务，并对暂停、恢复、删除生成 `plan_id` 后确认执行。
- `AgentResourceOfficer 0.2.11`：MP 下载/订阅命令支持无空格自然写法，例如“下载1”“下载第1个”“订阅蜘蛛侠”“订阅并搜索蜘蛛侠”；自然语言写入默认生成 `plan_id`，确认后才执行。
- `AgentResourceOfficer 0.2.10`：推荐列表选择支持自然语言指定后续来源，例如“选择 1 盘搜”“选择1影巢”“选 2 mp”，飞书与智能体可不用结构化 mode 参数。
- `AgentResourceOfficer 0.2.09`：热门推荐入口支持自然语言别名，例如“看看最近有什么热门影视”“豆瓣热门电影”“正在热映”“今日番剧”，智能体和飞书可直接用人话触发 MP 推荐。
- `AgentResourceOfficer 0.2.08`：MP 热门推荐列表支持保存会话并按编号继续搜索，智能体可把推荐条目直接转入 MP 原生搜索、影巢或盘搜。
- `AgentResourceOfficer 0.2.07`：影巢搜索默认使用自动媒体类型识别，未指定电影/剧集时不再提前按电影过滤，修复新剧搜索被误判无结果的问题。
- `AgentResourceOfficer 0.2.06`：新增 `scoring_policy` 能力，结构化暴露插件内置云盘/PT 评分规则与硬门槛，方便智能体解释但不重打分。
- `AgentResourceOfficer 0.2.05`：新增低 token `score_summary`，让智能体直接读取云盘和 PT 评分推荐、风险与确认建议。
- `AgentResourceOfficer 0.2.04`：增强智能体偏好引导协议，主响应返回低 token `preference_status`，未初始化时优先提示保存偏好。
- `AgentResourceOfficer 0.2.03`：新增智能体偏好画像、云盘/PT 分源评分、MP 原生搜索下载订阅推荐工作流，并让写入动作优先生成 `plan_id`。
- `AgentResourceOfficer 0.2.02`：新增影巢资源搜索/解锁总开关与单资源积分上限，降低外部智能体误解锁高积分资源的风险。
- `AgentResourceOfficer 0.2.01`：减少状态轮询时的重复工具加载日志，并同步新展示名 `Agent影视助手`、专属图标、外部智能体文档和飞书/Skill 接入口说明。
- `AgentResourceOfficer 0.1.119`：新增本插件内置影巢签到日志，可通过 API、飞书或智能体查看最近签到、自动刷新 Cookie 和失败原因。
- `AgentResourceOfficer 0.1.118`：本插件内置影巢 Cookie 自动刷新：签到兜底失败时可使用账号密码自动登录、保存新 Cookie 并重试。
- `AgentResourceOfficer 0.1.117`：影巢签到收口到本插件：新增定时签到配置、默认赌狗模式、网页 Cookie 兜底和智能入口签到命令。
- `AgentResourceOfficer 0.1.116`：新增 `workbuddy_quickstart` 请求模板和 `route_text` 模板，方便 WorkBuddy、微信侧智能体复现标准接入口。
- `AgentResourceOfficer 0.1.115`：`assistant/route` 支持 `MP搜索`、`原生搜索`、`搜索资源`、`搜索` 前缀，统一外部智能体与飞书入口的原生 MP 搜索用法。
- `AgentResourceOfficer 0.1.114`：飞书冲突检测会结合旧桥接配置、health 和 get_state，避免把已禁用但仍加载的旧插件误判为冲突。
- `AgentResourceOfficer 0.1.113`：飞书健康检查补充可启用判断、缺失项和迁移建议，便于从旧飞书桥接迁移。
- `AgentResourceOfficer 0.1.112`：修正 `assistant/startup` 在无可恢复会话时仍推荐 `continue` 的问题，避免外部智能体被空会话误导。
- `AgentResourceOfficer 0.1.111`：飞书配置页补充回复 ID 类型和命令白名单，便于从旧飞书桥接完整迁移。
- `FeishuCommandBridgeLong 0.5.26`：更新插件市场描述，明确本插件是旧飞书长连接兼容/备份入口。
- `AgentResourceOfficer 0.1.110`：飞书健康检查新增旧桥接运行状态和冲突提示，避免内置飞书入口与 `FeishuCommandBridgeLong` 同时监听同一个飞书 App。
- `AgentResourceOfficer 0.1.109` 新增 MP 原生 Tool `agent_resource_officer_feishu_health`，让内置智能助手可直接检查本插件内置飞书入口状态。
- 新增完整发布前检查脚本：`scripts/pre-release-check.sh`。
- 新增统一打包脚本：`scripts/package-plugin.sh`。
- 新增仓库布局同步脚本：`scripts/sync-repo-layout.sh`。
- GitHub Actions 已接入完整发布前检查，避免 README、package 元数据、运行代码版本和 ZIP 包产物不一致。
- `package.v2.json` 现在由 `package.json` 去除 `v2` 字段后保持一致。
- CI 已升级到 `actions/checkout@v6` 和 `actions/setup-python@v6`，并支持手动 `workflow_dispatch`。
- 发布检查现在会校验插件清单、必填元数据、图标文件、Python 语法、Skill helper 自测、Skill 安装 dry-run、ZIP 入口文件、README 和生成文件污染。
- `package-plugin.sh` 支持 `--help`、`--list`、`--all`，并支持按 `package.json` 进行大小写不敏感插件名规范化。
- `package-plugin.sh --all` 和 `pre-release-check.sh` 会在打包前清理旧 ZIP，避免旧版本附件混入发布。
- `update-draft-release-assets.sh` 会在覆盖 Draft Release 前清理旧版本 ZIP 与旧校验附件，避免同一插件多个版本同时出现在草稿附件中。

## 历史版本

## v2026.04.28.1

- 同日补丁发布，更新 `FeishuCommandBridgeLong 0.5.26`。
- 插件市场描述明确旧飞书桥接的兼容/备份定位，新用户优先使用 `AgentResourceOfficer` 内置飞书入口。
- Release 附件重新打包，包含 `FeishuCommandBridgeLong-0.5.26.zip`。

## v2026.04.28

- 正式发布多插件套件 Release，附件包含 8 个 MoviePilot 本地安装 ZIP、2 个公开 Skill ZIP、插件/Skill manifest 和 SHA256 校验文件。
- `AgentResourceOfficer 0.1.116` 作为主资源入口，统一承接影巢、盘搜、115、夸克、飞书 Channel 和智能体 Tool。
- 内置飞书入口默认关闭，可作为新远程控制入口；`FeishuCommandBridgeLong` 保留为兼容/备份插件。
- 115 直转层支持扫码会话，并在必要时回退 `P115StrmHelper`；STRM 生成和 302 仍建议由 `P115StrmHelper` 负责。
- 发布链路已验证：本地 `pre-release-check`、GitHub Actions、正式 Release 下载回验均通过。

## v2.0.0-alpha.1

- 拆分为独立插件仓库
- 统一对外文案为 AI Gateway
- 保留 `standard` / `enhanced` 识别增强模式
- 保留异步回调与二次整理流程
- 与 `moviepilot-ai-recognizer-gateway` 配套设计
