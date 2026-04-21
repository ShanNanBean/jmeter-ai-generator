# Component Catalog

Available JMeter component types for IR generation:

## Samplers
- **HTTPSamplerProxy**: HTTP request sampler. Fields: name, method, domain, port, protocol, path, body, params, headers, connectTimeout, responseTimeout, followRedirects, useKeepalive, multipart, fileUploads
- **JDBCSampler**: Database query sampler. Fields: name, dataSource, query, queryType
- **TCPSampler**: TCP protocol sampler. Fields: name, server, port_tcp, classname

## Controllers
- **LoopController**: Loop execution N times. Fields: name, loops, continueForever
- **IfController**: Conditional execution. Fields: name, condition, evaluateAll
- **WhileController**: Loop while condition is true. Fields: name, whileCondition
- **TransactionController**: Group steps as a transaction. Fields: name, includeTimers
- **ForEachController**: Iterate over variable prefix. Fields: name, inputVar, outputVar, separator

## Assertions
- **ResponseAssertion**: Check response content/code. Fields: name, pattern, field, test_type
  - field: "16"=Response Code, "2"=Response Data, "4"=Response Headers
  - test_type: 8=Equals, 2=Contains, 4=Matches, 1=Substring
- **DurationAssertion**: Check response time. Fields: name, maxMs
- **SizeAssertion**: Check response size. Fields: name, maxSize, minSize
- **JSONAssertion**: Check JSON value. Fields: name, jsonPath, expectedValue

## Extractors
- **JSONExtractor**: Extract value via JSONPath. Fields: variable, path, defaultValue, matchNo
- **RegexExtractor**: Extract value via regex. Fields: variable, regex, template, defaultValue, matchNo
- **CSSExtractor**: Extract via CSS selector. Fields: variable, expression, attribute, defaultValue, matchNo

## Timers
- **ConstantTimer**: Fixed delay. Fields: delayMs
- **UniformRandomTimer**: Random delay in range. Fields: rangeMs [min, max]
- **GaussianRandomTimer**: Gaussian distribution delay. Fields: meanMs, deviationMs

## Config Elements
- **HeaderManager**: HTTP headers. Fields: name, headers [{key, value}]
- **CookieManager**: Cookie handling. Fields: name, clearEachIteration
- **CacheManager**: HTTP cache. Fields: name, clearEachIteration, useExpires
- **CSVDataSet**: CSV data parameterization. Fields: name, file, vars, delimiter, recycle, stopThread

## Data Sources
- **CounterConfig**: Incrementing counter. Fields: name, variable, start, increment, end, format, perUser
- **UserParameters**: Static parameter sets. Fields: name, parameters

## Processors
- **JSR223PreProcessor**: Pre-request script. Fields: name, language, script, cacheKey
- **JSR223PostProcessor**: Post-response script. Fields: name, language, script, cacheKey

## Listeners
- **SummaryReport**: Summary statistics report. Fields: name
- **SimpleDataWriter**: Write results to file. Fields: name, file
- **AggregateReport**: Aggregate statistics report. Fields: name
- **ViewResultsFullVisualizer**: View results tree. Fields: name