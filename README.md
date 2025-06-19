# Film Script to Storyboard Generation Pipeline

A comprehensive Python pipeline that converts film scripts into detailed shot lists, generates cinematic image prompts, and creates structured data tables for storyboard production using Google's Gemini AI API.

## Features

- **Multi-stage Pipeline**: Complete workflow from script to storyboard data
- **Script to Shot Lists**: Convert film scripts (.txt/.rtf) into detailed cinematographic shot lists
- **Shot Lists to Image Prompts**: Generate detailed Imagen prompts for each shot
- **Prompt Organization**: Convert prompts into structured CSV tables for easy management
- **Data Consolidation**: Merge multiple CSV files into a single consolidated dataset
- **Professional Quality**: Professional cinematography specifications with technical notes
- **Batch Processing**: Process multiple files simultaneously
- **Multilingual Support**: Handles Chinese and English scripts (outputs in English)
- **RTF Support**: Reads both plain text and RTF formatted scripts

## Pipeline Overview

The pipeline consists of 6 modular scripts that can be run independently or in sequence:

1. **`script2shots.py`** - Convert film scripts to detailed shot lists
2. **`shots2prompts_IMGN.py`** - Generate cinematic image prompts from shot lists (Google Imagen format)
3. **`shots2prompts_MJ.py`** - Generate cinematic image prompts from shot lists (Midjourney format)
4. **`prompts2tables.py`** - Convert image prompts to structured CSV tables
5. **`tables_consolidate.py`** - Consolidate multiple CSV files into one dataset
6. **`table2images.py`** - Generate images from prompts in a csv (TODO: RunwayML integration)

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- RunwayML API key (for image generation - future feature)

## Installation

1. Clone or download this repository
2. Install dependencies using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv sync
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
If no API key is found in environment variables, the scripts will prompt you to enter it securely during runtime.

### Character Descriptions (Optional)
Create a `text_files/characters.txt` file with character descriptions to ensure visual consistency across generated image prompts.

## Usage

### Step 1: Script to Shot Lists

Convert film scripts into detailed shot lists:

```bash
python script2shots.py
```

**Features:**
- Supports both `.txt` and `.rtf` script files
- Handles Chinese and English scripts (outputs in English)
- Generates professional cinematographic shot lists
- Interactive file/directory selection
- Batch processing of multiple scripts

**Output:** Detailed shot lists saved to `text_files/shot_lists/`

### Step 2: Shot Lists to Image Prompts

Generate cinematic image prompts from shot lists. Choose between two specialized versions:

#### Option A: Google Imagen Format
```bash
python shots2prompts_IMGN.py
```

**Features:**
- Optimized for Google's Imagen AI image generator
- Detailed photorealistic prompts with technical photography specifications
- Uses comprehensive descriptive format for high-quality cinematic results
- Includes aspect ratio suggestions and film grain effects

#### Option B: Midjourney Format
```bash
python shots2prompts_MJ.py
```

**Features:**
- Optimized for Midjourney AI image generator
- Structured prompt format with specific Midjourney parameters
- Uses cinematic 21:9 aspect ratio (--ar 21:9)
- Includes Midjourney-specific styling parameters (--v 7, --s values)
- Follows Midjourney's recommended prompt structure

**Common Features (Both Versions):**
- Uses character descriptions for visual consistency
- Color palette guidance based on story timeline and location
- Professional cinematic prompt engineering
- Time period-appropriate props, clothing, and vehicles

**Output:** Image prompts saved to `text_files/image_prompts/`

### Step 3: Prompts to Structured Tables

Convert image prompts into organized CSV tables:

```bash
python prompts2tables.py
```

**Features:**
- Parses multiple prompt files simultaneously
- Extracts scene, shot, and prompt data
- Outputs clean CSV format for easy management

**Output:** CSV tables saved to `text_files/image_prompts_tables/`

### Step 4: Consolidate Tables

Merge multiple CSV files into a single consolidated dataset:

```bash
python tables_consolidate.py
```

**Features:**
- Natural alphanumeric sorting of files
- Dynamic column detection
- Handles mismatched columns gracefully

**Output:** Consolidated CSV file (e.g., `consolidated.csv`)

## Project Structure

```
storyboard_gen/
├── script2shots.py           # Script → Shot Lists
├── shots2prompts_IMGN.py     # Shot Lists → Image Prompts (Imagen format)
├── shots2prompts_MJ.py       # Shot Lists → Image Prompts (Midjourney format)
├── prompts2tables.py         # Prompts → CSV Tables
├── tables_consolidate.py     # Consolidate CSV Files
├── table2images.py          # Prompts → Images (TODO)
├── text_files/              # Working directory
│   ├── scripts/             # Input: Film scripts
│   ├── shot_lists/          # Output: Generated shot lists
│   ├── image_prompts/       # Output: Image prompts
│   ├── image_prompts_tables/ # Output: CSV tables
│   └── characters.txt       # Optional: Character descriptions
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## Output Examples

### Shot List Format

```
SCENE 1: KITCHEN - MORNING 1999
Shot 1A: Wide Shot - Static
- Establishing shot of kitchen, natural morning light
- Character enters from left, laughing and excited
- Duration: 3-5 seconds
- Tech notes: Wide angle lens, natural lighting

Shot 1B: Medium Shot - Slight push-in
- Character at coffee machine, looking excited about making coffee
- Dialogue: "Another day begins..."
- Duration: 8-10 seconds
- Tech notes: 50mm lens, focus on hands making coffee
```

### Image Prompt Formats

#### Imagen Format (from shots2prompts_IMGN.py)
```
SCENE 1 - SHOT 1A: KITCHEN - MORNING 1999
Imagen Prompt: "Cinematic wide angle view of a quintessential 1990s kitchen, featuring oak cabinets, subtle patterned linoleum floor, and cereal box on formica countertop. Warm golden morning sunlight streaming through large window, illuminating dust motes. Young woman in oversized flannel shirt enters from left with bright, excited smile. Hyper-realistic film photography, shallow depth of field, warm faded color palette, 35mm film grain, 16:9 aspect ratio."
```

#### Midjourney Format (from shots2prompts_MJ.py)
```
SCENE 1 - SHOT 1A: KITCHEN - MORNING 1999
Image Prompt: "Cinematic wide angle view of quintessential 1990s kitchen, oak cabinets and linoleum floor, ultra-wide 35mm lens, warm golden morning sunlight streaming through window, dust motes dancing in air, young woman in oversized flannel shirt entering from left with bright smile, hyper-realistic film photography, shallow depth of field, warm faded color palette --ar 21:9 --v 7"
```

### CSV Table Format

| Scene | Shot | Prompt |
|-------|------|--------|
| 1 | 1A | Cinematic wide angle view of a quintessential 1990s kitchen... |
| 1 | 1B | Detailed medium shot, 50mm lens perspective, focused on hands... |

## Input Requirements

- **Scripts**: `.txt` or `.rtf` format, properly formatted screenplay text
- **Encoding**: Supports UTF-8 and GBK (for Chinese scripts)
- **Structure**: Scene headers, action descriptions, and dialogue

## Advanced Features

### Color Palette Guidance
The system includes sophisticated color palette guidance based on story timeline:
- **Pre-1940s (US)**: Warm colors emphasizing student life and social status
- **1940s-1950s (China)**: Cold colors reflecting challenging times
- **1969-1973**: Especially cold and gray colors for difficult periods
- **Outside China**: Warm and bright colors (except USSR)
- **Beijing**: Less cold colors for hope and utopian feel
- **Post-1978**: Warmer colors reflecting life improvements

### Character Consistency
- Uses `characters.txt` for consistent character descriptions across all prompts
- Accounts for character aging and appearance changes over time
- Maintains visual continuity throughout the storyboard

## Error Handling

Comprehensive error handling for:
- Missing or invalid API keys
- Unreadable files and encoding issues
- Network connectivity problems
- API rate limits and errors
- File system permissions
- Malformed data formats

## Dependencies

- **google-genai**: Modern Google Gemini API client
- **python-dotenv**: Environment variable management
- **inquirer**: Interactive command-line prompts
- **striprtf**: RTF file format support
- **pandas**: Data manipulation and CSV handling
- **pathlib**: Modern file path handling

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Gemini API key is valid and properly set
2. **No Files Found**: Check that your input directories contain the expected file types
3. **Permission Errors**: Ensure read access to input files and write access to output directories
4. **Rate Limiting**: API rate limits are handled automatically
5. **Encoding Issues**: The scripts handle multiple encodings automatically

### File Organization Tips

- Keep scripts organized in `text_files/scripts/`
- Shot lists are automatically saved to `text_files/shot_lists/`
- Image prompts go to `text_files/image_prompts/`
- CSV tables are saved to `text_files/image_prompts_tables/`

## Future Features

- **Image Generation**: Complete RunwayML API integration for automatic image generation
- **Storyboard Assembly**: Automatic storyboard layout and formatting
- **Video Preview**: Generate video previews from storyboards
- **Export Formats**: Additional export formats (PDF, Final Draft, etc.)

## License

This project is open source. Please ensure you comply with Google's Gemini API terms of service when using this tool.

## Contributing

This is a modular pipeline designed for easy extension. Each script can be run independently or as part of the complete workflow. Contributions welcome for additional features and improvements.
