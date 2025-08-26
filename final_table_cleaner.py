#!/usr/bin/env python3
"""
Final Table Data Cleaner
Takes the extracted data and applies comprehensive cleaning and correction
"""

import pandas as pd
import re


def parse_ticket_info(text):
    """Parse ticket information from mixed content"""
    if not text:
        return {'ticket_id': '', 'title': '', 'status': ''}
    
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
    
    # Extract status from the text
    status_patterns = [
        r'\b(Done|DONE)\b',
        r'\b(Open)\b',
        r'\b(IN-PROGRESS)\b',
        r'\b(unreproducible)\b',
        r'\b(postpone)\b',
        r'\b(CANCELLED)\b',
        r'\b(CODE PREVIEW)\b'
    ]
    
    status = ''
    for pattern in status_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            status = match.group(1).upper()
            break
    
    # Extract title (everything after ticket ID, before status)
    title = text
    if ticket_id:
        title = re.sub(rf'{re.escape(ticket_id)}:?\s*', '', title, 1)
    if status:
        title = re.sub(rf'\s*{re.escape(status)}\s*$', '', title, flags=re.IGNORECASE)
    
    # Clean up title
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'^[\[\]\s\-:]+|[\[\]\s\-:]+$', '', title)
    
    return {
        'ticket_id': ticket_id,
        'title': title[:100] if title else '',  # Limit title length
        'status': status
    }


def parse_pic_info(text):
    """Parse PIC information"""
    if not text:
        return ''
    
    # Look for @username pattern
    username_match = re.search(r'(@\w+(?:\s+\w+)*)', text)
    if username_match:
        return username_match.group(1)
    
    # Check for specific patterns
    if text in ['iOS', 'General', 'Bug Fix', 'Technical Improvement']:
        return text
    
    # If it's clearly a ticket description, return empty
    if re.search(r'[A-Z]+-\d+:', text) or len(text) > 30:
        return ''
    
    return text


def clean_excel_data():
    """Clean the extracted Excel data"""
    input_file = r'D:\code\BOT\auto-scrape\cleaned_table_data.xlsx'
    output_file = r'D:\code\BOT\auto-scrape\final_cleaned_data.xlsx'
    
    # Read the data
    df = pd.read_excel(input_file)
    print(f"Loaded {len(df)} rows from {input_file}")
    
    # Create new cleaned dataset
    cleaned_records = []
    
    for idx, row in df.iterrows():
        pic_raw = str(row.get('PIC', '')) if pd.notna(row.get('PIC')) else ''
        ticket_raw = str(row.get('Ticket Open IN-PROGRESS CODE PREVIEW DONE qa ready unreproducible postpone QA test passed', '')) if pd.notna(row.get('Ticket Open IN-PROGRESS CODE PREVIEW DONE qa ready unreproducible postpone QA test passed')) else ''
        story_points = row.get('Story Points', '')
        status_raw = str(row.get('Status', '')) if pd.notna(row.get('Status')) else ''
        remark = str(row.get('Remark: Explanation for the undone ticket', '')) if pd.notna(row.get('Remark: Explanation for the undone ticket')) else ''
        committed_points = row.get('Committed Story Points', '')
        capacity = row.get('Capacity in a sprint', '')
        actual_completed = row.get('Actual Completed', '')
        
        # Determine where the real ticket info is
        ticket_info = None
        pic_info = ''
        
        # Case 1: Ticket info is in PIC column
        if re.search(r'[A-Z]+-\d+:', pic_raw):
            ticket_info = parse_ticket_info(pic_raw)
            # Try to extract PIC from ticket column
            pic_info = parse_pic_info(ticket_raw)
        
        # Case 2: Normal structure
        elif ticket_raw and not re.search(r'^\d+$', ticket_raw):
            ticket_info = parse_ticket_info(ticket_raw)
            pic_info = parse_pic_info(pic_raw)
        
        # Case 3: Just numeric values in ticket column (story points?)
        else:
            ticket_info = {'ticket_id': '', 'title': ticket_raw if ticket_raw else '', 'status': ''}
            pic_info = parse_pic_info(pic_raw)
        
        # Determine status from multiple sources
        final_status = ''
        if ticket_info and ticket_info['status']:
            final_status = ticket_info['status']
        elif story_points and story_points in ['DONE', 'Open', 'unreproducible']:
            final_status = str(story_points).upper()
        elif status_raw:
            final_status = status_raw
        
        # Clean story points (should be numeric)
        clean_story_points = ''
        if story_points and str(story_points).isdigit():
            clean_story_points = int(story_points)
        elif ticket_raw and str(ticket_raw).isdigit():
            clean_story_points = int(ticket_raw)
        
        # Build clean record
        clean_record = {
            'PIC': pic_info,
            'Ticket_ID': ticket_info['ticket_id'] if ticket_info else '',
            'Ticket_Title': ticket_info['title'] if ticket_info else '',
            'Story_Points': clean_story_points,
            'Status': final_status,
            'Remark': remark,
            'Committed_Story_Points': committed_points if pd.notna(committed_points) else '',
            'Capacity_in_Sprint': capacity if pd.notna(capacity) else '',
            'Actual_Completed': actual_completed if pd.notna(actual_completed) else ''
        }
        
        # Only add if there's meaningful content
        if any([clean_record['PIC'], clean_record['Ticket_ID'], clean_record['Ticket_Title']]):
            cleaned_records.append(clean_record)
    
    # Create new DataFrame
    final_df = pd.DataFrame(cleaned_records)
    
    # Final cleanup
    final_df = final_df.replace('', pd.NA)  # Replace empty strings with NA
    final_df = final_df.dropna(how='all')  # Drop completely empty rows
    
    # Convert numeric columns
    numeric_cols = ['Story_Points', 'Committed_Story_Points', 'Capacity_in_Sprint', 'Actual_Completed']
    for col in numeric_cols:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
    
    # Save to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        final_df.to_excel(writer, sheet_name='Final_Cleaned_Data', index=False)
        
        # Format the worksheet
        workbook = writer.book
        worksheet = writer.sheets['Final_Cleaned_Data']
        
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
            
            adjusted_width = min(max_length + 2, 70)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Format header row
        from openpyxl.styles import Font, PatternFill, Alignment
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
    
    print(f"\n=== Final Results ===")
    print(f"Total cleaned rows: {len(final_df)}")
    print(f"Data saved to: {output_file}")
    
    # Show summary statistics
    print(f"\nColumn completeness:")
    for col in final_df.columns:
        non_null_count = final_df[col].notna().sum()
        percentage = (non_null_count / len(final_df)) * 100
        print(f"  {col}: {non_null_count}/{len(final_df)} ({percentage:.1f}%)")
    
    if 'Status' in final_df.columns:
        print(f"\nStatus distribution:")
        status_counts = final_df['Status'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
    
    if 'PIC' in final_df.columns:
        print(f"\nTop 5 PICs:")
        pic_counts = final_df['PIC'].value_counts()
        for pic, count in pic_counts.head().items():
            print(f"  {pic}: {count}")
    
    # Show sample of final data
    print(f"\n=== Sample Final Data ===")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(final_df.head(3).to_string())
    
    return final_df


if __name__ == "__main__":
    try:
        df = clean_excel_data()
        print("\n[SUCCESS] Data cleaning completed successfully!")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()