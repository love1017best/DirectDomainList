#!/usr/bin/env python3
import sys
import os

def convert_list_to_yaml(input_path, output_path):
    """
    Convert a .list file to .yaml format preserving comments and structure
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        yaml_lines = ['payload:']
        for line in lines:
            stripped = line.strip()
            # Preserve empty lines and comments
            if not stripped or stripped.startswith('#'):
                # Section headers (##) and regular comments
                yaml_lines.append(f'  # {stripped.lstrip("# ")}' if stripped.startswith('##') else f'  # {stripped[1:]}')
            else:
                # Convert rules to YAML list format
                yaml_lines.append(f'  - {stripped}')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(yaml_lines))
            
        print(f"Successfully converted {input_path} to {output_path}")
        return True
            
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_list_to_yaml.py <input.list> <output.yaml>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)
        
    if convert_list_to_yaml(input_file, output_file):
        sys.exit(0)
    else:
        sys.exit(1)
