# JMeter AI Generator

面向 JMeter 小白的 AI 压测脚本设计助手。用户只需要描述接口、参数传递、压测目标和校验要求，系统会自动设计合理的压测执行模型，生成可预览、可编辑、可校验、可下载的 `.jmx` 文件。

## 产品定位

本项目不是要求用户直接理解 ThreadGroup、Timer、Extractor、Assertion 等 JMeter 术语，而是把业务压测需求转换为可运行的 JMeter 脚本：

- 用户描述业务接口、调用顺序、参数传递和压测目标
- AI 解析为 IR（Intermediate Representation）
- 系统展示推荐压测方案、变量传递链和合理性提醒
- 用户在编辑页按业务语言确认并调整并发、等待时间、循环、线程组等参数
- 后端组装为合法 JMX，并返回校验结果与插件兼容性提示

## 架构

```text
用户业务化压测需求
        ↓
   LLM 意图解析层
        ↓
   中间表示层 (IR JSON)
        ↓
推荐压测方案 + 伪脚本预览 + 合理性提醒
        ↓
业务化编辑确认（线程组 / 等待时间 / 参数链 / 断言）
        ↓
   JMX 模板引擎 + 组件库 (Jinja2)
        ↓
合法性校验 + 插件兼容性提示
        ↓
   输出 .jmx 文件
```

## 功能特性

- **业务化输入**：支持“自由描述 / 按要素描述”，用户无需掌握 JMeter 术语
- **解析偏好**：用“严格按描述生成 / 自动补全常见配置 / 尽量生成完整压测方案”替代裸露 temperature 参数
- **多接口链路**：支持登录、查询、下单、支付等多步骤业务流程
- **参数传递链**：自动识别 token、orderId、productId 等提取与引用关系
- **等待时间编辑**：支持固定等待、随机等待，用于模拟真实用户思考时间
- **线程组编辑**：支持多线程组、新增/删除线程组、场景归属线程组、循环次数编辑
- **合理性提醒**：提示 ramp-up 过短、持续时间过短、缺少断言、无等待时间、变量依赖缺失等问题
- **QPS 推导**：输入目标 QPS，自动推算线程数、Ramp-up、持续时间和循环参数
- **两阶段生成**：先展示推荐方案和伪脚本，确认后再生成正式 JMX
- **JMX 校验**：校验 XML 结构、hashTree 嵌套、组件关键属性和语义问题
- **插件兼容性提示**：说明当前脚本是否依赖第三方插件，或是否可用原生 JMeter 运行
- **多 LLM 适配**：支持 Claude API、OpenAI API、OpenAI-compatible API（如 Qwen、DeepSeek、本地模型等）
- **iframe 嵌入**：前端构建为独立 SPA，可通过 iframe 嵌入其他系统

## 支持的 JMeter 组件 (P0 + P1)

| 类别 | 组件 |
|------|------|
| Samplers | HTTPSamplerProxy, JDBCSampler, TCPSampler |
| Controllers | LoopController, IfController, WhileController, TransactionController, ForEachController |
| Assertions | ResponseAssertion, DurationAssertion, SizeAssertion, JSONAssertion |
| Extractors | JSONExtractor, RegexExtractor, CSSExtractor |
| Timers | ConstantTimer, UniformRandomTimer, GaussianRandomTimer |
| Config | HeaderManager, CookieManager, CacheManager, CSVDataSet |
| Data Sources | CounterConfig, UserParameters |
| Processors | JSR223PreProcessor, JSR223PostProcessor |
| Listeners | SummaryReport, SimpleDataWriter, AggregateReport, ViewResultsFullVisualizer |

> 精准 QPS / 阶梯并发类插件目前以“输入约束 + 结果页提示”为主，不会生成缺少模板支持的插件 XML。

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 至少一个可用的 LLM API Key

### 后端启动

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn api.main:app --reload
```

后端默认端口为 `8000`，API 文档可访问：

```text
http://localhost:8000/docs
```

### 前端启动

```bash
cd web
npm install
npm run dev
```

前端默认端口为 `3000`，开发环境会代理 `/api` 到后端 `8000`。

```text
http://localhost:3000
```

### 前端构建

```bash
npm run build --prefix web
```

构建产物位于 `web/dist/`。生产部署时后端可同时提供前端页面和 API：

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

访问：

```text
http://localhost:8000/static/
```

嵌入其他系统：

```html
<iframe src="http://your-host:8000/static/"
        style="width:100%;height:700px;border:none;">
</iframe>
```

## 配置 LLM

编辑 `config/llm_providers.yaml` 配置默认 Provider。支持直接在配置文件中写入 `api_key`，也支持通过 `env_key` 从环境变量读取。

### 直接配置 API Key

```yaml
default: qwen

providers:
  qwen:
    type: openai
    model: qwen-plus
    api_key: your-api-key
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    kwargs:
      timeout: 60
```

### 使用环境变量

```yaml
providers:
  claude:
    type: anthropic
    model: claude-sonnet-4-20250514
    env_key: ANTHROPIC_API_KEY
    kwargs:
      timeout: 60
```

```bash
export ANTHROPIC_API_KEY=your-key
```

### OpenAI-compatible API

```yaml
providers:
  deepseek:
    type: openai
    model: deepseek-chat
    base_url: https://api.deepseek.com/v1
    env_key: DEEPSEEK_API_KEY
```

## 使用流程

1. 在输入页选择“自由描述”或“按要素描述”
2. 填写接口步骤、参数传递、目标并发/QPS、持续时间、等待时间、校验要求
3. 选择解析偏好和插件策略
4. 生成推荐压测方案
5. 在预览页确认：
   - 系统推荐压测方案
   - 参数传递链
   - 合理性提醒
   - 伪脚本
6. 在编辑页调整：
   - 线程数、Ramp-up、持续时间、循环次数
   - 多线程组与场景归属
   - 步骤等待时间
   - 断言与提取器
   - 目标 QPS 推导
7. 生成 JMX
8. 在结果页查看校验结果、插件兼容性提示，并下载 JMX 文件

## 使用示例

### 单接口登录压测

```text
对 https://api.example.com 的登录接口做压测，50 个用户并发，持续 1 分钟，检查响应码为 200，响应时间不超过 2 秒。
```

### 多步骤业务流程

```text
测试电商下单流程：登录获取 token，浏览商品列表提取 productId，创建订单提取 orderId，最后支付。100 并发持续 5 分钟，目标 QPS 200，每步随机等待 1-3 秒。
```

### 参数传递说明

```text
登录接口返回 token，后续查询商品、创建订单、支付接口都需要在 Header 中携带 token。创建订单接口返回 orderId，支付接口 body 中使用 orderId。
```

### 多线程组并发

```text
同时模拟两类用户：普通用户浏览商品列表，100 并发持续 10 分钟；购买用户执行登录、下单、支付链路，30 并发持续 10 分钟。
```

### 原生组件优先

```text
只使用 JMeter 原生组件，不依赖第三方插件。目标尽量接近 200 QPS，如果无法精准控制，请给出可运行的近似方案。
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generation/parse` | POST | 业务描述 → IR JSON |
| `/api/v1/generation/generate` | POST | IR → JMX 文件，返回校验结果与插件提示 |
| `/api/v1/generation/derive-qps` | POST | 根据目标 QPS 推导线程组参数 |
| `/api/v1/generation/stream` | POST | 流式生成 (SSE) |
| `/api/v1/preview/generate` | POST | IR → 推荐方案、伪脚本、变量链、合理性提醒 |
| `/api/v1/preview/update` | POST | 根据用户反馈修改 IR 并重新生成预览 |
| `/api/v1/preview/dependency-check` | POST | 变量依赖链校验，返回变量来源和使用位置 |
| `/api/v1/validation/validate` | POST | 校验 JMX XML |
| `/api/v1/validation/validate-ir` | POST | 校验 IR 结构 |
| `/api/v1/validation/validate-ir-reasonable` | POST | 校验 IR 压测设计合理性 |
| `/api/v1/config/providers` | GET | 列出可用 LLM Provider |
| `/api/v1/config/components` | GET | 列出可用组件模板 |
| `/api/v1/config/jmeter-versions` | GET | 列出支持的 JMeter 版本 |
| `/api/v1/config/status` | GET | 服务状态 |

## 项目结构

```text
jmeter-ai-generator/
├── core/                         # 核心引擎
│   ├── ir_model.py               # Pydantic IR 数据模型
│   ├── assembler.py              # IR → JMX 组装引擎 (Jinja2)
│   ├── validator.py              # JMX 校验
│   ├── llm_adapter.py            # 多 LLM Provider 适配层
│   ├── llm_parser.py             # LLM 意图解析 → IR
│   ├── scenario_preview.py       # 推荐方案与伪脚本生成
│   ├── dependency_checker.py     # 变量依赖链校验与可视化数据
│   ├── sanity_checker.py         # 业务化合理性提醒
│   ├── reasonableness_checker.py # 合理性校验接口封装
│   ├── plugin_analyzer.py        # 插件依赖/兼容性提示
│   ├── qps_deriver.py            # QPS 推导引擎
│   └── path_config.py            # 项目路径配置
├── components/                   # Jinja2 XML 组件模板
├── config/                       # 配置文件
│   ├── settings.yaml             # 全局设置
│   ├── jmeter_versions.yaml      # JMeter 版本兼容配置
│   └── llm_providers.yaml        # LLM Provider 配置
├── schemas/ir_schema.json        # IR JSON Schema
├── prompts/                      # LLM Prompt 工程
├── api/                          # FastAPI 后端
│   ├── routes/                   # API 路由
│   ├── models/                   # 请求/响应模型
│   └── middleware/               # CORS + 错误处理
├── web/                          # Vue 3 前端
│   ├── src/views/                # 输入、预览、编辑、结果页
│   ├── src/stores/               # Pinia 状态管理
│   └── src/api/                  # API 客户端与类型定义
├── tests/                        # 测试
├── extensions/                   # 自定义组件扩展
└── scripts/run_dev.py            # 开发服务器启动
```

## 测试与构建

### 后端测试

```bash
python -m pytest tests/
```

当前测试覆盖：

- 组件模板渲染冒烟测试
- 组装引擎测试
- 变量依赖链校验测试
- QPS 推导测试
- JMX 校验器测试

### 前端构建

```bash
npm run build --prefix web
```

## 自定义组件扩展

编辑 `extensions/custom_components.yaml` 添加自定义 JMeter 组件：

```yaml
- name: CustomDubboSampler
  guiclass: "DubboSampleGui"
  testclass: "DubboSample"
  template: "templates/DubboSampler.xml.j2"
  description: "Dubbo RPC 协议采样器"
  params:
    - name: "interface"
      required: true
    - name: "method"
      required: true
```

LLM 会自动注入自定义组件描述到 prompt 中。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python + FastAPI + Pydantic + Jinja2 |
| 前端 | Vue 3 + Vite + Pinia + Vue Router (Hash 模式) |
| LLM | Claude API / OpenAI API / OpenAI-compatible API |
| 模板引擎 | Jinja2 XML 模板 |
| 校验 | Python XML Parser + 规则引擎 |
| 嵌入 | iframe (SPA + 相对路径) |

## License

MIT
