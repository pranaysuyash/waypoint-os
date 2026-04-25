# AIML_01: LLM Integration Patterns Deep Dive

> Comprehensive guide to Large Language Model integration patterns for the Travel Agency Agent platform

---

## Table of Contents

1. [Overview](#overview)
2. [LLM Provider Architecture](#llm-provider-architecture)
3. [Prompt Engineering Patterns](#prompt-engineering-patterns)
4. [Context Management](#context-management)
5. [Retrieval-Augmented Generation (RAG)](#retrieval-augmented-generation-rag)
6. [Function Calling & Tools](#function-calling--tools)
7. [Streaming Responses](#streaming-responses)
8. [Token Optimization](#token-optimization)
9. [Error Handling & Fallbacks](#error-handling--fallbacks)
10. [Cost Management](#cost-management)

---

## Overview

### Goals

- **Flexibility**: Support multiple LLM providers with unified interface
- **Reliability**: Handle failures gracefully with fallbacks
- **Efficiency**: Optimize token usage and caching
- **Quality**: Implement prompt engineering best practices
- **Safety**: Add guardrails for appropriate outputs

### LLM Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM INTEGRATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Request  │───►│ Context  │───►│ Prompt   │───►│ LLM      │ │
│  │ Input    │    │ Builder  │    │ Template │    │ Provider │ │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘ │
│                                                  │          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    │          │
│  │ RAG      │◄───│ Vector   │◄───│ Document │    │          │
│  │ Enrich   │    │ Search   │    │ Index    │    │          │
│  └──────────┘    └──────────┘    └──────────┘    │          │
│                                                  │          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    │          │
│  │ Function │◄───│ Tool     │◄───│ Schema   │◄───┘          │
│  │ Calling  │    │ Registry │    │ Parser   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                                  │          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    │          │
│  │ Response │◄───│ Stream   │◄───│ Parser   │◄───┘          │
│  │ Handler  │    │ Processor│    │          │                │
│  └──────────┘    └──────────┘    └──────────┘                │
│                                                  │          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    │          │
│  │ Safety   │◄───│ Content  │◄───│ Policy   │◄───┘          │
│  │ Rails    │    │ Filter   │    │ Engine   │                │
│  └──────────┘    └──────────┘    └──────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Supported LLM Providers

| Provider | Models | Use Case |
|----------|--------|----------|
| **OpenAI** | GPT-4o, GPT-4o-mini, o1 | General purpose, complex reasoning |
| **Anthropic** | Claude 3.5 Sonnet, Haiku | Long context, nuanced responses |
| **Google** | Gemini Pro | Multimodal, large context |
| **Cohere** | Command R | RAG, citation-heavy |
| **Local** | Llama, Mistral | Cost-sensitive, privacy |

---

## LLM Provider Architecture

### Provider Abstraction Layer

```typescript
// lib/ai/providers/base.ts

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  toolCalls?: ToolCall[];
  toolCallId?: string;
}

export interface ToolCall {
  id: string;
  type: string;
  function: {
    name: string;
    arguments: string;
  };
}

export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface LLMCompletionOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  stop?: string[];
  tools?: Tool[];
  toolChoice?: 'auto' | 'required' | 'none';
  stream?: boolean;
}

export interface LLMCompletionResult {
  content: string;
  toolCalls?: ToolCall[];
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  model: string;
  finishReason: string;
}

export interface LLMStreamChunk {
  content: string;
  toolCalls?: ToolCall[];
  done: boolean;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export abstract class BaseLLMProvider {
  abstract complete(
    messages: LLMMessage[],
    options?: LLMCompletionOptions
  ): Promise<LLMCompletionResult>;

  abstract stream(
    messages: LLMMessage[],
    options?: LLMCompletionOptions
  ): AsyncIterableIterator<LLMStreamChunk>;

  abstract countTokens(text: string): number;

  abstract getEmbedding(text: string): Promise<number[]>;
}
```

### OpenAI Provider Implementation

```typescript
// lib/ai/providers/openai.ts

import OpenAI from 'openai';
import { BaseLLMProvider, LLMMessage, LLMCompletionOptions, LLMCompletionResult, LLMStreamChunk, Tool } from './base';

export class OpenAIProvider extends BaseLLMProvider {
  private client: OpenAI;

  constructor(apiKey: string) {
    super();
    this.client = new OpenAI({ apiKey });
  }

  async complete(
    messages: LLMMessage[],
    options: LLMCompletionOptions = {}
  ): Promise<LLMCompletionResult> {
    const response = await this.client.chat.completions.create({
      model: options.model || 'gpt-4o',
      messages: messages.map(this.convertMessage),
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 2048,
      top_p: options.topP,
      frequency_penalty: options.frequencyPenalty,
      presence_penalty: options.presencePenalty,
      stop: options.stop,
      tools: options.tools ? options.tools.map(this.convertTool) : undefined,
      tool_choice: options.toolChoice,
    });

    const choice = response.choices[0];

    return {
      content: choice.message.content || '',
      toolCalls: choice.message.tool_calls?.map(this.convertToolCall),
      usage: {
        promptTokens: response.usage.prompt_tokens,
        completionTokens: response.usage.completion_tokens,
        totalTokens: response.usage.total_tokens,
      },
      model: response.model,
      finishReason: choice.finish_reason,
    };
  }

  async *stream(
    messages: LLMMessage[],
    options: LLMCompletionOptions = {}
  ): AsyncIterableIterator<LLMStreamChunk> {
    const stream = await this.client.chat.completions.create({
      model: options.model || 'gpt-4o',
      messages: messages.map(this.convertMessage),
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 2048,
      tools: options.tools ? options.tools.map(this.convertTool) : undefined,
      tool_choice: options.toolChoice,
      stream: true,
    });

    let accumulatedToolCalls: Record<string, ToolCall> = {};

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta;

      if (!delta) continue;

      // Handle content
      if (delta.content) {
        yield {
          content: delta.content,
          toolCalls: undefined,
          done: false,
        };
      }

      // Handle tool calls
      if (delta.tool_calls) {
        for (const toolCall of delta.tool_calls) {
          if (!toolCall.index) continue;

          if (!accumulatedToolCalls[toolCall.index]) {
            accumulatedToolCalls[toolCall.index] = {
              id: toolCall.id || '',
              type: toolCall.type || 'function',
              function: {
                name: toolCall.function?.name || '',
                arguments: toolCall.function?.arguments || '',
              },
            };
          } else {
            if (toolCall.function?.name) {
              accumulatedToolCalls[toolCall.index].function.name = toolCall.function.name;
            }
            if (toolCall.function?.arguments) {
              accumulatedToolCalls[toolCall.index].function.arguments += toolCall.function.arguments;
            }
          }
        }
      }

      // Handle completion
      if (chunk.choices[0]?.finish_reason) {
        const toolCalls = Object.values(accumulatedToolCalls);
        yield {
          content: '',
          toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
          done: true,
          usage: chunk.usage ? {
            promptTokens: chunk.usage.prompt_tokens,
            completionTokens: chunk.usage.completion_tokens,
            totalTokens: chunk.usage.total_tokens,
          } : undefined,
        };
      }
    }
  }

  countTokens(text: string): number {
    // Approximate token count (4 chars per token)
    return Math.ceil(text.length / 4);
  }

  async getEmbedding(text: string): Promise<number[]> {
    const response = await this.client.embeddings.create({
      model: 'text-embedding-3-small',
      input: text,
    });

    return response.data[0].embedding;
  }

  private convertMessage(message: LLMMessage): OpenAI.Chat.Completions.ChatCompletionMessageParam {
    const base = {
      role: message.role,
      content: message.content,
    };

    if (message.toolCalls) {
      return {
        ...base,
        tool_calls: message.toolCalls.map(tc => ({
          id: tc.id,
          type: tc.type,
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        })),
      };
    }

    if (message.toolCallId) {
      return {
        ...base,
        role: 'tool',
        tool_call_id: message.toolCallId,
      };
    }

    return base;
  }

  private convertTool(tool: Tool): OpenAI.Chat.Completions.ChatCompletionTool {
    return {
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
      },
    };
  }

  private convertToolCall(tc: OpenAI.Chat.Completions.ChatCompletionMessageToolCall): ToolCall {
    return {
      id: tc.id,
      type: tc.type,
      function: {
        name: tc.function.name,
        arguments: tc.function.arguments,
      },
    };
  }
}
```

### Anthropic (Claude) Provider

```typescript
// lib/ai/providers/anthropic.ts

import Anthropic from '@anthropic-ai/sdk';
import { BaseLLMProvider, LLMMessage, LLMCompletionOptions, LLMCompletionResult } from './base';

export class AnthropicProvider extends BaseLLMProvider {
  private client: Anthropic;

  constructor(apiKey: string) {
    super();
    this.client = new Anthropic({ apiKey });
  }

  async complete(
    messages: LLMMessage[],
    options: LLMCompletionOptions = {}
  ): Promise<LLMCompletionResult> {
    const systemMessage = messages.find(m => m.role === 'system');
    const chatMessages = messages.filter(m => m.role !== 'system');

    const response = await this.client.messages.create({
      model: options.model || 'claude-3-5-sonnet-20241022',
      system: systemMessage?.content,
      messages: chatMessages.map(this.convertMessage),
      max_tokens: options.maxTokens ?? 4096,
      temperature: options.temperature ?? 0.7,
      top_p: options.topP,
      stop_sequences: options.stop,
      tools: options.tools ? options.tools.map(this.convertTool) : undefined,
      tool_choice: options.toolChoice,
    });

    const contentBlock = response.content.find(b => b.type === 'text');

    return {
      content: contentBlock?.type === 'text' ? contentBlock.text : '',
      toolCalls: response.content
        .filter(b => b.type === 'tool_use')
        .map(b => ({
          id: b.id,
          type: 'function',
          function: {
            name: b.name,
            arguments: JSON.stringify(b.input),
          },
        })),
      usage: {
        promptTokens: response.usage.input_tokens,
        completionTokens: response.usage.output_tokens,
        totalTokens: response.usage.input_tokens + response.usage.output_tokens,
      },
      model: response.model,
      finishReason: response.stop_reason,
    };
  }

  async *stream(
    messages: LLMMessage[],
    options: LLMCompletionOptions = {}
  ): AsyncIterableIterator {
    const systemMessage = messages.find(m => m.role === 'system');
    const chatMessages = messages.filter(m => m.role !== 'system');

    const stream = await this.client.messages.create({
      model: options.model || 'claude-3-5-sonnet-20241022',
      system: systemMessage?.content,
      messages: chatMessages.map(this.convertMessage),
      max_tokens: options.maxTokens ?? 4096,
      temperature: options.temperature ?? 0.7,
      tools: options.tools ? options.tools.map(this.convertTool) : undefined,
      stream: true,
    });

    for await (const chunk of stream) {
      if (chunk.type === 'content_block_delta') {
        if (chunk.delta.type === 'text_delta') {
          yield {
            content: chunk.delta.text,
            done: false,
          };
        }
      }
    }

    yield { content: '', done: true };
  }

  countTokens(text: string): number {
    // Claude uses a different tokenizer
    return Math.ceil(text.length / 3.5);
  }

  async getEmbedding(text: string): Promise<number[]> {
    // Use a different embedding service for Claude
    throw new Error('Embeddings not supported by Anthropic directly');
  }

  private convertMessage(message: LLMMessage): Anthropic.MessageParam {
    if (message.role === 'tool') {
      return {
        role: 'user',
        content: [{
          type: 'tool_result',
          tool_use_id: message.toolCallId,
          content: message.content,
        }],
      };
    }

    return {
      role: message.role === 'assistant' ? 'assistant' : 'user',
      content: message.content,
    };
  }

  private convertTool(tool: Tool): Anthropic.Tool {
    return {
      name: tool.name,
      description: tool.description,
      input_schema: tool.parameters as Anthropic.Tool.InputSchema,
    };
  }
}
```

### Provider Factory

```typescript
// lib/ai/providers/factory.ts

import { BaseLLMProvider } from './base';
import { OpenAIProvider } from './openai';
import { AnthropicProvider } from './anthropic';

export interface ProviderConfig {
  type: 'openai' | 'anthropic' | 'google' | 'cohere';
  apiKey: string;
  model?: string;
  fallback?: ProviderConfig;
}

export class LLMProviderFactory {
  private static providers: Map<string, BaseLLMProvider> = new Map();

  static create(config: ProviderConfig): BaseLLMProvider {
    const cacheKey = `${config.type}:${config.apiKey.slice(0, 8)}`;

    if (this.providers.has(cacheKey)) {
      return this.providers.get(cacheKey)!;
    }

    let provider: BaseLLMProvider;

    switch (config.type) {
      case 'openai':
        provider = new OpenAIProvider(config.apiKey);
        break;
      case 'anthropic':
        provider = new AnthropicProvider(config.apiKey);
        break;
      default:
        throw new Error(`Unsupported provider: ${config.type}`);
    }

    this.providers.set(cacheKey, provider);
    return provider;
  }

  static createWithFallback(config: ProviderConfig): BaseLLMProvider {
    const primary = this.create(config);

    if (!config.fallback) {
      return primary;
    }

    return new FallbackProvider(primary, this.create(config.fallback));
  }
}

// Provider that falls back to another on failure
class FallbackProvider extends BaseLLMProvider {
  constructor(
    private primary: BaseLLMProvider,
    private fallback: BaseLLMProvider
  ) {
    super();
  }

  async complete(messages: LLMMessage[], options?: LLMCompletionOptions): Promise<LLMCompletionResult> {
    try {
      return await this.primary.complete(messages, options);
    } catch (error) {
      console.warn('Primary LLM provider failed, using fallback:', error);
      return await this.fallback.complete(messages, options);
    }
  }

  async *stream(messages: LLMMessage[], options?: LLMCompletionOptions): AsyncIterableIterator {
    try {
      yield* this.primary.stream(messages, options);
    } catch (error) {
      console.warn('Primary LLM provider failed, using fallback:', error);
      yield* this.fallback.stream(messages, options);
    }
  }

  countTokens(text: string): number {
    return this.primary.countTokens(text);
  }

  async getEmbedding(text: string): Promise<number[]> {
    try {
      return await this.primary.getEmbedding(text);
    } catch {
      return await this.fallback.getEmbedding(text);
    }
  }
}
```

---

## Prompt Engineering Patterns

### Prompt Template System

```typescript
// lib/ai/prompts/templates.ts

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  template: string;
  variables: PromptVariable[];
  version: number;
  systemMessage?: string;
}

export interface PromptVariable {
  name: string;
  description: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  default?: unknown;
}

export class PromptTemplateManager {
  private templates: Map<string, PromptTemplate> = new Map();

  constructor() {
    this.loadTemplates();
  }

  render(templateId: string, variables: Record<string, unknown>): {
    systemMessage?: string;
    userMessage: string;
  } {
    const template = this.templates.get(templateId);

    if (!template) {
      throw new Error(`Template not found: ${templateId}`);
    }

    // Validate required variables
    for (const variable of template.variables) {
      if (variable.required && !(variable.name in variables)) {
        throw new Error(`Missing required variable: ${variable.name}`);
      }
    }

    // Render template with variables
    const rendered = this.renderTemplate(template.template, variables);

    return {
      systemMessage: template.systemMessage,
      userMessage: rendered,
    };
  }

  private renderTemplate(template: string, variables: Record<string, unknown>): string {
    let result = template;

    for (const [key, value] of Object.entries(variables)) {
      const placeholder = `{{${key}}}`;
      result = result.replace(new RegExp(placeholder, 'g'), String(value));
    }

    // Handle conditional blocks
    result = result.replace(/{{#if (\w+)}}(.*?){{\/if}}/gs, (_, condition, content) => {
      return variables[condition] ? content : '';
    });

    // Handle loops
    result = result.replace(/{{#each (\w+)}}(.*?){{\/each}}/gs, (_, arrayKey, content) => {
      const array = variables[arrayKey] as unknown[];
      if (!Array.isArray(array)) return '';

      return array.map(item => {
        let itemContent = content;
        for (const [k, v] of Object.entries(item as Record<string, unknown>)) {
          itemContent = itemContent.replace(new RegExp(`{{${k}}}`, 'g'), String(v));
        }
        return itemContent;
      }).join('\n');
    });

    return result;
  }

  private loadTemplates(): void {
    // Trip inquiry analysis template
    this.templates.set('trip-inquiry-analysis', {
      id: 'trip-inquiry-analysis',
      name: 'Trip Inquiry Analysis',
      description: 'Analyze customer trip inquiries and extract structured data',
      category: 'intake',
      version: 1,
      systemMessage: `You are a travel agent assistant specializing in analyzing customer trip inquiries. Extract key information accurately and ask for clarification when details are missing.`,
      template: `Analyze the following customer inquiry and extract structured information.

Customer Inquiry:
{{inquiry}}

Previous Context:
{{#if previousMessages}}
{{#each previousMessages}}
- {{role}}: {{content}}
{{/each}}
{{/if}}

Extract the following information:
1. Destination(s): Where does the customer want to go?
2. Travel Dates: When do they want to travel? (departure and return)
3. Number of Travelers: How many adults, children?
4. Budget: What is their approximate budget?
5. Preferences: Any specific requirements (accommodation type, activities, etc.)?
6. Urgency: When do they need a decision by?

Respond in JSON format:
{
  "destinations": ["string"],
  "departureDate": "YYYY-MM-DD or null",
  "returnDate": "YYYY-MM-DD or null",
  "travelers": {
    "adults": number,
    "children": number,
    "infants": number
  },
  "budget": {
    "amount": number,
    "currency": "string",
    "perPerson": boolean
  },
  "preferences": ["string"],
  "urgency": "low|medium|high",
  "missingInfo": ["string"],
  "questionsToAsk": ["string"]
}`,
      variables: [
        { name: 'inquiry', description: 'Customer inquiry text', type: 'string', required: true },
        { name: 'previousMessages', description: 'Previous conversation history', type: 'array', required: false },
      ],
    });

    // Quote generation template
    this.templates.set('quote-generation', {
      id: 'quote-generation',
      name: 'Quote Generation',
      description: 'Generate a travel quote based on itinerary details',
      category: 'booking',
      version: 1,
      systemMessage: `You are a travel agent creating quotes for customers. Be clear, professional, and transparent about all costs.`,
      template: `Generate a detailed travel quote for the following itinerary:

Customer: {{customerName}}
Destination: {{destination}}
Travel Dates: {{startDate}} to {{endDate}}
Travelers: {{numTravelers}} ({{numAdults}} adults{{#if numChildren}}, {{numChildren}} children{{/if}})

Selected Services:
{{#each services}}
- {{type}}: {{name}} ({{provider}})
  - Duration: {{duration}}
  - Price: {{price}} {{currency}}
  - Description: {{description}}
{{/each}}

Total Cost Breakdown:
{{#each costBreakdown}}
- {{category}}: {{amount}} {{currency}}
{{/each}}

Generate a professional quote including:
1. Executive summary
2. Detailed itinerary with timings
3. Itemized cost breakdown
4. Payment schedule
5. Cancellation policy
6. Terms and conditions
7. Validity period

Use a warm, professional tone suitable for a travel agency.`,
      variables: [
        { name: 'customerName', description: 'Customer name', type: 'string', required: true },
        { name: 'destination', description: 'Trip destination', type: 'string', required: true },
        { name: 'startDate', description: 'Trip start date', type: 'string', required: true },
        { name: 'endDate', description: 'Trip end date', type: 'string', required: true },
        { name: 'numTravelers', description: 'Total number of travelers', type: 'number', required: true },
        { name: 'numAdults', description: 'Number of adults', type: 'number', required: true },
        { name: 'numChildren', description: 'Number of children', type: 'number', required: false },
        { name: 'services', description: 'List of selected services', type: 'array', required: true },
        { name: 'costBreakdown', description: 'Cost breakdown by category', type: 'array', required: true },
      ],
    });

    // Customer response template
    this.templates.set('customer-response', {
      id: 'customer-response',
      name: 'Customer Response',
      description: 'Generate helpful responses to customer questions',
      category: 'communication',
      version: 1,
      systemMessage: `You are a helpful travel agent assistant. Provide accurate, friendly, and professional responses. Always maintain a warm, service-oriented tone.`,
      template: `Customer Question: {{question}}

Context:
{{#if tripDetails}}
- Trip Destination: {{tripDetails.destination}}
- Travel Dates: {{tripDetails.startDate}} to {{tripDetails.endDate}}
- Current Status: {{tripDetails.status}}
{{/if}}

{{#if previousContext}}
Previous Conversation:
{{#each previousContext}}
{{speaker}}: {{message}}
{{/each}}
{{/if}}

Generate a helpful response that:
1. Directly addresses their question
2. Provides relevant information from the context
3. Offers to help with next steps
4. Maintains a friendly, professional tone

Keep the response concise (2-3 paragraphs) and conversational.`,
      variables: [
        { name: 'question', description: 'Customer question', type: 'string', required: true },
        { name: 'tripDetails', description: 'Trip context if available', type: 'object', required: false },
        { name: 'previousContext', description: 'Conversation history', type: 'array', required: false },
      ],
    });
  }
}
```

### Few-Shot Prompting

```typescript
// lib/ai/prompts/few-shot.ts

export interface FewShotExample {
  input: string;
  output: string;
  description?: string;
}

export class FewShotPromptBuilder {
  private examples: FewShotExample[] = [];

  addExample(example: FewShotExample): this {
    this.examples.push(example);
    return this;
  }

  addExamples(examples: FewShotExample[]): this {
    this.examples.push(...examples);
    return this;
  }

  build(instruction: string, input: string): string {
    let prompt = instruction;

    prompt += '\n\nHere are some examples:\n\n';

    for (const example of this.examples) {
      prompt += `Input: ${example.input}\n`;
      prompt += `Output: ${example.output}\n\n`;
    }

    prompt += `Now, process this input:\n`;
    prompt += `Input: ${input}\n`;
    prompt += `Output:`;

    return prompt;
  }
}

// Pre-defined examples for trip classification
export const tripClassificationExamples: FewShotExample[] = [
  {
    input: 'Planning a family vacation to Disney World in Florida for 5 days next month',
    output: JSON.stringify({
      type: 'leisure',
      destination: 'Orlando, Florida',
      duration: '5 days',
      travelers: 'family',
      urgency: 'medium',
    }),
    description: 'Family leisure trip',
  },
  {
    input: 'Need to book a flight to New York for a client meeting on Tuesday',
    output: JSON.stringify({
      type: 'business',
      destination: 'New York',
      duration: 'day trip',
      travelers: 'solo',
      urgency: 'high',
    }),
    description: 'Business trip',
  },
  {
    input: 'Looking for a romantic honeymoon in Maldives for 7 nights in June',
    output: JSON.stringify({
      type: 'leisure',
      destination: 'Maldives',
      duration: '7 nights',
      travelers: 'couple',
      urgency: 'low',
    }),
    description: 'Honeymoon trip',
  },
  {
    input: 'Emergency travel to attend funeral - need flight for tomorrow',
    output: JSON.stringify({
      type: 'personal',
      destination: 'unknown',
      duration: 'short',
      travelers: 'solo',
      urgency: 'critical',
    }),
    description: 'Emergency travel',
  },
];
```

### Chain of Thought Prompting

```typescript
// lib/ai/prompts/chain-of-thought.ts

export class ChainOfThoughtBuilder {
  static buildForTask(task: string, context: Record<string, unknown>): string {
    return `
Task: ${task}

Context:
${Object.entries(context).map(([k, v]) => `- ${k}: ${JSON.stringify(v)}`).join('\n')}

Let's think through this step by step:

1. First, I'll analyze what information is available:
   - [List available information]

2. Next, I'll identify what's missing or unclear:
   - [Identify gaps]

3. Then, I'll consider the constraints and requirements:
   - [Consider constraints]

4. Based on this analysis, my approach will be:
   - [Describe approach]

5. Finally, I'll provide the answer:
   - [Final answer]
`;
  }

  static buildForComplexQuery(query: string, availableData: Record<string, unknown>): string {
    return `
I need to answer this query: "${query}"

Here's the data I have access to:
${JSON.stringify(availableData, null, 2)}

Let me think through this:

Step 1: Understand what the user is asking for
- The user wants to know: [parse query]
- Key entities: [identify entities]
- Required information: [list requirements]

Step 2: Check what data is available
- I have access to: [list available data]
- This matches: [identify matches]
- Missing: [identify gaps]

Step 3: Formulate the answer
- Based on the available data, I can say: [formulate answer]
- For the missing parts, I should: [handle gaps]

Step 4: Provide the final response
[final response]
`;
  }
}
```

---

## Context Management

### Conversation Context

```typescript
// lib/ai/context/conversation.ts

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

export interface ConversationContext {
  conversationId: string;
  userId: string;
  agencyId: string;
  tripId?: string;
  messages: ConversationMessage[];
  summary?: string;
  metadata: Record<string, unknown>;
  lastUpdated: Date;
}

export class ConversationContextManager {
  private contexts: Map<string, ConversationContext> = new Map();
  private maxMessages = 50; // Keep last 50 messages
  private maxTokens = 8000; // Approximate token limit

  async getContext(conversationId: string): Promise<ConversationContext> {
    if (!this.contexts.has(conversationId)) {
      const stored = await this.loadFromDatabase(conversationId);

      if (stored) {
        this.contexts.set(conversationId, stored);
      } else {
        // Create new context
        this.contexts.set(conversationId, {
          conversationId,
          userId: '',
          agencyId: '',
          messages: [],
          metadata: {},
          lastUpdated: new Date(),
        });
      }
    }

    return this.contexts.get(conversationId)!;
  }

  async addMessage(
    conversationId: string,
    role: 'user' | 'assistant',
    content: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    const context = await this.getContext(conversationId);

    context.messages.push({
      role,
      content,
      timestamp: new Date(),
      metadata,
    });

    // Trim if exceeding limits
    await this.trimContext(context);

    context.lastUpdated = new Date();

    // Persist to database
    await this.saveToDatabase(context);
  }

  async summarizeConversation(conversationId: string): Promise<string> {
    const context = await this.getContext(conversationId);

    if (context.messages.length < 10) {
      return context.summary || '';
    }

    // Generate summary using LLM
    const llm = getLLMProvider();
    const summaryPrompt = this.buildSummaryPrompt(context.messages);

    const result = await llm.complete([
      { role: 'system', content: 'Summarize the conversation concisely, capturing key points and decisions.' },
      { role: 'user', content: summaryPrompt },
    ]);

    context.summary = result.content;

    // Keep only last few messages and summary
    const recentMessages = context.messages.slice(-5);
    context.messages = [
      {
        role: 'system',
        content: `Previous conversation summary: ${context.summary}`,
        timestamp: new Date(),
      },
      ...recentMessages,
    ];

    await this.saveToDatabase(context);

    return context.summary;
  }

  private async trimContext(context: ConversationContext): Promise<void> {
    // Trim by message count
    if (context.messages.length > this.maxMessages) {
      const excess = context.messages.length - this.maxMessages;

      // Generate summary before trimming
      if (context.messages.length > 20) {
        await this.summarizeConversation(context.conversationId);
        return; // summarizeConversation will handle trimming
      }

      context.messages = context.messages.slice(excess);
    }

    // Trim by token count (approximate)
    const totalTokens = this.estimateTokens(context.messages);
    if (totalTokens > this.maxTokens) {
      // Remove oldest messages until under limit
      while (context.messages.length > 5 && this.estimateTokens(context.messages) > this.maxTokens) {
        context.messages.shift();
      }
    }
  }

  private estimateTokens(messages: ConversationMessage[]): number {
    // Rough estimation: 4 chars per token
    const totalChars = messages.reduce((sum, m) => sum + m.content.length, 0);
    return Math.ceil(totalChars / 4);
  }

  private buildSummaryPrompt(messages: ConversationMessage[]): string {
    return `Summarize the following conversation between a customer and travel agent:

${messages.map(m => `${m.role}: ${m.content}`).join('\n\n')}

Focus on:
1. Customer's travel requirements
2. Destinations discussed
3. Key decisions made
4. Any constraints or preferences mentioned
5. Next steps or pending items

Keep it concise (2-3 paragraphs).`;
  }

  private async loadFromDatabase(conversationId: string): Promise<ConversationContext | null> {
    // Implementation depends on your database
    return null;
  }

  private async saveToDatabase(context: ConversationContext): Promise<void> {
    // Implementation depends on your database
  }
}
```

### Dynamic Context Injection

```typescript
// lib/ai/context/injection.ts

export interface ContextSource {
  name: string;
  priority: number; // Higher = more important
  fetch: (query: Record<string, unknown>) => Promise<string>;
  maxSize?: number; // Maximum tokens
}

export class ContextInjector {
  private sources: Map<string, ContextSource> = new Map();

  registerSource(source: ContextSource): void {
    this.sources.set(source.name, source);
  }

  async buildContext(
    query: string,
    contextParams: Record<string, unknown>
  ): Promise<{
    systemContext: string;
    userContext: string;
    sources: string[];
  }> {
    // Sort sources by priority
    const sortedSources = Array.from(this.sources.values()).sort(
      (a, b) => b.priority - a.priority
    );

    const systemParts: string[] = [];
    const userParts: string[] = [];
    const usedSources: string[] = [];
    let currentTokens = 0;
    const maxTokens = 4000; // Reserve space for user query

    for (const source of sortedSources) {
      if (currentTokens >= maxTokens) break;

      try {
        const content = await source.fetch(contextParams);
        const tokens = this.estimateTokens(content);

        if (currentTokens + tokens > maxTokens) {
          // Trim content to fit
          const remainingTokens = maxTokens - currentTokens;
          const trimmedContent = this.trimToTokens(content, remainingTokens);
          userParts.push(trimmedContent);
        } else {
          userParts.push(content);
        }

        usedSources.push(source.name);
        currentTokens += this.estimateTokens(content);
      } catch (error) {
        console.warn(`Failed to fetch context from ${source.name}:`, error);
      }
    }

    return {
      systemContext: systemParts.join('\n\n'),
      userContext: userParts.join('\n\n---\n\n'),
      sources: usedSources,
    };
  }

  private estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
  }

  private trimToTokens(text: string, maxTokens: number): string {
    const maxChars = maxTokens * 4;
    if (text.length <= maxChars) return text;

    // Try to trim at a sentence boundary
    const truncated = text.slice(0, maxChars);
    const lastPeriod = truncated.lastIndexOf('.');
    const lastNewline = truncated.lastIndexOf('\n');

    const cutPoint = Math.max(lastPeriod, lastNewline);

    return cutPoint > 0 ? text.slice(0, cutPoint + 1) + '\n...[truncated]' : truncated;
  }
}

// Register context sources
export const contextInjector = new ContextInjector();

// Trip details source
contextInjector.registerSource({
  name: 'trip-details',
  priority: 100,
  maxSize: 1000,
  fetch: async (params) => {
    const tripId = params.tripId as string;
    if (!tripId) return '';

    const trip = await db.trip.findUnique({
      where: { id: tripId },
      include: {
        travelers: true,
        bookings: true,
      },
    });

    if (!trip) return '';

    return `
Current Trip Details:
- Destination: ${trip.destination}
- Dates: ${trip.startDate} to ${trip.endDate}
- Status: ${trip.status}
- Budget: ${trip.budget ? `$${trip.budget}` : 'Not specified'}
- Travelers: ${trip.travelers.map(t => t.name).join(', ')}
- Bookings: ${trip.bookings.map(b => `${b.type} - ${b.status}`).join(', ')}
    `.trim();
  },
});

// Agency policies source
contextInjector.registerSource({
  name: 'agency-policies',
  priority: 80,
  maxSize: 800,
  fetch: async (params) => {
    const agencyId = params.agencyId as string;
    if (!agencyId) return '';

    const agency = await db.agency.findUnique({
      where: { id: agencyId },
      select: {
        policies: true,
        paymentTerms: true,
        cancellationPolicy: true,
      },
    });

    if (!agency) return '';

    return `
Agency Policies:
${agency.policies || 'No specific policies mentioned.'}

Payment Terms: ${agency.paymentTerms || 'Contact for details'}

Cancellation Policy: ${agency.cancellationPolicy || 'Contact for details'}
    `.trim();
  },
});

// Customer history source
contextInjector.registerSource({
  name: 'customer-history',
  priority: 60,
  maxSize: 500,
  fetch: async (params) => {
    const customerId = params.customerId as string;
    if (!customerId) return '';

    const customer = await db.customer.findUnique({
      where: { id: customerId },
      include: {
        trips: {
          take: 3,
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    if (!customer) return '';

    return `
Customer History:
- Name: ${customer.name}
- Email: ${customer.email}
- Phone: ${customer.phone}
- Previous Trips: ${customer.trips.map(t => `${t.destination} (${t.status})`).join(', ')}
- VIP Status: ${customer.isVip ? 'Yes' : 'No'}
- Notes: ${customer.notes || 'None'}
    `.trim();
  },
});
```

---

## Retrieval-Augmented Generation (RAG)

### Vector Store Integration

```typescript
// lib/ai/rag/vector-store.ts

import { OpenAIProvider } from '../providers/openai';

export interface DocumentChunk {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
  embedding?: number[];
}

export class VectorStore {
  private chunks: Map<string, DocumentChunk> = new Map();
  private embeddingProvider: OpenAIProvider;

  constructor(apiKey: string) {
    this.embeddingProvider = new OpenAIProvider(apiKey);
  }

  async addDocument(
    id: string,
    content: string,
    metadata: Record<string, unknown>
  ): Promise<void> {
    // Generate embedding
    const embedding = await this.embeddingProvider.getEmbedding(content);

    // Chunk document if too large
    const chunks = this.chunkContent(content, 500); // 500 tokens per chunk

    for (let i = 0; i < chunks.length; i++) {
      const chunkId = `${id}_${i}`;
      const chunkEmbedding = await this.embeddingProvider.getEmbedding(chunks[i]);

      this.chunks.set(chunkId, {
        id: chunkId,
        content: chunks[i],
        metadata: {
          ...metadata,
          chunkIndex: i,
          totalChunks: chunks.length,
        },
        embedding: chunkEmbedding,
      });
    }
  }

  async search(
    query: string,
    topK: number = 5,
    filter?: (metadata: Record<string, unknown>) => boolean
  ): Promise<Array<DocumentChunk & { score: number }>> {
    // Generate query embedding
    const queryEmbedding = await this.embeddingProvider.getEmbedding(query);

    // Calculate similarity scores
    const results: Array<DocumentChunk & { score: number }> = [];

    for (const chunk of this.chunks.values()) {
      if (filter && !filter(chunk.metadata)) continue;
      if (!chunk.embedding) continue;

      const score = this.cosineSimilarity(queryEmbedding, chunk.embedding);

      results.push({
        ...chunk,
        score,
      });
    }

    // Sort by score and return top K
    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length) return 0;

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  private chunkContent(content: string, maxTokens: number): string[] {
    // Simple chunking by character count
    // In production, use more sophisticated chunking
    const chunkSize = maxTokens * 4; // Approximate chars per token
    const chunks: string[] = [];

    for (let i = 0; i < content.length; i += chunkSize) {
      chunks.push(content.slice(i, i + chunkSize));
    }

    return chunks;
  }

  async deleteDocument(documentId: string): Promise<void> {
    for (const chunkId of this.chunks.keys()) {
      if (chunkId.startsWith(documentId)) {
        this.chunks.delete(chunkId);
      }
    }
  }
}
```

### RAG Pipeline

```typescript
// lib/ai/rag/pipeline.ts

export interface RAGConfig {
  vectorStore: VectorStore;
  topK: number;
  minScore: number;
  contextTemplate: string;
}

export class RAGPipeline {
  constructor(private config: RAGConfig) {}

  async query(
    question: string,
    metadata: Record<string, unknown> = {}
  ): Promise<{
    context: string;
    sources: Array<{ id: string; content: string; score: number }>;
  }> {
    // Search for relevant documents
    const results = await this.config.vectorStore.search(
      question,
      this.config.topK,
      (docMetadata) => {
        // Apply metadata filter
        if (metadata.agencyId && docMetadata.agencyId !== metadata.agencyId) return false;
        if (metadata.tripId && docMetadata.tripId !== metadata.tripId) return false;
        return true;
      }
    );

    // Filter by minimum score
    const relevant = results.filter(r => r.score >= this.config.minScore);

    // Build context
    const context = relevant
      .map((r, i) => `[Source ${i + 1}] ${r.content}`)
      .join('\n\n');

    const sources = relevant.map(r => ({
      id: r.id,
      content: r.content,
      score: r.score,
    }));

    return {
      context: this.config.contextTemplate
        .replace('{{context}}', context)
        .replace('{{question}}', question),
      sources,
    };
  }

  async queryWithLLM(
    question: string,
    llm: BaseLLMProvider,
    metadata: Record<string, unknown> = {}
  ): Promise<{
    answer: string;
    sources: Array<{ id: string; content: string; score: number }>;
  }> {
    // Get relevant context
    const { context, sources } = await this.query(question, metadata);

    // Generate answer using LLM
    const response = await llm.complete([
      {
        role: 'system',
        content: 'You are a helpful travel agent assistant. Answer questions based on the provided context. If the context doesn\'t contain enough information, say so.',
      },
      {
        role: 'user',
        content: `Context:\n${context}\n\nQuestion: ${question}\n\nAnswer:`,
      },
    ]);

    return {
      answer: response.content,
      sources,
    };
  }
}

// Usage example
export const ragPipeline = new RAGPipeline({
  vectorStore: new VectorStore(process.env.OPENAI_API_KEY!),
  topK: 3,
  minScore: 0.7,
  contextTemplate: `Based on the following context, answer the question.

Context:
{{context}}

Question: {{question}}

Answer:`,
});
```

---

## Function Calling & Tools

### Tool Registry

```typescript
// lib/ai/tools/registry.ts

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  handler: (args: Record<string, unknown>, context: ToolContext) => Promise<unknown>;
}

export interface ToolContext {
  userId: string;
  agencyId: string;
  conversationId?: string;
  tripId?: string;
}

export class ToolRegistry {
  private tools: Map<string, ToolDefinition> = new Map();

  register(tool: ToolDefinition): void {
    this.tools.set(tool.name, tool);
  }

  unregister(name: string): void {
    this.tools.delete(name);
  }

  get(name: string): ToolDefinition | undefined {
    return this.tools.get(name);
  }

  getAll(): ToolDefinition[] {
    return Array.from(this.tools.values());
  }

  async execute(
    name: string,
    args: Record<string, unknown>,
    context: ToolContext
  ): Promise<unknown> {
    const tool = this.tools.get(name);

    if (!tool) {
      throw new Error(`Tool not found: ${name}`);
    }

    return await tool.handler(args, context);
  }
}

// Global tool registry
export const toolRegistry = new ToolRegistry();

// Register built-in tools
toolRegistry.register({
  name: 'search_trips',
  description: 'Search for trips by destination, dates, and other criteria',
  parameters: {
    type: 'object',
    properties: {
      destination: {
        type: 'string',
        description: 'Travel destination (e.g., "Paris, France")',
      },
      startDate: {
        type: 'string',
        description: 'Travel start date (YYYY-MM-DD format)',
      },
      endDate: {
        type: 'string',
        description: 'Travel end date (YYYY-MM-DD format)',
      },
      numTravelers: {
        type: 'number',
        description: 'Number of travelers',
      },
    },
    required: ['destination', 'startDate', 'endDate'],
  },
  handler: async (args, context) => {
    const { destination, startDate, endDate, numTravelers } = args;

    const trips = await db.trip.findMany({
      where: {
        agencyId: context.agencyId,
        destination: { contains: destination, mode: 'insensitive' },
        startDate: { gte: new Date(startDate) },
        endDate: { lte: new Date(endDate) },
      },
      take: 10,
    });

    return trips.map(trip => ({
      id: trip.id,
      destination: trip.destination,
      startDate: trip.startDate,
      endDate: trip.endDate,
      status: trip.status,
    }));
  },
});

toolRegistry.register({
  name: 'get_trip_details',
  description: 'Get detailed information about a specific trip',
  parameters: {
    type: 'object',
    properties: {
      tripId: {
        type: 'string',
        description: 'The unique identifier of the trip',
      },
    },
    required: ['tripId'],
  },
  handler: async (args, context) => {
    const trip = await db.trip.findUnique({
      where: { id: args.tripId as string },
      include: {
        travelers: true,
        bookings: true,
        payments: true,
      },
    });

    if (!trip) {
      throw new Error('Trip not found');
    }

    if (trip.agencyId !== context.agencyId) {
      throw new Error('Access denied');
    }

    return trip;
  },
});

toolRegistry.register({
  name: 'create_booking',
  description: 'Create a new booking for a trip',
  parameters: {
    type: 'object',
    properties: {
      tripId: {
        type: 'string',
        description: 'The trip ID to create a booking for',
      },
      type: {
        type: 'string',
        enum: ['flight', 'hotel', 'car', 'activity', 'insurance'],
        description: 'The type of booking',
      },
      supplierId: {
        type: 'string',
        description: 'The supplier ID for the booking',
      },
      details: {
        type: 'object',
        description: 'Booking details (varies by type)',
      },
    },
    required: ['tripId', 'type', 'supplierId'],
  },
  handler: async (args, context) => {
    const booking = await db.booking.create({
      data: {
        tripId: args.tripId as string,
        type: args.type as string,
        supplierId: args.supplierId as string,
        details: args.details as Record<string, unknown>,
        status: 'pending',
        createdBy: context.userId,
      },
    });

    return {
      id: booking.id,
      status: booking.status,
      message: 'Booking created successfully',
    };
  },
});

toolRegistry.register({
  name: 'get_pricing',
  description: 'Get pricing information for flights, hotels, or activities',
  parameters: {
    type: 'object',
    properties: {
      type: {
        type: 'string',
        enum: ['flight', 'hotel', 'activity'],
        description: 'The type of pricing to get',
      },
      origin: {
        type: 'string',
        description: 'Origin city or airport code (for flights)',
      },
      destination: {
        type: 'string',
        description: 'Destination city or airport code',
      },
      date: {
        type: 'string',
        description: 'Travel date (YYYY-MM-DD)',
      },
    },
    required: ['type', 'destination', 'date'],
  },
  handler: async (args) => {
    // This would call external pricing APIs
    // For now, return mock data
    return {
      type: args.type,
      currency: 'USD',
      options: [
        { id: 'opt1', name: 'Economy', price: 500 },
        { id: 'opt2', name: 'Business', price: 1500 },
      ],
    };
  },
});
```

### Function Calling Orchestrator

```typescript
// lib/ai/tools/orchestrator.ts

export class FunctionCallingOrchestrator {
  constructor(
    private llm: BaseLLMProvider,
    private tools: ToolRegistry
  ) {}

  async execute(
    messages: LLMMessage[],
    context: ToolContext,
    maxIterations = 10
  ): Promise<{
    finalResponse: string;
    toolCalls: Array<{ name: string; args: Record<string, unknown>; result: unknown }>;
  }> {
    let currentMessages = [...messages];
    const toolCallHistory: Array<{ name: string; args: Record<string, unknown>; result: unknown }> = [];

    for (let iteration = 0; iteration < maxIterations; iteration++) {
      // Get LLM response with tools
      const response = await this.llm.complete(currentMessages, {
        tools: this.tools.getAll().map(t => ({
          name: t.name,
          description: t.description,
          parameters: t.parameters,
        })),
      });

      // Check if LLM wants to call tools
      if (response.toolCalls && response.toolCalls.length > 0) {
        // Execute tool calls
        for (const toolCall of response.toolCalls) {
          const toolName = toolCall.function.name;
          const toolArgs = JSON.parse(toolCall.function.arguments);

          try {
            const result = await this.tools.execute(toolName, toolArgs, context);

            toolCallHistory.push({
              name: toolName,
              args: toolArgs,
              result,
            });

            // Add tool result to messages
            currentMessages.push({
              role: 'tool',
              content: JSON.stringify(result),
              toolCallId: toolCall.id,
            });
          } catch (error) {
            // Add error result
            currentMessages.push({
              role: 'tool',
              content: JSON.stringify({ error: (error as Error).message }),
              toolCallId: toolCall.id,
            });
          }
        }
      } else {
        // LLM provided final response
        return {
          finalResponse: response.content,
          toolCalls: toolCallHistory,
        };
      }
    }

    throw new Error('Max iterations reached without final response');
  }

  async executeStreaming(
    messages: LLMMessage[],
    context: ToolContext,
    onChunk: (chunk: string) => void
  ): Promise<string> {
    // For streaming, we need to handle tool calls differently
    // This is a simplified version
    const result = await this.execute(messages, context);
    onChunk(result.finalResponse);
    return result.finalResponse;
  }
}
```

---

## Streaming Responses

### Streaming Handler

```typescript
// lib/ai/streaming/handler.ts

export type StreamChunkHandler = (chunk: string) => void;
export type StreamDoneHandler = () => void;
export type StreamErrorHandler = (error: Error) => void;

export interface StreamHandlers {
  onChunk: StreamChunkHandler;
  onDone?: StreamDoneHandler;
  onError?: StreamErrorHandler;
}

export class StreamingLLMHandler {
  constructor(private llm: BaseLLMProvider) {}

  async streamChat(
    messages: LLMMessage[],
    options: LLMCompletionOptions,
    handlers: StreamHandlers
  ): Promise<void> {
    try {
      const stream = this.llm.stream(messages, { ...options, stream: true });

      for await (const chunk of stream) {
        if (chunk.content) {
          handlers.onChunk(chunk.content);
        }

        if (chunk.done) {
          handlers.onDone?.();
          break;
        }
      }
    } catch (error) {
      handlers.onError?.(error as Error);
      throw error;
    }
  }

  async streamToResponse(
    messages: LLMMessage[],
    options: LLMCompletionOptions,
    response: Response
  ): Promise<void> {
    const stream = this.llm.stream(messages, { ...options, stream: true });

    const encoder = new TextEncoder();
    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of stream) {
            if (chunk.content) {
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content: chunk.content })}\n\n`));
            }

            if (chunk.done) {
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ done: true })}\n\n`));
              controller.close();
              break;
            }
          }
        } catch (error) {
          controller.error(error);
        }
      },
    });

    return new Response(readableStream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }
}
```

### Server-Sent Events Endpoint

```typescript
// app/api/chat/stream/route.ts

import { StreamingLLMHandler } from '@/lib/ai/streaming/handler';
import { LLMProviderFactory } from '@/lib/ai/providers/factory';

export async function POST(request: Request) {
  const { messages, conversationId } = await request.json();

  const provider = LLMProviderFactory.createWithFallback({
    type: 'openai',
    apiKey: process.env.OPENAI_API_KEY!,
    fallback: {
      type: 'anthropic',
      apiKey: process.env.ANTHROPIC_API_KEY!,
    },
  });

  const handler = new StreamingLLMHandler(provider);

  return handler.streamToResponse(
    messages,
    { model: 'gpt-4o', temperature: 0.7 },
    new Response()
  );
}
```

### Client-Side Streaming

```typescript
// hooks/use-streaming-chat.ts

export function useStreamingChat() {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const streamChat = async (messages: LLMMessage[]) => {
    setIsStreaming(true);
    setResponse('');
    setError(null);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader available');

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.content) {
              setResponse(prev => prev + data.content);
            }

            if (data.done) {
              setIsStreaming(false);
            }
          }
        }
      }
    } catch (err) {
      setError(err as Error);
      setIsStreaming(false);
    }
  };

  return { response, isStreaming, error, streamChat };
}
```

---

## Token Optimization

### Token Caching

```typescript
// lib/ai/optimization/token-cache.ts

export interface CacheEntry {
  prompt: string;
  response: string;
  tokens: number;
  createdAt: Date;
  expiresAt: Date;
}

export class TokenCache {
  private cache: Map<string, CacheEntry> = new Map();
  private maxSize = 1000; // Maximum cache entries
  private ttl = 3600000; // 1 hour TTL

  generateKey(prompt: string, model: string): string {
    // Simple hash - use better hashing in production
    return `${model}:${prompt.slice(0, 100)}`;
  }

  get(prompt: string, model: string): string | null {
    const key = this.generateKey(prompt, model);
    const entry = this.cache.get(key);

    if (!entry) return null;

    // Check expiration
    if (entry.expiresAt < new Date()) {
      this.cache.delete(key);
      return null;
    }

    return entry.response;
  }

  set(
    prompt: string,
    model: string,
    response: string,
    tokens: number
  ): void {
    // Enforce max size
    if (this.cache.size >= this.maxSize) {
      this.evictOldest();
    }

    const key = this.generateKey(prompt, model);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + this.ttl);

    this.cache.set(key, {
      prompt,
      response,
      tokens,
      createdAt: now,
      expiresAt,
    });
  }

  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime: Date | null = null;

    for (const [key, entry] of this.cache.entries()) {
      if (!oldestTime || entry.createdAt < oldestTime) {
        oldestKey = key;
        oldestTime = entry.createdAt;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  clear(): void {
    this.cache.clear();
  }

  getStats(): { size: number; totalTokens: number } {
    let totalTokens = 0;

    for (const entry of this.cache.values()) {
      totalTokens += entry.tokens;
    }

    return {
      size: this.cache.size,
      totalTokens,
    };
  }
}

export const tokenCache = new TokenCache();
```

### Prompt Compression

```typescript
// lib/ai/optimization/compression.ts

export class PromptCompressor {
  compress(messages: LLMMessage[], maxTokens: number): LLMMessage[] {
    const currentTokens = this.countTokens(messages);

    if (currentTokens <= maxTokens) {
      return messages;
    }

    // Remove oldest non-system messages first
    const compressed: LLMMessage[] = [];
    let tokenCount = 0;

    // Keep system message
    const systemMessage = messages.find(m => m.role === 'system');
    if (systemMessage) {
      compressed.push(systemMessage);
      tokenCount += this.countTokens([systemMessage]);
    }

    // Add recent messages until we hit the limit
    const chatMessages = messages.filter(m => m.role !== 'system').reverse();

    for (const message of chatMessages) {
      const messageTokens = this.countTokens([message]);

      if (tokenCount + messageTokens > maxTokens) {
        break;
      }

      compressed.unshift(message);
      tokenCount += messageTokens;
    }

    return compressed;
  }

  summarizeOldMessages(
    messages: LLMMessage[],
    llm: BaseLLMProvider
  ): Promise<LLMMessage[]> {
    const recentMessages = messages.slice(-6);
    const oldMessages = messages.slice(0, -6);

    if (oldMessages.length === 0) {
      return messages;
    }

    // Generate summary of old messages
    const summaryPrompt = this.buildSummaryPrompt(oldMessages);
    const summary = await llm.complete([
      {
        role: 'system',
        content: 'Summarize the conversation concisely.',
      },
      {
        role: 'user',
        content: summaryPrompt,
      },
    ]);

    const summaryMessage: LLMMessage = {
      role: 'system',
      content: `[Previous conversation summary]: ${summary.content}`,
    };

    return [summaryMessage, ...recentMessages];
  }

  private countTokens(messages: LLMMessage[]): number {
    // Rough estimation
    const totalChars = messages.reduce((sum, m) => sum + m.content.length, 0);
    return Math.ceil(totalChars / 4);
  }

  private buildSummaryPrompt(messages: LLMMessage[]): string {
    return `Summarize these messages:

${messages.map(m => `${m.role}: ${m.content}`).join('\n\n')}

Provide a concise summary of key points discussed.`;
  }
}
```

---

## Error Handling & Fallbacks

### Error Types and Recovery

```typescript
// lib/ai/errors/handling.ts

export enum LLMErrorType {
  RATE_LIMIT = 'rate_limit',
  TIMEOUT = 'timeout',
  INVALID_REQUEST = 'invalid_request',
  INSUFFICIENT_QUOTA = 'insufficient_quota',
  MODEL_OVERLOADED = 'model_overloaded',
  NETWORK = 'network',
  UNKNOWN = 'unknown',
}

export class LLMError extends Error {
  constructor(
    public type: LLMErrorType,
    public originalError: Error,
    public retryable: boolean
  ) {
    super(originalError.message);
    this.name = 'LLMError';
  }
}

export class LLMErrorHandler {
  private retryConfig = {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 30000,
  };

  async handle<T>(
    fn: () => Promise<T>,
    context: { operation: string; conversationId?: string }
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.retryConfig.maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        const llmError = this.classifyError(error as Error);

        // Log error
        console.error(`LLM error (attempt ${attempt + 1}):`, llmError);

        // Check if retryable
        if (!llmError.retryable || attempt === this.retryConfig.maxAttempts) {
          // Try fallback or throw
          return await this.handleFallback(context, llmError);
        }

        // Wait before retry with exponential backoff
        const delay = Math.min(
          this.retryConfig.baseDelay * Math.pow(2, attempt),
          this.retryConfig.maxDelay
        );

        await this.sleep(delay);
      }
    }

    throw new LLMError(LLMErrorType.UNKNOWN, lastError!, false);
  }

  private classifyError(error: Error): LLMError {
    const message = error.message.toLowerCase();

    if (message.includes('rate limit') || message.includes('429')) {
      return new LLMError(LLMErrorType.RATE_LIMIT, error, true);
    }

    if (message.includes('timeout') || message.includes('timed out')) {
      return new LLMError(LLMErrorType.TIMEOUT, error, true);
    }

    if (message.includes('quota') || message.includes('billing')) {
      return new LLMError(LLMErrorType.INSUFFICIENT_QUOTA, error, false);
    }

    if (message.includes('overloaded') || message.includes('503')) {
      return new LLMError(LLMErrorType.MODEL_OVERLOADED, error, true);
    }

    if (message.includes('network') || message.includes('fetch')) {
      return new LLMError(LLMErrorType.NETWORK, error, true);
    }

    return new LLMError(LLMErrorType.UNKNOWN, error, false);
  }

  private async handleFallback(
    context: { operation: string; conversationId?: string },
    error: LLMError
  ): Promise<never> {
    // Try fallback provider
    if (error.type !== LLMErrorType.INSUFFICIENT_QUOTA) {
      try {
        const fallbackProvider = LLMProviderFactory.createWithFallback({
          type: 'anthropic',
          apiKey: process.env.ANTHROPIC_API_KEY!,
        });

        // Retry with fallback - this would need more context
        throw error; // For now, just throw
      } catch {
        // Fallback also failed
      }
    }

    // Send notification about persistent failures
    await this.notifyFailure(context, error);

    throw error;
  }

  private async notifyFailure(
    context: { operation: string; conversationId?: string },
    error: LLMError
  ): Promise<void> {
    // Send alert to monitoring system
    console.error('Persistent LLM failure:', {
      operation: context.operation,
      conversationId: context.conversationId,
      errorType: error.type,
      message: error.originalError.message,
    });
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

## Cost Management

### Token Usage Tracker

```typescript
// lib/ai/monitoring/token-usage.ts

export interface TokenUsageRecord {
  timestamp: Date;
  model: string;
  provider: string;
  operation: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCost: number;
  userId?: string;
  agencyId?: string;
  conversationId?: string;
}

export class TokenUsageTracker {
  private records: TokenUsageRecord[] = [];
  private pricing: Record<string, { prompt: number; completion: number }> = {
    'gpt-4o': { prompt: 0.005, completion: 0.015 }, // per 1M tokens
    'gpt-4o-mini': { prompt: 0.00015, completion: 0.0006 },
    'claude-3-5-sonnet': { prompt: 0.003, completion: 0.015 },
    'claude-3-haiku': { prompt: 0.00025, completion: 0.00125 },
  };

  track(
    model: string,
    provider: string,
    operation: string,
    usage: { promptTokens: number; completionTokens: number },
    context?: { userId?: string; agencyId?: string; conversationId?: string }
  ): void {
    const pricing = this.pricing[model] || { prompt: 0, completion: 0 };
    const estimatedCost =
      (usage.promptTokens * pricing.prompt) / 1000000 +
      (usage.completionTokens * pricing.completion) / 1000000;

    const record: TokenUsageRecord = {
      timestamp: new Date(),
      model,
      provider,
      operation,
      promptTokens: usage.promptTokens,
      completionTokens: usage.completionTokens,
      totalTokens: usage.promptTokens + usage.completionTokens,
      estimatedCost,
      ...context,
    };

    this.records.push(record);

    // Persist to database
    this.persistRecord(record);
  }

  getUsageByAgency(agencyId: string, startDate: Date, endDate: Date): {
    totalTokens: number;
    totalCost: number;
    byModel: Record<string, { tokens: number; cost: number }>;
  } {
    const filtered = this.records.filter(
      r =>
        r.agencyId === agencyId &&
        r.timestamp >= startDate &&
        r.timestamp <= endDate
    );

    const byModel: Record<string, { tokens: number; cost: number }> = {};

    for (const record of filtered) {
      if (!byModel[record.model]) {
        byModel[record.model] = { tokens: 0, cost: 0 };
      }

      byModel[record.model].tokens += record.totalTokens;
      byModel[record.model].cost += record.estimatedCost;
    }

    return {
      totalTokens: filtered.reduce((sum, r) => sum + r.totalTokens, 0),
      totalCost: filtered.reduce((sum, r) => sum + r.estimatedCost, 0),
      byModel,
    };
  }

  getUserStats(userId: string, days = 30): {
    totalRequests: number;
    totalTokens: number;
    totalCost: number;
    averageTokensPerRequest: number;
  } {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const userRecords = this.records.filter(
      r => r.userId === userId && r.timestamp >= since
    );

    const totalTokens = userRecords.reduce((sum, r) => sum + r.totalTokens, 0);
    const totalCost = userRecords.reduce((sum, r) => sum + r.estimatedCost, 0);

    return {
      totalRequests: userRecords.length,
      totalTokens,
      totalCost,
      averageTokensPerRequest: userRecords.length > 0 ? totalTokens / userRecords.length : 0,
    };
  }

  private async persistRecord(record: TokenUsageRecord): Promise<void> {
    // Store in database for analytics
    await db.tokenUsage.create({ data: record });
  }
}

export const tokenUsageTracker = new TokenUsageTracker();
```

### Budget Limits

```typescript
// lib/ai/monitoring/budget.ts

export interface BudgetLimit {
  agencyId: string;
  period: 'daily' | 'weekly' | 'monthly';
  maxTokens: number;
  maxCost: number;
  alertThreshold: number; // Alert at this percentage (0-1)
}

export class BudgetMonitor {
  private limits: Map<string, BudgetLimit> = new Map();

  setLimit(limit: BudgetLimit): void {
    const key = `${limit.agencyId}:${limit.period}`;
    this.limits.set(key, limit);
  }

  async checkLimit(
    agencyId: string,
    estimatedTokens: number,
    model: string
  ): Promise<{ allowed: boolean; reason?: string }> {
    const tracker = new TokenUsageTracker();
    const now = new Date();

    // Check all periods
    for (const period of ['daily', 'weekly', 'monthly'] as const) {
      const key = `${agencyId}:${period}`;
      const limit = this.limits.get(key);

      if (!limit) continue;

      // Get period start
      const periodStart = this.getPeriodStart(period);

      // Get current usage
      const usage = tracker.getUsageByAgency(agencyId, periodStart, now);

      // Check token limit
      if (usage.totalTokens + estimatedTokens > limit.maxTokens) {
        return {
          allowed: false,
          reason: `Token limit exceeded for ${period} period (${usage.totalTokens}/${limit.maxTokens} tokens used)`,
        };
      }

      // Check cost limit
      const estimatedCost = this.estimateCost(model, estimatedTokens);
      if (usage.totalCost + estimatedCost > limit.maxCost) {
        return {
          allowed: false,
          reason: `Cost limit exceeded for ${period} period ($${usage.totalCost.toFixed(2)}/$${limit.maxCost} spent)`,
        };
      }

      // Check alert threshold
      const tokenPercent = (usage.totalTokens + estimatedTokens) / limit.maxTokens;
      const costPercent = (usage.totalCost + estimatedCost) / limit.maxCost;

      if (tokenPercent >= limit.alertThreshold || costPercent >= limit.alertThreshold) {
        await this.sendAlert(agencyId, period, tokenPercent, costPercent);
      }
    }

    return { allowed: true };
  }

  private getPeriodStart(period: 'daily' | 'weekly' | 'monthly'): Date {
    const now = new Date();

    switch (period) {
      case 'daily':
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
      case 'weekly':
        const dayOfWeek = now.getDay();
        return new Date(now.getTime() - dayOfWeek * 24 * 60 * 60 * 1000);
      case 'monthly':
        return new Date(now.getFullYear(), now.getMonth(), 1);
    }
  }

  private estimateCost(model: string, tokens: number): number {
    const pricing = {
      'gpt-4o': 0.01 / 1000, // Average per token
      'gpt-4o-mini': 0.0003 / 1000,
      'claude-3-5-sonnet': 0.009 / 1000,
    } as Record<string, number>;

    return (pricing[model] || 0.005 / 1000) * tokens;
  }

  private async sendAlert(
    agencyId: string,
    period: string,
    tokenPercent: number,
    costPercent: number
  ): Promise<void> {
    // Send notification to agency admins
    await db.notification.create({
      data: {
        type: 'budget_alert',
        agencyId,
        title: `AI Usage Alert - ${period} budget`,
        message: `Your AI usage is at ${Math.max(tokenPercent, costPercent) * 100}% of the ${period} limit.`,
        priority: tokenPercent >= 1 || costPercent >= 1 ? 'high' : 'medium',
      },
    });
  }
}

export const budgetMonitor = new BudgetMonitor();
```

---

## Summary

The LLM Integration system provides comprehensive functionality for:

- **Multi-Provider Support**: OpenAI, Anthropic, Google, Cohere with unified interface
- **Prompt Engineering**: Templates, few-shot learning, chain of thought
- **Context Management**: Conversation history, dynamic injection, summarization
- **RAG**: Vector store integration, semantic search, context retrieval
- **Function Calling**: Tool registry, orchestration, execution
- **Streaming**: Server-sent events, real-time responses
- **Token Optimization**: Caching, compression, budget limits
- **Error Handling**: Classification, retry with backoff, fallbacks
- **Cost Management**: Usage tracking, budget alerts, optimization

### Key Components

| Component | Purpose |
|-----------|---------|
| **Provider Factory** | Create LLM providers with fallbacks |
| **Prompt Templates** | Reusable prompt patterns with variables |
| **Context Manager** | Manage conversation history and context |
| **RAG Pipeline** | Enrich responses with retrieved context |
| **Tool Registry** | Register and execute function calls |
| **Token Cache** | Cache responses to reduce API calls |
| **Budget Monitor** | Enforce usage limits and alert on thresholds |

### Next Steps

See [AIML_02_DECISION_INTELLIGENCE.md](./AIML_02_DECISION_INTELLIGENCE.md) for recommendation engines and prediction models.

---

**Last Updated:** 2026-04-25
