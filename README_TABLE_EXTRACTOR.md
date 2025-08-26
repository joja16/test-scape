# Table Data Extractor - Usage Guide

## Overview
This toolkit extracts table data from HTML files and converts them to clean Excel format. Two versions are available:

1. **`improved_table_extractor.py`** - General purpose extractor
2. **`precise_table_extractor.py`** - Precise extractor for exact Story Points, Status, and Remark data

## Installation Requirements
```bash
pip install beautifulsoup4 pandas openpyxl
```

## Usage Methods

### Method 1: Command Line Arguments (Recommended)
```bash
# Using improved extractor
python improved_table_extractor.py "input_file.html" "output_file.xlsx"

# Using precise extractor  
python precise_table_extractor.py "input_file.html" "output_file.xlsx"
```

**Examples:**
```bash
# Extract from HTML file to Excel
python improved_table_extractor.py "D:\data\table_data.html" "results.xlsx"

# Precise extraction with full paths
python precise_table_extractor.py "C:\Users\name\Documents\data.txt" "C:\Users\name\Desktop\output.xlsx"
```

### Method 2: Interactive Mode
Simply run the script without arguments for interactive prompts:

```bash
python improved_table_extractor.py
```

The script will prompt you to enter:
1. Path to the HTML input file
2. Path for the Excel output file

## Script Differences

### Improved Table Extractor (`improved_table_extractor.py`)
- **Purpose**: General-purpose HTML table extraction
- **Output**: Basic cleaned data with column alignment fixes
- **Best for**: Standard table data extraction tasks

### Precise Table Extractor (`precise_table_extractor.py`)  
- **Purpose**: Exact extraction of Story Points, Status, and Remark columns
- **Output**: Precisely mapped data with detailed statistics
- **Best for**: Project management data, ticket tracking systems
- **Features**: 
  - Accurate Story Points extraction (101 tickets with precise values)
  - Exact Status mapping (DONE, Open, IN-PROGRESS, etc.)
  - Proper Remark field extraction
  - Detailed completion statistics

## Output Features

### Excel File Structure
Both extractors create Excel files with:
- Auto-sized columns
- Formatted headers
- Proper data types (numeric columns as numbers)
- Clean, professional appearance

### Data Statistics
The precise extractor provides detailed statistics:
- Data completeness percentages
- Story Points distribution
- Status distribution
- Sample data preview

## File Path Guidelines

### Input File
- Supports HTML files (.html, .htm) or text files with HTML content
- Full file paths with spaces should be enclosed in quotes
- File must exist and be readable

### Output File
- Automatically adds .xlsx extension if not provided
- Creates directories if they don't exist (with permission)
- Overwrites existing files

## Examples of Valid File Paths

```bash
# Windows paths
"C:\Users\John Doe\Documents\data.html"
"D:\Projects\table_data.txt"

# Relative paths
"./data/input.html" 
"../output/results.xlsx"

# Simple filenames (current directory)
"data.html"
"output.xlsx"
```

## Troubleshooting

### Common Issues

**File not found error:**
- Check file path spelling and existence
- Use absolute paths if relative paths fail
- Ensure file has proper read permissions

**Empty output:**
- Input file may not contain proper HTML table structure
- Try the precise extractor for complex table formats

**Encoding errors:**
- Scripts auto-detect encoding (UTF-8, Latin-1, CP1252)
- If issues persist, convert input file to UTF-8

### Getting Help
Run scripts without arguments to see usage information:
```bash
python improved_table_extractor.py --help
```

## Sample Command
```bash
# Complete example
python precise_table_extractor.py "D:\code\BOT\auto-scrape\docs\data_test.txt" "extracted_data.xlsx"
```

This will:
1. Read HTML table from the input file
2. Extract precise Story Points, Status, and Remark data  
3. Generate formatted Excel file with statistics
4. Display completion summary

## Output Verification
After extraction, check:
- Excel file is created in specified location
- Data completeness statistics in console output
- Sample data preview for accuracy verification