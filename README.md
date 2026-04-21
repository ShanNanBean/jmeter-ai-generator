# JMeter AI Generator

AI 驱动的 JMeter 压测脚本自动生成工具。通过自然语言描述测试场景，自动生成合法的 .jmx 文件。

## 架构

```
用户自然语言输入
        ↓
   LLM 意图解析层
        ↓
   中间表示层 (IR JSON)
        ↓
   伪脚本预览 → 用户确认/修改
        ↓
   JMX 模板引擎 + 组件库 (Jinja2)
        ↓
   合法性校验层
        ↓
   输出 .jmx 文件
```

## 功能特性

- **自然语言输入**: 用中文/英文描述测试场景，AI 自动解析为结构化测试计划
- **半结构化输入**: 支持模板化的测试规格描述
- **两阶段生成**: 先生成人类可读的伪脚本预览，确认后再生成正式 JMX
- **变量依赖链校验**: 自动检查提取器-引用链完整性，避免断链
- **QPS 推导**: 输入目标 QPS，自动推算线程数、Ramp-up、持续时间
- **多 LLM 适配**: 支持 Claude API、OpenAI API 及 OpenAI-compatible API（如 DeepSeek）
- **iframe 嵌入**: 前端构建为独立 SPA，可通过 iframe 嵌入其他系统

## 支持的 JMeter 组件 (P0+P1)

| 类别 | 组件 |
|------|------|
| Samplers | HTTPSamplerProxy, JDBCSampler, TCPSampler |
| Controllers | LoopController, IfController, WhileController, TransactionController, ForEachController |
| Assertions | ResponseAssertion, DurationAssertion, SizeAssertion, JSONAssertion |
| Extractors | JSONExtractor (JSONPath), RegexExtractor, CSSExtractor |
| Timers | ConstantTimer, UniformRandomTimer, GaussianRandomTimer |
| Config | HeaderManager, CookieManager, CacheManager, CSVDataSet |
| Data Sources | CounterConfig, UserParameters |
| Processors | JSR223PreProcessor, JSR223PostProcessor |
| Listeners | SummaryReport, SimpleDataWriter, AggregateReport, ViewResultsFullVisualizer |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+ (前端开发)
- 至少一个 LLM API Key (Anthropic 或 OpenAI)

### 安装与启动

#### 后端

```bash
# 1. 创建并激活虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动后端服务 (端口 8000)
uvicorn api.main:app --reload
```

后端 API 文档自动生成，访问 http://localhost:8000/docs 查看 Swagger UI。

#### 前端

```bash
# 1. 进入前端目录并安装依赖
cd web
npm install

# 2. 启动前端开发服务 (端口 3000，自动代理 /api 到后端 8000)
npm run dev
```

访问 http://localhost:3000 使用完整界面。

#### 前端构建 (生产部署 / iframe 嵌入)

```bash
cd web && npm run build
```

产物在 `web/dist/`，后端自动通过 `/static/` 路径提供静态文件。

生产部署时后端同时提供前端页面和 API，只需启动后端即可：

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/static/ 即可使用。

嵌入其他系统：

```html
<iframe src="http://your-host:8000/static/"
        style="width:100%;height:700px;border:none;">
</iframe>
```

### 配置 LLM

编辑 `config/llm_providers.yaml`，或通过环境变量设置 API Key：

```bash
export ANTHROPIC_API_KEY=your-key       # Claude
export OPENAI_API_KEY=your-key          # OpenAI
```

添加自定义 OpenAI-compatible API（如 DeepSeek）：

```yaml
# config/llm_providers.yaml
providers:
  deepseek:
    type: openai
    model: deepseek-chat
    base_url: https://api.deepseek.com/v1
    env_key: DEEPSEEK_API_KEY
```

## 使用示例

### 简单登录压测

输入：
> 对 https://api.example.com 的登录接口做压测，50个用户并发，持续1分钟，检查响应码为200，响应时间不超过2秒

### 多步骤业务流程

输入：
> 测试电商下单流程：1) 登录获取token 2) 浏览商品列表提取商品ID 3) 创建订单提取订单号 4) 支付，100并发持续5分钟，目标QPS 200

### 带条件判断的复杂场景

输入：
> 支付接口想加一个 IfController，只有 orderId 不为 NOT_FOUND 才执行支付

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generation/parse` | POST | 自然语言 → IR JSON |
| `/api/v1/generation/generate` | POST | IR → JMX 文件 |
| `/api/v1/generation/stream` | POST | 流式生成 (SSE) |
| `/api/v1/preview/generate` | POST | IR → 伪脚本预览 |
| `/api/v1/preview/update` | POST | 根据反馈修改 IR |
| `/api/v1/preview/dependency-check` | POST | 变量依赖链校验 |
| `/api/v1/validation/validate` | POST | 校验 JMX XML |
| `/api/v1/validation/validate-ir` | POST | 校验 IR 结构 |
| `/api/v1/config/providers` | GET | 列出可用 LLM Provider |
| `/api/v1/config/components` | GET | 列出可用组件模板 |
| `/api/v1/config/status` | GET | 服务状态 |

## 项目结构

```
jmeter-ai-generator/
├── core/                       # 核心引擎
│   ├── ir_model.py             # Pydantic IR 数据模型
│   ├── assembler.py            # IR → JMX 组装引擎 (Jinja2)
│   ├── validator.py            # JMX 校验
│   ├── llm_adapter.py          # 多 LLM Provider 适配层
│   ├── llm_parser.py           # LLM 意图解析 → IR
│   ├── scenario_preview.py     # 伪脚本生成
│   ├── dependency_checker.py   # 变量依赖链校验
│   └── qps_deriver.py          # QPS 推导引擎
├── components/                 # 30 个 Jinja2 XML 组件模板
├── config/                     # 配置文件
│   ├── settings.yaml           # 全局设置
│   └── llm_providers.yaml      # LLM Provider 配置
├── schemas/ir_schema.json      # IR JSON Schema
├── prompts/                    # LLM Prompt 工程
├── api/                        # FastAPI 后端
│   ├── routes/                 # API 路由
│   ├── models/                 # 请求/响应模型
│   └── middleware/             # CORS + 错误处理
├── web/                        # Vue 3 前端
│   ├── src/views/              # 4 个页面视图
│   ├── src/stores/             # Pinia 状态管理
│   └── src/api/                # API 客户端
├── tests/                      # 测试 (45 个)
├── extensions/                 # 自定义组件扩展
└── scripts/run_dev.py          # 开发服务器启动
```

## 测试

```bash
python -m pytest tests/ -v
```

当前 45 个测试覆盖：
- 32 个组件模板冒烟测试（所有模板渲染为有效 XML）
- 4 个依赖链校验测试
- 3 个 QPS 推导测试
- 3 个校验器测试
- 3 个组装引擎测试

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
| LLM | Claude API / OpenAI API / OpenAI-compatible |
| 模板引擎 | Jinja2 XML 模板 |
| 校验 | Python XML Parser + 规则引擎 |
| 嵌入 | iframe (SPA + 相对路径) |

## License

MIT