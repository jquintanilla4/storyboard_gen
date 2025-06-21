import re
import pandas as pd
import inquirer
from pathlib import Path


def natural_sort_key(text):
    """
    Generate a key for natural/alphanumeric sorting.

    This function splits the input string into a list of alternating
    numeric and non-numeric substrings, so that numbers are compared
    as integers and text as lowercase strings. This ensures that
    filenames like 'chunk_2.txt' are sorted before 'chunk_10.txt'.

    Args:
        text (str): The string to generate a sort key for.

    Returns:
        list: A list of elements (int or str) for natural sorting.
    """
    def convert(substring):
        if substring.isdigit():
            return int(substring)
        # Otherwise, convert to lowercase string for case-insensitive comparison
        return substring.lower()

    # Split the text into digit and non-digit parts using regex,
    parts = re.split(r'(\d+)', str(text))
    # then convert each part appropriately for sorting
    return [convert(part) for part in parts]


def consolidate_csv_files(input_directory, output_file=None):
    """
    Consolidate multiple CSV files from a directory into a single CSV file.

    Files are sorted in alphanumeric order to maintain chronological sequence.
    Columns are detected dynamically from the first CSV file.

    Args:
        input_directory (str): Path to directory containing CSV files
        output_file (str, optional): Path for output CSV file. If None, saves as 'consolidated.csv' in input directory

    Returns:
        str: Path to the consolidated CSV file
    """
    input_path = Path(input_directory)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input directory '{input_directory}' does not exist")

    # Find all CSV files in the directory
    csv_files = list(input_path.glob("*.csv"))

    if not csv_files:
        raise ValueError(
            f"No CSV files found in directory '{input_directory}'")

    # Sort files using natural/alphanumeric ordering
    csv_files.sort(key=lambda x: natural_sort_key(x.name))

    print(f"Found {len(csv_files)} CSV files:")
    for i, file in enumerate(csv_files, 1):
        print(f"  {i}. {file.name}")

    # List to store all dataframes
    dataframes = []
    columns = None

    # Process each CSV file
    for file_path in csv_files:
        try:
            print(f"Processing: {file_path.name}")
            df = pd.read_csv(file_path)

            # Set columns from first file (dynamic column detection)
            if columns is None:
                columns = df.columns.tolist()
                print(f"Detected columns: {columns}")

            # Ensure all files have the same columns
            if not df.columns.tolist() == columns:
                print(
                    f"Warning: {file_path.name} has different columns. Attempting to align...")
                # Reindex to match expected columns, filling missing columns with NaN
                df = df.reindex(columns=columns)

            dataframes.append(df)

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue

    if not dataframes:
        raise ValueError("No valid CSV files could be processed")

    # Concatenate all dataframes
    print("Consolidating data...")
    consolidated_df = pd.concat(dataframes, ignore_index=True)

    # Determine output file path
    if output_file is None:
        output_file = input_path / "consolidated.csv"
    else:
        output_file = Path(output_file)

    # Save consolidated CSV
    consolidated_df.to_csv(output_file, index=False)

    print(
        f"Successfully consolidated {len(dataframes)} files into '{output_file}'")
    print(f"Total rows: {len(consolidated_df)}")
    print(f"Columns: {consolidated_df.columns.tolist()}")

    return str(output_file)


def main():
    """Interactive interface for the CSV consolidation tool."""
    print("=== CSV File Consolidation Tool ===")
    print("This tool consolidates multiple CSV files into a single file with proper alphanumeric ordering.\n")

    # Get current working directory and common directories for suggestions
    current_dir = Path.cwd()
    text_files_dir = current_dir / "text_files"

    # Create list of suggested directories
    suggested_dirs = [str(current_dir)]
    if text_files_dir.exists():
        suggested_dirs.append(str(text_files_dir))
        # Add subdirectories of text_files
        for subdir in text_files_dir.iterdir():
            if subdir.is_dir():
                suggested_dirs.append(str(subdir))

    # Prompt for input directory
    questions = [
        inquirer.Path(
            'input_directory',
            message="Select the directory containing CSV files to consolidate",
            path_type=inquirer.Path.DIRECTORY,
            default=str(current_dir),
            exists=True
        )
    ]

    answers = inquirer.prompt(questions)
    if not answers:
        print("Operation cancelled.")
        return 1

    input_directory = answers['input_directory']

    # Check if directory contains CSV files
    csv_files = list(Path(input_directory).glob("*.csv"))
    if not csv_files:
        print(f"\nNo CSV files found in '{input_directory}'")
        return 1

    print(f"\nFound {len(csv_files)} CSV file(s) in '{input_directory}'")

    # Ask if user wants to specify custom output file
    output_questions = [
        inquirer.Confirm(
            'custom_output',
            message="Do you want to specify a custom output file name/location?",
            default=False
        )
    ]

    output_answers = inquirer.prompt(output_questions)
    if not output_answers:
        print("Operation cancelled.")
        return 1

    output_file = None
    if output_answers['custom_output']:
        output_file_questions = [
            inquirer.Path(
                'output_file',
                message="Enter the output CSV file path",
                path_type=inquirer.Path.FILE,
                default=str(Path(input_directory) / "consolidated.csv")
            )
        ]

        output_file_answers = inquirer.prompt(output_file_questions)
        if not output_file_answers:
            print("Operation cancelled.")
            return 1

        output_file = output_file_answers['output_file']

    # Perform consolidation
    try:
        print("\nStarting consolidation...")
        output_path = consolidate_csv_files(input_directory, output_file)
        print(f"\nConsolidation complete! Output saved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
