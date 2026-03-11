"""
Write mode - paste content to overwrite files
"""
import os
import sys
import subprocess
import termios
import platform

# Auto-detect paste mode based on OS
def get_default_paste_mode():
    """Determine default paste mode based on OS."""
    system = platform.system().lower()
    if system == 'linux':
        return 'terminal'
    else:  # darwin (Mac) or windows
        return 'clipboard'

# Global paste mode
PASTE_MODE = get_default_paste_mode()

# Track last 3 writes
WRITE_HISTORY = []

def write_file_from_paste(project_root):
    """
    Main write mode - paste content with file path comment.
    """
    global PASTE_MODE

    os.system('clear' if os.name != 'nt' else 'cls')

    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RESET = '\033[0m'

    # Show header with current mode
    print(f"\n{RED}{'='*80}{RESET}")
    print(f"{RED}✏️  WRITE MODE{RESET} - Current: {YELLOW}{PASTE_MODE.upper()}{RESET}")
    print(f"{RED}{'='*80}{RESET}")
    print(f"📁 Project Root: {project_root}")

    # Show write history
    if WRITE_HISTORY:
        print(f"\n{YELLOW}📝 Last {len(WRITE_HISTORY)} writes:{RESET}")
        for entry in WRITE_HISTORY:
            status_icon = "✅" if entry['success'] else "❌"
            lines_info = f"{entry['lines']} lines" if entry['success'] else entry['error']
            print(f"  {status_icon} {entry['file'][:50]} - {lines_info}")

    print(f"\n{RED}Paste content (first line: // path/to/file){RESET}")
    if PASTE_MODE == 'clipboard':
        print(f"{RED}⌘C to copy, then press Enter to submit{RESET}")
    else:
        print(f"{RED}Paste, then press Enter TWICE to submit{RESET}")

    print(f"\nCommands: [t] Terminal mode | [p] Clipboard mode | [c] Copy context | [r] Read mode | [x] Refresh repo structure | [q] Quit")
    print(f"{RED}{'='*80}{RESET}")
    print()

    # FLUSH buffer
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

    # Check for mode switches or commands first
    if PASTE_MODE == 'clipboard':
        # In clipboard mode, wait for Enter or command
        try:
            cmd = input("Press Enter to read clipboard (or command): ").strip().lower()
            
            if cmd == 'q':
                return False
            elif cmd == 'x':
                return 'REFRESH'
            elif cmd == 'r':
                return 'READ_MODE'
            elif cmd == 'c':
                return 'COPY_CONTEXT'
            elif cmd == 't':
                PASTE_MODE = 'terminal'
                print(f"{YELLOW}✓ Switched to TERMINAL mode{RESET}")
                import time
                time.sleep(1)
                return True
            elif cmd == 'p':
                # Already in clipboard mode
                pass
            
            # Read from clipboard
            return _clipboard_paste(project_root)
            
        except (EOFError, KeyboardInterrupt):
            return False

    else:  # terminal mode
        return _terminal_paste(project_root)

def _clipboard_paste(project_root):
    """Read content directly from clipboard."""
    RED = '\033[91m'
    RESET = '\033[0m'

    os.system('clear' if os.name != 'nt' else 'cls')
    print(f"\n{RED}📋 Reading from clipboard...{RESET}")

    try:
        # Try Mac first
        result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            text=True,
            check=True
        )
        content = result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Try Linux (X11)
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                check=True
            )
            content = result.stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Try Linux (Wayland)
            try:
                result = subprocess.run(
                    ['wl-paste'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                content = result.stdout
            except (FileNotFoundError, subprocess.CalledProcessError):
                print("❌ No clipboard tool found (pbpaste/xclip/wl-paste)")
                import time
                time.sleep(2)
                return True

    if not content.strip():
        print("❌ Clipboard is empty")
        import time
        time.sleep(1)
        return True

    # Parse and write
    lines = content.split('\n')

    print(f"📝 Got {len(lines)} lines from clipboard")

    success, msg = _parse_and_write(lines, project_root)
    print(f"{'✅' if success else '❌'} {msg}")

    # Add to history
    _add_to_history(lines, success, msg)

    import time
    time.sleep(2)
    return True

def _terminal_paste(project_root):
    """Traditional terminal paste with Enter twice."""
    global PASTE_MODE

    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

    os.system('clear' if os.name != 'nt' else 'cls')

    print(f"\n{RED}{'='*80}{RESET}")
    print(f"{RED}✏️  TERMINAL PASTE{RESET}")
    print(f"{RED}{'='*80}{RESET}")
    print(f"📁 Project Root: {project_root}")
    print("\nPaste content (first line: // path/to/file)")
    print(f"\n{RED}⚠️  Press Enter THRICE after pasting to submit{RESET}")
    print("\nCommands: [p] Switch to clipboard mode | [c] Copy context | [r] Read mode | [x] Refresh repo structure | [q] Quit")
    print(f"{RED}{'='*80}{RESET}")
    print()

    # FLUSH buffer before reading
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

    lines = []
    first_line = True
    empty_count = 0

    while True:
        try:
            line = input()
            
            # Check for commands only on very first line
            if first_line and line.strip():
                cmd = line.strip().lower()
                if cmd == 'q':
                    return False
                elif cmd == 'x':
                    return 'REFRESH'
                elif cmd == 'r':
                    return 'READ_MODE'
                elif cmd == 'c':
                    return 'COPY_CONTEXT'
                elif cmd == 'p':
                    PASTE_MODE = 'clipboard'
                    print(f"{YELLOW}✓ Switched to CLIPBOARD mode{RESET}")
                    import time
                    time.sleep(1)
                    return True
                first_line = False
            
            # Count consecutive empty lines
            if not line:
                empty_count += 1
                if empty_count >= 2 and len(lines) > 0:
                    # Remove the trailing empty lines
                    while lines and not lines[-1]:
                        lines.pop()
                    break
            else:
                empty_count = 0
                first_line = False
            
            lines.append(line)
            
        except (EOFError, KeyboardInterrupt):
            return False

    if not lines:
        return True

    # Write file
    os.system('clear' if os.name != 'nt' else 'cls')
    print(f"\n{RED}✏️  Writing...{RESET}")
    print(f"📝 Got {len(lines)} lines")

    success, msg = _parse_and_write(lines, project_root)
    print(f"{'✅' if success else '❌'} {msg}")

    # Add to history
    _add_to_history(lines, success, msg)

    # FLUSH buffer after processing
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

    import time
    time.sleep(2)
    return True

def _parse_and_write(lines, project_root):
    """Parse content and write to file."""
    if not lines:
        return False, "No content"

    first_line = lines[0].strip()

    if not first_line.startswith('//'):
        return False, f"First line must start with '//'"

    file_path = first_line[2:].strip()

    if not file_path:
        return False, "No file path after '//'"

    # Remove comment line and leading blanks
    content_lines = lines[1:]
    while content_lines and not content_lines[0].strip():
        content_lines.pop(0)

    # Join - preserve all content including empty lines
    content = '\n'.join(content_lines)

    full_path = os.path.join(project_root, file_path)

    if not os.path.exists(full_path):
        return False, f"File not found: {file_path}"

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, f"Wrote {len(content)} bytes to: {file_path}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def _add_to_history(lines, success, message):
    """Add write operation to history."""
    global WRITE_HISTORY

    # Extract file path from first line
    if lines and lines[0].strip().startswith('//'):
        file_path = lines[0].strip()[2:].strip()
    else:
        file_path = "unknown"

    entry = {
        'file': file_path,
        'lines': len(lines) - 1,  # Exclude comment line
        'success': success,
        'error': message if not success else None
    }

    WRITE_HISTORY.insert(0, entry)  # Add to beginning
    WRITE_HISTORY = WRITE_HISTORY[:3]  # Keep only last 3