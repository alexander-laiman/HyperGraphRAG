#!/usr/bin/env python3
"""
Generic script to convert any text file into structured JSON format.
Automatically detects sections, stories, and content boundaries.
"""

import json
import re
import argparse
from typing import Dict, List, Any, Tuple
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove common content markers and special characters
    text = re.sub(r'⟪[^⟫]*⟫', '', text)
    text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)
    return text

def detect_section_patterns(content: str) -> List[Dict[str, Any]]:
    """Automatically detect section boundaries in the text."""
    lines = content.split('\n')
    sections = []
    
    # Common patterns for section headers
    section_patterns = [
        r'^[A-Z][A-Z\s]+$',  # ALL CAPS headers
        r'^[A-Z][a-z\s]+:$',  # Title Case: headers
        r'^Chapter\s+\d+',    # Chapter X
        r'^Part\s+\d+',       # Part X
        r'^Section\s+\d+',    # Section X
        r'^Story\s+\d+',      # Story X
        r'^[A-Z][a-z\s]{10,}$',  # Long title case lines
    ]
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line matches any section pattern
        for pattern in section_patterns:
            if re.match(pattern, line):
                # Look for content start (next non-empty line or after a few lines)
                content_start = i + 1
                while content_start < len(lines) and not lines[content_start].strip():
                    content_start += 1
                
                sections.append({
                    "title": line,
                    "line": i + 1,
                    "start_content": content_start + 1
                })
                break
    
    return sections

def detect_story_boundaries(content: str) -> List[Dict[str, Any]]:
    """Detect story or chapter boundaries using various heuristics."""
    lines = content.split('\n')
    stories = []
    
    # Look for common story/chapter indicators
    story_indicators = [
        r'^[A-Z][a-z\s]{15,}$',  # Long title case lines (likely story titles)
        r'^Chapter\s+\d+',       # Chapter X
        r'^Part\s+\d+',          # Part X
        r'^Story\s+\d+',         # Story X
        r'^[A-Z][A-Z\s]+$',      # ALL CAPS (likely story titles)
    ]
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 10:  # Skip short lines
            continue
            
        # Check if line matches story patterns
        for pattern in story_indicators:
            if re.match(pattern, line):
                # Find where actual content starts (skip empty lines)
                content_start = i + 1
                while content_start < len(lines) and not lines[content_start].strip():
                    content_start += 1
                
                # Only consider it a story if there's substantial content after
                if content_start < len(lines) - 10:  # At least 10 lines of content
                    stories.append({
                        "title": line,
                        "line": i + 1,
                        "start_content": content_start + 1
                    })
                break
    
    return stories

def extract_content_sections(content: str) -> List[Dict[str, Any]]:
    """Extract all content sections from the book using automatic detection."""
    lines = content.split('\n')
    
    # Try to detect stories/chapters first
    stories = detect_story_boundaries(content)
    
    # If no stories detected, try general sections
    if not stories:
        stories = detect_section_patterns(content)
    
    # If still no sections, create a single section for the entire content
    if not stories:
        return [{
            "type": "content",
            "title": "Full Content",
            "content": clean_text(content),
            "start_line": 1,
            "end_line": len(lines),
            "word_count": len(clean_text(content).split()),
            "character_count": len(clean_text(content))
        }]
    
    sections = []
    
    # Process each detected section
    for i, story in enumerate(stories):
        start_line = story["start_content"] - 1  # Convert to 0-based index
        
        # Find the end line (start of next section or end of file)
        if i < len(stories) - 1:
            end_line = stories[i + 1]["start_content"] - 1
        else:
            end_line = len(lines)
        
        # Extract content
        story_lines = lines[start_line:end_line]
        story_content = '\n'.join(story_lines)
        
        # Clean the content
        cleaned_content = clean_text(story_content)
        
        # Skip sections with very little content
        if len(cleaned_content.split()) < 50:
            continue
        
        sections.append({
            "type": "story",
            "title": story["title"],
            "content": cleaned_content,
            "start_line": start_line + 1,
            "end_line": end_line,
            "word_count": len(cleaned_content.split()),
            "character_count": len(cleaned_content)
        })
    
    return sections

def create_book_metadata(input_file: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create metadata for the book based on filename and content analysis."""
    file_path = Path(input_file)
    
    # Extract basic info from filename
    title = file_path.stem.replace('_', ' ').title()
    
    return {
        "title": title,
        "source_file": input_file,
        "total_sections": len(sections),
        "stories": len([s for s in sections if s["type"] == "story"]),
        "conversion_date": "2024",
        "conversion_notes": "Converted from text format to structured JSON using automatic section detection"
    }

def convert_book_to_json(input_file: str, output_file: str) -> None:
    """Convert any text file to structured JSON format."""
    
    print(f"Reading text from: {input_file}")
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(input_file, 'r', encoding='latin-1') as f:
            content = f.read()
    
    print("Analyzing content structure...")
    
    # Extract sections using automatic detection
    sections = extract_content_sections(content)
    
    # Create book metadata
    metadata = create_book_metadata(input_file, sections)
    
    # Create the final JSON structure
    book_json = {
        "metadata": metadata,
        "sections": sections,
        "statistics": {
            "total_sections": len(sections),
            "stories": len([s for s in sections if s["type"] == "story"]),
            "total_words": sum(s["word_count"] for s in sections),
            "total_characters": sum(s["character_count"] for s in sections)
        }
    }
    
    print(f"Writing structured JSON to: {output_file}")
    
    # Write the JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(book_json, f, indent=2, ensure_ascii=False)
    
    print("Conversion completed successfully!")
    print(f"Total sections processed: {len(sections)}")
    print(f"Total words: {book_json['statistics']['total_words']}")
    print(f"Total characters: {book_json['statistics']['total_characters']}")

def main():
    """Main function to run the conversion."""
    parser = argparse.ArgumentParser(description='Convert any text file to structured JSON format')
    parser.add_argument('input_file', help='Input text file to convert')
    parser.add_argument('-o', '--output', help='Output JSON file (default: input_file_structured.json)')
    parser.add_argument('--individual', action='store_true', help='Create individual section files')
    
    args = parser.parse_args()
    
    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.input_file)
        output_file = f"{input_path.stem}_structured.json"
    
    try:
        convert_book_to_json(args.input_file, output_file)
        
        # Create individual section files if requested
        if args.individual:
            print("\nCreating individual section files...")
            with open(output_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            for section in book_data["sections"]:
                # Create a safe filename
                safe_title = re.sub(r'[^\w\s-]', '', section["title"])
                safe_title = re.sub(r'[-\s]+', '_', safe_title)
                section_file = f"section_{safe_title}.json"
                
                with open(section_file, 'w', encoding='utf-8') as f:
                    json.dump(section, f, indent=2, ensure_ascii=False)
                
                print(f"Created: {section_file}")
        
        print(f"\nConversion completed!")
        print(f"Main structured file: {output_file}")
        if args.individual:
            print(f"Individual section files: section_*.json")
        
    except FileNotFoundError:
        print(f"Error: Could not find input file '{args.input_file}'")
        print("Please make sure the file exists and the path is correct.")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

if __name__ == "__main__":
    main()