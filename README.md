# Film Script to Shot List Generator

A Python script that converts film scripts (.txt files) into detailed shot lists using Google's Gemini AI API.

## Features

- Process single script files or entire directories
- Detailed shot lists with cinematographic specifications
- Professional formatting with camera angles, movements, and technical notes
- Batch processing of multiple scripts
- Comprehensive error handling and logging
- Command-line interface with multiple options

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Installation

1. Clone or download this repository
2. Install dependencies using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Configuration

### API Key Setup

You can provide your Gemini API key in two ways:

#### Option 1: Environment Variable (Recommended)
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
# OR
GOOGLE_API_KEY=your_gemini_api_key_here
```

#### Option 2: Interactive Prompt
If no API key is found in environment variables, the script will prompt you to enter it securely during runtime.

## Usage

### Interactive Mode

Simply run the script and follow the interactive prompts:

```bash
python main.py
```

The script will guide you through:
1. **📁 Selecting your script file or directory** - Use arrow keys to navigate and select
2. **📂 Choosing output directory** - Default is `shot_lists/`
3. **🔧 Verbose logging option** - Enable for detailed processing logs
4. **🔑 API key input** - If not set in environment variables
5. **✅ Confirmation** - Review your selections before processing

### Example Interactive Session

```
🎬 Film Script to Shot List Generator
==================================================
? Select script file or directory containing scripts: /path/to/scripts/
? Output directory for shot lists: shot_lists
? Enable verbose logging? No

📄 Found 3 script file(s) to process:
  1. script1.txt
  2. script2.txt
  3. script3.txt

? Proceed with converting 3 script(s) to shot lists? Yes

🔧 Initializing Gemini API client...
🎯 Processing scripts...
✅ Shot lists saved to: /path/to/shot_lists

📋 Generated shot lists:
  📄 script1_shot_list.txt
  📄 script2_shot_list.txt
  📄 script3_shot_list.txt
```

## Output Format

The generated shot lists include:

- **Scene Information**: Number and description
- **Shot Details**: Type (Wide Shot, Close-up, etc.)
- **Camera Movement**: Static, Pan, Dolly, etc.
- **Shot Description**: Visual content and action
- **Dialogue/Audio**: Relevant audio notes
- **Duration Estimates**: Approximate shot length
- **Technical Notes**: Equipment, lighting, special requirements

### Example Output

```
SCENE 1: KITCHEN - MORNING
Shot 1A: Wide Shot - Static
- Establishing shot of kitchen, natural morning light
- Character enters from left
- Duration: 3-5 seconds
- Tech notes: Wide angle lens, natural lighting

Shot 1B: Medium Shot - Slight push-in
- Character at coffee machine
- Dialogue: "Another day begins..."
- Duration: 8-10 seconds
- Tech notes: 50mm lens, focus on hands making coffee
```

## Input Requirements

- Script files must be in `.txt` format
- Files should contain properly formatted screenplay text
- The script will automatically find all `.txt` files in directories and subdirectories

## Error Handling

The script includes comprehensive error handling for:
- Missing or invalid API keys
- Unreadable files
- Network connectivity issues
- API rate limits and errors
- File system permissions

## Logging

The script provides detailed logging:
- Processing status for each file
- Error messages with specific details
- Success/failure statistics
- Use `-v` flag for verbose output

## Dependencies

- `google-genai`: Modern Google Gemini API client (replaces deprecated google-generativeai)
- `python-dotenv`: Environment variable management
- `inquirer`: Interactive command-line prompts with beautiful UI
- `pathlib`: Modern file path handling
- `typing`: Type hints support

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Gemini API key is valid and properly set
2. **No Files Found**: Check that your input path contains `.txt` files
3. **Permission Errors**: Ensure the script has read access to input files and write access to output directory
4. **Rate Limiting**: The script handles API rate limits automatically, but very large batches may take time

### Getting Help

The script provides interactive guidance throughout the process. Simply run `python main.py` and follow the prompts. You can cancel at any time by pressing `Ctrl+C`.

## License

This project is open source. Please ensure you comply with Google's Gemini API terms of service when using this tool.
