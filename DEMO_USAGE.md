# Table Extractor - Demo Usage Examples

## ✅ Successfully Updated Scripts

Both table extraction scripts now support **manual file input** instead of hard-coded paths!

## 🚀 Quick Start Examples

### Method 1: Command Line Arguments (Fastest)

```bash
# Basic extraction
python improved_table_extractor.py "input.html" "output.xlsx"

# Precise extraction with exact Story Points/Status/Remark data  
python precise_table_extractor.py "data.txt" "results.xlsx"

# Full paths example
python precise_table_extractor.py "D:\data\table_data.txt" "C:\results\extracted.xlsx"
```

### Method 2: Interactive Prompts

```bash
# Just run the script - it will ask for file paths
python improved_table_extractor.py

# Output example:
=== Table Data Extractor ===
Please provide the file paths for table extraction:

Enter the path to the HTML input file: D:\code\BOT\auto-scrape\docs\data_test.txt
Enter the path for the Excel output file: my_results.xlsx
```

## 📊 Real Demo Results

### Test Run Results:
```
Using command line arguments:
Input file: D:\code\BOT\auto-scrape\docs\data_test.txt
Output file: precise_manual_test.xlsx

=== EXTRACTION RESULTS ===
Total records: 136
✅ Story_Points: 101/136 tickets (74.3%)  
✅ Status: 120/136 tickets (88.2%)
✅ Remark: 21/136 tickets (15.4%)

Story Points Distribution:
- 0 points: 38 tickets
- 1 point: 37 tickets  
- 2 points: 19 tickets
- 3-5 points: 7 tickets

Status Distribution:
- DONE: 70 tickets
- CODE PREVIEW: 15 tickets
- qa ready: 13 tickets
- Open: 11 tickets
- IN-PROGRESS: 6 tickets
```

## 📁 File Path Examples

### Windows Paths
```bash
# With spaces (use quotes)
"C:\Users\John Doe\Documents\data.html"
"D:\Project Files\table_data.txt"

# Simple paths
D:\data\input.html
C:\results\output.xlsx
```

### Relative Paths
```bash
# Current directory
python script.py "data.html" "results.xlsx"

# Subdirectories  
python script.py "docs/data_test.txt" "output/results.xlsx"
```

## 🔧 Features Added

### ✅ Smart Path Handling
- Automatically removes quotes from file paths
- Validates input file exists before processing
- Auto-adds .xlsx extension to output files
- Creates output directories if needed

### ✅ Flexible Usage
- Command line arguments for automation
- Interactive prompts for manual use  
- Error handling for invalid paths
- Graceful cancellation (Ctrl+C)

### ✅ User-Friendly Prompts
- Clear instructions for file input
- File existence validation
- Directory creation assistance
- Progress feedback during extraction

## 🎯 Choose Your Script

### Use `improved_table_extractor.py` for:
- General HTML table extraction
- Basic data cleaning and formatting
- Standard table conversion tasks

### Use `precise_table_extractor.py` for:
- **Exact Story Points extraction** (101 tickets with precise values)
- **Accurate Status mapping** (DONE, Open, IN-PROGRESS, etc.)
- **Proper Remark field extraction**
- Project management data with detailed statistics

## 🚀 Ready to Use!

Both scripts are now fully updated with manual input capabilities. No more hard-coded file paths!