"""
Keyword input validation and processing module.
"""
import csv
import os
from pathlib import Path
from typing import List, Union
import typer


def validate_keywords(keywords: List[str]) -> List[str]:
    """
    Validate and clean keyword list.
    
    Args:
        keywords: List of raw keyword strings
        
    Returns:
        List of cleaned, validated keywords
        
    Raises:
        ValueError: If no valid keywords found
    """
    cleaned_keywords = []
    
    for keyword in keywords:
        # Strip whitespace and convert to lowercase
        clean_keyword = keyword.strip().lower()
        
        # Skip empty keywords
        if not clean_keyword:
            continue
            
        # Skip keywords that are too short or too long
        if len(clean_keyword) < 2 or len(clean_keyword) > 100:
            continue
            
        cleaned_keywords.append(clean_keyword)
    
    if not cleaned_keywords:
        raise ValueError("No valid keywords found. Keywords must be 2-100 characters long.")
    
    if len(cleaned_keywords) > 15:
        typer.echo(f"Warning: {len(cleaned_keywords)} keywords provided. Consider limiting to 15 for better performance.")
    
    return cleaned_keywords


def load_keywords_from_file(file_path: Union[str, Path]) -> List[str]:
    """
    Load keywords from a text or CSV file.
    
    Args:
        file_path: Path to the keywords file
        
    Returns:
        List of keywords
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported or contains no valid keywords
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Keywords file not found: {file_path}")
    
    keywords = []
    
    try:
        if file_path.suffix.lower() == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers_skipped = False
                for row in reader:
                    if row:  # Skip empty rows
                        # Skip header row if it looks like a header
                        if not headers_skipped and row[0].lower() in ['keyword', 'keywords', 'term', 'query']:
                            headers_skipped = True
                            continue
                        keywords.append(row[0])  # Take first column
        else:
            # Treat as plain text file
            with open(file_path, 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f if line.strip()]
                
    except Exception as e:
        raise ValueError(f"Error reading keywords file: {str(e)}")
    
    return validate_keywords(keywords)


def load_keywords_from_string(keywords_str: str) -> List[str]:
    """
    Load keywords from a comma-separated string.
    
    Args:
        keywords_str: Comma-separated keyword string
        
    Returns:
        List of keywords
    """
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    return validate_keywords(keywords)


def get_keywords_input(
    keywords_file: str = None,
    keywords_string: str = None
) -> List[str]:
    """
    Get keywords from either file or string input.
    
    Args:
        keywords_file: Path to keywords file
        keywords_string: Comma-separated keywords string
        
    Returns:
        List of validated keywords
        
    Raises:
        ValueError: If neither or both inputs provided, or no valid keywords found
    """
    if keywords_file and keywords_string:
        raise ValueError("Please provide either keywords file OR keywords string, not both.")
    
    if not keywords_file and not keywords_string:
        raise ValueError("Please provide either keywords file or keywords string.")
    
    if keywords_file:
        return load_keywords_from_file(keywords_file)
    else:
        return load_keywords_from_string(keywords_string)