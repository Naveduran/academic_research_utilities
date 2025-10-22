import os
import re
import logging
from pathlib import Path

class EmailExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, input_dir, output_file):
        """Extract emails from text files in directory"""
        input_path = Path(input_dir)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_path}")
        
        if not input_path.is_dir():
            raise ValueError(f"Input path is not a directory: {input_path}")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        emails = set()
        processed_files = 0
        
        for txt_file in input_path.rglob('*.txt'):
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find all email addresses
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                found_emails = re.findall(email_pattern, content)
                emails.update(found_emails)
                processed_files += 1
                
            except Exception as e:
                self.logger.warning(f"Error processing {txt_file}: {e}")
        
        # Write to output file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for email in sorted(emails):
                    f.write(email + '\n')
        except Exception as e:
            raise IOError(f"Failed to write output file: {e}")
        
        self.logger.info(f"Processed {processed_files} files, found {len(emails)} unique emails")
        self.logger.info(f"Results saved to: {output_path}")