import os
import re
import logging
from pathlib import Path

class ReferenceExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_doi(self, text):
        """Extract DOI from text"""
        doi_patterns = [
            r'DOI:\s*([^\s\n]+)',
            r'doi:\s*([^\s\n]+)',
            r'https://doi\.org/([^\s\n]+)',
            r'http://dx\.doi\.org/([^\s\n]+)',
            r'doi\.org/([^\s\n]+)',
            r'10\.\d{4,}/[^\s\n]+',
        ]
        
        for pattern in doi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doi = match.group(1) if len(match.groups()) > 0 else match.group(0)
                doi = re.sub(r'[.,;:\s]*$', '', doi)
                return doi
        return "Not found"
    
    def extract_authors(self, text, filename):
        """Extract authors from text using filename as guide"""
        basename = Path(filename).stem
        first_author = basename.split('_')[0] if '_' in basename else basename
        
        lines = text.split('\n')[:25]
        
        for line in lines:
            line_clean = line.strip()
            if first_author.lower() in line_clean.lower() and len(line_clean) > 10:
                clean_line = re.sub(r'^\d+\s*', '', line_clean)
                clean_line = re.sub(r'^[^A-Za-z]*', '', clean_line)
                
                if any(word in clean_line.lower() for word in ['journal', 'department', 'university']):
                    continue
                    
                if (',' in clean_line or ' and ' in clean_line) and len(clean_line) < 300:
                    return clean_line
        
        # Fallback pattern matching
        for line in lines[:15]:
            line_clean = line.strip()
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]*\s*,\s*[A-Z][a-z]+', line_clean):
                clean_line = re.sub(r'^\d+\s*', '', line_clean)
                if 10 < len(clean_line) < 300:
                    return clean_line
        
        return f"{first_author.title()} et al."
    
    def extract_title(self, text):
        """Extract title from text"""
        lines = text.split('\n')
        
        for line in lines[:15]:
            line = line.strip()
            if len(line) > 20 and not re.match(r'^\d+$', line) and not line.startswith('Journal'):
                title = re.sub(r'^\d+\s*', '', line)
                title = re.sub(r'^[A-Z\s]+$', '', title)
                if len(title) > 10:
                    return title
        
        return "Title not found"
    
    def extract_year(self, filename):
        """Extract year from filename"""
        match = re.search(r'(\d{4})', filename)
        return match.group(1) if match else "Year not found"
    
    def extract_webpage(self, text):
        """Extract webpage/URL from text"""
        url_patterns = [
            r'https?://[^\s\n]+',
            r'www\.[^\s\n]+',
            r'Available at:\s*([^\n]+)',
            r'URL:\s*([^\n]+)',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(1) if len(match.groups()) > 0 else match.group(0)
                url = re.sub(r'[.,;:\s]*$', '', url)
                return url
        
        return "No webpage found"
    
    def extract(self, input_dir, output_file):
        """Extract references from all text files in directory"""
        input_path = Path(input_dir)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_path}")
        
        if not input_path.is_dir():
            raise ValueError(f"Input path is not a directory: {input_path}")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results = []
        processed_files = 0
        
        for txt_file in input_path.rglob('*.txt'):
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract information
                doi = self.extract_doi(content)
                authors = self.extract_authors(content, txt_file.name)
                title = self.extract_title(content)
                year = self.extract_year(txt_file.name)
                webpage = self.extract_webpage(content)
                
                # Format result
                result = f"DOI: {doi}\n"
                result += f"Authors: {authors}\n"
                result += f"Title: {title}\n"
                result += f"Year: {year}\n"
                result += f"Webpage: {webpage}\n"
                
                results.append(result)
                processed_files += 1
                
            except Exception as e:
                self.logger.warning(f"Error processing {txt_file}: {e}")
        
        # Write to output file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, result in enumerate(results):
                    f.write(result)
                    if i < len(results) - 1:
                        f.write("\n")
        except Exception as e:
            raise IOError(f"Failed to write output file: {e}")
        
        self.logger.info(f"Processed {processed_files} files")
        self.logger.info(f"Results saved to: {output_path}")