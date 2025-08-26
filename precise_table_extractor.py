#!/usr/bin/env python3
"""
Precise Table Data Extractor
Extracts exact Story Points, Status, and Remark data based on identified HTML structure
"""

import re
import pandas as pd
from bs4 import BeautifulSoup
import html


def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\/\@\+\=\%\&\#\$\[\]\'\"]+', ' ', text)
    return text.strip()


def parse_ticket_info(text):
    """Parse ticket ID and description from ticket text"""
    if not text:
        return {'ticket_id': '', 'description': ''}
    
    # Look for ticket ID patterns
    ticket_patterns = [
        r'(IOS-\d+)',
        r'(QA-\d+)', 
        r'([A-Z]+-\d+)'
    ]
    
    ticket_id = ''
    for pattern in ticket_patterns:
        match = re.search(pattern, text)
        if match:
            ticket_id = match.group(1)
            break
    
    # Extract description (everything after ticket ID)
    description = text
    if ticket_id:
        description = re.sub(rf'{re.escape(ticket_id)}:\s*', '', description, 1)
    
    # Remove status words from description
    status_words = ['Done', 'DONE', 'Open', 'IN-PROGRESS', 'unreproducible', 'Cancelled', 'qa ready']
    for status in status_words:
        description = re.sub(rf'\s*{re.escape(status)}\s*$', '', description, flags=re.IGNORECASE)
    
    description = clean_text(description)
    
    return {
        'ticket_id': ticket_id,
        'description': description
    }


def extract_precise_table_data(file_path):
    """Extract table data with precise column mapping"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    
    all_records = []
    current_category = ''
    current_pic = ''
    pic_committed_points = ''
    pic_capacity = ''
    pic_actual_completed = ''
    
    # Use the second table which has the data
    if len(tables) < 2:
        print("Not enough tables found")
        return []
    
    table = tables[1]
    rows = table.find_all('tr')[1:]  # Skip header row
    
    print(f"Processing {len(rows)} data rows...")
    
    for row_idx, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        cell_count = len(cells)
        
        if cell_count == 0:
            continue
            
        # Extract cell texts
        cell_texts = []
        for cell in cells:
            text = clean_text(cell.get_text())
            cell_texts.append(text)
        
        # Pattern matching based on cell count
        if cell_count == 1 or cell_count == 2:
            # Category row (e.g., "iOS", "General")
            current_category = cell_texts[0]
            print(f"Found category: {current_category}")
            
        elif cell_count == 7:
            # PIC row with full info
            # Format: PIC | Ticket_Type | Empty | Empty | Remark/Points | Committed | Capacity | Actual
            current_pic = cell_texts[0]
            ticket_type = cell_texts[1]
            pic_committed_points = cell_texts[5] if len(cell_texts) > 5 else ''
            pic_capacity = cell_texts[6] if len(cell_texts) > 6 else ''
            pic_actual_completed = cell_texts[7] if len(cell_texts) > 7 else ''
            
            print(f"Found PIC: {current_pic}, Type: {ticket_type}, Committed: {pic_committed_points}, Capacity: {pic_capacity}")
            
            # Create a record for PIC summary if it has meaningful data
            if pic_committed_points or pic_capacity:
                record = {
                    'Category': current_category,
                    'PIC': current_pic,
                    'Ticket_ID': '',
                    'Ticket_Description': ticket_type,
                    'Story_Points': '',
                    'Status': '',
                    'Remark': '',
                    'Committed_Story_Points': pic_committed_points,
                    'Capacity_in_Sprint': pic_capacity,
                    'Actual_Completed': pic_actual_completed
                }
                all_records.append(record)
            
        elif cell_count == 4:
            # Ticket row with exact data
            # Format: Ticket_Description | Story_Points | Status | Remark
            ticket_text = cell_texts[0]
            story_points = cell_texts[1]
            status = cell_texts[2]
            remark = cell_texts[3] if len(cell_texts) > 3 else ''
            
            # Parse ticket information
            ticket_info = parse_ticket_info(ticket_text)
            
            # Clean story points (should be numeric)
            clean_story_points = ''
            if story_points and story_points.isdigit():
                clean_story_points = int(story_points)
            
            # Create record
            record = {
                'Category': current_category,
                'PIC': current_pic,
                'Ticket_ID': ticket_info['ticket_id'],
                'Ticket_Description': ticket_info['description'],
                'Story_Points': clean_story_points,
                'Status': status,
                'Remark': remark,
                'Committed_Story_Points': '',
                'Capacity_in_Sprint': '',
                'Actual_Completed': ''
            }
            
            all_records.append(record)
            print(f"Added ticket: {ticket_info['ticket_id']} | Points: {clean_story_points} | Status: {status} | Remark: {remark}")
            
        elif cell_count == 3:
            # Sometimes category is in 3-cell format
            current_category = cell_texts[0]
            print(f"Found category (3-cell): {current_category}")
        
        else:
            print(f"Unhandled row structure with {cell_count} cells: {cell_texts}")
    
    print(f"Total records extracted: {len(all_records)}")
    return all_records


def save_precise_excel(records, output_path):
    """Save precisely extracted data to Excel"""
    if not records:
        print("No records to save")
        return
    
    df = pd.DataFrame(records)
    
    # Remove empty rows
    df = df.dropna(axis=0, how='all')
    
    # Convert numeric columns
    numeric_columns = ['Story_Points', 'Committed_Story_Points', 'Capacity_in_Sprint', 'Actual_Completed']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Save with formatting
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Precise_Data', index=False)
        
        # Format worksheet
        workbook = writer.book
        worksheet = writer.sheets['Precise_Data']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
                except:
                    pass
            
            adjusted_width = min(max_length + 3, 80)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Format header
        from openpyxl.styles import Font, PatternFill, Alignment
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
    
    return df


def get_file_paths():
    """Get input and output file paths from user input"""
    print("=== PRECISE TABLE DATA EXTRACTOR ===")
    print("This tool extracts exact Story Points, Status, and Remark data from HTML tables.")
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
        output_file = input("Enter the path for the Excel output file (e.g., extracted_data.xlsx): ").strip()
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
        
        print("\n=== STARTING PRECISE TABLE EXTRACTION ===")
        
        # Extract with precise mapping
        records = extract_precise_table_data(input_file)
        
        # Save to Excel
        df = save_precise_excel(records, output_file)
        
        if df is not None:
            print(f"\n=== EXTRACTION RESULTS ===")
            print(f"Total records: {len(df)}")
            print(f"Output file: {output_file}")
            
            # Show data completeness
            print(f"\n=== DATA COMPLETENESS ===")
            for col in df.columns:
                non_null = df[col].notna().sum()
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                print(f"{col}: {non_empty}/{len(df)} ({(non_empty/len(df)*100):.1f}%)")
            
            # Show Story Points statistics
            if 'Story_Points' in df.columns:
                story_points = df['Story_Points'].dropna()
                if len(story_points) > 0:
                    print(f"\n=== STORY POINTS STATS ===")
                    print(f"Total tickets with story points: {len(story_points)}")
                    print(f"Total story points: {story_points.sum()}")
                    print(f"Average story points: {story_points.mean():.1f}")
                    print(f"Story points distribution:")
                    for points, count in story_points.value_counts().sort_index().items():
                        print(f"  {points} points: {count} tickets")
            
            # Show Status distribution
            if 'Status' in df.columns:
                status_counts = df['Status'].value_counts()
                print(f"\n=== STATUS DISTRIBUTION ===")
                for status, count in status_counts.items():
                    print(f"  {status}: {count}")
            
            # Show sample data
            print(f"\n=== SAMPLE DATA (First 5 rows) ===")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            print(df.head().to_string())
            
        print("\n[SUCCESS] Precise extraction completed!")
        print(f"Final output saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n[CANCELLED] Operation cancelled by user.")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()