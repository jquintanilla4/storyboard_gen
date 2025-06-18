import logging
import os
import sys
import re
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import inquirer
from striprtf.striprtf import rtf_to_text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# System prompt for shot list generation
SYSTEM_PROMPT = """You are a professional cinematographer and director of an oscar winning biographical film. Convert the provided film script into a detailed shot list. 

For each scene, provide:
1. Scene number, location and description
2. Time (e.g., morning)
3. Year of the scene taking place
4. Shot numbered within each scene
5. Shot type (e.g., Wide Shot, Close-up, Medium Shot, Two-shot, etc.)
6. Camera movement (e.g., Static, Pan, Tilt, Dolly, Tracking, etc.)
7. Shot description (what's happening in the frame)
8. Dialogue/Audio notes (if applicable)
9. Duration estimate
10. Technical notes (lighting, special equipment, etc.)

Format the output as a structured shot list with clear numbering and organization. Be specific about camera angles, framing, and visual storytelling elements.

Example format:
SCENE 1: KITCHEN - MORNING 1999
Shot 1A: Wide Shot - Static
- Establishing shot of kitchen, natural morning light
- Character enters from left, laughing and exctied.
- Duration: 3-5 seconds
- Tech notes: Wide angle lens, natural lighting

Shot 1B: Medium Shot - Slight push-in
- Character at coffee machine, looking at the coffee machine, excited about making a cup of coffee.
- Dialogue: "Another day begins..."
- Duration: 8-10 seconds
- Tech notes: 50mm lens, focus on hands making coffee

SCENE 2: CAR - MORNING 1999
Shot 1A: Close up shot - Static
- Close up shot of Dr. Li sitting in the car, in deep thoughts.
- Duration: 5 seconds
Tech notes: Close up lens, sunny day natural lighting

IMPORTANT: The input script may be in simplified Chinese or English, but you must ALWAYS return the shot list in English only.

The script format is:
Scene number, followed by day or night, followed by interior or exterior, 
followed by location and year as well as season of that year. Then the content of the scene, including character action and dialogue.
Sometimes the script will describe how the characters in the scene are feeling.

If the input script is in Chinese, translate all dialogue and descriptions to English in your shot list output.

Convert the following script:"""


def create_gemini_client(api_key):
    """Create and return a Gemini API client"""
    return genai.Client(api_key=api_key)


def read_script_file(file_path):
    """Read a script file and return its content, handling both .txt and .rtf formats"""
    try:
        file_extension = file_path.suffix.lower()

        if file_extension == '.rtf':
            # Handle RTF files
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                rtf_content = file.read()
            # Convert RTF to plain text
            content = rtf_to_text(rtf_content).strip()
            logger.info(f"Successfully converted RTF script: {file_path}")
        elif file_extension == '.txt':
            # Handle plain text files
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read().strip()
            logger.info(f"Successfully read text script: {file_path}")
        else:
            logger.error(f"Unsupported file format: {file_extension}")
            return ""

        if not content:
            logger.warning(
                f"File appears to be empty after processing: {file_path}")
            return ""

        return content

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        # Try with different encodings for Chinese text
        try:
            logger.info(f"Trying alternative encoding for: {file_path}")
            if file_path.suffix.lower() == '.rtf':
                with open(file_path, 'r', encoding='gbk', errors='ignore') as file:
                    rtf_content = file.read()
                content = rtf_to_text(rtf_content).strip()
            else:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as file:
                    content = file.read().strip()
            logger.info(f"Successfully read with GBK encoding: {file_path}")
            return content
        except Exception as e2:
            logger.error(f"Failed with alternative encoding: {e2}")
            return ""


def generate_shot_list(client, script_content, script_name):
    """Generate shot list from script content using Gemini API"""
    try:
        user_content = f"SCRIPT: {script_name}\n\n{script_content}"

        logger.info(f"Generating shot list for: {script_name}")

        response = client.models.generate_content(
            model='gemini-2.5-pro',  # Using a generally available and capable model
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

        if response and response.text:
            logger.info(f"Successfully generated shot list for: {script_name}")
            return response.text
        else:
            # It's helpful to log the actual response for debugging safety blocks
            logger.error(
                f"Empty or blocked response from Gemini for: {script_name}. Response: {response}")
            return f"Error: Could not generate shot list for {script_name}. The response was empty or blocked."

    except Exception as e:
        logger.error(f"Error generating shot list for {script_name}: {e}")
        return f"Error generating shot list for {script_name}: {str(e)}"


def save_shot_list(shot_list, output_path):
    """Save shot list to file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(shot_list)
        logger.info(f"Shot list saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving shot list to {output_path}: {e}")
        return False


def process_script_files(client, script_paths, output_dir):
    """Process multiple script files and generate shot lists"""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    successful_conversions = 0
    total_files = len(script_paths)

    for script_path in script_paths:
        if not script_path.exists():
            logger.warning(f"Script file not found: {script_path}")
            continue

        file_extension = script_path.suffix.lower()
        if file_extension not in ['.txt', '.rtf']:
            logger.warning(f"Skipping unsupported file type: {script_path}")
            continue

        # Read script content
        script_content = read_script_file(script_path)
        if not script_content:
            logger.warning(f"Empty or unreadable script: {script_path}")
            continue

        # Generate shot list
        shot_list = generate_shot_list(
            client, script_content, script_path.name)

        # Create output filename
        output_filename = f"{script_path.stem}_shot_list.txt"
        output_path = output_dir / output_filename

        # Save shot list
        if save_shot_list(shot_list, output_path):
            successful_conversions += 1

    logger.info(
        f"Conversion complete: {successful_conversions}/{total_files} files processed successfully")


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
        if substring.isdigit(): # If the substring is all digits, convert to int for numeric comparison
            return int(substring)
        return substring.lower() # Otherwise, convert to lowercase string for case-insensitive comparison

    parts = re.split(r'(\d+)', str(text)) # Split the text into digit and non-digit parts using regex,
    return [convert(part) for part in parts] # then convert each part appropriately for sorting


def process_combined_script(client, script_paths, output_dir, combined_script_name):
    """Combine multiple script files, generate a single shot list, and save it."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Combine content from all script files, sorting them in natural order
    full_script_content = []
    logger.info("Combining multiple script files into one.")

    # Sort files using natural sorting to handle chunk_0001, chunk_0002, etc.
    sorted_script_paths = sorted(script_paths, key=lambda x: natural_sort_key(x.name))

    logger.info("Script files will be combined in this order:")
    for i, script_path in enumerate(sorted_script_paths, 1):
        logger.info(f"  {i}. {script_path.name}")

    for script_path in sorted_script_paths:
        content = read_script_file(script_path)
        if content:
            full_script_content.append(content)
        else:
            logger.warning(
                f"Skipping empty or unreadable script: {script_path}")

    if not full_script_content:
        logger.error("No content found in script files to combine.")
        return

    combined_content = "\n\n".join(full_script_content)

    # Generate shot list for the combined script
    shot_list = generate_shot_list(
        client, combined_content, f"{combined_script_name} (Combined)")

    # Create output filename
    output_filename = f"{combined_script_name}_combined_shot_list.txt"
    output_path = output_dir / output_filename

    # Save shot list
    if save_shot_list(shot_list, output_path):
        logger.info(f"Combined shot list saved to: {output_path}")

    logger.info("Combined script processing complete.")


def find_script_files(directory):
    """Find all .txt and .rtf files in directory and subdirectories"""
    if directory.is_file() and directory.suffix.lower() in ['.txt', '.rtf']:
        return [directory]

    if directory.is_dir():
        txt_files = list(directory.rglob('*.txt'))
        rtf_files = list(directory.rglob('*.rtf'))
        return txt_files + rtf_files

    return []


def get_user_inputs():
    """Get user inputs through interactive prompts"""
    print("Film Script to Shot List Generator")
    print("Supports .txt and .rtf files with Chinese content")
    print("=" * 60)

    questions = [
        inquirer.Path(
            'input_path',
            message="Select script file or directory containing scripts (.txt/.rtf)",
            path_type=inquirer.Path.ANY,
            exists=True,
        ),
        inquirer.Text(
            'output_dir',
            message="Output directory for shot lists",
            default="text_files/shot_lists"
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
        # Strip spaces, single quotes, and double quotes
        cleaned_input_path = raw_input_path.strip().strip("'\"")
        input_path = Path(cleaned_input_path)
        if not input_path.exists():
            logger.error(f"Input path does not exist: {input_path}")
            sys.exit(1)

        # Find script files
        script_files = find_script_files(input_path)
        if not script_files:
            logger.error(
                f"No .txt or .rtf script files found in: {input_path}")
            print(f"\nNo .txt or .rtf script files found in: {input_path}")
            sys.exit(1)

        print(f"\nFound {len(script_files)} script file(s) to process:")
        for i, file_path in enumerate(script_files, 1):
            print(f"  {i}. {file_path.name}")
        print("\n")

        # Ask about combining if multiple files are in a directory
        combine_files = False
        if input_path.is_dir() and len(script_files) > 1:
            combine_question = [
                inquirer.Confirm(
                    'combine',
                    message="Combine these files into a single script for one shot list? (Recommended for sequential scenes)",
                    default=True
                )
            ]
            answers = inquirer.prompt(combine_question)
            if not answers:
                print("Operation cancelled.")
                sys.exit(0)
            if answers['combine']:
                combine_files = True

        # Get API key if needed
        api_key = get_api_key_if_needed()

        # Initialize Gemini client
        print("\n🔧 Initializing Gemini API client...")
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

        if combine_files:
            print(f"\nCombining scripts and generating a single shot list...")
            combined_script_name = input_path.name
            process_combined_script(
                client, script_files, output_dir, combined_script_name)
        else:
            print(f"\nProcessing text files individually...")
            process_script_files(client, script_files, output_dir)

        print(f"\nShot lists saved to: {output_dir.absolute()}")

        # Show output files
        output_glob = "*_combined_shot_list.txt" if combine_files else "*_shot_list.txt"
        output_files = list(output_dir.glob(output_glob))
        if output_files:
            print(f"\nGenerated shot lists:")
            for output_file in output_files:
                print(f"{output_file.name}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
