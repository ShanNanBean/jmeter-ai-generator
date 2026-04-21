"""IR (Intermediate Representation) data models for JMeter test plans."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ComponentType(str, Enum):
    # P0 核心组件
    HTTP_SAMPLER_PROXY = "HTTPSamplerProxy"
    THREAD_GROUP = "ThreadGroup"
    LOOP_CONTROLLER = "LoopController"
    TEST_PLAN = "TestPlan"
    RESPONSE_ASSERTION = "ResponseAssertion"
    DURATION_ASSERTION = "DurationAssertion"
    JSON_EXTRACTOR = "JSONExtractor"
    REGEX_EXTRACTOR = "RegexExtractor"
    UNIFORM_RANDOM_TIMER = "UniformRandomTimer"
    CONSTANT_TIMER = "ConstantTimer"
    HEADER_MANAGER = "HeaderManager"
    COOKIE_MANAGER = "CookieManager"
    CSV_DATA_SET = "CSVDataSet"
    SUMMARY_REPORT = "SummaryReport"
    SIMPLE_DATA_WRITER = "SimpleDataWriter"
    # P1 扩展组件
    IF_CONTROLLER = "IfController"
    WHILE_CONTROLLER = "WhileController"
    TRANSACTION_CONTROLLER = "TransactionController"
    FOR_EACH_CONTROLLER = "ForEachController"
    JDBC_SAMPLER = "JDBCSampler"
    TCP_SAMPLER = "TCPSampler"
    JSR223_PRE_PROCESSOR = "JSR223PreProcessor"
    JSR223_POST_PROCESSOR = "JSR223PostProcessor"
    COUNTER_CONFIG = "CounterConfig"
    USER_PARAMETERS = "UserParameters"
    SIZE_ASSERTION = "SizeAssertion"
    JSON_ASSERTION = "JSONAssertion"
    CSS_EXTRACTOR = "CSSExtractor"
    CACHE_MANAGER = "CacheManager"
    GAUSSIAN_RANDOM_TIMER = "GaussianRandomTimer"
    AGGREGATE_REPORT = "AggregateReport"
    VIEW_RESULTS_FULL_VISUALIZER = "ViewResultsFullVisualizer"


class AssertionModel(BaseModel):
    type: ComponentType
    name: Optional[str] = None
    # ResponseAssertion
    pattern: Optional[str] = None
    field: Optional[str] = None
    test_type: Optional[int] = None
    # DurationAssertion
    maxMs: Optional[int] = None
    # SizeAssertion
    maxSize: Optional[int] = None
    minSize: Optional[int] = None
    # JSONAssertion
    jsonPath: Optional[str] = None
    expectedValue: Optional[str] = None


class ExtractorModel(BaseModel):
    type: ComponentType
    variable: str
    # JSONExtractor
    path: Optional[str] = None
    defaultValue: Optional[str] = "NOT_FOUND"
    matchNo: Optional[int] = 0
    # RegexExtractor
    regex: Optional[str] = None
    template: Optional[str] = "$1$"
    # CSSExtractor
    expression: Optional[str] = None
    attribute: Optional[str] = None


class TimerModel(BaseModel):
    type: ComponentType
    # ConstantTimer
    delayMs: Optional[int] = None
    # UniformRandomTimer
    rangeMs: Optional[List[int]] = None
    # GaussianRandomTimer
    meanMs: Optional[int] = None
    deviationMs: Optional[int] = None


class DataSourceModel(BaseModel):
    type: ComponentType
    # CSVDataSet
    file: Optional[str] = None
    vars: Optional[List[str]] = None
    delimiter: Optional[str] = ","
    recycle: Optional[bool] = True
    stopThread: Optional[bool] = False
    # CounterConfig
    variable: Optional[str] = None
    start: Optional[int] = 1
    increment: Optional[int] = 1
    end: Optional[int] = None
    format: Optional[str] = None
    perUser: Optional[bool] = False
    # UserParameters
    parameters: Optional[List[Dict[str, str]]] = None


class ProcessorModel(BaseModel):
    type: ComponentType
    name: Optional[str] = None
    language: Optional[str] = "groovy"
    script: Optional[str] = None
    cacheKey: Optional[bool] = True


class StepModel(BaseModel):
    type: ComponentType = ComponentType.HTTP_SAMPLER_PROXY
    name: str
    # HTTPSamplerProxy
    method: Optional[str] = "GET"
    domain: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    path: Optional[str] = None
    body: Optional[str] = None
    params: Optional[List[Dict[str, str]]] = None
    headers: Optional[List[Dict[str, str]]] = None
    connectTimeout: Optional[int] = None
    responseTimeout: Optional[int] = None
    followRedirects: Optional[bool] = True
    useKeepalive: Optional[bool] = True
    multipart: Optional[bool] = False
    fileUploads: Optional[List[Dict[str, str]]] = None
    contentEncoding: Optional[str] = None
    # JDBCSampler
    dataSource: Optional[str] = None
    query: Optional[str] = None
    queryType: Optional[str] = None
    # TCPSampler
    server: Optional[str] = None
    port_tcp: Optional[int] = None
    classname: Optional[str] = None
    # 子组件
    assertions: Optional[List[AssertionModel]] = None
    extractors: Optional[List[ExtractorModel]] = None
    timers: Optional[List[TimerModel]] = None
    preProcessors: Optional[List[ProcessorModel]] = None
    postProcessors: Optional[List[ProcessorModel]] = None


class ControllerModel(BaseModel):
    type: ComponentType
    name: str
    # LoopController
    loops: Optional[int] = None
    continueForever: Optional[bool] = False
    # IfController
    condition: Optional[str] = None
    evaluateAll: Optional[bool] = False
    # WhileController
    whileCondition: Optional[str] = None
    # TransactionController
    includeTimers: Optional[bool] = False
    # ForEachController
    inputVar: Optional[str] = None
    outputVar: Optional[str] = None
    separator: Optional[str] = "_"


class ConfigElementModel(BaseModel):
    type: ComponentType
    name: Optional[str] = None
    # HeaderManager
    headers: Optional[List[Dict[str, str]]] = None
    # CookieManager
    clearEachIteration: Optional[bool] = False
    # CacheManager
    useExpires: Optional[bool] = True


class ScenarioModel(BaseModel):
    name: str
    threadGroup: str
    controllers: Optional[List[ControllerModel]] = None
    configElements: Optional[List[ConfigElementModel]] = None
    dataSources: Optional[List[DataSourceModel]] = None
    timers: Optional[List[TimerModel]] = None
    steps: List[StepModel]


class ThreadGroupModel(BaseModel):
    name: str
    threads: int = 10
    rampUp: int = 5
    duration: Optional[int] = None
    loop: Optional[int] = -1
    delay: Optional[int] = None
    onSampleError: Optional[str] = "continue"
    sameUserOnNextIteration: Optional[bool] = True


class VariableModel(BaseModel):
    key: str
    value: str


class TestPlanModel(BaseModel):
    name: str
    variables: Optional[List[VariableModel]] = None
    serializeThreadGroups: Optional[bool] = False


class ListenerModel(BaseModel):
    type: ComponentType
    name: Optional[str] = None
    file: Optional[str] = None


class IRDocument(BaseModel):
    """Complete Intermediate Representation of a JMeter test plan."""
    testPlan: TestPlanModel
    threadGroups: List[ThreadGroupModel]
    scenarios: List[ScenarioModel]
    listeners: Optional[List[ListenerModel]] = None
    configElements: Optional[List[ConfigElementModel]] = None