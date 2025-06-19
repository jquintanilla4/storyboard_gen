import logging
import os
import sys
import re
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

# System prompt for Imagen prompt generation
SYSTEM_PROMPT = """You are a professional prompt engineer specializing in image generation for film and cinematography. Convert the provided shot list into detailed Imagen prompts that will generate high-quality cinematic images.

You will be provided with:
1. Character descriptions (if available) to ensure consistency across all generated images
2. A shot list to convert into image prompts

For each shot in the shot list, create a comprehensive Imagen prompt that includes:
1. Scene setting and environment details
2. Character descriptions and positioning (use the provided character descriptions for consistency)
3. Camera angle and framing (translated to visual perspective)
4. Lighting conditions and mood
5. Technical visual elements (depth of field, composition, etc.)
6. Artistic style and cinematic quality descriptors
7. The color palette of the shots needs to be distinct between cold and warm colors, depending on the year and location of the story being told, for example:
- before 1940s in china, the Li Huan Ying was studying in the US, which uses warm colors to emphasize her student life in the US and her social status. 
- The color turns cold when she is back in China during the 1940s and 1950s.
- The colors are expecially cold and gray between 1969 and 1973 when her life is at the lowest point.
- Every time she is not in China, execpt for USSR, the colors are warm and bright.
- Every time she is in Beijing, the color is less cold, to give more hope and utopian feel.
- She is a bit lost before 1978 and the color should reflect that.
- She becames more busy at her work starting from 1979, which began to change her life for the better, and the color should reflect that.

Guidelines for Midjourney prompts:
[SUBJECT / ACTION],
[MEDIUM or CAMERA / LENS],
[KEY ADJECTIVES & STYLE CUES],
[LIGHTING],
[COLOUR / MOOD],
[ENVIRONMENT & COMPOSITION],
[OPTIONAL ARTIST / FILM REFERENCES]
--ar W:H --v 7 [other parameters]

- Do not exceed the stylization parameter over 200, e.g. --s 200
- Do not use sref parameters, e.g. --sref 987654321
- Be specific about visual details, lighting, and composition.
- The prompts should be in photorealism cinematic style with high contrast and cinematic lighting.
- Include camera terms translated to visual perspective (e.g., "wide shot" becomes "wide angle view").
- Describe the mood and atmosphere.
- Add technical photography terms for better results.
- Keep each prompt focused and detailed but concise.
- Use cinematic and photographic terminology.
- Use the cinematic aspect ratio of 21:9, e.g. --ar 21:9
- The character's clothing should match the time period, location, and season of the story and shots.
- The props in the shot's prompt should match the time period, location, and season of the story and shots.
- The vehicles in the shot's prompt should match the time period, location, and season of the story and shots.
- The location in the shot's prompt should match the time period, country, and season of the story and shots.
- **IMPORTANT:** Use the provided character descriptions consistently across all prompts to maintain visual continuity, but account for character aging and changes in appearance over time.

Format the output as numbered prompts corresponding to each shot:

SCENE 1 - SHOT 1A: KITCHEN - MORNING 1999
Image Prompt: "Cvast desert highway at golden hour, ultra-wide 40 mm anamorphic lens flare, dust in the air, warm back-light, inspired by Roger Deakins and No Country for Old Men, high-contrast realism —-ar 21:9"

SCENE 1 - SHOT 1B: KITCHEN - MORNING 1999
Image Prompt: "Cinematic close-up portrait of a strikingly beautiful, fashionable young woman wearing cool, stylish sunglasses. She looks directly at the viewer with a captivating, confident gaze. Her lips are the focal point, coated in a high-shine, luscious lip gloss, making them look incredibly shiny, plump, and invitingly tasty. Soft, glamorous studio lighting that catches the gloss, shallow depth of field. --ar 21:9"

Convert the following shot list:
"""


def create_gemini_client(api_key):
    """Create and return a Gemini API client"""
    return genai.Client(api_key=api_key)


def read_characters_file(base_dir="text_files"):
    """Read the characters.txt file and return its content"""
    characters_path = Path(base_dir) / "characters.txt"

    try:
        if not characters_path.exists():
            logger.warning(f"Characters file not found at: {characters_path}")
            logger.info(
                "Consider creating a characters.txt file in the text_files directory for consistent character descriptions")
            return ""

        with open(characters_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read().strip()

        if not content:
            logger.warning(
                f"Characters file appears to be empty: {characters_path}")
            return ""

        logger.info(f"Successfully read characters file: {characters_path}")
        return content

    except Exception as e:
        logger.error(f"Error reading characters file {characters_path}: {e}")
        return ""


def read_shot_list_file(file_path):
    """Read a shot list file and return its content"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read().strip()

        if not content:
            logger.warning(f"File appears to be empty: {file_path}")
            return ""

        logger.info(f"Successfully read shot list: {file_path}")
        return content

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""


def generate_image_prompts(client, shot_list_content, shot_list_name):
    """Generate image prompts from shot list content using Gemini API"""
    try:
        # Read character descriptions
        characters_content = read_characters_file()

        # Construct the user content with both characters and shot list
        if characters_content:
            user_content = f"CHARACTER DESCRIPTIONS:\n{characters_content}\n\nSHOT LIST: {shot_list_name}\n\n{shot_list_content}"
            logger.info(
                f"Including character descriptions in prompt for: {shot_list_name}")
        else:
            user_content = f"SHOT LIST: {shot_list_name}\n\n{shot_list_content}"
            logger.info(
                f"No character descriptions found, proceeding with shot list only for: {shot_list_name}")

        logger.info(f"Generating image prompts for: {shot_list_name}")

        response = client.models.generate_content(
            model='gemini-2.5-pro',  # Using a generally available and capable model
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

        if response and response.text:
            logger.info(
                f"Successfully generated image prompts for: {shot_list_name}")
            return response.text
        else:
            logger.error(
                f"Empty or blocked response from Gemini for: {shot_list_name}. Response: {response}")
            return f"Error: Could not generate image prompts for {shot_list_name}. The response was empty or blocked."

    except Exception as e:
        logger.error(
            f"Error generating image prompts for {shot_list_name}: {e}")
        return f"Error generating image prompts for {shot_list_name}: {str(e)}"


def save_image_prompts(prompts, output_path):
    """Save image prompts to file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(prompts)
        logger.info(f"Image prompts saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving image prompts to {output_path}: {e}")
        return False


def process_shot_list_files(client, shot_list_paths, output_dir):
    """Process multiple shot list files and generate image prompts"""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    successful_conversions = 0
    total_files = len(shot_list_paths)

    for shot_list_path in shot_list_paths:
        if not shot_list_path.exists():
            logger.warning(f"Shot list file not found: {shot_list_path}")
            continue

        if shot_list_path.suffix.lower() != '.txt':
            logger.warning(f"Skipping non-txt file: {shot_list_path}")
            continue

        # Read shot list content
        shot_list_content = read_shot_list_file(shot_list_path)
        if not shot_list_content:
            logger.warning(f"Empty or unreadable shot list: {shot_list_path}")
            continue

        # Generate image prompts
        image_prompts = generate_image_prompts(
            client, shot_list_content, shot_list_path.name)

        # Create output filename
        output_filename = f"{shot_list_path.stem}_image_prompts.txt"
        output_path = output_dir / output_filename

        # Save image prompts
        if save_image_prompts(image_prompts, output_path):
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
        if substring.isdigit():
            return int(substring)
        # Otherwise, convert to lowercase string for case-insensitive comparison
        return substring.lower()

    # Split the text into digit and non-digit parts using regex,
    parts = re.split(r'(\d+)', str(text))
    # then convert each part appropriately for sorting
    return [convert(part) for part in parts]


def process_combined_shot_lists(client, shot_list_paths, output_dir, combined_name):
    """Combine multiple shot list files, generate image prompts, and save them."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Combine content from all shot list files, sorting them in natural order
    full_shot_list_content = []
    logger.info("Combining multiple shot list files into one.")

    # Sort files using natural sorting
    sorted_shot_list_paths = sorted(
        shot_list_paths, key=lambda x: natural_sort_key(x.name))

    logger.info("Shot list files will be combined in this order:")
    for i, shot_list_path in enumerate(sorted_shot_list_paths, 1):
        logger.info(f"  {i}. {shot_list_path.name}")

    for shot_list_path in sorted_shot_list_paths:
        content = read_shot_list_file(shot_list_path)
        if content:
            full_shot_list_content.append(content)
        else:
            logger.warning(
                f"Skipping empty or unreadable shot list: {shot_list_path}")

    if not full_shot_list_content:
        logger.error("No content found in shot list files to combine.")
        return

    combined_content = "\n\n".join(full_shot_list_content)

    # Generate image prompts for the combined shot list
    image_prompts = generate_image_prompts(
        client, combined_content, f"{combined_name} (Combined)")

    # Create output filename
    output_filename = f"{combined_name}_combined_image_prompts.txt"
    output_path = output_dir / output_filename

    # Save image prompts
    if save_image_prompts(image_prompts, output_path):
        logger.info(f"Combined image prompts saved to: {output_path}")

    logger.info("Combined shot list processing complete.")


def find_shot_list_files(directory):
    """Find all .txt files in directory and subdirectories"""
    if directory.is_file() and directory.suffix.lower() == '.txt':
        return [directory]

    if directory.is_dir():
        txt_files = list(directory.rglob('*.txt'))
        return txt_files

    return []


def get_user_inputs():
    """Get user inputs through interactive prompts"""
    print("Shot List to Image Prompts Generator")
    print("Converts shot lists to detailed image generation prompts")
    print("=" * 60)

    questions = [
        inquirer.Path(
            'input_path',
            message="Select shot list file or directory containing shot lists (.txt)",
            path_type=inquirer.Path.ANY,
            exists=True,
        ),
        inquirer.Text(
            'output_dir',
            message="Output directory for image prompts",
            default="text_files/image_prompts"
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

        # Find shot list files
        shot_list_files = find_shot_list_files(input_path)
        if not shot_list_files:
            logger.error(f"No .txt shot list files found in: {input_path}")
            print(f"\nNo .txt shot list files found in: {input_path}")
            sys.exit(1)

        print(f"\nFound {len(shot_list_files)} shot list file(s) to process:")
        for i, file_path in enumerate(shot_list_files, 1):
            print(f"  {i}. {file_path.name}")
        print("\n")

        # Ask about combining if multiple files are in a directory
        combine_files = False
        if input_path.is_dir() and len(shot_list_files) > 1:
            combine_question = [
                inquirer.Confirm(
                    'combine',
                    message="Combine these shot lists into a single prompt file? (Recommended for sequential scenes)",
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
            print(f"\nCombining shot lists and generating image prompts...")
            combined_name = input_path.name
            process_combined_shot_lists(
                client, shot_list_files, output_dir, combined_name)
        else:
            print(f"\nProcessing shot list files individually...")
            process_shot_list_files(client, shot_list_files, output_dir)

        print(f"\nImage prompts saved to: {output_dir.absolute()}")

        # Show output files
        output_glob = "*_combined_image_prompts.txt" if combine_files else "*_image_prompts.txt"
        output_files = list(output_dir.glob(output_glob))
        if output_files:
            print(f"\nGenerated image prompt files:")
            for output_file in output_files:
                print(f"  {output_file.name}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
