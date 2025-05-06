import argparse

def parse_arguments():
    """
    Parse command-line arguments for the script.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Lint or fix SQL embedded in Python files."
    )
    
    parser.add_argument(
        "mode",
        choices=["lint", "fix"],
        default="lint",
        help="Mode of operation: 'lint' to check SQL or 'fix' to auto-correct SQL."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to a file or directory to process (default: current directory)."
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a specific configuration file."
    )
    parser.add_argument(
        "--rules",
        type=str,
        default=None,
        help="Comma-separated list of SQLFluff rules to include (merges with config)."
    )
    parser.add_argument(
        "--exclude-rules",
        type=str,
        default=None,
        help="Comma-separated list of SQLFluff rules to exclude (merges with config)."
    )
    
    return parser.parse_args()