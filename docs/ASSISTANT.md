# Armstrong: technical guide

Armstrong is Penumbra's in-app assistant (the **Ask** button). How to *use* it is in the
[README](../README.md#ask-armstrong); this page covers how it works, how to set up the optional AI chat, its tests and
its limits.

## How Armstrong answers

| | **Built-in guide** (default) | **Space assistant** (free LLM chat) | **AI assistant** (optional) |
|---|---|---|---|
| What it is | A scripted guide written for non-specialists: no AI involved | An open-source model (default `openai/gpt-oss-120b` on Groq) answering space and app questions | Claude (Anthropic's model), with tools that run Penumbra's analyses |
| Cost | Free | Free tier (Groq; rate-limited) or any OpenAI-compatible provider | Pay-as-you-go Claude API usage |
| Internet | Not needed: works fully offline | Needed | Needed |
| Answers | Buttons, plus common typed questions and requests | Typed questions the built-in guide doesn't recognise | Any question |
| Turns on | Always | When the server has `LLM_API_KEY` set | When the server has `ANTHROPIC_API_KEY` set (the panel then switches to it) |

Without a Claude key, the panel uses the built-in guide, and hands only the typed questions it doesn't recognise
(for example "What is the James Webb Space Telescope looking for?") to the space assistant. Its replies appear in
the same conversation under a small *Space assistant* label. The guide and the Claude assistant share the same
change cards (**Do it for me** / **Apply**).

---

## How it works

### Where the numbers come from
Penumbra does all its science on the server (terrain horizons, Sun/Earth geometry, simulated landings). Armstrong
follows the same rule and never computes science in the browser. Its numbers come from:

- **the mission card's results**, which the panel reads from the same requests the views make (cache hits, no extra
  work); or
- **the same API routes the app uses**: `POST /api/landing-risk`, `POST /api/visibility`, `POST /api/compare` and
  `POST /api/endurance` (for example, "what if I land on 15 July?" calls `/api/visibility` for both dates).

Answers state the settings they used (site, date, landing zone, caution level) so it's clear what was computed.

The exception is the **space assistant**: it doesn't see your mission's numbers and answers general space questions
from the AI model's own knowledge, so its replies carry a *Space assistant* label (see
[Space assistant](#space-assistant-free-llm-chat)).

### Built-in guide: the pieces
All in `src/features/assistant/guide/`, plain TypeScript, no AI and no network beyond Penumbra's own server.

| File | Role |
|---|---|
| `engine.ts` | Turns a request into an answer: greeting, walkthrough steps, explanations, decision helpers, what-ifs, typed commands. Each answer can carry change cards, follow-up buttons, a "Show me where" target and walkthrough progress. |
| `plain.ts` | Plain-language explanations of each choice (site, date, accuracy, caution level, aim, vehicle, mission length), the **In short** verdict and **Tell me more** texts. |
| `nlu.ts` | Understands typed text: finds sites (typo-tolerant), dates ("15 July", "July 15th", "2027-07-15"), distances, caution levels, mission length, sections, vehicles; recognises yes/no/next/more/show me/thanks. |
| `watch.ts` | Notices what changed in the app (site, date, accuracy, robust-aim result, skyline…) and builds the plain-language tip plus the next step. |
| `whatsthis.ts` | "What's this?": maps what you tap to an explanation. |
| `spotlight.ts` | "Show me where": switches to the right section, opens collapsed panels, scrolls the control into view and outlines it. |
| `content.ts` | Glossary, how-to answers, screen descriptions, limitations, validation summary, tappable words. |
| `util.ts` | Shared helpers, site names, and the guide's name (`GUIDE_NAME = "Armstrong"`). |

The panel itself is `src/features/assistant/AssistantPanel.tsx`. Changes are applied by `applyProposal.ts`
through the same functions the app's own controls use, after saving an undo snapshot. The welcome bubble is
`GuideWelcome.tsx`; the avatar is `GuideAvatar.tsx` (`src/assets/armstrong.png`).

### AI assistant (optional): the pieces
When `ANTHROPIC_API_KEY` is set, the panel sends each question to `POST /api/assistant` (server-sent events):

- **What it sends:** the conversation, a snapshot of the screen (`<app_state>`: section, site, settings and the
  numbers already computed) and a machine-readable copy of the settings.
- **What Claude knows:** a system prompt (`backend/app/assistant/guide.py`) describing every screen and control,
  the science concepts, the limitations and the rules: never state a mission number that didn't come from the
  screen snapshot or a tool, never claim a change was made.
- **Tools** (`backend/app/assistant/tools.py`), run by the Anthropic SDK's tool runner (up to 8 model turns per
  question). Each calls the same analysis code as the API, defaults to your current settings, and accepts
  overrides for "what if" questions:

  | Tool | Purpose |
  |---|---|
  | `get_mission_outlook` | Sunlight, Earth and DSN contact, longest darkness, battery and daily sunlight after landing |
  | `get_landing_risk` | Sunlight for a perfect landing and across 2,000 simulated landings (P50–P05) |
  | `find_robust_aim` | Brightest point vs the safer robust aim |
  | `compare_sites` | Ranks the sites for one mission (same method as the Compare page) |
  | `find_best_landing_dates` | Best landing days of 2027, with battery endurance |
  | `get_site_info` | Facts about the sites |
  | `propose_app_changes` | Prepares a change card; nothing changes until the person clicks Apply |

- **Model and settings:** `claude-opus-5-5` at `medium` effort by default, streaming, prompt caching on the system
  prompt, and the API's server-side fallback if a request is declined.
- The tools' numbers were checked against the API routes on the real NASA/JPL data: they match exactly.

---

## Setup

The built-in guide needs nothing: run Penumbra as usual (`python tasks.py dev`) and click **Ask**.

To turn on the AI assistant, put a Claude API key in `.env` (git-ignored) and restart the server:

```
ANTHROPIC_API_KEY=sk-ant-...
```

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | (none) | Turns on the AI assistant |
| `PENUMBRA_ASSISTANT_MODEL` | `claude-opus-5-5` | Claude model |
| `PENUMBRA_ASSISTANT_EFFORT` | `medium` | `low`, `medium` or `high` |
| `PENUMBRA_ASSISTANT` | `1` | `0` switches the AI assistant off |
| `PENUMBRA_OFFLINE` | `0` | `1` also switches it off (the built-in guide keeps working) |

`GET /api/assistant/status` reports whether the AI assistant is available and why not, and whether the space
assistant is set up (never any key).

### Space assistant (free LLM chat)

The space assistant calls any provider with an OpenAI-compatible API from the server (`POST /api/chat`, code in
`backend/app/assistant/llm_chat.py`), so the key never reaches the browser. By default it uses the **Groq API**,
which has a free tier. (Groq, with a *q*, at groq.com, runs open models quickly. It is not xAI's *Grok* chatbot.)

#### Getting a free Groq API key

1. Go to [console.groq.com](https://console.groq.com) and sign in (Google, GitHub or email). No credit card is needed.
2. Open **API Keys** ([console.groq.com/keys](https://console.groq.com/keys)) and click **Create API Key**. Give it a
   name such as `Penumbra`.
3. Copy the key straight away; Groq shows it only once. It starts with `gsk_`.
4. Put it in `.env` at the project root (the file is git-ignored, so the key is never committed), right after
   `LLM_API_KEY=`, with no spaces or quotes:

   ```
   LLM_BASE_URL=https://api.groq.com/openai/v1
   LLM_API_KEY=gsk_...
   LLM_MODEL=openai/gpt-oss-120b
   ```
5. Restart the server (`python tasks.py dev`). To check the key and model first, run the terminal chatbot below.

Keep the key private: don't share it or put it in code. If it leaks, delete it on the same API Keys page and create a
new one. Groq's free tier is rate-limited; when the limit is reached, the chat asks you to wait a minute.

Switching provider is a matter of changing those lines: `.env.example` lists Gemini, OpenRouter (models ending in
`:free`) and Ollama (local) as alternatives. Each question sends a system prompt (who the assistant is, Penumbra's
features, "say so if unsure", "steer off-topic questions back to space") plus the last 10 messages, with replies
capped at 500 tokens and `temperature` 0.7. Errors are shown in the chat as plain messages: invalid key (401), rate
limit, so wait a minute (429, not retried automatically), model not found (404), or a generic error.

### Terminal chatbot

`scripts/space_chat_cli.py` is the same chat in the terminal, a quick way to check a key and model:

```bash
pip install openai python-dotenv     # already in the project environment
python scripts/space_chat_cli.py     # reads LLM_BASE_URL, LLM_API_KEY, LLM_MODEL from .env; type exit to leave
```

---

## Tests

```bash
npx vitest run tests/frontend          # includes the guide, panel, change cards, undo and explanations
python -m pytest tests/api/test_assistant.py tests/api/test_assistant_tools.py   # AI endpoint and tools
python -m pytest tests/api/test_chat.py                                          # space assistant chat
```

The frontend tests cover typed-text understanding, the plain-language explanations, the walkthrough and its
auto-advance, the decision helpers, what-ifs, commands, tips, "What's this?", tappable words, Undo and a full render
of the panel. The backend tests cover prompt assembly, availability, the event stream and every tool, with the
science calls replaced so they run without data or an API key.

---

## Limits

- The built-in guide understands common phrasings, not everything; when it doesn't, it says so and offers options.
- Read aloud depends on the voices installed in the browser or operating system.
- Armstrong explains Penumbra's results, so it inherits their limits: terrain resolution, a landing-error model
  chosen by the user, geometric (not scheduled) DSN contact and a simplified battery estimate. See *Limitations* in
  [PENUMBRA.md](../PENUMBRA.md).
- The AI assistant needs internet access and costs money per question; the built-in guide is free and offline.
- The space assistant answers from the model's general knowledge, not from Penumbra's calculations, and models can
  get facts wrong. Free tiers are rate-limited: if many questions arrive quickly, it asks you to wait a minute.
