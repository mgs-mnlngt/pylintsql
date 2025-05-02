from pathlib import Path
from pylintsql.utils.config_utils import get_sqlfluff_config, get_excluded_paths
from pylintsql.utils.sql_utils import modify_file_in_place
from pylintsql.utils.arg_utils import parse_arguments

def process_all_files_in_directory(directory_path, mode, config, excluded_matcher):
    """
    Process Python files in directory, skipping excluded paths.
    Returns:
        int: Total number of SQL issues found across all processed files.
    """
    root_path = Path(directory_path)
    total_issues = 0

    # Find all Python files in the directory tree
    for py_file in root_path.glob("**/*.py"):
        # Convert to relative path for matching against patterns
        rel_path = py_file.relative_to(root_path)
        
        # Skip if the file matches any exclusion pattern
        if excluded_matcher.match_file(str(rel_path)):
            continue
            
        # Accumulate issues from each file
        file_issues = modify_file_in_place(str(py_file), mode, config)
        total_issues += file_issues

    return total_issues

if __name__ == "__main__":
    # Parse CLI arguments
    args = parse_arguments()

    # Get the SQLFluff configuration
    config = get_sqlfluff_config(
        search_path=args.path,
        config_path=args.config
    )

    # Get excluded paths from pyproject.toml
    excluded_matcher = get_excluded_paths(args.path)

    # Process all files in the specified directory
    process_all_files_in_directory(args.path, args.mode, config, excluded_matcher)