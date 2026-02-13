#!/usr/bin/env python3
"""
Domain list preprocessor: deduplicate and validate .list files while preserving group structure.
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple

# Supported rule types in Clash/Mihomo
VALID_RULE_TYPES = {
    'DOMAIN',
    'DOMAIN-SUFFIX',
    'DOMAIN-KEYWORD',
    'GEOIP',
    'IP-CIDR',
    'IP-CIDR6',
    'SRC-IP-CIDR',
    'PROCESS-NAME',
    'PROCESS-PATH',
    'RULE-SET',
    'USER-AGENT',
    'URL-REGEX',
    'AND',
    'OR',
    'NOT',
    'IN',
}


class Rule(NamedTuple):
    """Represents a single rule with its metadata."""
    raw: str
    type: str
    value: str
    is_comment: bool
    is_empty: bool


def parse_rule(line: str) -> Rule:
    """Parse a single line into a Rule object."""
    stripped = line.strip()

    # Empty line
    if not stripped:
        return Rule(raw=line, type='', value='', is_comment=False, is_empty=True)

    # Comment line
    if stripped.startswith('#'):
        return Rule(raw=line, type='', value='', is_comment=True, is_empty=False)

    # Rule line: TYPE,value
    if ',' in stripped:
        parts = stripped.split(',', 1)
        rule_type = parts[0].strip().upper()
        rule_value = parts[1].strip() if len(parts) > 1 else ''
        return Rule(raw=line, type=rule_type, value=rule_value, is_comment=False, is_empty=False)

    # Unknown format
    return Rule(raw=line, type='UNKNOWN', value=stripped, is_comment=False, is_empty=False)


def validate_rule(rule: Rule, valid_types: set) -> Tuple[bool, str]:
    """Validate a single rule. Returns (is_valid, error_message)."""
    if rule.is_comment or rule.is_empty:
        return True, ''

    if rule.type == 'UNKNOWN':
        return False, f"Unknown rule format: {rule.raw.strip()}"

    if rule.type not in valid_types:
        return False, f"Invalid rule type '{rule.type}': {rule.raw.strip()}"

    if not rule.value:
        return False, f"Missing value for rule type '{rule.type}': {rule.raw.strip()}"

    return True, ''


def load_rules(file_path: Path) -> Tuple[List[Rule], List[str]]:
    """Load rules from a .list file. Returns (rules, parse_errors)."""
    rules = []
    errors = []

    with file_path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            rule = parse_rule(line)
            rules.append(rule)

            # Check for parse issues
            if rule.type == 'UNKNOWN':
                errors.append(f"Line {line_num}: Unknown format - {line.strip()}")

    return rules, errors


def deduplicate_rules(rules: List[Rule]) -> Tuple[List[Rule], Dict[str, int]]:
    """
    Remove duplicate rules within each group (preserving group structure).
    Returns deduplicated rules and a dict of removed duplicates count by value.
    """
    duplicate_counts: Dict[str, int] = defaultdict(int)
    result: List[Rule] = []
    seen_in_group: set = set()  # Reset on each comment/empty line

    for rule in rules:
        if rule.is_comment or rule.is_empty:
            # Reset seen set for new group
            seen_in_group = set()
            result.append(rule)
        else:
            key = f"{rule.type},{rule.value}"
            if key not in seen_in_group:
                seen_in_group.add(key)
                result.append(rule)
            else:
                duplicate_counts[key] += 1

    return result, dict(duplicate_counts)


def validate_all_rules(rules: List[Rule]) -> List[str]:
    """Validate all rules and return list of errors."""
    errors = []
    for rule in rules:
        is_valid, error_msg = validate_rule(rule, VALID_RULE_TYPES)
        if not is_valid:
            errors.append(error_msg)
    return errors


def get_statistics(rules: List[Rule]) -> Dict[str, int]:
    """Calculate statistics for the rules."""
    stats = {
        'total_lines': len(rules),
        'empty_lines': 0,
        'comments': 0,
        'rules': 0,
        'by_type': defaultdict(int),
    }

    for rule in rules:
        if rule.is_empty:
            stats['empty_lines'] += 1
        elif rule.is_comment:
            stats['comments'] += 1
        else:
            stats['rules'] += 1
            stats['by_type'][rule.type] += 1

    stats['by_type'] = dict(stats['by_type'])
    return stats


def print_statistics(stats: Dict[str, int], title: str = "Statistics"):
    """Print formatted statistics."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    print(f"  Total lines:      {stats['total_lines']}")
    print(f"  Empty lines:      {stats['empty_lines']}")
    print(f"  Comments:         {stats['comments']}")
    print(f"  Rules:            {stats['rules']}")
    print(f"\n  Rules by type:")
    for rule_type, count in sorted(stats['by_type'].items()):
        print(f"    {rule_type:<20} {count:>5}")
    print(f"{'='*50}\n")


def process_file(
    input_path: Path,
    output_path: Path = None,
    deduplicate: bool = False,
    validate: bool = False,
    verbose: bool = False
) -> bool:
    """
    Process a .list file with optional operations.

    Args:
        input_path: Path to input .list file
        output_path: Path to output file (if None, overwrites input)
        deduplicate: Whether to remove duplicates (within groups)
        validate: Whether to validate rules
        verbose: Whether to print detailed output

    Returns:
        bool: True if successful, False otherwise
    """
    input_file = Path(input_path)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return False

    # Determine output file
    output_file = Path(output_path) if output_path else input_file

    if output_file == input_file and deduplicate:
        # Create backup
        backup_path = input_file.with_suffix('.list.bak')
        import shutil
        shutil.copy2(input_file, backup_path)
        if verbose:
            print(f"Backup created: {backup_path}")

    try:
        # Load rules
        if verbose:
            print(f"Loading rules from {input_file}...")
        rules, parse_errors = load_rules(input_file)

        if parse_errors:
            print(f"Warning: Found {len(parse_errors)} parse issues:")
            for error in parse_errors:
                print(f"  - {error}")

        stats_before = get_statistics(rules)
        if verbose:
            print_statistics(stats_before, "Before Processing")

        # Process rules
        if deduplicate:
            if verbose:
                print("Deduplicating rules (within groups)...")
            rules, duplicates = deduplicate_rules(rules)
            if duplicates:
                total_dups = sum(duplicates.values())
                print(f"Removed {total_dups} duplicate(s):")
                for dup, count in sorted(duplicates.items())[:10]:
                    print(f"  - {dup}: {count} duplicate(s)")
                if len(duplicates) > 10:
                    print(f"  ... and {len(duplicates) - 10} more")
            else:
                print("No duplicates found.")

        stats_after = get_statistics(rules)
        if verbose:
            print_statistics(stats_after, "After Processing")

        # Validate
        if validate:
            if verbose:
                print("Validating rules...")
            validation_errors = validate_all_rules(rules)
            if validation_errors:
                print(f"Error: Found {len(validation_errors)} invalid rules:")
                for error in validation_errors:
                    print(f"  - {error}")
                return False
            else:
                print(f"All {stats_after['rules']} rules are valid!")

        # Write output
        if verbose:
            print(f"Writing to {output_file}...")
        with output_file.open('w', encoding='utf-8') as f:
            for rule in rules:
                f.write(rule.raw)

        print(f"Successfully processed {input_file} -> {output_file}")
        return True

    except Exception as e:
        print(f"Error during processing: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess .list files: deduplicate and validate while preserving group structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.list                     # Show statistics
  %(prog)s input.list -o output.list      # Process and save to new file
  %(prog)s input.list --dedup             # Remove duplicates within groups
  %(prog)s input.list --validate          # Validate rules
  %(prog)s input.list -d -v               # Deduplicate with verbose output
  %(prog)s input.list -d -v --inplace      # Deduplicate in-place (with backup)
        """
    )
    parser.add_argument("input", help="Path to input .list file")
    parser.add_argument("-o", "--output", help="Path to output file (default: overwrite input)")
    parser.add_argument("-d", "--dedup", action="store_true", help="Remove duplicate rules within groups")
    parser.add_argument("-v", "--validate", action="store_true", help="Validate rule format")
    parser.add_argument("--inplace", action="store_true", help="Allow in-place modification (creates backup)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")

    args = parser.parse_args()

    # Determine output path
    output_path = Path(args.output) if args.output else None

    # Check if in-place modification
    if output_path is None and args.dedup and not args.inplace:
        print("Warning: In-place deduplication will overwrite the input file.")
        print("Use --inplace flag to confirm, or -o to specify output file.")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)

    success = process_file(
        input_path=args.input,
        output_path=output_path,
        deduplicate=args.dedup,
        validate=args.validate,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
