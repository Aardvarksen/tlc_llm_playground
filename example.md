I'll search for information about connecting local models or custom endpoints to Claude Code.Let me get the official Anthropic documentation for more precise details:Let me also check the model configuration docs for the specific environment variables:Let me fetch the official model configuration docs:Now I have a complete picture. Here's the technical breakdown for connecting your OpenAI-compatible queue server to Claude Code:

---

## Connecting Local Models to Claude Code

### The Core Challenge

Claude Code speaks the **Anthropic Messages API** (`/v1/messages`), while most local model servers (LM Studio, Ollama, vLLM) expose an **OpenAI-compatible API** (`/v1/chat/completions`). You need a translation layer.

### Option 1: LiteLLM Proxy (Recommended for Your Setup)

Since you're already looking at vLLM for local serving, LiteLLM is the most mature solution:

**Environment Variables:**
```bash
# Point Claude Code to your LiteLLM proxy
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_AUTH_TOKEN="your-litellm-master-key"

# Map Claude's model tiers to your local models
export ANTHROPIC_DEFAULT_HAIKU_MODEL="your-fast-model"
export ANTHROPIC_DEFAULT_SONNET_MODEL="your-main-model"  
export ANTHROPIC_DEFAULT_OPUS_MODEL="your-main-model"
```

**LiteLLM config.yaml example:**
```yaml
model_list:
  - model_name: "anthropic/*"  # Catch-all for Anthropic requests
    litellm_params:
      model: "openai/qwen3-14b"  # Your vLLM endpoint
      api_base: "http://localhost:8000/v1"
      api_key: "dummy"
      max_tokens: 65536
```

### Option 2: Direct Configuration (If Your Server Has Anthropic Pass-through)

If your queue server implements the Anthropic Messages format directly:

```bash
export ANTHROPIC_BASE_URL="http://your-queue-server:port"
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

Or in `~/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://your-queue-server:port",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key"
  }
}
```

### Gateway Requirements

For any proxy to work with Claude Code, it must:

1. Expose Anthropic Messages API format: `/v1/messages` and `/v1/messages/count_tokens`
2. Forward these request headers: `anthropic-beta`, `anthropic-version`
3. Handle streaming responses properly

### Other Useful Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_MODEL` | Override the default model |
| `DISABLE_PROMPT_CACHING` | Set to `1` for local models (they don't support it) |
| `API_TIMEOUT_MS` | Increase timeout for slower local inference |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Reduces unnecessary Anthropic calls |

### Practical Considerations

1. **Extended thinking** won't work with local models (Claude-specific feature)
2. **Background indexing** uses Haiku by default—you may want to route this to a smaller/faster local model
3. **Prompt caching** should be disabled for local models that don't support it
4. Context window limits will depend on your local model's capabilities

---

Given your setup with vLLM and Qwen3-14B, the LiteLLM proxy approach would integrate nicely with your existing infrastructure. Want me to dig into any specific aspect—like the LiteLLM config for vLLM specifically, or how to set up model routing for different task types?