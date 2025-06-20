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
- **Works everywhere** - Any folder, any project

## Setup

Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey), then:

```bash
git clone https://github.com/your-username/staffer.git
cd staffer
pip install -e .
export GEMINI_API_KEY=your_actual_api_key_here
```

## Examples

```bash
# Jump into any folder and ask AI about it
cd ~/my-python-project
staffer "what's in this folder?"
staffer "create a README for this project"
staffer "fix the bug in main.py"

# Chat with your folder interactively
cd ~/my-web-app
staffer --interactive
staffer> analyze this codebase
staffer> add tests for the main functions  
staffer> run the tests
staffer> exit

# Switch folders, AI adapts automatically
cd ~/my-data-project
staffer "what kind of project is this?"
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