#!/usr/bin/env python3

"""
Simple test script for the AI API Server
Usage: python test_api.py
"""

import requests
import json
import sys

# Base URL for the API
API_BASE_URL = 'http://localhost:3000'

def make_request(endpoint, method='GET', body=None):
    """Make a request to the API"""
    options = {
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    
    if body:
        options['json'] = body
    
    try:
        if method == 'GET':
            response = requests.get(f"{API_BASE_URL}{endpoint}", **options)
        elif method == 'POST':
            response = requests.post(f"{API_BASE_URL}{endpoint}", **options)
        else:
            print(f"Unsupported method: {method}")
            return {'status': 400, 'data': {'error': {'message': 'Unsupported method'}}}
        
        return {'status': response.status_code, 'data': response.json()}
    except Exception as e:
        print(f"Error making request: {str(e)}")
        return {'status': 500, 'data': {'error': {'message': str(e)}}}

def show_menu():
    """Display the main menu"""
    print("\n=== AI API Server Test Client ===")
    print("1. Check API health")
    print("2. List available models")
    print("3. List available providers")
    print("4. Generate a completion")
    print("5. Exit")
    
    choice = input("\nSelect an option (1-5): ")
    handle_menu_selection(choice)

def handle_menu_selection(choice):
    """Handle menu selection"""
    if choice == '1':
        check_health()
    elif choice == '2':
        list_models()
    elif choice == '3':
        list_providers()
    elif choice == '4':
        generate_completion()
    elif choice == '5':
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid option. Please try again.")
    
    show_menu()

def check_health():
    """Check API health"""
    print("\nChecking API health...")
    
    result = make_request('/api/health')
    
    print(f"Status: {result['status']}")
    print("Response:")
    print(json.dumps(result['data'], indent=2))

def list_models():
    """List available models"""
    print("\nFetching available models...")
    
    provider = input("Filter by provider (openai/deepseek/litellm/leave empty for all): ")
    
    endpoint = f"/api/models?provider={provider}" if provider else "/api/models"
    result = make_request(endpoint)
    
    print(f"Status: {result['status']}")
    print("Available Models:")
    
    if 'models' in result['data'] and result['data']['models']:
        for model in result['data']['models']:
            description = model.get('description', 'No description')
            print(f"- {model['name']} ({model['id']}) [{model['provider']}]: {description}")
    else:
        print("No models available or provider not found.")

def list_providers():
    """List available providers"""
    print("\nFetching available providers...")
    
    result = make_request('/api/providers')
    
    print(f"Status: {result['status']}")
    print("Available Providers:")
    
    if 'providers' in result['data']:
        for provider, info in result['data']['providers'].items():
            print(f"- {provider}: {'Available' if info['available'] else 'Not available'}")
            if info['available'] and info['models']:
                model_ids = [m['id'] for m in info['models']]
                print(f"  Models: {', '.join(model_ids)}")
    else:
        print("No provider information available.")

def generate_completion():
    """Generate a completion"""
    print("\nGenerating a completion...")
    
    # Get available models first
    models_result = make_request('/api/models')
    available_models = models_result['data'].get('models', [])
    
    if not available_models:
        print("No models available. Please check your API keys.")
        return
    
    print("\nAvailable models:")
    for i, model in enumerate(available_models):
        print(f"{i + 1}. {model['name']} ({model['id']}) [{model['provider']}]")
    
    model_index = input("\nSelect a model (number): ")
    try:
        index = int(model_index) - 1
        if index < 0 or index >= len(available_models):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid selection.")
        return
    
    selected_model = available_models[index]
    
    prompt = input("\nEnter your prompt: ")
    if not prompt.strip():
        print("Prompt cannot be empty.")
        return
    
    print(f"\nGenerating completion using {selected_model['name']}...")
    
    request_body = {
        "model": selected_model['id'],
        "prompt": prompt,
        "temperature": 0.7,
    }
    
    result = make_request('/api/completions', 'POST', request_body)
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 200 and 'content' in result['data']:
        print("\n=== Generated Content ===")
        print(result['data']['content'])
        print("\n=== Usage ===")
        print(f"Prompt tokens: {result['data']['usage']['prompt_tokens']}")
        print(f"Completion tokens: {result['data']['usage']['completion_tokens']}")
        print(f"Total tokens: {result['data']['usage']['total_tokens']}")
    else:
        print("Error generating completion:")
        print(json.dumps(result['data'], indent=2))

# Start the application
if __name__ == "__main__":
    print("Starting AI API Server test client...")
    print(f"API Base URL: {API_BASE_URL}")
    show_menu()
