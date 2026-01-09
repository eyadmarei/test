import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

dotenv.config();

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

async function testAPI() {
  try {
    console.log('Testing API key with claude-3-haiku-20240307...');
    const message = await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 100,
      messages: [{
        role: 'user',
        content: 'Say hello'
      }]
    });
    console.log('✓ API key works!');
    console.log('Response:', message.content[0]);
  } catch (error) {
    console.error('✗ API test failed:', error);
  }
}

testAPI();
