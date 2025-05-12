import sys
from pylintsql.utils.arg_utils import parse_arguments
from pylintsql.utils.config_utils import get_sqlfluff_config, get_excluded_paths
from pylintsql import process_all_files_in_directory

def main():
    """
    Main CLI entry point with proper exit codes:
    0 - Success (no issues found)
    1 - Linting errors found
    2 - System error (invalid config, file access issues, etc.)
    """
    try:
        # Parse arguments using the existing parser logic
        args = parse_arguments()

        # Get the SQLFluff configuration
        config = get_sqlfluff_config(
            search_path=args.path,
            config_path=args.config,
            rules=args.rules,
            exclude_rules=args.exclude_rules,
        )

        # Get the matcher for excluded paths
        excluded_matcher = get_excluded_paths(args.path, args.config)

        # Process the directory
        issues_count, affected_files = process_all_files_in_directory(args.path, args.mode, config, excluded_matcher, args.verbose)
        
        # Return appropriate exit code
        if issues_count > 0:
            print(f"{issues_count} SQL linting issues found in {affected_files} files")
            return 1  # Issues found
        elif args.mode == "fix":
            print("SQL Fix executed successfully")
            return 0  # Success
        else:
            print("No SQL linting issues found")
            return 0
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2  # System error

if __name__ == "__main__":
    sys.exit(main())