# GH-LLM-Web

A prototype that connects a web-based 3D viewer to Grasshopper via natural language. Chat with an LLM to control parametric models in real-time.

![Architecture](https://img.shields.io/badge/Vue%203-4FC08D?logo=vue.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Socket.IO](https://img.shields.io/badge/Socket.IO-010101?logo=socket.io&logoColor=white)

![Overview](docs/screenshots/overview.png)

## How It Works

```
┌─────────────┐     WebSocket      ┌─────────────┐     WebSocket      ┌─────────────┐
│   Web App   │◄──────────────────►│  Flask Hub  │◄──────────────────►│ Grasshopper │
│   (Vue 3)   │                    │  (Python)   │                    │  (Rhino)    │
└─────────────┘                    └──────┬──────┘                    └─────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │   LLM API   │
                                   │ (OpenAI or  │
                                   │   Ollama)   │
                                   └─────────────┘
```

1. **Web App** - Vue 3 app with 3D mesh viewer and chat interface
2. **Flask Hub** - Coordination server that routes messages and calls the LLM
3. **Grasshopper** - Parametric model with tagged sliders (e.g., `RH_IN:width`)
4. **LLM** - Interprets natural language and returns parameter updates

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Rhino 8 with Grasshopper
- (Optional) Ollama for local LLM, or OpenAI API key

### 1. Install Dependencies

```bash
# Python dependencies
pip install flask flask-socketio python-socketio websocket-client python-dotenv openai-whisper

# Node dependencies
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` (or set environment variables):

```bash
# LLM Configuration
LLM_HOST_URL=http://localhost:11434/v1/chat/completions  # Ollama default
LLM_MODEL=llama3.2:1b
OPENAI_API_KEY=sk-...  # Only needed for OpenAI API

# Server
PORT=5001
```

### 3. Start the Flask Hub

```bash
python flask_hub.py
```

### 4. Start the Web App

```bash
npm run dev
```

Open http://localhost:5173

### 5. Connect Grasshopper

1. Open your Grasshopper definition
2. Add the `gh_socketio_hub.py` component (from `gh-components/`)
3. Tag your sliders by grouping them with names like `RH_IN:width`, `RH_IN:height`
4. Connect your mesh output to the component
5. Set `run=True` and `scan_params=True`

## Grasshopper Setup

### Tagging Parameters

Create groups around your sliders with the naming convention `RH_IN:<param_name>`:

```
┌─────────────────────────┐
│  Group: RH_IN:width     │
│  ┌─────────────────┐    │
│  │  Number Slider  │────┼──► to your definition
│  └─────────────────┘    │
└─────────────────────────┘
```

The component scans for these tagged groups and registers them with the Flask Hub.

### Component Inputs

| Input         | Type        | Description                                      |
| ------------- | ----------- | ------------------------------------------------ |
| `server_url`  | String      | Flask Hub URL (default: `http://localhost:5001`) |
| `scan_params` | Boolean     | Trigger parameter scan and registration          |
| `meshes`      | Mesh/List   | Mesh geometry to send to web viewer              |
| `materials`   | String/List | Optional material names for meshes               |
| `run`         | Boolean     | Enable/disable the component                     |

## Using the Chat

Once connected, you can use natural language to control parameters:

- _"Make it wider"_ - Increases width parameter
- _"Set height to maximum"_ - Sets height to its max value
- _"Make it much shorter but slightly wider"_ - Adjusts multiple params
- _"Double the depth"_ - Doubles the current depth value

![Chat Example](docs/screenshots/chat-conversation.png)

The LLM interprets relative terms:

- "slightly" / "a bit" → ~10-20% change
- "more" / "increase" → ~25-50% change
- "much" / "significantly" → ~50-100% change

## Project Structure

```
gh-llm-web/
├── flask_hub.py              # Flask coordination server
├── gh-components/
│   └── gh_socketio_hub.py    # Grasshopper Python component
├── src/
│   ├── App.vue               # Main app layout
│   ├── components/
│   │   ├── MeshViewer.vue    # Three.js 3D viewer
│   │   ├── Chat.vue          # Chat interface
│   │   ├── Sidebar.vue       # Parameter sliders
│   │   └── ...
│   ├── services/
│   │   └── socket.js         # WebSocket client
│   └── store/
│       └── index.js          # Vuex state management
├── package.json
└── .env.example
```

## Configuration Options

### Flask Hub Environment Variables

| Variable         | Default                                      | Description                   |
| ---------------- | -------------------------------------------- | ----------------------------- |
| `LLM_HOST_URL`   | `http://localhost:11434/v1/chat/completions` | LLM API endpoint              |
| `LLM_MODEL`      | `llama3.2:1b`                                | Model name                    |
| `OPENAI_API_KEY` | -                                            | API key (optional for Ollama) |
| `PORT`           | `5001`                                       | Server port                   |
| `WHISPER_MODEL`  | `base`                                       | Whisper model for voice input |

### Using with OpenAI

```bash
LLM_HOST_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-your-key-here
```

### Using with Ollama (Local)

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.2:1b

# No API key needed
LLM_HOST_URL=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.2:1b
```

## Features

- **Real-time sync** - Parameter changes sync instantly between web and Grasshopper
- **Multi-client** - Multiple web clients can view and control the same model
- **Voice input** - Speech-to-text via Whisper (click microphone icon)
- **3D viewer** - Three.js mesh rendering with orbit controls
- **Dark/light theme** - Toggle in the UI

## Troubleshooting

### "Connection failed" in Grasshopper

- Ensure Flask Hub is running on the correct port
- Check firewall settings
- Verify `python-socketio` and `websocket-client` are installed

### Parameters not syncing

- Check that sliders are in groups named `RH_IN:<name>`
- Ensure `scan_params=True` on the GH component
- Check Flask Hub console for `[GH-SOCKET]` messages

### LLM not responding

- Verify LLM endpoint is accessible
- Check API key is set (for OpenAI)
- Check Flask Hub console for `[CHAT]` error messages

## License

MIT
