#!/usr/bin/env python3
"""
Improved Table Data Extractor and Excel Converter
Handles complex HTML table structures and cleans data properly
"""

import re
import pandas as pd
from bs4 import BeautifulSoup
import html


def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up special characters but preserve important ones
    text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\/\@\+\=\%\&\#\$\[\]\'\"]+', ' ', text)
    
    return text.strip()


def extract_table_data_improved(file_path):
    """Extract table data from HTML file with improved parsing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Could not decode file with any supported encoding")
    
    # Parse HTML content
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    
    all_data = []
    
    for table_idx, table in enumerate(tables):
        print(f"Processing table {table_idx + 1}...")
        
        rows = table.find_all('tr')
        if not rows:
            continue
            
        # Extract headers - look for the header row more carefully
        headers = []
        header_row = None
        
        # Find the row with proper headers
        for row in rows:
            cells = row.find_all(['th', 'td'])
            potential_headers = []
            for cell in cells:
                text = clean_text(cell.get_text())
                if text and any(keyword in text.upper() for keyword in ['PIC', 'TICKET', 'STORY', 'STATUS', 'REMARK', 'COMMITTED', 'CAPACITY', 'ACTUAL']):
                    potential_headers.append(text)
            
            if len(potential_headers) >= 6:  # Should have at least 6 main columns
                headers = potential_headers
                header_row = row
                break
        
        if not headers:
            # Fallback to first row
            header_row = rows[0]
            for cell in header_row.find_all(['th', 'td']):
                text = clean_text(cell.get_text())
                if 'Ticket' in text and len(text) > 20:
                    text = 'Ticket'  # Simplify complex ticket header
                headers.append(text if text else f"Column_{len(headers)}")
        
        print(f"Final headers: {headers}")
        
        # Find data rows (skip header rows)
        data_rows = []
        header_found = False
        
        for row in rows:
            if row == header_row:
                header_found = True
                continue
            
            if not header_found:
                continue
                
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:  # Should have at least 3 cells to be a data row
                data_rows.append(row)
        
        print(f"Found {len(data_rows)} data rows")
        
        # Process data rows
        for row_idx, row in enumerate(data_rows):
            cells = row.find_all(['td', 'th'])
            row_data = {}
            
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell_text = clean_text(cell.get_text())
                    
                    # Special processing for different columns
                    if i == 1 and headers[i].upper() == 'TICKET':  # Ticket column
                        # Look for ticket IDs and status information
                        ticket_match = re.search(r'(IOS-\d+|[A-Z]+-\d+)', cell_text)
                        if ticket_match:
                            cell_text = ticket_match.group(1)
                        elif 'Bug Fix' in cell_text:
                            cell_text = 'Bug Fix'
                        elif 'General' in cell_text:
                            cell_text = 'General'
                    
                    elif 'STATUS' in headers[i].upper() or i == 3:  # Status column
                        # Extract status keywords
                        statuses = re.findall(r'\b(Open|IN-PROGRESS|DONE|unreproducible|postpone|CANCELLED|CODE PREVIEW|QA test passed|qa ready)\b', cell_text, re.IGNORECASE)
                        if statuses:
                            cell_text = ', '.join(set(statuses))  # Remove duplicates
                    
                    elif 'STORY' in headers[i].upper() and 'POINTS' in headers[i].upper():  # Story Points
                        # Extract numeric values
                        numbers = re.findall(r'\b(\d+)\b', cell_text)
                        if numbers:
                            cell_text = numbers[0]
                    
                    row_data[headers[i]] = cell_text if cell_text else ""
                    
            # Only add rows that have meaningful content
            if any(value.strip() for value in row_data.values()):
                # Try to fix misaligned data
                if len(row_data) > 0:
                    all_data.append(row_data)
    
    return all_data


def post_process_data(data):
    """Post-process extracted data to fix common issues"""
    cleaned_data = []
    
    for row in data:
        cleaned_row = {}
        
        # Fix common column misalignments
        for key, value in row.items():
            if not value:
                continue
                
            # If PIC column contains ticket info, try to redistribute
            if key.upper() == 'PIC' and ('IOS-' in value or len(value) > 50):
                # This looks like ticket description, move it
                if 'Ticket' in row and not row['Ticket']:
                    cleaned_row['Ticket'] = value
                    # Extract PIC from the beginning if present
                    pic_match = re.match(r'^(@\w+)', value)
                    if pic_match:
                        cleaned_row['PIC'] = pic_match.group(1)
                    else:
                        cleaned_row['PIC'] = ''
                else:
                    cleaned_row[key] = value
            else:
                cleaned_row[key] = value
        
        # Ensure all expected columns exist
        expected_columns = ['PIC', 'Ticket', 'Story Points', 'Status', 'Remark: Explanation for the undone ticket', 
                          'Committed Story Points', 'Capacity in a sprint', 'Actual Completed']
        
        for col in expected_columns:
            if col not in cleaned_row:
                cleaned_row[col] = ""
        
        cleaned_data.append(cleaned_row)
    
    return cleaned_data


def save_to_excel_improved(data, output_path):
    """Save data to Excel file with improved formatting"""
    if not data:
        print("No data to save")
        return
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Reorder columns in logical order
    column_order = ['PIC', 'Ticket', 'Story Points', 'Status', 'Remark: Explanation for the undone ticket', 
                   'Committed Story Points', 'Capacity in a sprint', 'Actual Completed']
    
    # Only include columns that exist in the data
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    
    # Clean up data types
    numeric_columns = ['Story Points', 'Committed Story Points', 'Capacity in a sprint', 'Actual Completed']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove completely empty rows
    df = df.dropna(axis=0, how='all')
    
    # Save to Excel with formatting
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Cleaned_Data']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 60)  # Cap at 60 characters
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Add header formatting
        from openpyxl.styles import Font, PatternFill
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
    
    print(f"Data saved to {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    return df


def get_file_paths():
    """Get input and output file paths from user input"""
    print("=== Table Data Extractor ===")
    print("Please provide the file paths for table extraction:\n")
    
    # Get input file path
    while True:
        input_file = input("Enter the path to the HTML input file: ").strip()
        if not input_file:
            print("Input file path cannot be empty. Please try again.")
            continue
        
        # Remove quotes if present
        input_file = input_file.strip('"\'')
        
        # Check if file exists
        import os
        if not os.path.exists(input_file):
            print(f"File not found: {input_file}")
            print("Please check the path and try again.")
            continue
        
        break
    
    # Get output file path
    while True:
        output_file = input("Enter the path for the Excel output file (e.g., output.xlsx): ").strip()
        if not output_file:
            print("Output file path cannot be empty. Please try again.")
            continue
        
        # Remove quotes if present
        output_file = output_file.strip('"\'')
        
        # Add .xlsx extension if not present
        if not output_file.lower().endswith('.xlsx'):
            output_file += '.xlsx'
        
        # Check if directory exists
        import os
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            print(f"Directory not found: {output_dir}")
            create_dir = input("Would you like to create this directory? (y/n): ").strip().lower()
            if create_dir == 'y':
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    print(f"Directory created: {output_dir}")
                except Exception as e:
                    print(f"Failed to create directory: {e}")
                    continue
            else:
                continue
        
        break
    
    return input_file, output_file


def main():
    import sys
    
    try:
        # Check if command line arguments are provided
        if len(sys.argv) == 3:
            input_file = sys.argv[1]
            output_file = sys.argv[2]
            
            # Validate input file exists
            import os
            if not os.path.exists(input_file):
                print(f"Error: Input file not found: {input_file}")
                return
            
            # Add .xlsx extension if not present
            if not output_file.lower().endswith('.xlsx'):
                output_file += '.xlsx'
            
            print(f"Using command line arguments:")
            print(f"Input file: {input_file}")
            print(f"Output file: {output_file}")
        else:
            # Get file paths from user input
            input_file, output_file = get_file_paths()
            
            print(f"\nInput file: {input_file}")
            print(f"Output file: {output_file}")
        
        print("\nStarting improved table extraction...")
        
        # Extract data from HTML file
        raw_data = extract_table_data_improved(input_file)
        print(f"Extracted {len(raw_data)} raw rows")
        
        # Post-process data
        cleaned_data = post_process_data(raw_data)
        print(f"Cleaned to {len(cleaned_data)} rows")
        
        if cleaned_data:
            # Display sample data
            print("\nSample cleaned data (first 5 rows):")
            for i, row in enumerate(cleaned_data[:5]):
                print(f"Row {i+1}:")
                for key, value in row.items():
                    if value:  # Only show non-empty values
                        print(f"  {key}: {value}")
                print()
        
        # Save to Excel
        df = save_to_excel_improved(cleaned_data, output_file)
        
        # Show summary statistics
        print("\n=== Data Summary ===")
        print(f"Total rows with data: {len(df)}")
        
        # Count by status
        if 'Status' in df.columns:
            status_counts = df['Status'].value_counts()
            print("\nStatus distribution:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
        
        # Count by PIC
        if 'PIC' in df.columns:
            pic_counts = df['PIC'].value_counts()
            print(f"\nTop PICs:")
            for pic, count in pic_counts.head().items():
                print(f"  {pic}: {count}")
        
        print("\n[SUCCESS] Table extraction completed successfully!")
        print(f"Output saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n[CANCELLED] Operation cancelled by user.")
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()