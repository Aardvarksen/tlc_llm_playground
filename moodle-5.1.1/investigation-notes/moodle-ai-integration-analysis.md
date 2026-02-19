# Moodle 5.1 AI Integration Analysis

> **Purpose**: Document how Moodle's AI Placements build context for LLM requests, so we can replicate this behavior in a Streamlit test application.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Built-in AI Placements](#built-in-ai-placements)
3. [System Prompts](#system-prompts)
4. [Context Building: How `[role="main"]` Works](#context-building-how-rolemain-works)
5. [Third-Party Plugins](#third-party-ai-placement-plugins)
6. [Provider Compatibility](#provider-compatibility-openai-compatible-api)
7. [Model Selection & Parameter Configuration](#model-selection--parameter-configuration)
8. [Replicating in Streamlit](#replicating-in-streamlit)

---

## Architecture Overview

Moodle's AI subsystem follows a **Placement → Action → Manager → Provider** architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND (Browser)                                                   │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ placement.js                                                     │ │
│ │ - User clicks "Summarise" or "Explain" button                   │ │
│ │ - getTextContent() grabs [role="main"].innerText                │ │
│ │ - Sends AJAX request to external API                            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND (PHP)                                                        │
│ ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────┐ │
│ │ External API        │→ │ Action Class        │→ │ Manager       │ │
│ │ (summarise_text.php)│  │ (summarise_text.php)│  │ (manager.php) │ │
│ └─────────────────────┘  └─────────────────────┘  └───────┬───────┘ │
│                                                           │         │
│                                                           ▼         │
│                                              ┌────────────────────┐ │
│                                              │ Provider           │ │
│                                              │ (ollama/openai/etc)│ │
│                                              └────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LLM API (Ollama, OpenAI, LM Studio, etc.)                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Files**:
- `public/ai/placement/courseassist/` - The "Course Assist" placement (Summarise/Explain buttons)
- `public/ai/classes/aiactions/` - Action class definitions
- `public/ai/provider/ollama/` - Ollama provider implementation
- `public/lang/en/ai.php` - System prompts and strings

---

## Built-in AI Placements

Moodle 5.1 ships with **2 built-in placements**:

### 1. Course Assist (`aiplacement_courseassist`)

**Location**: `public/ai/placement/courseassist/`

**Actions supported**:
- `summarise_text` - Summarize page content
- `explain_text` - Explain page content

**How it works**:
1. Adds "Summarise" and "Explain" buttons to course pages
2. When clicked, grabs ALL text from `[role="main"]` element
3. Sends to configured AI provider with system prompt
4. Displays response in a drawer panel

**Source Reference**: `public/ai/placement/courseassist/classes/placement.php:28-35`
```php
public function get_action_list(): array {
    return [
        \core_ai\aiactions\summarise_text::class,
        \core_ai\aiactions\explain_text::class,
    ];
}
```

### 2. Editor (`aiplacement_editor`)

**Location**: `public/ai/placement/editor/`

**Actions supported**:
- `generate_text` - Generate text in TinyMCE editor
- `generate_image` - Generate images in TinyMCE editor

**Use case**: Content creation assistance for teachers/admins

---

## System Prompts

All system prompts are defined in `public/lang/en/ai.php`.

### Summarise Text (lines 54-63)

```
You will receive a text input from the user. Your task is to summarize the provided text. Follow these guidelines:
    1. Condense: Shorten long passages into key points.
    2. Simplify: Make complex information easier to understand, especially for learners.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the summary is easy to read and effectively conveys the main points of the original text.
```

### Explain Text (lines 30-41)

```
You will receive a text input from the user. Your task is to explain the provided text. Follow these guidelines:
    1. Elaborate: Expand on key ideas and concepts, ensuring the explanation adds meaningful depth and avoids restating the text verbatim.
    2. Simplify: Break down complex terms or ideas into simpler components, making them easy to understand for a wide audience, including learners.
    3. Provide Context: Explain why something happens, how it works, or what its purpose is. Include relevant examples or analogies to enhance understanding where appropriate.
    4. Organise Logically: Structure your explanation to flow naturally, beginning with fundamental ideas before moving to finer details.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the explanation is easy to read and effectively conveys the main points of the original text.
```

### Generate Text (lines 48-50)

```
You will receive a text input from the user. Your task is to generate text based on their request. Follow these important instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
```

---

## Context Building: How `[role="main"]` Works

### The Critical Code

**JavaScript Context Extraction** (`public/ai/placement/courseassist/amd/src/placement.js:527-530`):

```javascript
getTextContent() {
    const mainRegion = document.querySelector(Selectors.ELEMENTS.MAIN_REGION);
    return mainRegion.innerText || mainRegion.textContent;
}
```

**Selector Definition** (`public/ai/placement/courseassist/amd/src/selectors.js:28`):

```javascript
ELEMENTS: {
    // ...
    MAIN_REGION: '[role="main"]',
    // ...
}
```

### What `[role="main"]` Contains

The `[role="main"]` div is rendered by Moodle's core renderer.

**Source**: `public/lib/classes/output/core_renderer.php:461`
```php
return '<div role="main">' . $this->unique_main_content_token . '</div>';
```

**Theme Template** (`public/theme/boost/templates/columns2.mustache:76-92`):
```html
<div id="region-main" {{#hasblocks}}class="has-blocks mb-3"{{/hasblocks}}>
    {{#hasregionmainsettingsmenu}}
        <div class="region_main_settings_menu_proxy"></div>
    {{/hasregionmainsettingsmenu}}
    {{{ output.course_content_header }}}
    {{#headercontent}}
        {{> core/activity_header }}
    {{/headercontent}}
    {{#overflow}}
        {{> core/url_select}}
    {{/overflow}}
    {{{ output.main_content }}}           <!-- THIS IS THE MAIN CONTENT -->
    {{{ output.activity_navigation }}}
    {{{ output.course_content_footer }}}
</div>
```

### What Actually Gets Captured

The `[role="main"]` region contains:
1. **Course content header** - Breadcrumbs, activity header
2. **Activity header** - Title, completion info, dates
3. **Main content** - THE ACTUAL PAGE CONTENT (varies by activity type)
4. **Activity navigation** - Previous/Next buttons
5. **Course content footer** - Any footer content

**IMPORTANT LIMITATION**: The JavaScript uses `.innerText`, which:
- Extracts ALL visible text from the entire region
- Includes navigation text, button labels, headers
- Does NOT intelligently select just the "educational content"
- May include irrelevant UI text that ends up in the LLM prompt

**CRITICAL LIMITATION - Iframe Content Not Captured**:

The `.innerText` property only extracts text from the current document's DOM tree. Content inside `<iframe>` elements is NOT captured because:
- Iframes are separate documents with their own DOM
- Cross-origin iframes (different domain) are completely inaccessible due to browser security
- Even same-origin iframes require explicit traversal that Moodle's code doesn't perform

**Affected Moodle activity types**:
- **URL resources** embedding external content (e.g., Pressbooks, external documentation)
- **H5P interactive content** (renders in iframe)
- **SCORM packages** (content loads in iframe)
- **LTI external tools** (third-party content in iframe)
- **Embedded media players** (some implementations)

**Example**: A Moodle URL resource embedding a Pressbooks chapter will only capture the fallback text (e.g., "Click on Course Settings to open the resource") rather than the actual educational content displayed in the iframe.

This means **Moodle's AI features (Summarise/Explain) are effectively useless for any page where the primary content is delivered via iframe**.

### Example: What a Quiz Page Contains

For a quiz view page (`public/mod/quiz/view.php`), the main content includes:
- Quiz name and description
- Quiz timing information
- Attempt history table
- "Attempt quiz" button text
- Grade information
- Navigation elements

ALL of this text gets sent to the LLM when a user clicks "Summarise".

---

## Third-Party AI Placement Plugins

As of January 2025, the ecosystem is minimal:

### 1. Text Insights (`aiplacement_textinsights`)
- **URL**: https://moodle.org/plugins/aiplacement_textinsights
- **Sites**: 18
- **Features**: Right-click context menu with Explain/Summarize/Validate
- **Moodle**: 5.0 only

### 2. Exabis AI Chat (`aiplacement_exaaichat`)
- **URL**: https://moodle.org/plugins/aiplacement_exaaichat
- **Sites**: 7
- **Features**: AI chat widget in every course/activity
- **Moodle**: 4.5, 5.0, 5.1

---

## Provider Compatibility: OpenAI-Compatible API

### Key Finding

The `aiprovider_openaicompatible` plugin allows Moodle to connect to ANY OpenAI-compatible API endpoint, including:
- LM Studio
- Ollama (via OpenAI compatibility mode)
- Our Queue Server (if we implement OpenAI-compatible endpoints)

### How Ollama Provider Builds the Request

**Source**: `public/ai/provider/ollama/classes/process_generate_text.php:37-66`

```php
protected function create_request_object(string $userid): RequestInterface {
    $requestobj = new \stdClass();
    $requestobj->model = $this->get_model();
    $requestobj->stream = false;
    $requestobj->prompt = $this->action->get_configuration('prompttext');  // THE PAGE TEXT
    $requestobj->user = $userid;
    $requestobj->options = new \stdClass();

    // System instruction from config
    $systeminstruction = $this->get_system_instruction();
    if (!empty($systeminstruction)) {
        $requestobj->system = $systeminstruction;
    }

    // Model settings (temperature, top_k, etc.)
    $modelsettings = $this->get_model_settings();
    foreach ($modelsettings as $setting => $value) {
        $requestobj->options->$setting = $value;
    }

    return new Request(
        method: 'POST',
        uri: '',
        body: json_encode($requestobj),
        headers: ['Content-Type' => 'application/json'],
    );
}
```

### Ollama API Endpoint

**Source**: `public/ai/provider/ollama/classes/abstract_processor.php:41-46`

```php
protected function get_endpoint(): UriInterface {
    $url = rtrim($this->provider->config['endpoint'], '/')
        . '/api/generate';

    return new Uri($url);
}
```

The Ollama provider uses the `/api/generate` endpoint (Ollama's native API), NOT the OpenAI-compatible `/v1/chat/completions` endpoint.

---

## Model Selection & Parameter Configuration

**Key Finding**: Model selection and all parameters are configured by the Moodle administrator. The provider sends EXPLICIT values with each request - it does NOT rely on Ollama/LM Studio server defaults.

### Admin Configuration Flow

1. **Site Administration** → **AI** → **AI Providers** → Configure provider instance
2. For each **action** (summarise_text, explain_text, generate_text), admin configures:
   - Model name (dropdown of presets OR custom model name)
   - System instruction (editable, defaults from `ai.php`)
   - Model-specific parameters (temperature, top_k, top_p, etc.)

### Configuration Storage

**Source**: `public/ai/classes/provider.php:51-68`

```php
public function __construct(
    public readonly bool $enabled,
    public string $name,
    string $config,           // JSON: endpoint, auth settings
    string $actionconfig = '', // JSON: per-action model + params
    public readonly ?int $id = null,
) {
    $this->config = json_decode($config, true);
    $this->actionconfig = json_decode($actionconfig, true);
}
```

Settings are stored as JSON in the database with this structure:
```json
{
  "core_ai\\aiactions\\summarise_text": {
    "enabled": true,
    "settings": {
      "model": "llama3.3",
      "systeminstruction": "You will receive a text input...",
      "temperature": 0.8,
      "top_k": 40,
      "top_p": 0.9
    }
  }
}
```

### Model Selection UI

**Source**: `public/ai/provider/ollama/classes/form/action_form.php:156-204`

The admin form provides:
- **Dropdown** with pre-defined models (e.g., "Llama 3.3")
- **"Custom" option** for any model name not in the list
- **Per-model settings** that change based on selection

```php
// Default model
$defaultmodel = $this->actionconfig['model'] ?? 'llama3.3';

// Model list includes 'custom' option
$models['custom'] = get_string('custom', 'core_form');
foreach (helper::get_model_classes() as $class) {
    $model = new $class();
    $models[$model->get_model_name()] = $model->get_model_display_name();
}
```

### Pre-defined Model Settings

**Source**: `public/ai/provider/ollama/classes/aimodel/llama33.php:42-105`

Each pre-defined model can expose configurable parameters:

```php
public function get_model_settings(): array {
    return [
        'mirostat' => [...],      // 0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0
        'temperature' => [...],   // Default: 0.8
        'seed' => [...],          // For reproducibility
        'top_k' => [...],         // Default: 40
        'top_p' => [...],         // Default: 0.9
    ];
}
```

Additionally, there's a `modelextraparams` JSON field for custom parameters:
```json
{
    "num_ctx": 4096,
    "repeat_penalty": 1.1
}
```

### How Settings Flow to the Request

**Source**: `public/ai/provider/ollama/classes/abstract_processor.php:52-80`

```php
// Model name from admin config
protected function get_model(): string {
    return $this->provider->actionconfig[$this->action::class]['settings']['model'];
}

// All model settings from admin config
protected function get_model_settings(): array {
    $settings = $this->provider->actionconfig[$this->action::class]['settings'];

    // Merge in any custom extra params
    if (!empty($settings['modelextraparams'])) {
        $params = json_decode($settings['modelextraparams'], true);
        foreach ($params as $key => $param) {
            $settings[$key] = $param;
        }
    }

    // Remove non-model settings before returning
    unset($settings['model'], $settings['systeminstruction'], ...);
    return $settings;
}
```

### Final Request to Ollama

**Source**: `public/ai/provider/ollama/classes/process_generate_text.php:37-66`

```php
$requestobj = new \stdClass();
$requestobj->model = $this->get_model();           // "llama3.3" from admin config
$requestobj->stream = false;
$requestobj->prompt = $prompttext;                  // The page content
$requestobj->system = $systeminstruction;           // From admin config
$requestobj->user = $userid;
$requestobj->options = new \stdClass();

// ALL model settings explicitly included
$modelsettings = $this->get_model_settings();
foreach ($modelsettings as $setting => $value) {
    $requestobj->options->$setting = $value;        // temperature, top_p, etc.
}
```

**Example request body sent to Ollama:**
```json
{
  "model": "llama3.3",
  "prompt": "Introduction to Python Programming\nThis quiz will test...",
  "system": "You will receive a text input from the user. Your task is to summarize...",
  "stream": false,
  "user": "a]sha256hash",
  "options": {
    "temperature": 0.8,
    "top_k": 40,
    "top_p": 0.9,
    "mirostat": 0
  }
}
```

### Implications for Queue Server / LM Studio

1. **Model name is explicit** - Moodle sends `"model": "llama3.3"`, your server must handle this
2. **Parameters are explicit** - Moodle sends temperature, top_p, etc. - don't rely on server defaults
3. **No parameter inheritance** - If admin leaves a field blank, it's not sent (Ollama uses its defaults)

**For Queue Server compatibility**, you'll need to either:
- Pass through model name and parameters to LM Studio as-is
- Map Moodle model names to LM Studio model identifiers
- Have configuration that mirrors what a Moodle admin would set

---

## Replicating in Streamlit

To replicate Moodle's AI placement behavior in a Streamlit test app:

### 1. Input Simulation

Since we don't have actual Moodle pages, we need to simulate the `[role="main"]` content:

```python
# Option A: Manual text input
page_content = st.text_area("Paste Moodle page content here")

# Option B: Sample content presets
SAMPLE_CONTENTS = {
    "quiz_intro": """Introduction to Python Programming
    This quiz will test your understanding of basic Python concepts...
    Time limit: 30 minutes
    Attempts allowed: 3
    """,
    "lesson_page": """Chapter 3: Variables and Data Types
    In Python, variables are containers for storing data values...
    """
}
```

### 2. System Prompt Selection

```python
SYSTEM_PROMPTS = {
    "summarise_text": """You will receive a text input from the user. Your task is to summarize the provided text. Follow these guidelines:
    1. Condense: Shorten long passages into key points.
    2. Simplify: Make complex information easier to understand, especially for learners.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the summary is easy to read and effectively conveys the main points of the original text.""",

    "explain_text": """You will receive a text input from the user. Your task is to explain the provided text. Follow these guidelines:
    1. Elaborate: Expand on key ideas and concepts, ensuring the explanation adds meaningful depth and avoids restating the text verbatim.
    2. Simplify: Break down complex terms or ideas into simpler components, making them easy to understand for a wide audience, including learners.
    3. Provide Context: Explain why something happens, how it works, or what its purpose is. Include relevant examples or analogies to enhance understanding where appropriate.
    4. Organise Logically: Structure your explanation to flow naturally, beginning with fundamental ideas before moving to finer details.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the explanation is easy to read and effectively conveys the main points of the original text.""",

    "generate_text": """You will receive a text input from the user. Your task is to generate text based on their request. Follow these important instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes."""
}

action = st.selectbox("AI Action", list(SYSTEM_PROMPTS.keys()))
system_prompt = SYSTEM_PROMPTS[action]
```

### 3. API Request Format

For OpenAI-compatible endpoints (like our Queue Server):

```python
def send_to_llm(system_prompt: str, user_content: str, model: str = "llama3"):
    """
    Replicates Moodle's AI placement request format.

    Note: Moodle's Ollama provider uses /api/generate (native Ollama format).
    For OpenAI-compatible endpoints, use /v1/chat/completions format.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    response = requests.post(
        "http://localhost:8000/v1/chat/completions",  # Queue Server endpoint
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    return response.json()["choices"][0]["message"]["content"]
```

### 4. Key Differences to Account For

| Aspect | Moodle | Streamlit Replica |
|--------|--------|-------------------|
| Content source | `[role="main"].innerText` | Manual paste or preset |
| Content quality | Raw page text (includes UI) | Can be cleaned/curated |
| API format | Ollama native (`/api/generate`) | OpenAI-compatible (`/v1/chat/completions`) |
| System prompt | Configurable in admin | Hardcoded from Moodle source |

---

## References

### Source Files (Moodle 5.1.1)
- System prompts: `public/lang/en/ai.php:30-63`
- JS context extraction: `public/ai/placement/courseassist/amd/src/placement.js:527-530`
- JS selectors: `public/ai/placement/courseassist/amd/src/selectors.js:28`
- External API handler: `public/ai/placement/courseassist/classes/external/summarise_text.php`
- Action class: `public/ai/classes/aiactions/summarise_text.php`
- Ollama provider: `public/ai/provider/ollama/classes/process_generate_text.php`
- Core renderer (role="main"): `public/lib/classes/output/core_renderer.php:461`
- Theme template: `public/theme/boost/templates/columns2.mustache:76-92`
- Provider base class: `public/ai/classes/provider.php:51-68`
- Ollama action form: `public/ai/provider/ollama/classes/form/action_form.php:156-204`
- Ollama model class: `public/ai/provider/ollama/classes/aimodel/llama33.php:42-105`
- Ollama abstract processor: `public/ai/provider/ollama/classes/abstract_processor.php:52-80`

### External Resources
- [Moodle AI Subsystem Docs](https://moodledev.io/docs/4.5/apis/subsystems/ai)
- [Moodle Placement Plugin Guide](https://moodledev.io/docs/4.5/apis/plugintypes/ai/placement)
- [CLAMP Analysis of Moodle 4.5 AI](https://www.clamp-it.org/blog/2025/01/31/ai-subsystem-in-moodle-4-5/)
- [Moodle Plugins Directory - AI Placements](https://moodle.org/plugins/browse.php?list=category&id=89)
- [Moodle Plugins Directory - AI Providers](https://moodle.org/plugins/browse.php?list=category&id=90)

---

*Document created: 2025-01-19*
*Based on: Moodle 5.1.1 source code analysis*
