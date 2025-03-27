# 股票预测 Agent 开发指南

本文档将指导您如何使用现有的脚手架快速开发一个股票预测 agent。我们将以股票预测功能为例，展示如何利用现有框架进行业务逻辑开发。

## 功能概述

该示例实现了一个股票预测 API，它可以：
- 接收股票代码作为输入
- 从 Bing 和 Yahoo Finance 获取市场数据
- 使用 DeepSeek V3 模型分析数据并预测股票走势
- 返回预测结果（上涨/下跌）、置信度和分析摘要

## 快速开始

1. 确保已安装所需依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量（参考 .env.example）：
```bash
OPENAI_COMPATIBLE_API_KEY=your_api_key_here
OPENAI_COMPATIBLE_API_BASE=your_api_base_here
```

3. 启动服务器：
```bash
python main.py
```

4. 测试 API：
```bash
curl -X POST http://localhost:3000/api/predict/stock \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

## 开发指南

### 1. 定义数据模型

在 `src/types/schemas.py` 中定义请求和响应模型：

```python
class StockPredictionRequestSchema(BaseModel):
    """股票预测请求模型"""
    ticker: str = Field(..., min_length=1, max_length=10)

class StockPredictionResponseSchema(BaseModel):
    """股票预测响应模型"""
    ticker: str
    prediction: str = Field(..., pattern="^(up|down)$")
    confidence: float = Field(..., ge=0, le=1)
    summary: str
```

### 2. 添加路由处理

在 `src/routes/api_routes.py` 中添加新的路由处理器：

```python
@api_bp.route('/predict/stock', methods=['POST'])
@validate_request(StockPredictionRequestSchema)
def predict_stock(validated_data: StockPredictionRequestSchema) -> Tuple[dict, int]:
    # 实现预测逻辑
    pass
```

### 3. 实现业务逻辑

主要步骤包括：
1. 数据采集（例如从 Bing 和 Yahoo Finance 抓取数据）
2. 数据处理和格式化
3. 调用 AI 模型进行分析
4. 处理响应并返回结果

示例代码：
```python
# 1. 采集数据
bing_text = scrape_bing(ticker)
market_data = scrape_yahoo(ticker)

# 2. 构建 prompt
prompt = format_prompt(ticker, market_data, bing_text)

# 3. 调用 AI 模型
completion_request = CompletionRequestSchema(
    model="deepseek-v3",
    prompt=prompt,
    max_tokens=500,
    temperature=0.7,
    provider=AIProvider.OPENAI_COMPATIBLE
)

result = async_to_sync(AIService.generate_completion)(completion_request)

# 4. 处理响应
response = StockPredictionResponseSchema(
    ticker=ticker,
    prediction=result.prediction,
    confidence=result.confidence,
    summary=result.summary
)
```

## 最佳实践

1. **错误处理**
   - 使用 try-except 块处理可能的异常
   - 利用框架提供的 `handle_error` 和 `ApiError` 进行统一的错误处理
   - 为每种可能的错误提供清晰的错误消息

2. **数据验证**
   - 使用 Pydantic 模型进行请求和响应的数据验证
   - 在模型中定义字段约束和验证规则

3. **模块化设计**
   - 将数据采集、处理和分析逻辑分离到不同的函数或类中
   - 保持代码的可维护性和可测试性

4. **配置管理**
   - 使用环境变量进行配置管理
   - 避免在代码中硬编码敏感信息

## 扩展开发

要开发新的 agent 功能，您可以参考以下步骤：

1. 在 `src/types/schemas.py` 中定义新的请求/响应模型
2. 在 `src/routes/api_routes.py` 中添加新的路由
3. 实现数据采集和处理逻辑
4. 构建适当的 prompt 并调用 AI 服务
5. 处理响应并返回结果

## 调试技巧

1. 使用 `print` 语句或日志记录关键信息
2. 在开发模式下，服务器会自动重新加载修改的代码
3. 使用 curl 或 Postman 测试 API 端点
4. 检查服务器日志以获取错误信息

## 常见问题

1. **模型返回格式不正确**
   - 确保 prompt 中明确指定了所需的返回格式
   - 使用 try-except 处理解析错误

2. **数据采集失败**
   - 检查网络连接
   - 验证目标网站的可访问性
   - 更新 User-Agent 等请求头

3. **API 调用失败**
   - 检查 API 密钥配置
   - 验证 API 端点的可用性
   - 检查请求限制和配额

## 结论

通过这个示例，您可以了解如何使用现有的脚手架快速开发新的 agent 功能。框架提供了完整的错误处理、请求验证和 AI 集成能力，让您可以专注于业务逻辑的开发。