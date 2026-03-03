"""
Output generation.
"""
import os
import base64
import sys

# Configuration - Easy to toggle output strategies
WRITE_TO_FILE = True      # Write to _output.txt file
COPY_TO_CLIPBOARD = True  # Copy to clipboard using OSC 52

OUTPUT_FILE = '_output.txt'

def generate_output(selected_files, project_root='.'):
    """
    Concatenate selected files into output file and/or clipboard.
    Returns tuple: (output_path, errors_list)
    """
    if not selected_files:
        return None, []

    # Generate the concatenated content and track errors
    content, errors = _build_content(selected_files, project_root)

    # Write to file (in tool_cp directory)
    output_path = None
    if WRITE_TO_FILE:
        output_path = os.path.join(os.getcwd(), OUTPUT_FILE)
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                outfile.write(content)
        except Exception as e:
            errors.append(f"Failed to write output file: {e}")
            output_path = None

    # Copy to clipboard using OSC 52
    if COPY_TO_CLIPBOARD:
        _copy_to_clipboard_osc52(content)

    return output_path, errors

def _build_content(selected_files, project_root):
    """Build the concatenated content string. Returns (content, errors)."""
    lines = []
    errors = []
    successful = 0

    for filepath in selected_files:
        full_path = os.path.join(project_root, filepath)
        
        # Write header
        lines.append("="*80)
        lines.append(f"FILE: {filepath}")
        lines.append("="*80)
        lines.append("")
        
        # Write content
        try:
            if not os.path.exists(full_path):
                error_msg = f"File not found: {filepath}"
                lines.append(f"[ERROR: {error_msg}]")
                lines.append("")
                errors.append(error_msg)
                continue
                
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                content = infile.read()
                lines.append(content)
                successful += 1
                
                # Ensure newline at end
                if content and not content.endswith('\n'):
                    lines.append("")
                    
        except Exception as e:
            error_msg = f"{filepath}: {str(e)}"
            lines.append(f"[ERROR: {error_msg}]")
            lines.append("")
            errors.append(error_msg)
        
        lines.append("")

    return '\n'.join(lines), errors

def _copy_to_clipboard_osc52(content):
    """
    Copy content to clipboard using OSC 52 escape sequence.
    Works over SSH with compatible terminals (iTerm2, tmux, etc.)
    """
    try:
        # Encode content to base64
        b64_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        # Check if content is too large (some terminals have limits)
        # Most terminals support up to ~100KB, some up to several MB
        max_size = 100000  # 100KB base64 encoded
        if len(b64_content) > max_size:
            # Truncate and add warning
            b64_content = b64_content[:max_size]
            print(f"⚠️  Clipboard content truncated (too large for OSC 52)")
        
        # Send OSC 52 escape sequence
        # Format: \033]52;c;{base64_content}\007
        osc52_sequence = f"\033]52;c;{b64_content}\007"
        
        # Write directly to terminal
        sys.stdout.write(osc52_sequence)
        sys.stdout.flush()
        
    except Exception as e:
        print(f"⚠️  Clipboard copy failed: {e}")