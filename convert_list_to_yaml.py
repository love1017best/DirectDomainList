#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import List, Union

def convert_list_to_yaml(input_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Convert a .list file to .yaml format preserving comments and structure.
    
    Args:
        input_path: Path to the input .list file
        output_path: Path to the output .yaml file
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    try:
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}")
            return False

        yaml_lines: List[str] = ['payload:']
        
        with input_file.open('r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                
                # Preserve empty lines
                if not stripped:
                    yaml_lines.append('')
                    continue
                
                # Handle comments
                if stripped.startswith('#'):
                    # Normalize comment spacing
                    content = stripped.lstrip('#').strip()
                    # Indent comments to match list items
                    yaml_lines.append(f'  # {content}')
                else:
                    # Convert rules to YAML list format
                    yaml_lines.append(f'  - {stripped}')
        
        with output_file.open('w', encoding='utf-8') as f:
            f.write('\n'.join(yaml_lines) + '\n')
            
        print(f"Successfully converted {input_file} to {output_file}")
        return True
            
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert .list files to .yaml format for clash/mihomo.")
    parser.add_argument("input", help="Path to input .list file")
    parser.add_argument("output", help="Path to output .yaml file")
    
    args = parser.parse_args()
    
    success = convert_list_to_yaml(args.input, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
