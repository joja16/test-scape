#!/usr/bin/env python3
"""
Table Data Extractor and Excel Converter
Extracts table data from HTML file and converts to clean Excel format
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
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\/\@\+\=\%\&\#\$]', '', text)
    
    return text.strip()


def extract_table_data(file_path):
    """Extract table data from HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try different encodings
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
            
        # Extract headers from first row
        header_row = rows[0]
        headers = []
        for cell in header_row.find_all(['th', 'td']):
            header_text = clean_text(cell.get_text())
            
            # Handle the complex "Ticket" column that contains status tags
            if 'Ticket' in header_text and len(header_text) > 50:
                # Extract just "Ticket" and the status values
                header_text = "Ticket"
                
            headers.append(header_text)
        
        print(f"Headers found: {headers}")
        
        # Process data rows
        table_data = []
        for row_idx, row in enumerate(rows[1:], 1):  # Skip header row
            cells = row.find_all(['td', 'th'])
            row_data = {}
            
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell_text = clean_text(cell.get_text())
                    
                    # Special handling for status-like cells
                    if i == 1 and ('Open' in cell_text or 'DONE' in cell_text or 'PROGRESS' in cell_text):
                        # Extract individual status values
                        statuses = re.findall(r'\b(Open|IN-PROGRESS|CODE PREVIEW|DONE|qa ready|unreproducible|postpone|QA test passed)\b', cell_text)
                        cell_text = ', '.join(statuses) if statuses else cell_text
                    
                    row_data[headers[i]] = cell_text
            
            if row_data:  # Only add non-empty rows
                table_data.append(row_data)
        
        all_data.extend(table_data)
    
    return all_data


def save_to_excel(data, output_path):
    """Save data to Excel file"""
    if not data:
        print("No data to save")
        return
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Clean column names
    df.columns = [clean_text(str(col)) for col in df.columns]
    
    # Remove completely empty columns
    df = df.dropna(axis=1, how='all')
    
    # Remove completely empty rows
    df = df.dropna(axis=0, how='all')
    
    # Save to Excel with formatting
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Extracted_Data', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Extracted_Data']
        
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
            
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"Data saved to {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Column names: {list(df.columns)}")


def main():
    input_file = r'D:\code\BOT\auto-scrape\docs\data_test.txt'
    output_file = r'D:\code\BOT\auto-scrape\extracted_table_data.xlsx'
    
    print("Starting table extraction...")
    
    try:
        # Extract data from HTML file
        data = extract_table_data(input_file)
        
        print(f"Extracted {len(data)} rows of data")
        
        if data:
            # Display sample data
            print("\nSample data (first 3 rows):")
            for i, row in enumerate(data[:3]):
                print(f"Row {i+1}: {row}")
        
        # Save to Excel
        save_to_excel(data, output_file)
        
        print("[SUCCESS] Table extraction completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()