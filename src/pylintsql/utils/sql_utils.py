import sqlfluff
import re
from pathlib import Path
import libcst as cst
from typing import Union


def normalize_sql_indentation(sql_string):
    """
    Removes common leading whitespace from lines 2 onwards,
    preserving relative indentation within the SQL.
    Keeps the first line as is.
    """
    lines = sql_string.splitlines()
    if len(lines) <= 1:
        return sql_string

    # Find minimum indent from lines 2 onwards
    min_indent = float("inf")
    for line in lines[1:]:
        if line.strip():  # Only consider non-empty lines
            leading_space = len(line) - len(line.lstrip(" "))
            min_indent = min(min_indent, leading_space)

    # If no indented lines found or min_indent is 0, return original
    if min_indent == float("inf") or min_indent == 0:
        return "\n".join(lines)

    # Rebuild the string, removing the common indent
    normalized_lines = [lines[0]]  # Keep first line
    for line in lines[1:]:
        # Remove the common prefix, preserve empty lines
        if line.strip():
            normalized_lines.append(line[min_indent:])
        else:
            normalized_lines.append("")

    return "\n".join(normalized_lines)


def lint_or_fix_sql(sql, mode, config, file_path=None):
    """
    Lint or fix a SQL string using the provided FluffConfig object.

    Args:
        sql (str): The SQL string to lint or fix.
        mode (str): Either 'lint' or 'fix'.
        config (FluffConfig): The SQLFluff configuration object.
        file_path (str): The path to the file being processed (for error reporting).

    Returns:
        tuple[str, int]: A tuple containing:
                         - The fixed SQL string (if mode is 'fix') or the original SQL string (if mode is 'lint').
                         - The number of linting issues found (0 if mode is 'fix' or no issues).
    """
    issues_count = 0
    try:
        if mode == "fix":
            # Use the FluffConfig object for fixing
            fixed_sql = sqlfluff.fix(sql, config=config)
            return fixed_sql, 0  # Return 0 issues for fix mode
        else:
            # Use the FluffConfig object for linting
            lint_result = sqlfluff.lint(sql, config=config)
            if lint_result:
                issues_count = len(lint_result)  # Count the issues
                print("Error: ", Path(file_path))
                for error in lint_result:
                    print(f"  - Code: {error['code']}")
                    print(f"    Description: {error['description']}")
                    print(
                        f"    Line: {error['start_line_no']}, Position: {error['start_line_pos']}"
                    )
                    print("-" * 40)
            # Return original SQL and the count of issues found
            return sql, issues_count
    except Exception as e:
        print(f"Error processing SQL in {file_path}: {sql}\nError: {e}")
        # Return original SQL and 0 issues in case of error during lint/fix
        return sql, 0


class SQLStringTransformer(cst.CSTTransformer):
    """Transform SQL strings marked with --sql prefix."""

    def __init__(self, mode, config, file_path, sql_pattern):
        self.mode = mode
        self.config = config
        self.file_path = file_path
        self.sql_pattern = sql_pattern
        self.total_issues_in_file = 0  # Initialize issue counter for the file

    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> Union[cst.SimpleString, cst.FormattedString]:
        """
        Handle simple strings (e.g., triple-quoted strings) that may contain SQL
        """
        try:
            text = updated_node.evaluated_value
            if not isinstance(text, str) or not re.search(
                self.sql_pattern, text.lstrip()
            ):
                return updated_node

            # --- 1. Find Python Indent ---
            lines = text.splitlines()
            python_indent_prefix = ""
            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        match = re.match(r"^(\s*)", line)
                        if match:
                            python_indent_prefix = match.group(1)
                        break

            # --- 2. Normalize SQL ---
            normalized_sql = normalize_sql_indentation(text)

            # --- 3. Lint/Fix Normalized SQL ---
            processed_normalized_sql, issues_found = lint_or_fix_sql(
                normalized_sql, self.mode, self.config, self.file_path
            )
            self.total_issues_in_file += issues_found

            # --- 4. Re-apply Python Indent ---
            processed_lines = processed_normalized_sql.splitlines()
            final_sql_lines = []
            if processed_lines:
                final_sql_lines.append(processed_lines[0])  # Keep first line as is
                for line in processed_lines[1:]:
                    # Add the original python indent back
                    final_sql_lines.append(python_indent_prefix + line)

            final_sql = "\n".join(final_sql_lines)

            # --- 5. Determine original quote & closing-quote indent
            raw = original_node.value
            if raw.startswith(('"""', "'''")):
                quote = raw[:3]
                # get last line of the literal, e.g. "        """"
                last_line = raw.split("\n")[-1]
                m = re.match(r"^(\s*)" + re.escape(quote) + r"$", last_line)
                closing_indent = m.group(1) if m else ""
            else:
                quote = raw[0]
                closing_indent = ""

            # --- 6. Strip any trailing newlines from your fixed SQL
            body = final_sql.rstrip("\n")

            # --- 7. Rebuild: open-quote + body + newline + indent + close-quote
            new_value = f"{quote}{body}\n{closing_indent}{quote}"

            return cst.SimpleString(value=new_value)

        except Exception as e:
            print(f"Error processing string in {self.file_path}: {e}")
            return updated_node


def modify_file_in_place(file_path, mode, config, pattern=None):
    """
    Modify a Python file in place by linting or fixing embedded SQL strings.

    Args:
        file_path (str): Path to the Python file to modify.
        mode (str): Either 'lint' or 'fix'.
        config (FluffConfig): The SQLFluff configuration object.
        pattern (str): Optional regex pattern to identify SQL strings.

    Returns:
        int: Number of issues found in the file (0 if none or in fix mode)
    """
    SQL_KEYWORDS_PATTERN = r"^--sql"
    sql_pattern = pattern or SQL_KEYWORDS_PATTERN

    try:
        # Read the file content
        with open(file_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        # Parse the source code using LibCST
        module = cst.parse_module(source_code)

        # Create and apply the transformer
        transformer = SQLStringTransformer(mode, config, file_path, sql_pattern)
        modified_module = module.visit(transformer)

        # Write back the modified code if in fix mode
        if mode == "fix":
            # Check if the code actually changed before writing
            if modified_module.code != source_code:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(modified_module.code)

        # Return the total count of issues found by the transformer
        return transformer.total_issues_in_file

    except cst.ParserSyntaxError as e:
        print(f"Syntax error parsing {file_path}: {e}. Skipping file.")
        return 0  # Treat as 0 issues for this file
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0
