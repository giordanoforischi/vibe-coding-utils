#!/usr/bin/env python3
"""
Project File Concatenator
A CLI tool to concatenate project files or generate repo structure.
"""
import os
import sys
import subprocess
from pathlib import Path
from output import generate_output, OUTPUT_FILE, WRITE_TO_FILE, COPY_TO_CLIPBOARD

def find_project_root():
    """
    Find the project root - it's the parent directory of where this script is.
    """
    # Get the directory where app.py is located
    script_dir = Path(__file__).resolve().parent
    # Project root is the parent of the script directory
    project_root = script_dir.parent
    return str(project_root)

def clear_screen():
    """Clear the console screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def generate_repo_structure(project_root):
    """Generate repository structure using tree command."""
    output_file = os.path.join(os.getcwd(), '_repo_structure.txt')

    # Directories and files to exclude
    exclude_patterns = [
        'node_modules',
        '.git',
        'dist',
        'build',
        '.next',
        'coverage',
        '.turbo',
        'env',
        '__pycache__',
        '*.pyc',
        '.venv',
        'venv',
        'lib',
        'lib64',
        'include',
        'share',
        'bin',
        'pyvenv.cfg',
        'tool_cp'  # Exclude the tool itself
    ]

    exclude_arg = '|'.join(exclude_patterns)

    try:
        # Try to use tree command
        result = subprocess.run(
            ['tree', '-I', exclude_arg, '--dirsfirst', '-a'],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        return output_file, None
        
    except FileNotFoundError:
        return None, "tree command not found. Please install it: sudo apt install tree"
    except subprocess.CalledProcessError as e:
        return None, f"tree command failed: {e}"
    except Exception as e:
        return None, f"Error generating structure: {e}"

def get_file_list_input(project_root):
    """Get file paths from user input."""
    clear_screen()
    print("\n" + "="*80)
    print("📋 FILE LIST INPUT")
    print("="*80)
    print(f"📁 Project Root: {project_root}")
    print("\nPaste file paths (separated by newlines, commas, or semicolons)")
    print("Examples:")
    print("  admin/frontend/index.html")
    print("  front/src/App.tsx")
    print("  back/src/prisma/prisma.ts")
    print("\nCommands:")
    print("  [r] Refresh repository structure")
    print("  [q] Quit")
    print("\nPress Enter on empty line when done with file list")
    print("="*80)
    print()

    lines = []
    first_line = True

    while True:
        try:
            line = input()
            
            # Check for commands only on first line
            if first_line and line.strip():
                line_lower = line.strip().lower()
                
                if line_lower == 'q':
                    return 'QUIT'
                
                if line_lower == 'r':
                    return 'REFRESH'
                
                first_line = False
            
            if not line:
                break
            
            lines.append(line)
            first_line = False
            
        except EOFError:
            break
        except KeyboardInterrupt:
            return 'QUIT'

    if not lines:
        return []

    # Combine all lines and parse
    full_text = '\n'.join(lines)

    # Split by newlines, commas, and semicolons
    full_text = full_text.replace(',', '\n').replace(';', '\n')
    file_paths = [path.strip() for path in full_text.split('\n') if path.strip()]

    return file_paths

def main():
    """Main application loop."""
    # Find project root (parent directory of where this script is)
    project_root = find_project_root()

    print(f"\n🔍 Detected project root: {project_root}")
    print(f"📂 Tool location: {os.getcwd()}")

    # Verify project root
    if not os.path.exists(project_root):
        print(f"❌ Error: Project root doesn't exist!")
        return

    import time
    time.sleep(2)

    while True:
        try:
            # Get file list or command
            result = get_file_list_input(project_root)
            
            if result == 'QUIT':
                clear_screen()
                print("\n👋 Goodbye!\n")
                break
            
            elif result == 'REFRESH':
                # Generate repo structure
                clear_screen()
                print(f"\n📂 Generating repository structure...")
                output_path, error = generate_repo_structure(project_root)
                
                if output_path:
                    print(f"✅ Repository structure saved: {output_path}")
                else:
                    print(f"❌ Error: {error}")
                
                import time
                time.sleep(1.5)
                continue
            
            elif not result:
                # Empty input, just loop back
                continue
            
            else:
                # File paths provided - generate output
                file_paths = result
                
                clear_screen()
                print(f"\n📝 Generating output...")
                print(f"📁 Looking in: {project_root}")
                output_path, errors = generate_output(file_paths, project_root)
                
                # Show results
                successful = len(file_paths) - len(errors)
                print(f"📊 Total files: {len(file_paths)} | Successful: {successful}")
                
                if WRITE_TO_FILE and output_path:
                    print(f"✅ File: {output_path}")
                
                if COPY_TO_CLIPBOARD:
                    print(f"✅ Copied to clipboard (OSC 52)")
                
                # Show errors if any
                if errors:
                    print(f"\n⚠️  Errors ({len(errors)}):")
                    for error in errors[:10]:
                        print(f"   • {error}")
                    if len(errors) > 10:
                        print(f"   ... and {len(errors) - 10} more")
                
                if not output_path and not COPY_TO_CLIPBOARD:
                    print("❌ Failed to generate output")
                
                # Pause to show results
                import time
                time.sleep(2.5 if errors else 2)
                
        except KeyboardInterrupt:
            clear_screen()
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            import time
            time.sleep(2)

if __name__ == '__main__':
    main()