# Project File Concatenator - Technical Documentation

## Purpose
A CLI tool for quickly reading and writing project files. Designed for developers who need to:
1. **READ mode**: Concatenate multiple files into a single output (for sharing with LLMs)
2. **WRITE mode**: Update file contents from clipboard/paste
3. Generate repository structure documentation

## Architecture

### File Structure
tool_cp/ # Tool directory (lives inside project root) ├── app.py # Main application loop, mode switching ├── write_mode.py # WRITE mode implementation ├── output.py # File concatenation and clipboard copying ├── _output.txt # Generated output (READ mode) └── _repo_structure.txt # Generated tree structure


### Project Root Detection
- Tool lives in `project_root/tool_cp/`
- Project root = `Path(__file__).parent.parent`
- All file paths are relative to project root

## Key Business Rules

### READ Mode (Green UI)
**Purpose**: Concatenate multiple files for context sharing

**Input Format**:
admin/frontend/index.html back/src/schema.prisma front/components/App.tsx


**Behavior**:
- Paste file paths (newlines, commas, or semicolons as separators)
- Press Enter ONCE after pasting
- Generates `_output.txt` with file headers and contents
- Also copies to clipboard via OSC 52 (works over SSH)

**Output Format**:
================================================================================ FILE: path/to/file.ext
================================================================================ FILE: next/file.ext
...


### WRITE Mode (Red UI)
**Purpose**: Update file contents quickly from clipboard/paste

**Input Format**:
// path/to/file.ext

Behavior:

First line MUST be comment with file path: // path/to/file.ext
Removes comment line and leading blank lines
Overwrites file with new content
Preserves empty lines within content
Two Paste Methods:

Clipboard mode (default on Mac/Windows):
Copy content (⌘C)
Press Enter
Reads from clipboard using pbpaste/xclip/wl-paste
Works instantly, no buffering issues
Terminal mode (default on Linux):
Paste into terminal
Press Enter TWICE to submit
Why twice? Code can contain empty lines - first empty might be IN content, second empty = done
Mode Switching:

Press [t] → Terminal mode (persists for session)
Press [p] → Clipboard mode (persists for session)
Auto-detects OS on startup
Repository Structure Generation
Command: [x] Refresh repo structure

Behavior:

Runs tree command with exclusions
Saves to _repo_structure.txt in tool_cp directory
Copies to clipboard automatically
Exclusions: node_modules, .git, dist, build, __pycache__, venv, tool_cp, etc.

Copy Context
Command: [c] Copy context

Behavior:

Reads Claude.md from project root
Generates repo structure
Concatenates both with headers
Copies combined content to clipboard
Format:

================================================================================
CLAUDE.MD
================================================================================

<Claude.md contents>

================================================================================
REPOSITORY STRUCTURE
================================================================================

<tree output>
Technical Implementation
Input Buffering Challenges
Problem: Terminal stdin buffering caused issues with paste detection

Solution:

Use termios.tcflush(sys.stdin, termios.TCIFLUSH) before AND after reading
Flushes input buffer to prevent leftover characters from being read as new commands
Why needed:

When you paste, ALL lines are buffered in stdin immediately
Without flushing, leftovers from one operation leak into the next
Critical for preventing infinite loops
Clipboard vs Terminal Paste
Why two methods exist:

Clipboard reading (pbpaste) doesn't work over SSH (reads remote clipboard, not local)
Terminal paste works everywhere but has buffering complexities
Auto-detect OS, but allow manual switching
Why WRITE Mode Needs 2 Enters
Problem: Can't use 1 Enter because code content may contain empty lines

Example:

typescript
export const schema = z.object({
name: z.string(),
})
                        ← This empty line would trigger "done" with 1 Enter
export const other = z.object({
Solution: Require 2 consecutive empty lines to signal "done"

OSC 52 Clipboard
What: ANSI escape sequence that copies to clipboard even over SSH

Format: \033]52;c;{base64_content}\007

Support: Modern terminals (iTerm2, tmux, VSCode terminal)

Limitations: ~100KB max size in most terminals

Configuration Points
In write_mode.py:
Paste mode auto-detection logic
Write history size (currently 3)
In output.py:
python
WRITE_TO_FILE = True      # Toggle file output
COPY_TO_CLIPBOARD = True  # Toggle clipboard copy
OUTPUT_FILE = '_output.txt'
In app.py:
Repo structure exclusions
Tree command flags
File Discovery (Historical - Not Used in Current Version)
Previous versions had full file discovery system - removed for simplicity

Original approach:

Used git ls-files + git ls-files --others --exclude-standard
Tracked + untracked files while respecting .gitignore
Sorted by mtime (newest first)
Organized by folders: front, back, grpc_server, other
Why removed: User workflow changed to direct file path input instead of selection UI

Error Handling
Missing Files
Shows error in output: [ERROR: File not found: path]
Continues processing other files
Shows error summary after completion
Write Failures
Shows error message
File remains unchanged
Returns to WRITE mode for retry
Mode Switching
[r] → Switch to READ mode
[w] → Switch to WRITE mode
Modes persist - don't reset after operations
Screen clearing between modes for clean UI
Key Gotchas
Always flush stdin buffer before reading input
WRITE mode requires 2 Enters for terminal paste (not a bug!)
Clipboard mode won't work over SSH (use terminal mode instead)
File paths are relative to project root, not tool directory
First line in WRITE must be // filepath - no exceptions
Future Considerations
Clipboard mode over SSH would require clipboard forwarding setup
Could add file watching to auto-detect changes
Could add undo functionality for WRITE mode
Could add batch write mode (multiple files at once)