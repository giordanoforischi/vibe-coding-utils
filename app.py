#!/usr/bin/env python3
"""
Project File Concatenator
A CLI tool to concatenate project files or generate repo structure.
"""
import os
import sys
import subprocess
import termios
import base64
from pathlib import Path
from output import generate_output, OUTPUT_FILE, WRITE_TO_FILE, COPY_TO_CLIPBOARD
from write_mode import write_file_from_paste

def find_project_root():
    """Find the project root - parent directory of where this script is."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    return str(project_root)

def clear_screen():
    """Clear the console screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def copy_to_clipboard_osc52(content):
    """Copy content to clipboard using OSC 52."""
    try:
        b64_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        max_size = 100000
        if len(b64_content) > max_size:
            b64_content = b64_content[:max_size]
            print(f"⚠️  Clipboard content truncated (too large)")
        
        osc52_sequence = f"\033]52;c;{b64_content}\007"
        sys.stdout.write(osc52_sequence)
        sys.stdout.flush()
        
    except Exception as e:
        print(f"⚠️  Clipboard copy failed: {e}")

def generate_repo_structure(project_root):
    """Generate repository structure using tree command."""
    output_file = os.path.join(os.getcwd(), '_repo_structure.txt')

    exclude_patterns = [
        'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
        '.turbo', 'env', '__pycache__', '*.pyc', '.venv', 'venv',
        'lib', 'lib64', 'include', 'share', 'bin', 'pyvenv.cfg', 'tool_cp'
    ]

    exclude_arg = '|'.join(exclude_patterns)

    try:
        result = subprocess.run(
            ['tree', '-I', exclude_arg, '--dirsfirst', '-a'],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        # Also copy to clipboard
        copy_to_clipboard_osc52(result.stdout)
        
        return output_file, None
        
    except FileNotFoundError:
        return None, "tree command not found. Install: sudo apt install tree"
    except subprocess.CalledProcessError as e:
        return None, f"tree command failed: {e}"
    except Exception as e:
        return None, f"Error: {e}"

def copy_context(project_root):
    """Copy context (Claude.md + repo structure) to clipboard."""
    clear_screen()
    print("\n📋 Generating context...")

    # Read Claude.md
    claude_md_path = os.path.join(project_root, 'Claude.md')
    claude_content = ""

    if os.path.exists(claude_md_path):
        try:
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                claude_content = f.read()
            print(f"✅ Read Claude.md ({len(claude_content)} bytes)")
        except Exception as e:
            print(f"⚠️  Error reading Claude.md: {e}")
    else:
        print(f"⚠️  Claude.md not found at project root")

    # Generate repo structure
    exclude_patterns = [
        'node_modules', '.git', 'dist', 'build', '.next', 'coverage',
        '.turbo', 'env', '__pycache__', '*.pyc', '.venv', 'venv',
        'lib', 'lib64', 'include', 'share', 'bin', 'pyvenv.cfg', 'tool_cp'
    ]

    exclude_arg = '|'.join(exclude_patterns)
    repo_structure = ""

    try:
        result = subprocess.run(
            ['tree', '-I', exclude_arg, '--dirsfirst', '-a'],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        repo_structure = result.stdout
        print(f"✅ Generated repo structure ({len(repo_structure)} bytes)")
    except Exception as e:
        print(f"⚠️  Error generating repo structure: {e}")

    # Concatenate
    combined = ""
    if claude_content:
        combined += "="*80 + "\n"
        combined += "CLAUDE.MD\n"
        combined += "="*80 + "\n\n"
        combined += claude_content
        combined += "\n\n"

    if repo_structure:
        combined += "="*80 + "\n"
        combined += "REPOSITORY STRUCTURE\n"
        combined += "="*80 + "\n\n"
        combined += repo_structure

    if not combined:
        print("❌ No content to copy")
        import time
        time.sleep(1.5)
        return

    # Copy to clipboard
    copy_to_clipboard_osc52(combined)
    print(f"✅ Copied {len(combined)} bytes to clipboard")

    import time
    time.sleep(1.5)

def get_file_list_input(project_root):
    """Get file paths from user input (READ mode)."""
    clear_screen()

    GREEN = '\033[92m'
    RESET = '\033[0m'

    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}📋 FILE LIST INPUT (READ MODE){RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    print(f"📁 Project Root: {project_root}")
    print("\nPaste file paths (one per line)")
    print(f"\n{GREEN}⚠️  Press Enter ONCE after pasting to submit{RESET}")
    print("\nCommands: [w] Write mode | [c] Copy context | [x] Refresh repo structure | [q] Quit")
    print(f"{GREEN}{'='*80}{RESET}")
    print()

    # FLUSH buffer
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

    lines = []
    first_line = True

    while True:
        try:
            line = input()
            
            # Check commands on first line
            if first_line and line.strip():
                cmd = line.strip().lower()
                if cmd == 'q':
                    return 'QUIT'
                elif cmd == 'x':
                    return 'REFRESH'
                elif cmd == 'w':
                    return 'WRITE_MODE'
                elif cmd == 'c':
                    return 'COPY_CONTEXT'
                first_line = False
            
            # Empty line after content = done
            if not line:
                if len(lines) > 0:
                    break
            else:
                first_line = False
            
            lines.append(line)
            
        except (EOFError, KeyboardInterrupt):
            return 'QUIT'

    if not lines:
        return []

    # Parse file paths
    full_text = '\n'.join(lines)
    full_text = full_text.replace(',', '\n').replace(';', '\n')
    file_paths = [path.strip() for path in full_text.split('\n') if path.strip()]

    # FLUSH buffer after processing
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

    return file_paths

def main():
    """Main application loop."""
    project_root = find_project_root()

    print(f"\n🔍 Project root: {project_root}")

    if not os.path.exists(project_root):
        print(f"❌ Error: Project root doesn't exist!")
        return

    import time
    time.sleep(1)

    current_mode = 'READ'

    while True:
        try:
            if current_mode == 'READ':
                result = get_file_list_input(project_root)
                
                if result == 'QUIT':
                    clear_screen()
                    print("\n👋 Goodbye!\n")
                    break
                
                elif result == 'REFRESH':
                    clear_screen()
                    print(f"\n📂 Refreshing repository structure...")
                    output_path, error = generate_repo_structure(project_root)
                    
                    if output_path:
                        print(f"✅ Saved: {output_path}")
                        print(f"✅ Copied to clipboard")
                    else:
                        print(f"❌ Error: {error}")
                    
                    time.sleep(1.5)
                    continue
                
                elif result == 'COPY_CONTEXT':
                    copy_context(project_root)
                    continue
                
                elif result == 'WRITE_MODE':
                    current_mode = 'WRITE'
                    continue
                
                elif not result:
                    continue
                
                else:
                    file_paths = result
                    
                    clear_screen()
                    print(f"\n📝 Generating output...")
                    output_path, errors = generate_output(file_paths, project_root)
                    
                    successful = len(file_paths) - len(errors)
                    print(f"📊 Total: {len(file_paths)} | Success: {successful}")
                    
                    if WRITE_TO_FILE and output_path:
                        print(f"✅ File: {output_path}")
                    
                    if COPY_TO_CLIPBOARD:
                        print(f"✅ Copied to clipboard")
                    
                    if errors:
                        print(f"\n⚠️  Errors ({len(errors)}):")
                        for error in errors[:10]:
                            print(f"   • {error}")
                        if len(errors) > 10:
                            print(f"   ... and {len(errors) - 10} more")
                    
                    time.sleep(2.5 if errors else 2)
            
            elif current_mode == 'WRITE':
                result = write_file_from_paste(project_root)
                
                if result == False:
                    clear_screen()
                    print("\n👋 Goodbye!\n")
                    break
                elif result == 'REFRESH':
                    clear_screen()
                    print(f"\n📂 Refreshing repository structure...")
                    output_path, error = generate_repo_structure(project_root)
                    
                    if output_path:
                        print(f"✅ Saved: {output_path}")
                        print(f"✅ Copied to clipboard")
                    else:
                        print(f"❌ Error: {error}")
                    
                    time.sleep(1.5)
                elif result == 'COPY_CONTEXT':
                    copy_context(project_root)
                elif result == 'READ_MODE':
                    current_mode = 'READ'
                # If True, loop back to write mode
                
        except KeyboardInterrupt:
            clear_screen()
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(2)

if __name__ == '__main__':
    main()