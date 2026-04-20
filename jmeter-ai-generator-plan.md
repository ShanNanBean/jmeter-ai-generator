# AI 自动生成 JMeter 脚本方案

## 一、整体架构

```
用户自然语言输入
        ↓
   LLM 意图解析层
        ↓
   中间表示层 (IR)
        ↓
  JMX 模板引擎 + 组件库
        ↓
   合法性校验层
        ↓
   输出 .jmx 文件
```

## 二、实现流程

### 第1步：用户输入意图 → LLM 解析

用户通过自然语言描述测试场景，LLM 将其解析为结构化的**中间表示 (IR)**。

**IR 示例 JSON：**

```json
{
  "testPlan": {
    "name": "登录接口压测",
    "variables": [{"key": "base_url", "value": "https://api.example.com"}]
  },
  "threadGroups": [
    {
      "name": "用户组",
      "threads": 100,
      "rampUp": 10,
      "duration": 300,
      "loop": -1
    }
  ],
  "scenarios": [
    {
      "name": "登录流程",
      "threadGroup": "用户组",
      "steps": [
        {
          "type": "HTTPSamplerProxy",
          "name": "登录请求",
          "method": "POST",
          "path": "/api/login",
          "body": {"username": "${user}", "password": "${pwd}"},
          "assertions": [
            {"type": "ResponseAssertion", "pattern": "200", "field": "code"},
            {"type": "DurationAssertion", "maxMs": 2000}
          ],
          "extractors": [
            {"type": "JSONExtractor", "variable": "token", "path": "$.data.token"}
          ]
        }
      ],
      "dataSources": [
        {"type": "CSVDataSet", "file": "users.csv", "vars": ["user", "pwd"]}
      ],
      "timers": [
        {"type": "UniformRandomTimer", "rangeMs": [500, 2000]}
      ]
    }
  ],
  "listeners": [
    {"type": "SummaryReport"},
    {"type": "SimpleDataWriter", "file": "results.jtl"}
  ]
}
```

### 第2步：IR → JMX 生成

使用 **JMeter HashTree API** 或 **直接 XML 模板引擎** 将 IR 转换为合法 .jmx 文件。

**两种实现路径：**

| 方式 | 优点 | 缺点 |
|------|------|------|
| **Java HashTree API** (SaveService) | 100% 合法性保证，支持所有组件 | 需要 JVM 环境，部署复杂 |
| **Python XML 模板引擎** | 部署简单，与 LLM 集成方便 | 需要自行维护组件 XML 模板库 |

**推荐：Python XML 模板引擎**，更适合 AI 集成场景。

### 第3步：合法性校验

- **结构校验**：XML schema 级别检查（hashTree 嵌套正确性、属性完整性）
- **语义校验**：组件组合合法性（如 ThreadGroup 必须包含 Controller）
- **引用校验**：变量引用存在性、CSV 文件路径有效性

### 第4步：输出 + 可选执行

- 生成 .jmx 文件供用户在 JMeter GUI 中查看/编辑
- 可选调用 `StandardJMeterEngine` 直接执行

## 三、核心实现方式

### 3.1 组件模板库

为每种 JMeter 组件建立 XML 模板，覆盖核心组件：

```
components/
├── samplers/
│   ├── HTTPSamplerProxy.xml
│   ├── JDBCSampler.xml
│   └── TCPSampler.xml
├── controllers/
│   ├── LoopController.xml
│   ├── IfController.xml
│   ├── WhileController.xml
│   ├── TransactionController.xml
│   └── ForEachController.xml
├── assertions/
│   ├── ResponseAssertion.xml
│   ├── DurationAssertion.xml
│   ├── SizeAssertion.xml
│   └── JSONAssertion.xml
├── extractors/
│   ├── RegexExtractor.xml
│   ├── JSONExtractor.xml
│   └── CSSExtractor.xml
├── timers/
│   ├── ConstantTimer.xml
│   ├── UniformRandomTimer.xml
│   └── GaussianRandomTimer.xml
├── config/
│   ├── HeaderManager.xml
│   ├── CookieManager.xml
│   ├── CacheManager.xml
│   └── CSVDataSet.xml
├── data_sources/
│   ├── CounterConfig.xml
│   └── UserParameters.xml
├── processors/
│   ├── JSR223PreProcessor.xml
│   ├── JSR223PostProcessor.xml
├── listeners/
│   ├── SummaryReport.xml
│   ├── SimpleDataWriter.xml
│   ├── AggregateReport.xml
│   └── ViewResultsFullVisualizer.xml
└── TestPlan.xml
    ThreadGroup.xml
```

每个模板包含该组件的**完整 XML 结构骨架**，参数通过占位符填充：

```xml
<!-- HTTPSamplerProxy.xml 模板示例 -->
<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{{name}}">
  <stringProp name="HTTPSampler.domain">{{domain}}</stringProp>
  <stringProp name="HTTPSampler.port">{{port}}</stringProp>
  <stringProp name="HTTPSampler.protocol">{{protocol}}</stringProp>
  <stringProp name="HTTPSampler.path">{{path}}</stringProp>
  <stringProp name="HTTPSampler.method">{{method}}</stringProp>
  <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
  <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
  {{#if body}}
  <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
  <elementProp name="HTTPSampler.arguments" elementType="Arguments">
    <collectionProp name="Arguments.arguments">
      <elementProp name="" elementType="HTTPArgument">
        <boolProp name="HTTPArgument.always_encode">false</boolProp>
        <stringProp name="Argument.value">{{body}}</stringProp>
      </elementProp>
    </collectionProp>
  </elementProp>
  {{/if}}
  {{#if params}}
  <elementProp name="HTTPSampler.arguments" elementType="Arguments">
    <collectionProp name="Arguments.arguments">
      {{#each params}}
      <elementProp name="{{name}}" elementType="HTTPArgument">
        <stringProp name="Argument.name">{{name}}</stringProp>
        <stringProp name="Argument.value">{{value}}</stringProp>
      </elementProp>
      {{/each}}
    </collectionProp>
  </elementProp>
  {{/if}}
  {{#if fileUploads}}
  <boolProp name="HTTPSampler.use_multipart">true</boolProp>
  <elementProp name="HTTPsampler.Files" elementType="HTTPFileArgs">
    <collectionProp name="HTTPFileArgs.files">
      {{#each fileUploads}}
      <elementProp name="{{paramName}}" elementType="HTTPFileArg">
        <stringProp name="File.path">{{filePath}}</stringProp>
        <stringProp name="File.paramname">{{paramName}}</stringProp>
        <stringProp name="File.mimetype">{{mimeType}}</stringProp>
      </elementProp>
      {{/each}}
    </collectionProp>
  </elementProp>
  {{/if}}
</HTTPSamplerProxy>
```

### 3.2 组装引擎

Python 实现，按 HashTree 嵌套规则组装组件：

```python
class JMXAssembler:
    """按 JMeter HashTree 规范组装 JMX XML"""

    # 组件嵌套层级规则
    NESTING_RULES = {
        "CounterConfig":    ["threadGroupTree", "controllerTree"],
        "CSVDataSet":       ["threadGroupTree", "controllerTree"],
        "JSR223PreProcessor": ["samplerTree"],
        "JSR223PostProcessor": ["samplerTree"],
        "RegexExtractor":   ["samplerTree"],
        "JSONExtractor":    ["samplerTree"],
        "ResponseAssertion": ["samplerTree"],
        "DurationAssertion": ["samplerTree"],
        "UniformRandomTimer": ["threadGroupTree", "controllerTree", "samplerTree"],
        "TransactionController": ["threadGroupTree"],
        "HeaderManager":   ["samplerTree", "threadGroupTree"],
    }

    def assemble(self, ir: dict) -> str:
        root = self._create_root()
        plan_tree = self._add_testplan(root, ir["testPlan"])
        for tg in ir["threadGroups"]:
            tg_tree = self._add_threadgroup(plan_tree, tg)
            for scenario in ir["scenarios"]:
                if scenario["threadGroup"] == tg["name"]:
                    self._add_scenario(tg_tree, scenario)
        self._add_listeners(plan_tree, ir["listeners"])
        return self._serialize(root)

    def _add_scenario(self, parent, scenario):
        # 添加 Controller 包裹
        controller = self._add_controller(parent, scenario)
        ctrl_tree = parent.add_hashTree(controller)
        # 添加 DataSource
        for ds in scenario.get("dataSources", []):
            ctrl_tree.add_component(self._render(ds))
        # 添加 Timers
        for timer in scenario.get("timers", []):
            ctrl_tree.add_component(self._render(timer))
        # 添加 Steps (Samplers)
        for step in scenario["steps"]:
            sampler = ctrl_tree.add_component(self._render(step))
            sampler_tree = ctrl_tree.add_hashTree(sampler)
            # Assertions 和 Extractors 作为 Sampler 的子节点
            for assertion in step.get("assertions", []):
                sampler_tree.add_component(self._render(assertion))
            for extractor in step.get("extractors", []):
                sampler_tree.add_component(self._render(extractor))

    def _add_step(self, parent_tree, step_ir):
        """组装单个 Sampler 及其附属组件"""
        sampler_xml = self.render_component("HTTPSamplerProxy", step_ir)
        sampler_tree = parent_tree.add(sampler_xml)

        # 附属组件按 JMeter 规范顺序排列
        for pre in step_ir.get("preProcessors", []):
            sampler_tree.add(self.render_component(pre["type"], pre))
        for ext in step_ir.get("extractors", []):
            sampler_tree.add(self.render_component(ext["type"], ext))
        for assertion in step_ir.get("assertions", []):
            sampler_tree.add(self.render_component(assertion["type"], assertion))

        return sampler_tree
```

### 3.3 LLM 集成层

LLM 负责：**自然语言 → IR JSON**

```python
PROMPT_TEMPLATE = """
你是 JMeter 压测脚本生成器。根据用户描述，输出以下 JSON 格式的测试计划 IR。

可用组件类型：
- Samplers: HTTPSamplerProxy, JDBCSampler, TCPSampler
- Controllers: LoopController, IfController, WhileController, TransactionController, ForEachController
- Assertions: ResponseAssertion, DurationAssertion, SizeAssertion, JSONAssertion
- Extractors: JSONExtractor (JSONPath), RegexExtractor, CSSExtractor
- Timers: ConstantTimer, UniformRandomTimer, GaussianRandomTimer
- DataSources: CSVDataSet, UserParameters, CounterConfig
- ConfigElements: HeaderManager, CookieManager, CacheManager, Authorization
- Processors: JSR223PreProcessor, JSR223PostProcessor
- Listeners: SummaryReport, SimpleDataWriter, ViewResultsFullVisualizer, AggregateReport

IR 格式规范：
{ir_schema}

用户描述：
{user_input}

请输出合法的 IR JSON，不要输出其他内容。
"""
```

### 3.4 校验器

```python
class JMXValidator:
    """校验生成的 JMX 文件合法性"""

    RULES = {
        # 结构规则
        "hashTree_nesting": "每个 TestElement 后必须紧跟 hashTree",
        "threadgroup_controller": "ThreadGroup 内必须包含 Controller",
        "sampler_under_controller": "Sampler 必须在 Controller 或 ThreadGroup 下",
        # 属性规则
        "required_props": {
            "HTTPSamplerProxy": ["domain", "path", "method"],
            "ThreadGroup": ["num_threads", "ramp_time"],
            "LoopController": ["loops"],
        },
        # 语义规则
        "variable_reference": "引用的变量必须存在定义",
        "csv_columns": "CSVDataSet 的变量名必须匹配 CSV 列数",
    }

    def validate(self, jmx_str: str) -> ValidationResult:
        # XML 解析 + 规则校验
        ...
```

## 四、用户输入要求

### 4.1 输入格式

支持三种输入方式，按自由度递减排列：

| 方式 | 示例 | 适用场景 |
|------|------|----------|
| **自然语言** | "对 https://api.example.com 的登录接口做压测，100个用户并发，持续5分钟，检查响应时间不超过2秒" | 非技术用户 |
| **半结构化** | 见下方模板 | 技术用户，精确控制 |
| **API Spec + 补充** | 提供 Swagger/OpenAPI JSON + 压测参数描述 | 已有 API 文档的项目 |

**半结构化输入模板：**

```
目标: https://api.example.com
场景: 登录接口压测

线程组:
  - 名称: 用户组
  - 并发数: 100
  - ramp-up: 10秒
  - 持续时间: 5分钟

请求序列:
  1. POST /api/login
     - Body: {"username": "${user}", "password": "${pwd}"}
     - 提取: token = $.data.token
     - 断言: 响应码 200, 响应时间 < 2s
  2. GET /api/profile
     - Header: Authorization: Bearer ${token}
     - 断言: 响应码 200

数据源: users.csv (字段: user, pwd)
思考时间: 0.5-2秒随机
```

### 4.2 输入约束

- **必填项**：目标 URL/域名、至少一个请求
- **选填项**：并发数（默认 10）、持续时间（默认 60s）、断言、提取器、数据源
- **LLM 会自动推断**：缺失的合理默认值（如 port 根据 protocol 推断，Header 根据接口类型推断）

## 五、复杂场景实现能力

### 5.1 接口间参数传递（正则提取 → 传递）

**用户输入：**
```
A接口返回 {"code":0,"data":{"orderId":"ORD20260420-001"}}
用正则提取 orderId，传给B接口 /api/pay 的 body
```

**IR 表示：**

```json
{
  "steps": [
    {
      "type": "HTTPSamplerProxy",
      "name": "下单接口",
      "method": "POST",
      "path": "/api/order",
      "extractors": [
        {
          "type": "RegexExtractor",
          "variable": "orderId",
          "regex": "orderId\":\"([^\"]+)\"",
          "template": "$1$",
          "matchNo": 1,
          "defaultValue": "NOT_FOUND"
        }
      ]
    },
    {
      "type": "HTTPSamplerProxy",
      "name": "支付接口",
      "method": "POST",
      "path": "/api/pay",
      "body": "{\"orderId\":\"${orderId}\"}",
      "headers": [{"key": "Content-Type", "value": "application/json"}]
    }
  ]
}
```

**对应 JMX XML（关键片段）：**

```xml
<!-- 正则提取器 -->
<RegexExtractor guiclass="RegexExtractorGui" testclass="RegexExtractor" testname="提取orderId">
  <stringProp name="RegexExtractor.useHeaders">false</stringProp>
  <stringProp name="RegexExtractor.refname">orderId</stringProp>
  <stringProp name="RegexExtractor.regex">orderId":"([^"]+)"</stringProp>
  <stringProp name="RegexExtractor.template">$1$</stringProp>
  <stringProp name="RegexExtractor.match_number">1</stringProp>
  <stringProp name="RegexExtractor.default_value">NOT_FOUND</stringProp>
</RegexExtractor>

<!-- B接口引用变量 -->
<stringProp name="Argument.value">{"orderId":"${orderId}"}</stringProp>
```

### 5.2 文件上传

**用户输入：**
```
B接口需要上传文件，multipart/form-data，字段名 file，文件路径 /data/report.csv
```

**IR 表示：**

```json
{
  "type": "HTTPSamplerProxy",
  "name": "文件上传",
  "method": "POST",
  "path": "/api/upload",
  "multipart": true,
  "fileUploads": [
    {
      "paramName": "file",
      "filePath": "/data/report.csv",
      "mimeType": "text/csv"
    }
  ],
  "formFields": [
    {"name": "description", "value": "月度报告"}
  ]
}
```

**对应 JMX XML：**

```xml
<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="文件上传">
  <stringProp name="HTTPSampler.method">POST</stringProp>
  <boolProp name="HTTPSampler.use_multipart">true</boolProp>
  <elementProp name="HTTPsampler.Files" elementType="HTTPFileArgs">
    <collectionProp name="HTTPFileArgs.files">
      <elementProp name="file" elementType="HTTPFileArg">
        <stringProp name="File.path">/data/report.csv</stringProp>
        <stringProp name="File.paramname">file</stringProp>
        <stringProp name="File.mimetype">text/csv</stringProp>
      </elementProp>
    </collectionProp>
  </elementProp>
  <elementProp name="HTTPSampler.arguments" elementType="Arguments">
    <collectionProp name="Arguments.arguments">
      <elementProp name="description" elementType="HTTPArgument">
        <stringProp name="Argument.name">description</stringProp>
        <stringProp name="Argument.value">月度报告</stringProp>
      </elementProp>
    </collectionProp>
  </elementProp>
</HTTPSamplerProxy>
```

### 5.3 计数器

**用户输入：**
```
需要一个计数器，从1开始每次递增1，存到变量 counter，给每个请求编号
```

**IR 表示：**

```json
{
  "type": "CounterConfig",
  "name": "请求计数器",
  "variable": "counter",
  "start": 1,
  "increment": 1,
  "end": 999999,
  "format": "000000",
  "perUser": false
}
```

**对应 JMX XML：**

```xml
<CounterConfig guiclass="CounterConfigGui" testclass="CounterConfig" testname="请求计数器">
  <stringProp name="CounterConfig.start">1</stringProp>
  <stringProp name="CounterConfig.increment">1</stringProp>
  <stringProp name="CounterConfig.end">999999</stringProp>
  <stringProp name="CounterConfig.format">000000</stringProp>
  <stringProp name="CounterConfig.var_name">counter</stringProp>
  <boolProp name="CounterConfig.per_user">false</boolProp>
</CounterConfig>
```

### 5.4 JSR223 / BeanShell 脚本

**用户输入：**
```
在请求前用BeanShell生成一个随机签名 sign=MD5(timestamp+secret+body)，
存到变量 signStr，然后在请求Header里带上去
```

**IR 表示：**

```json
{
  "type": "JSR223PreProcessor",
  "name": "生成签名",
  "language": "groovy",
  "script": "import java.security.MessageDigest\ndef md5(s) { MessageDigest.getInstance('MD5').digest(s.bytes).encodeHex().toString() }\ndef ts = System.currentTimeMillis().toString()\ndef body = vars.get('requestBody')\ndef secret = vars.get('appSecret')\nvars.put('signStr', md5(ts + secret + body))\nvars.put('timestamp', ts)",
  "cacheKey": true
}
```

**对应 JMX XML：**

```xml
<JSR223PreProcessor guiclass="JSR223PreProcessorGui" testclass="JSR223PreProcessor" testname="生成签名">
  <stringProp name="scriptLanguage">groovy</stringProp>
  <stringProp name="parameters"></stringProp>
  <stringProp name="cacheKey">true</stringProp>
  <stringProp name="script">import java.security.MessageDigest
def md5(s) { MessageDigest.getInstance('MD5').digest(s.bytes).encodeHex().toString() }
def ts = System.currentTimeMillis().toString()
def body = vars.get('requestBody')
def secret = vars.get('appSecret')
vars.put('signStr', md5(ts + secret + body))
vars.put('timestamp', ts)</stringProp>
</JSR223PreProcessor>
```

### 5.5 综合复杂场景组合

把以上所有组合在一起时的 IR：

```json
{
  "testPlan": { "name": "下单支付上传复杂流程" },
  "threadGroups": [{
    "name": "用户流程",
    "threads": 50,
    "rampUp": 10,
    "duration": 300
  }],
  "scenarios": [{
    "name": "完整业务流程",
    "threadGroup": "用户流程",
    "controllers": [{
      "type": "TransactionController",
      "name": "下单-支付-上传",
      "includeTimers": true
    }],
    "configElements": [
      { "type": "CounterConfig", "variable": "counter", "start": 1, "increment": 1 },
      { "type": "CSVDataSet", "file": "users.csv", "vars": ["user", "pwd", "secret"], "delimiter": "," }
    ],
    "timers": [
      { "type": "UniformRandomTimer", "rangeMs": [500, 2000] }
    ],
    "steps": [
      {
        "type": "HTTPSamplerProxy",
        "name": "下单",
        "method": "POST",
        "path": "/api/order",
        "body": "{\"user\":\"${user}\",\"counter\":\"${counter}\"}",
        "preProcessors": [{
          "type": "JSR223PreProcessor",
          "language": "groovy",
          "script": "vars.put('requestBody', '{\"user\":\"' + vars.get('user') + '\"}')"
        }],
        "extractors": [
          { "type": "RegexExtractor", "variable": "orderId", "regex": "orderId\":\"([^\"]+)\"" },
          { "type": "JSONExtractor", "variable": "orderStatus", "path": "$.data.status" }
        ],
        "assertions": [
          { "type": "ResponseAssertion", "pattern": "200", "field": "code" },
          { "type": "DurationAssertion", "maxMs": 3000 }
        ]
      },
      {
        "type": "HTTPSamplerProxy",
        "name": "支付",
        "method": "POST",
        "path": "/api/pay",
        "body": "{\"orderId\":\"${orderId}\"}",
        "extractors": [
          { "type": "JSONExtractor", "variable": "payToken", "path": "$.data.token" }
        ]
      },
      {
        "type": "HTTPSamplerProxy",
        "name": "上传报告",
        "method": "POST",
        "path": "/api/upload",
        "multipart": true,
        "fileUploads": [{ "paramName": "file", "filePath": "/data/${orderId}.csv" }],
        "headers": [
          { "key": "Authorization", "value": "Bearer ${payToken}" }
        ]
      }
    ]
  }],
  "listeners": [
    { "type": "SummaryReport" },
    { "type": "SimpleDataWriter", "file": "results.jtl" }
  ]
}
```

### 5.6 复杂度极限评估

| 复杂度等级 | 场景 | 可自动化程度 |
|-----------|------|-------------|
| **简单** | 单接口 HTTP 压测 + 基本断言 | 100% |
| **中等** | 多接口串行、变量传递、CSV参数化、JSON提取 | 95% |
| **复杂** | 正则提取 + 文件上传 + 计数器 + 事务控制器 | 90% |
| **高复杂** | 以上 + JSR223脚本 + If/While控制流 + 数据依赖链 | 85% |
| **极高** | 自定义 Sampler + Dubbo/Kafka + 复杂 BeanShell 业务逻辑 | 70-80% |

**85%+ 的常见复杂场景都可以自动生成**，剩余部分通过用户确认后微调即可。

## 六、两阶段生成：伪脚本 → 确认 → 正式脚本

### 6.1 第一阶段：生成伪脚本（Scenario Preview）

伪脚本不是可执行的 JMX，而是**人类可读的业务流程描述 + 压测参数设计**，让用户确认意图理解是否正确。

**用户输入示例：**

```
我想测试一个电商下单流程的性能：
- 用户先登录，拿到token
- 然后浏览商品列表，随机选一个商品
- 下单，提取订单号
- 支付，上传支付凭证
- 目标 QPS 500，想验证在 500 QPS 下订单创建成功率不低于 99%，响应时间 P99 < 3s
```

**系统输出伪脚本：**

```
╔══════════════════════════════════════════════════════════════╗
║  压测场景预览 — 电商下单全流程                                ║
╠══════════════════════════════════════════════════════════════╣

【压测参数设计】
  目标QPS: 500
  → 线程数: 100 (按平均RT 200ms 计算: QPS = threads / RT)
  → Ramp-up: 20秒 (逐步加压避免瞬时冲击)
  → 持续时间: 10分钟 (稳态观察期)
  → 循环次数: 持续模式 (-1, 由duration控制)

【业务流程】
  Step 1 — 登录
    POST ${base_url}/api/login
    Body: {"username": "${user}", "password": "${pwd}"}
    提取: token ← JSON $.data.token
    断言: HTTP 200, RT < 1s

  Step 2 — 浏览商品
    GET ${base_url}/api/products?page=1&size=20
    提取: productId ← JSON $.data.items[${randomIdx}].id
    断言: HTTP 200

  Step 3 — 创建订单
    POST ${base_url}/api/order
    Body: {"productId": "${productId}", "quantity": 1}
    Header: Authorization: Bearer ${token}
    提取: orderId ← Regex "orderId":"([^"]+)"
    断言: HTTP 200, RT < 3s, body含"success"

  Step 4 — 支付
    POST ${base_url}/api/pay
    Body: {"orderId": "${orderId}", "method": "alipay"}
    Header: Authorization: Bearer ${token}
    提取: payUrl ← JSON $.data.payUrl
    断言: HTTP 200

  Step 5 — 上传支付凭证
    POST ${base_url}/api/upload/receipt
    Multipart: file=${orderId}_receipt.png
    Header: Authorization: Bearer ${token}
    断言: HTTP 200

【数据源】
  CSV: users.csv (字段: user, pwd)
  计数器: requestNo (1→∞, 格式0001)

【全局配置】
  思考时间: 0.5~2秒随机 (模拟真实用户)
  Cookie管理: 开启
  超时设置: 连接5s, 响应10s
  失败重试: 不重试 (避免干扰压测数据)

【结果收集】
  聚合报告 + 结果文件(results.jtl) + 响应码分布图

【验证指标】
  ✓ 订单创建成功率 ≥ 99%  → ResponseAssertion + 聚合统计
  ✓ P99 响应时间 < 3s     → DurationAssertion(maxMs=3000) + 聚合统计
  ✓ 整体 QPS ≥ 500        → 聚合报告 Throughput 列

╚══════════════════════════════════════════════════════════════╝

是否确认此场景？回复"确认"生成正式JMX脚本，或提出修改意见。
```

### 6.2 第二阶段：确认后生成正式 JMX

用户确认后，系统将伪脚本对应的 IR 转换为完整 .jmx 文件。

**确认交互流程：**

```
用户: 确认，但支付接口想加一个 IfController，只有orderId不为NOT_FOUND才支付
系统: 修改已更新，生成 JMX...

       ↓ 正式生成 .jmx

用户: 第3步的商品ID想用随机函数而不是固定索引
系统: 已修改，将 JSONExtractor 的 randomIdx 替换为 __Random 函数...
      → 重新生成
```

### 6.3 LLM 生成伪脚本的关键 Prompt 设计

```python
SCENARIO_PREVIEW_PROMPT = """
你是压测场景设计师。根据用户的业务描述和性能目标，设计完整的压测方案。

输出格式为【伪脚本】，包含以下部分：

1. 【压测参数设计】— 根据目标QPS推导线程数、ramp-up、持续时间
   公式参考：
   - QPS = 线程数 / 平均RT(秒)
   - 若目标QPS=500，预估RT=200ms → 线程数≈100
   - Ramp-up ≈ 线程数×0.2秒（平滑加压）
   - 持续时间 ≥ 10分钟（稳态观察）

2. 【业务流程】— 每个Step列出：
   - HTTP方法和路径
   - 请求参数/Body（标注变量引用 ${var}）
   - 需要提取的变量（标注提取方式：JSON/Regex/CSS）
   - 断言要求

3. 【数据源】— CSV参数化、计数器等

4. 【全局配置】— 思考时间、超时、Cookie等

5. 【结果收集】— Listener配置

6. 【验证指标】— 将用户的验证目标映射到具体的JMeter断言和统计方式

重要规则：
- 变量传递链必须完整：A提取的变量必须在B中引用，不能断裂
- 如果提取失败要有默认值，避免后续请求报错
- 文件上传场景标注 Multipart
- JSR223脚本只在必要时使用（签名计算、复杂逻辑等）
- 优先用JMeter内置函数(__Random, __counter, __time等)代替BeanShell

用户描述：
{user_input}
"""
```

### 6.4 QPS 推导引擎

当用户给出 QPS 目标时，自动推算线程配置：

```python
class QPSDeriver:
    """根据目标QPS推算线程组参数"""

    KNOWN_RT_ESTIMATES = {
        # 常见接口的预估RT，用于初始计算
        "login":       200,   # ms
        "query":       100,
        "create":      300,
        "upload":      500,
        "payment":     400,
        "default":     200,
    }

    def derive(self, target_qps: int, scenario_steps: list) -> dict:
        # 计算单次流程总RT
        total_rt = sum(
            self.KNOWN_RT_ESTIMATES.get(s.get("type", "default"), 200)
            for s in scenario_steps
        )
        # 加上思考时间
        think_time_avg = 1250  # 0.5-2s 随机，均值1.25s

        cycle_time = total_rt / 1000 + think_time_avg  # 单次循环时间(秒)

        # QPS = threads / cycle_time
        threads = int(target_qps * cycle_time)
        threads = max(threads, 10)  # 最小10线程

        ramp_up = max(int(threads * 0.2), 5)
        duration = 600  # 默认10分钟

        return {
            "threads": threads,
            "rampUp": ramp_up,
            "duration": duration,
            "loop": -1,
            "note": f"目标QPS={target_qps}, 预估单流程RT={total_rt}ms+思考时间{think_time_avg}ms, "
                    f"周期={cycle_time:.1f}s, 需要{threads}线程"
        }
```

### 6.5 变量依赖链校验

伪脚本确认前，自动校验变量传递链是否完整：

```python
class DependencyChecker:
    """检查变量定义和引用的完整性"""

    def check(self, scenario_ir: dict) -> list[str]:
        defined_vars = set()
        issues = []

        # 收集全局变量定义
        for ds in scenario_ir.get("dataSources", []):
            if ds["type"] == "CSVDataSet":
                defined_vars.update(ds["vars"])
            if ds["type"] == "CounterConfig":
                defined_vars.add(ds["variable"])

        # 收集提取器产出的变量
        for step in scenario_ir["steps"]:
            for ext in step.get("extractors", []):
                defined_vars.add(ext["variable"])

        # 检查每个引用是否在之前的步骤中被定义
        available_at_step = set(defined_vars)
        for i, step in enumerate(scenario_ir["steps"]):
            referenced = self._extract_references(step)
            for ref in referenced:
                if ref not in available_at_step:
                    issues.append(
                        f"Step{i+1} '{step['name']}' 引用了 ${ref}，"
                        f"但该变量在此之前未被定义（缺少提取器或数据源）"
                    )
            for ext in step.get("extractors", []):
                available_at_step.add(ext["variable"])

        return issues
```

**伪脚本生成时自动附带校验结果：**

```
【变量依赖校验】
  ✓ token      → Step1提取, Step2/3/4/5引用 → OK
  ✓ productId  → Step2提取, Step3引用        → OK
  ✓ orderId    → Step3提取, Step4/5引用      → OK
  ✓ user/pwd   → CSV数据源                  → OK
  ✗ signStr    → Step3引用, 但未定义提取器    → 需补充签名生成逻辑
```

## 七、完整交互流程

```
┌──────────────────────────────────────────────┐
│ 用户输入                                      │
│ "电商下单流程，目标500QPS，                    │
│  成功率≥99%，P99<3s"                          │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│ LLM 解析 + QPS推导 + 依赖校验                 │
│ → 生成伪脚本                                  │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│ 伪脚本展示给用户                               │
│ （人类可读，含流程、参数、校验结果）            │
└──────────────────┬───────────────────────────┘
                   ↓
          ┌────────┴────────┐
          │ 用户反馈        │
     ┌────┴────┐       ┌────┴────┐
     │ 确认    │       │ 修改    │
     └────┬────┘       └────┬────┘
          ↓                 ↓
          │          LLM 修改伪脚本
          │          → 再次展示
          │                 │
          ↓                 ↓ (最终确认)
┌──────────────────────────────────────────────┐
│ IR → JMX 组装引擎 → 校验器                    │
│ → 输出 .jmx 文件                              │
└──────────────────┬───────────────────────────┘
                   ↓
┌──────────────────────────────────────────────┐
│ 可选：JMeter 非GUI模式执行                     │
│ → 结果分析反馈                                │
└──────────────────────────────────────────────┘
```

## 八、技术选型

| 层 | 技术 | 说明 |
|----|------|------|
| LLM | Claude API / OpenAI API | 意图解析 + IR 生成 |
| 中间表示 | JSON IR | 结构化测试计划描述 |
| 生成引擎 | Python + XML 模板 (Jinja2) | 组件模板库 + 组装逻辑 |
| 校验 | Python XML Parser + 规则引擎 | 结构 + 语义校验 |
| 执行（可选） | JMeter CLI 非GUI模式 | `jmeter -n -t xxx.jmx` |
| 前端（可选） | Web UI / CLI | 用户交互界面 |

## 九、扩展插件机制

支持自定义组件模板，用户可扩展 JMeter 插件组件：

```yaml
# custom_components.yaml
- name: CustomDubboSampler
  guiclass: "DubboSampleGui"
  testclass: "DubboSample"
  template: "templates/DubboSampler.xml"
  description: "Dubbo RPC 协议采样器"
  params:
    - name: "interface"
      required: true
    - name: "method"
      required: true
    - name: "version"
      default: "1.0.0"
```

LLM prompt 中会自动注入这些自定义组件的描述，使其能理解并生成包含自定义组件的 IR。

## 十、项目结构

```
jmeter-ai-generator/
├── core/
│   ├── llm_parser.py          # LLM 意图解析 → IR
│   ├── assembler.py           # IR → JMX 组装
│   ├── validator.py           # JMX 校验
│   ├── executor.py            # JMX 执行（可选）
│   ├── qps_deriver.py         # QPS推导引擎
│   └── dependency_checker.py  # 变量依赖链校验
│   └── scenario_preview.py    # 伪脚本生成与展示
├── components/                # 组件 XML 模板库
│   ├── samplers/
│   ├── controllers/
│   ├── assertions/
│   ├── extractors/
│   ├── timers/
│   ├── config/
│   ├── listeners/
│   ├── data_sources/
│   └── processors/
├── extensions/                # 自定义组件扩展
│   └── custom_components.yaml
├── schemas/
│   ├── ir_schema.json         # IR 格式定义
│   └── jmx_schema.xsd         # JMX 结构校验
├── prompts/
│   ├── system_prompt.md       # LLM 系统提示词
│   ├── component_catalog.md   # 组件目录描述
│   └── examples/              # IR 生成示例
├── web/                       # 前端 UI（可选）
├── tests/
└── main.py
```

## 十一、路线图

| 阶段 | 内容 | 产出 |
|------|------|------|
| **P0** | 组件模板库（HTTPSampler、ThreadGroup、基本断言/提取器）+ LLM 解析 + JMX 生成 + 伪脚本交互 | 核心可用 |
| **P1** | 扩展组件（JDBC、TCP、If/While 控制器、事务控制器、JSR223、文件上传）+ 校验器 + 变量依赖链 | 完善覆盖 |
| **P2** | Swagger/OpenAPI 导入 + HAR 导入 + 自定义组件扩展 + QPS推导 | 多源输入 |
| **P3** | Web UI + 执行回调 + 结果分析反馈 | 闭环体验 |