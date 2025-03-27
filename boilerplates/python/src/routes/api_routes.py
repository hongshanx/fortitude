"""API route handlers for the AI service.

This module defines the Flask Blueprint containing all API endpoints
for model management, completions, and health checks.
"""

import asyncio
import datetime
import json
from typing import Generator, List, Optional, Tuple, Union

from asgiref.sync import async_to_sync
from flask import Blueprint, Response, jsonify, request, stream_with_context
import requests
from bs4 import BeautifulSoup

from src.middlewares.error_handler import ApiError, handle_error, validate_request
from src.services.ai_service import AIService
from src.types.api import (
    AIModel,
    AIProvider,
    DEEPSEEK_MODELS,
    OPENAI_MODELS,
    get_litellm_models,
    get_openai_compatible_models,
    get_all_models,
)
from src.types.schemas import (
    CompletionRequestSchema,
    StockPredictionRequestSchema,
    StockPredictionResponseSchema
)

# Create blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/models', methods=['GET'])
def get_models() -> Tuple[dict, int]:
    """Get list of available models.

    Returns:
        Tuple[dict, int]: JSON response with models and providers, and HTTP status code.
    """
    # Parse and validate query parameters
    provider_param = request.args.get('provider')
    provider: Optional[AIProvider] = None

    if provider_param:
        try:
            provider = AIProvider(provider_param)
        except ValueError:
            return jsonify({
                "error": {
                    "message": f"Invalid provider: {provider_param}",
                    "code": "INVALID_PROVIDER"
                }
            }), 400

    try:
        # Get available providers
        providers = async_to_sync(AIService.get_available_providers)()

        # Get the latest models including any dynamically fetched ones
        models = get_all_models()

        # Filter by provider if specified
        if provider:
            models = [model for model in models if model.provider == provider]

        # Filter out models from unavailable providers
        models = [
            model for model in models
            if ((model.provider != AIProvider.OPENAI or providers["openai"]) and
                (model.provider != AIProvider.DEEPSEEK or providers["deepseek"]) and
                (model.provider != AIProvider.LITELLM or providers["litellm"]) and
                (model.provider != AIProvider.OPENAI_COMPATIBLE or
                 providers["openai_compatible"]))
        ]

        # Convert models to dict for JSON response
        models_json = [model.model_dump() for model in models]

        return jsonify({
            "models": models_json,
            "providers": providers,
        }), 200

    except (KeyError, ValueError) as e:
        return handle_error(
            ApiError(400, str(e), "INVALID_REQUEST")
        )
    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (TypeError, AttributeError) as e:
        return handle_error(
            ApiError(500, f"Internal server error: {str(e)}", "SERVER_ERROR")
        )


@api_bp.route('/providers', methods=['GET'])
def get_providers() -> Tuple[dict, int]:
    """Get available AI providers.

    Returns:
        Tuple[dict, int]: JSON response with provider information and HTTP status code.
    """
    def get_provider_models(
        models: List[AIModel],
        is_available: bool
    ) -> List[dict]:
        """Helper to get models for a provider if available."""
        if not is_available:
            return []
        return [model.model_dump() for model in models]

    try:
        providers = async_to_sync(AIService.get_available_providers)()

        return jsonify({
            "providers": {
                "openai": {
                    "available": providers["openai"],
                    "models": get_provider_models(
                        OPENAI_MODELS,
                        providers["openai"]
                    ),
                },
                "deepseek": {
                    "available": providers["deepseek"],
                    "models": get_provider_models(
                        DEEPSEEK_MODELS,
                        providers["deepseek"]
                    ),
                },
                "litellm": {
                    "available": providers["litellm"],
                    "models": get_provider_models(
                        get_litellm_models(),
                        providers["litellm"]
                    ),
                },
                "openai_compatible": {
                    "available": providers["openai_compatible"],
                    "models": get_provider_models(
                        get_openai_compatible_models(),
                        providers["openai_compatible"]
                    ),
                },
            },
        }), 200

    except KeyError as e:
        return handle_error(
            ApiError(500, f"Missing provider configuration: {e}", "PROVIDER_ERROR")
        )
    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (TypeError, AttributeError) as e:
        return handle_error(
            ApiError(500, f"Internal server error: {str(e)}", "SERVER_ERROR")
        )


CompletionResponse = Union[Response, Tuple[dict, int]]


@api_bp.route('/completions', methods=['POST'])
@validate_request(CompletionRequestSchema)
def generate_completion(validated_data: CompletionRequestSchema) -> CompletionResponse:
    """Generate a completion.

    Args:
        validated_data: Validated completion request data.

    Returns:
        CompletionResponse: Streaming response or JSON response with completion.
    """
    try:
        if validated_data.stream:
            return stream_completion(validated_data)

        result = async_to_sync(AIService.generate_completion)(validated_data)
        return jsonify(result.model_dump()), 200

    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except ValueError as e:
        return handle_error(
            ApiError(400, str(e), "INVALID_REQUEST")
        )
    except (KeyError, TypeError) as e:
        return handle_error(
            ApiError(400, f"Invalid request format: {str(e)}", "INVALID_FORMAT")
        )
    except (RuntimeError, AssertionError) as e:
        print(f"Internal error in generate_completion: {e}")
        return handle_error(
            ApiError(500, "Internal server error", "SERVER_ERROR")
        )


def stream_completion(validated_data: CompletionRequestSchema) -> Response:
    """Stream a completion response.

    Args:
        validated_data: Validated completion request data.

    Returns:
        Response: Streaming response with Server-Sent Events.
    """
    def generate() -> Generator[str, None, None]:
        """Generate SSE formatted chunks.

        Yields:
            str: SSE formatted data chunks.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            async_gen = AIService.generate_stream(validated_data)

            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    chunk_data = chunk.model_dump()
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                except StopAsyncIteration:
                    break
                except (ConnectionError, TimeoutError) as e:
                    error_data = {
                        "error": {
                            "message": f"Service unavailable: {str(e)}",
                            "code": "SERVICE_UNAVAILABLE"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except json.JSONDecodeError as e:
                    print(f"JSON encoding error in stream_completion: {e}")
                    error_data = {
                        "error": {
                            "message": "Failed to encode response",
                            "code": "ENCODING_ERROR"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except (KeyError, TypeError) as e:
                    error_data = {
                        "error": {
                            "message": f"Invalid response format: {str(e)}",
                            "code": "INVALID_RESPONSE"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except ValueError as e:
                    error_data = {
                        "error": {
                            "message": f"Invalid data in response: {str(e)}",
                            "code": "INVALID_DATA"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except (AttributeError, RuntimeError, AssertionError) as e:
                    print(f"Internal error in stream_completion: {e}")
                    error_data = {
                        "error": {
                            "message": "Internal server error",
                            "code": "SERVER_ERROR"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break

            yield "data: [DONE]\n\n"

        finally:
            loop.close()

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable buffering in Nginx
        }
    )


def scrape_market_data(ticker: str) -> Tuple[str, str, float, Optional[float], Optional[float]]:
    """Scrape market data from Bing and Yahoo Finance.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Tuple containing bing_text, market_data_str, price_change, current_price, prev_close.
    """
    # Scrape Bing
    bing_url = f"https://www.bing.com/search?q={ticker}+stock+analysis+prediction"
    bing_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    bing_response = requests.get(bing_url, headers=bing_headers, timeout=10)
    bing_soup = BeautifulSoup(bing_response.text, 'html.parser')
    bing_results = bing_soup.find_all('p')
    bing_text = ' '.join([p.get_text() for p in bing_results[:3]])

    # Scrape Yahoo Finance
    yahoo_url = f"https://finance.yahoo.com/quote/{ticker}"
    yahoo_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    yahoo_response = requests.get(yahoo_url, headers=yahoo_headers, timeout=10)
    yahoo_soup = BeautifulSoup(yahoo_response.text, 'html.parser')

    # Initialize variables
    current_price = None
    prev_close = None
    price_change = 0.0
    market_data_str = "Unable to fetch current market data"

    # Try to get current price and previous close
    try:
        current_price = float(yahoo_soup.find(
            'fin-streamer',
            {'data-field': 'regularMarketPrice'}
        ).text.replace(',', ''))
        prev_close = float(yahoo_soup.find(
            'td',
            {'data-test': 'PREV_CLOSE-value'}
        ).text.replace(',', ''))
        price_change = ((current_price - prev_close) / prev_close) * 100
        market_data_str = (
            f"Current price: ${current_price:.2f}\n"
            f"Previous close: ${prev_close:.2f}\n"
            f"Price change: {price_change:.1f}%"
        )
    except (AttributeError, ValueError, TypeError):
        pass

    return bing_text, market_data_str, price_change, current_price, prev_close


@api_bp.route('/predict/stock', methods=['POST'])
@validate_request(StockPredictionRequestSchema)
def predict_stock(validated_data: StockPredictionRequestSchema) -> Tuple[dict, int]:
    """Predict stock movement based on web scraping and AI analysis.

    Args:
        validated_data: Validated stock prediction request data.

    Returns:
        Tuple[dict, int]: JSON response with prediction and HTTP status code.
    """
    try:
        ticker = validated_data.ticker.upper()

        # Scrape market data
        bing_text, market_data_str, _, _, _ = scrape_market_data(ticker)
        print('bing_text:', bing_text)
        print('market_data_str:', market_data_str)
        # Prepare prompt for AI analysis
        prompt = (
            f"Analyze the following stock information and predict whether the "
            f"stock price will go up or down.\nReturn your response in this exact format:\n"
            f'{{\n    "prediction": "up" or "down",\n    "confidence": <float between '
            f'0 and 1>,\n    "summary": "<brief explanation>"\n}}\n\n'
            f"Stock: {ticker}\n"
            f"Market Data: {market_data_str}\n"
            f"Market analysis from Bing: {bing_text}"
        )

        # Use AI service for prediction with DeepSeek V3
        completion_request = CompletionRequestSchema(
            model="deepseek-v3",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
            provider=AIProvider.OPENAI_COMPATIBLE
        )

        result = async_to_sync(AIService.generate_completion)(completion_request)

        try:
            # Parse AI response
            ai_response = json.loads(result.content)

            # Create response
            response = StockPredictionResponseSchema(
                ticker=ticker,
                prediction=ai_response["prediction"],
                confidence=ai_response["confidence"],
                summary=ai_response["summary"]
            )

            return jsonify(response.model_dump()), 200

        except (json.JSONDecodeError, KeyError) as e:
            # If AI response parsing fails, return error
            return handle_error(
                ApiError(500, f"Failed to parse AI response: {str(e)}", "AI_RESPONSE_ERROR")
            )

    except requests.RequestException as e:
        return handle_error(
            ApiError(503, f"Failed to fetch stock data: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (ValueError, AttributeError) as e:
        return handle_error(
            ApiError(400, f"Failed to parse stock data: {str(e)}", "INVALID_DATA")
        )
    except (RuntimeError, AssertionError) as e:
        print(f"Unexpected error in predict_stock: {e}")
        return handle_error(
            ApiError(500, "Internal server error", "SERVER_ERROR")
        )


@api_bp.route('/health', methods=['GET'])
def health_check() -> Tuple[dict, int]:
    """Health check endpoint.

    Returns:
        Tuple[dict, int]: JSON response with health status and HTTP status code.
    """
    try:
        providers = async_to_sync(AIService.get_available_providers)()

        return jsonify({
            "status": "ok",
            "timestamp": datetime.datetime.now().isoformat(),
            "providers": providers,
        }), 200

    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (KeyError, ValueError) as e:
        return handle_error(
            ApiError(500, f"Invalid provider configuration: {str(e)}", "CONFIG_ERROR")
        )
    except (TypeError, AttributeError) as e:
        return handle_error(
            ApiError(500, f"Internal server error: {str(e)}", "SERVER_ERROR")
        )
