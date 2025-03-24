#!/usr/bin/env node

/**
 * Simple test script for the AI API Server
 * Usage: node test-api.js
 */

import fetch from 'node-fetch';
import readline from 'readline';

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Base URL for the API
const API_BASE_URL = 'http://localhost:3000';

/**
 * Make a request to the API
 */
async function makeRequest(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    const data = await response.json();
    return { status: response.status, data };
  } catch (error) {
    console.error('Error making request:', error.message);
    return { status: 500, data: { error: { message: error.message } } };
  }
}

/**
 * Display the main menu
 */
function showMenu() {
  console.log('\n=== AI API Server Test Client ===');
  console.log('1. Check API health');
  console.log('2. List available models');
  console.log('3. List available providers');
  console.log('4. Generate a completion');
  console.log('5. Exit');
  
  rl.question('\nSelect an option (1-5): ', handleMenuSelection);
}

/**
 * Handle menu selection
 */
async function handleMenuSelection(choice) {
  switch (choice) {
    case '1':
      await checkHealth();
      break;
    case '2':
      await listModels();
      break;
    case '3':
      await listProviders();
      break;
    case '4':
      await generateCompletion();
      break;
    case '5':
      console.log('Goodbye!');
      rl.close();
      return;
    default:
      console.log('Invalid option. Please try again.');
  }
  
  showMenu();
}

/**
 * Check API health
 */
async function checkHealth() {
  console.log('\nChecking API health...');
  
  const { status, data } = await makeRequest('/api/health');
  
  console.log(`Status: ${status}`);
  console.log('Response:');
  console.log(JSON.stringify(data, null, 2));
}

/**
 * List available models
 */
async function listModels() {
  console.log('\nFetching available models...');
  
  rl.question('Filter by provider (openai/deepseek/litellm/leave empty for all): ', async (provider) => {
    const endpoint = provider ? `/api/models?provider=${provider}` : '/api/models';
    const { status, data } = await makeRequest(endpoint);
    
    console.log(`Status: ${status}`);
    console.log('Available Models:');
    
    if (data.models && data.models.length > 0) {
      data.models.forEach(model => {
        console.log(`- ${model.name} (${model.id}) [${model.provider}]: ${model.description || 'No description'}`);
      });
    } else {
      console.log('No models available or provider not found.');
    }
    
    showMenu();
  });
  
  return new Promise(() => {}); // Prevent immediate return to menu
}

/**
 * List available providers
 */
async function listProviders() {
  console.log('\nFetching available providers...');
  
  const { status, data } = await makeRequest('/api/providers');
  
  console.log(`Status: ${status}`);
  console.log('Available Providers:');
  
  if (data.providers) {
    Object.entries(data.providers).forEach(([provider, info]) => {
      console.log(`- ${provider}: ${info.available ? 'Available' : 'Not available'}`);
      if (info.available && info.models) {
        console.log(`  Models: ${info.models.map(m => m.id).join(', ')}`);
      }
    });
  } else {
    console.log('No provider information available.');
  }
}

/**
 * Generate a completion
 */
async function generateCompletion() {
  console.log('\nGenerating a completion...');
  
  // Get available models first
  const { data: modelsData } = await makeRequest('/api/models');
  const availableModels = modelsData.models || [];
  
  if (availableModels.length === 0) {
    console.log('No models available. Please check your API keys.');
    return;
  }
  
  console.log('\nAvailable models:');
  availableModels.forEach((model, index) => {
    console.log(`${index + 1}. ${model.name} (${model.id}) [${model.provider}]`);
  });
  
  rl.question('\nSelect a model (number): ', (modelIndex) => {
    const index = parseInt(modelIndex) - 1;
    
    if (isNaN(index) || index < 0 || index >= availableModels.length) {
      console.log('Invalid selection.');
      showMenu();
      return;
    }
    
    const selectedModel = availableModels[index];
    
    rl.question('\nEnter your prompt: ', async (prompt) => {
      if (!prompt.trim()) {
        console.log('Prompt cannot be empty.');
        showMenu();
        return;
      }
      
      console.log(`\nGenerating completion using ${selectedModel.name}...`);
      
      const requestBody = {
        model: selectedModel.id,
        prompt: prompt,
        temperature: 0.7,
      };
      
      const { status, data } = await makeRequest('/api/completions', 'POST', requestBody);
      
      console.log(`Status: ${status}`);
      
      if (status === 200 && data.content) {
        console.log('\n=== Generated Content ===');
        console.log(data.content);
        console.log('\n=== Usage ===');
        console.log(`Prompt tokens: ${data.usage.promptTokens}`);
        console.log(`Completion tokens: ${data.usage.completionTokens}`);
        console.log(`Total tokens: ${data.usage.totalTokens}`);
      } else {
        console.log('Error generating completion:');
        console.log(JSON.stringify(data, null, 2));
      }
      
      showMenu();
    });
  });
  
  return new Promise(() => {}); // Prevent immediate return to menu
}

// Start the application
console.log('Starting AI API Server test client...');
console.log(`API Base URL: ${API_BASE_URL}`);
showMenu();
