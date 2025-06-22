# Staffer - AI in Folders

AI that works in whatever folder you're in. Just `cd` to any project and talk to AI about your code.

## Quick Start

```bash
# Install
pip install -e .

# Set your API key
export GEMINI_API_KEY=your_key_here

# Go to any folder and use AI
cd /your/project
staffer "what files are here?"
staffer "add error handling to main.py"

# Or chat with your folder
staffer --interactive
```

## How it works

- **AI knows your folder** - Understands what's in your current directory
- **Reads and writes files** - Can view and modify files in your folder
- **Runs code** - Executes Python scripts when needed
- **Remembers conversations** - Picks up where you left off
- **Adapts to folder changes** - Asks if you want to continue or start fresh when you switch projects
- **Enhanced terminal UI** - Rich prompts, command history, and syntax highlighting
- **Works everywhere** - Any folder, any project

## How UX works

- **Smart sessions** - Automatically saves and restores your conversations
- **Directory detection** - Notices when you switch folders and asks what to do
- **Session commands** - Use `/reset`, `/session`, `/help` in interactive mode  
- **Natural exit** - Just type `exit` or `quit` to save and leave
- **Arrow key history** - Use ↑↓ to navigate through previous commands
- **Persistent history** - Command history saved across sessions

## How UI works

- **Rich prompts** - Shows `staffer ~/project [5 msgs]>` with context
- **Visual feedback** - ✅ success messages, ⚠️ warnings, ❌ errors
- **Processing indicators** - Spinners show when AI is thinking
- **Syntax highlighting** - Code in responses gets proper colors
- **Function indicators** - See when AI calls functions like `🔧 Calling get_files_info...`
- **Auto-fallback** - Works in any terminal, enhanced when dependencies available

## ✨ Interactive Features

**Enhanced Terminal Experience:**

- 🎨 **Syntax highlighting** for code output
- 📝 **Rich context prompts** showing current directory and message count
- ⬆️ **Command history** with arrow key navigation (persistent across sessions)
- ⚡ **Visual feedback** with spinners and progress indicators
- 🎯 **Function call indicators** showing what AI is doing
- 🛡️ **Graceful fallback** to basic mode if dependencies are missing

**Terminal Dependencies (optional):**

```bash
pip install prompt-toolkit rich yaspin
```

If not installed, Staffer automatically falls back to basic terminal mode.

## Setup

Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey), then:

```bash
git clone https://github.com/your-username/staffer.git
cd staffer
pip install -e .

# Optional: Install enhanced terminal dependencies
pip install prompt-toolkit rich yaspin

export GEMINI_API_KEY=your_actual_api_key_here
```

## Examples

```bash
# Jump into any folder and ask AI about it
cd ~/my-python-project
staffer "what's in this folder?"
staffer "create a README for this project"
staffer "fix the bug in main.py"

# Chat with your folder interactively (enhanced terminal mode)
cd ~/my-web-app
staffer --interactive
# 🚀 Staffer - AI in Folders
# Enhanced terminal mode enabled
staffer ~/my-web-app [0 msgs]> analyze this codebase
# 🔧 Calling get_files_info...
# [AI analyzes your code with syntax highlighting]
staffer ~/my-web-app [4 msgs]> add tests for the main functions  
# ⚡ AI is thinking...
# [AI creates test files]
staffer ~/my-web-app [8 msgs]> exit
# ✅ Session saved
# ✅ Goodbye!

# Switch folders, AI adapts automatically
cd ~/my-data-project
staffer --interactive
# Staffer notices you changed folders
Directory changed from ~/my-web-app to ~/my-data-project
[N] Start new session  [K] Keep old session
Choice (N/k): n
staffer> what kind of project is this?
```

## Troubleshooting

**API Key not working?**
```bash
echo $GEMINI_API_KEY  # Should show your key
```

**Command not found?**
```bash
pip install -e .  # Reinstall
which staffer      # Check if in PATH
```

**Need help?**
```bash
staffer --help
```

That's it! AI that understands your folders and helps with your code.