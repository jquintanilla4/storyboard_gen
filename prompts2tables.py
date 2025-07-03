import logging
import os
import sys
import re
import csv
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import inquirer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# System prompt for parsing image prompts into structured format
SYSTEM_PROMPT = """You are a data extraction specialist. Your task is to parse image prompt files and extract the scene, shot, and prompt information into a structured markdown table format.

The input will contain multiple image prompt files concatenated together. Each file may have slightly different formatting, but generally follows patterns like:

- Scene headers: ### **SCENE X: [TITLE]** or similar variations
- Shot identifiers: **Shot XY: [Description]** or similar variations  
- Image prompts: **Imagen Prompt:** "[prompt text]" or similar variations

Your task is to:
1. Identify all scenes, shots, and their corresponding image prompts
2. Extract the scene number/identifier, shot identifier, and the full prompt text
3. Output ONLY a clean markdown table with three columns: Scene, Shot, Prompt

The output format should be:
| Scene | Shot | Prompt |
|-------|------|--------|
| 1 | 1A | [full prompt text] |
| 1 | 1B | [full prompt text] |
| 2 | 2A | [full prompt text] |

Requirements:
- Include ALL prompts found in the input
- Keep the full prompt text intact (don't truncate)
- Use consistent scene and shot identifiers
- Don't include any other text or explanations, just the markdown table
- If a prompt spans multiple lines, keep it as one entry
- Remove any markdown formatting from within the prompt text itself (like **bold** text)
"""


def create_gemini_client(api_key):
    """Create and return a Gemini API client"""
    return genai.Client(api_key=api_key)


def read_prompt_file(file_path):
    """Read a prompt file and return its content"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read().strip()

        if not content:
            logger.warning(f"File appears to be empty: {file_path}")
            return ""

        logger.info(f"Successfully read prompt file: {file_path}")
        return content

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""


def concatenate_prompt_files(prompt_file_paths):
    """Concatenate multiple prompt files into one large text"""
    if not prompt_file_paths:
        logger.error("No prompt files provided for concatenation")
        return ""

    # Sort files using natural sorting for consistent order
    sorted_prompt_files = sorted(
        prompt_file_paths, key=lambda x: natural_sort_key(x.name))

    logger.info("Concatenating prompt files in this order:")
    for i, file_path in enumerate(sorted_prompt_files, 1):
        logger.info(f"  {i}. {file_path.name}")

    combined_content = []
    successful_files = 0

    for prompt_file_path in sorted_prompt_files:
        if not prompt_file_path.exists():
            logger.warning(f"Prompt file not found: {prompt_file_path}")
            continue

        if prompt_file_path.suffix.lower() != '.txt':
            logger.warning(f"Skipping non-txt file: {prompt_file_path}")
            continue

        # Read prompt file content
        file_content = read_prompt_file(prompt_file_path)
        if file_content:
            # Add file separator and content
            combined_content.append(f"=== FILE: {prompt_file_path.name} ===")
            combined_content.append(file_content)
            combined_content.append("")  # Add blank line between files
            successful_files += 1
        else:
            logger.warning(f"No content read from: {prompt_file_path}")

    if not combined_content:
        logger.error("No content found in any prompt files")
        return ""

    final_content = "\n".join(combined_content)
    logger.info(
        f"Successfully concatenated {successful_files} files into one text block")
    logger.info(
        f"Total combined content length: {len(final_content)} characters")

    return final_content


def parse_prompts(client, combined_content):
    """Send concatenated content to Gemini API for structured parsing"""
    try:
        logger.info(
            "Sending concatenated content to Gemini for structured parsing...")

        response = client.models.generate_content(
            model='gemini-2.5-pro',  # Using a generally available and capable model
            contents=combined_content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.5, # lower (0.1) for consistent formatting
                max_output_tokens=32000,
            )
        )

        if response and response.text:
            logger.info("Successfully received structured table from Gemini")
            return response.text
        else:
            logger.error(
                f"Empty or blocked response from Gemini. Response: {response}")
            return f"Error: Could not parse prompts. The response was empty or blocked."

    except Exception as e:
        logger.error(f"Error parsing prompts with Gemini: {e}")
        return f"Error parsing prompts with Gemini: {str(e)}"


def parse_markdown_table_to_csv(markdown_table, output_path):
    """Parse markdown table output and convert to CSV"""
    try:
        lines = markdown_table.strip().split('\n')

        # Find the table start (look for header row)
        table_start = -1
        for i, line in enumerate(lines):
            if '|' in line and ('Scene' in line or 'scene' in line):
                table_start = i
                break

        if table_start == -1:
            logger.error("Could not find markdown table in Gemini response")
            return False

        # Extract table rows (skip header and separator rows)
        table_rows = []
        for i in range(table_start, len(lines)):
            line = lines[i].strip()
            # Skip separator row
            if '|' in line and not line.startswith('|---'):
                # Split by | and clean up
                cells = [cell.strip() for cell in line.split('|')]
                # Remove empty first/last elements if they exist
                if cells and cells[0] == '':
                    cells = cells[1:]
                if cells and cells[-1] == '':
                    cells = cells[:-1]

                # Only add rows with 3 columns
                if len(cells) == 3:
                    table_rows.append(cells)

        if not table_rows:
            logger.error("No valid table rows found in markdown output")
            return False

        # Skip the header row (first row)
        data_rows = table_rows[1:] if len(table_rows) > 1 else []

        if not data_rows:
            logger.error("No data rows found in markdown table")
            return False

        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['scene', 'shot', 'prompt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            for row in data_rows:
                if len(row) >= 3:
                    writer.writerow({
                        'scene': row[0],
                        'shot': row[1],
                        'prompt': row[2]
                    })

        logger.info(
            f"Successfully created CSV with {len(data_rows)} rows: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error converting markdown table to CSV: {e}")
        return False


def process_prompt_files_to_csv(client, prompt_file_paths, output_dir):
    """Process multiple prompt files and create a single CSV table"""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Concatenate all prompt files
    combined_content = concatenate_prompt_files(prompt_file_paths)
    if not combined_content:
        logger.error("No content to process")
        return

    # Send to Gemini for structured parsing
    structured_output = parse_prompts(client, combined_content)
    if not structured_output or structured_output.startswith("Error"):
        logger.error("Failed to get structured output from Gemini")
        print(f"Error: {structured_output}")
        return

    # Create output filename
    output_filename = "prompts_table.csv"
    output_path = output_dir / output_filename

    # Convert markdown table to CSV
    if parse_markdown_table_to_csv(structured_output, output_path):
        print(f"\nCSV table created successfully: {output_path}")

        # Count rows for feedback
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                row_count = sum(1 for line in f) - 1  # Subtract header row
            print(f"Total prompts extracted: {row_count}")
        except Exception:
            pass
    else:
        logger.error("Failed to create CSV table")


def process_prompt_files_individually(client, prompt_file_paths, output_dir):
    """Process each prompt file individually and create separate CSV tables.

    Each file is sent to Gemini on its own so that the request stays well
    under the model's ~32k token response limit (roughly 100-115 shots).
    This method is the most robust for very large directories because no
    prompt file is ever combined with another.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Sort files using natural ordering for consistency
    sorted_files = sorted(prompt_file_paths, key=lambda x: natural_sort_key(x.name))

    for prompt_file_path in sorted_files:
        if not prompt_file_path.exists() or prompt_file_path.suffix.lower() != '.txt':
            logger.warning(f"Skipping invalid file: {prompt_file_path}")
            continue

        logger.info(f"Processing {prompt_file_path.name} individually")

        file_content = read_prompt_file(prompt_file_path)
        if not file_content:
            logger.warning(f"Empty or unreadable prompt file: {prompt_file_path}")
            continue

        structured_output = parse_prompts(client, file_content)
        if not structured_output or structured_output.startswith("Error"):
            logger.error(f"Failed to parse {prompt_file_path.name}")
            print(f"Error processing {prompt_file_path.name}: {structured_output}")
            continue

        output_filename = f"{prompt_file_path.stem}_prompts_table.csv"
        output_path = output_dir / output_filename

        if parse_markdown_table_to_csv(structured_output, output_path):
            print(f"Created CSV: {output_path.name}")
        else:
            logger.error(f"Failed to create CSV for {prompt_file_path.name}")


def process_prompt_files_in_pairs(client, prompt_file_paths, output_dir):
    """Process prompt files two at a time and create separate CSV tables.

    Two files are concatenated and parsed in a single Gemini request. This
    reduces the number of API calls when dealing with many small files while
    still helping to keep each request under the token limit.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    sorted_files = sorted(prompt_file_paths, key=lambda x: natural_sort_key(x.name))

    pair_num = 1
    for i in range(0, len(sorted_files), 2):
        pair_files = [f for f in sorted_files[i:i+2] if f.exists() and f.suffix.lower() == '.txt']
        if not pair_files:
            continue

        names = ', '.join(f.name for f in pair_files)
        logger.info(f"Processing pair {pair_num}: {names}")

        combined_content = concatenate_prompt_files(pair_files)
        if not combined_content:
            logger.warning(f"Skipping pair {pair_num} due to empty content")
            pair_num += 1
            continue

        structured_output = parse_prompts(client, combined_content)
        if not structured_output or structured_output.startswith("Error"):
            logger.error(f"Failed to parse pair {pair_num}")
            print(f"Error processing pair {pair_num}: {structured_output}")
            pair_num += 1
            continue

        if len(pair_files) == 1:
            fname = f"{pair_files[0].stem}"
        else:
            fname = f"{pair_files[0].stem}_{pair_files[1].stem}"
        output_filename = f"{fname}_prompts_table.csv"
        output_path = output_dir / output_filename

        if parse_markdown_table_to_csv(structured_output, output_path):
            print(f"Created CSV: {output_path.name}")
        else:
            logger.error(f"Failed to create CSV for pair {pair_num}")

        pair_num += 1


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


def find_prompt_files(directory):
    """Find all .txt files in directory and subdirectories"""
    if directory.is_file() and directory.suffix.lower() == '.txt':
        return [directory]

    if directory.is_dir():
        txt_files = list(directory.rglob('*.txt'))
        return txt_files

    return []


def get_user_inputs():
    """Get user inputs through interactive prompts"""
    print("Image Prompts to CSV Table Generator (via Gemini API)")
    print("Concatenates prompt files, uses Gemini to parse them, and outputs a CSV table")
    print("=" * 80)

    questions = [
        inquirer.Path(
            'input_path',
            message="Select prompt file or directory containing prompt files (.txt)",
            path_type=inquirer.Path.ANY,
            exists=True,
        ),
        inquirer.Text(
            'output_dir',
            message="Output directory for CSV table",
            default="text_files"
        ),
        inquirer.Confirm(
            'verbose',
            message="Enable verbose logging?",
            default=False
        )
    ]

    answers = inquirer.prompt(questions)
    if not answers:
        print("Operation cancelled.")
        sys.exit(0)

    return answers


def get_api_key_if_needed():
    """Prompt for API key if not found in environment"""
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

    if not api_key:
        print("\nAPI Key Required")
        print("No Gemini API key found in environment variables.")

        questions = [
            inquirer.Confirm(
                'provide_key',
                message="Would you like to provide your API key now?",
                default=True
            )
        ]

        if inquirer.prompt(questions)['provide_key']:
            api_key_question = [
                inquirer.Password(
                    'api_key',
                    message="Enter your Gemini API key"
                )
            ]
            api_key = inquirer.prompt(api_key_question)['api_key']
        else:
            print(
                "Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable and try again.")
            sys.exit(1)

    return api_key


def main():
    """Main function with interactive prompts"""
    try:
        # Get user inputs interactively
        inputs = get_user_inputs()

        if inputs['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

        # Validate input path
        raw_input_path = inputs['input_path']
        cleaned_input_path = raw_input_path.strip().strip("'\"")
        input_path = Path(cleaned_input_path)
        if not input_path.exists():
            logger.error(f"Input path does not exist: {input_path}")
            sys.exit(1)

        # Find prompt files
        prompt_files = find_prompt_files(input_path)
        if not prompt_files:
            logger.error(f"No .txt prompt files found in: {input_path}")
            print(f"\nNo .txt prompt files found in: {input_path}")
            sys.exit(1)

        print(f"\nFound {len(prompt_files)} prompt file(s) to process:")
        for i, file_path in enumerate(prompt_files, 1):
            print(f"  {i}. {file_path.name}")
        print("\n")

        process_choice = 'individual'
        # Offer a choice between processing files individually or in
        # two-file batches. Individual mode avoids token limit issues
        # with large directories, while pair mode can reduce the number
        # of API requests for smaller datasets.
        if input_path.is_dir() and len(prompt_files) > 1:
            mode_question = [
                inquirer.List(
                    'mode',
                    message="Process prompt files individually or in pairs?",
                    choices=['individual', 'pairs'],
                    default='individual'
                )
            ]
            answers = inquirer.prompt(mode_question)
            if not answers:
                print("Operation cancelled.")
                sys.exit(0)
            process_choice = answers['mode']

        # Get API key if needed
        api_key = get_api_key_if_needed()

        # Initialize Gemini client
        print("🔧 Initializing Gemini API client...")
        try:
            client = create_gemini_client(api_key)
        except Exception as e:
            logger.error(f"Failed to create Gemini client: {e}")
            print(f"Failed to initialize API client: {e}")
            sys.exit(1)

        # Process files
        output_dir = Path(inputs['output_dir'])

        # Create output directory if it doesn't exist
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
            except Exception as e:
                logger.error(
                    f"Failed to create output directory {output_dir}: {e}")
                print(
                    f"Error: Could not create output directory {output_dir}: {e}")
                sys.exit(1)

        if process_choice == 'pairs':
            print("\nProcessing prompt files in pairs...")
            process_prompt_files_in_pairs(client, prompt_files, output_dir)
        else:
            print("\nProcessing prompt files individually...")
            process_prompt_files_individually(client, prompt_files, output_dir)

        print(f"\nOutput saved to: {output_dir.absolute()}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
