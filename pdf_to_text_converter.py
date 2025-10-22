#!/usr/bin/env python3
import os
import sys
import argparse
import shutil
from pathlib import Path
import PyPDF2
import pdfplumber
from io import StringIO

class PDFToTextConverter:
    def __init__(self, output_base_dir="plain_text_files"):
        self.output_base_dir = Path(output_base_dir)
        self.conversion_errors = []
        
    def extract_text_pypdf2(self, pdf_path):
        """Extract text using PyPDF2 - good for simple PDFs"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"PyPDF2 extraction failed: {str(e)}")
    
    def extract_text_pdfplumber(self, pdf_path):
        """Extract text using pdfplumber - better for complex layouts"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"pdfplumber extraction failed: {str(e)}")
    
    def convert_pdf_to_text(self, pdf_path):
        """Convert a single PDF to text using multiple methods"""
        pdf_path = Path(pdf_path)
        
        # Try pdfplumber first (better for research papers)
        try:
            text = self.extract_text_pdfplumber(pdf_path)
            if text and len(text.strip()) > 100:  # Ensure meaningful content
                return text
        except Exception as e:
            print(f"pdfplumber failed for {pdf_path.name}: {e}")
        
        # Fallback to PyPDF2
        try:
            text = self.extract_text_pypdf2(pdf_path)
            if text and len(text.strip()) > 100:
                return text
        except Exception as e:
            print(f"PyPDF2 failed for {pdf_path.name}: {e}")
        
        raise Exception("All extraction methods failed")
    
    def get_output_path(self, pdf_path, source_folder=None):
        """Generate output path maintaining folder structure"""
        pdf_path = Path(pdf_path)
        
        if source_folder:
            # Batch processing - maintain folder structure
            source_folder = Path(source_folder)
            relative_folder = source_folder.name
            output_dir = self.output_base_dir / relative_folder
        else:
            # Single file processing
            output_dir = self.output_base_dir / "single_files"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{pdf_path.stem}.txt"
    
    def convert_single_file(self, pdf_path):
        """Convert a single PDF file"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            print(f"Error: File {pdf_path} does not exist")
            return False
        
        if not pdf_path.suffix.lower() == '.pdf':
            print(f"Error: {pdf_path} is not a PDF file")
            return False
        
        output_path = self.get_output_path(pdf_path)
        
        # Skip if already converted
        if output_path.exists():
            print(f"Skipping {pdf_path.name} - already converted")
            return True
        
        try:
            print(f"Converting {pdf_path.name}...")
            text = self.convert_pdf_to_text(pdf_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"[OK] Converted: {pdf_path.name} -> {output_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to convert {pdf_path.name}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.conversion_errors.append(error_msg)
            return False
    
    def convert_folder(self, folder_path):
        """Convert all PDFs in a folder"""
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            print(f"Error: Folder {folder_path} does not exist")
            return False
        
        pdf_files = list(folder_path.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {folder_path}")
            return True
        
        print(f"Found {len(pdf_files)} PDF files in {folder_path}")
        
        success_count = 0
        for pdf_file in pdf_files:
            output_path = self.get_output_path(pdf_file, folder_path)
            
            # Skip if already converted
            if output_path.exists():
                print(f"Skipping {pdf_file.name} - already converted")
                success_count += 1
                continue
            
            try:
                print(f"Converting {pdf_file.name}...")
                text = self.convert_pdf_to_text(pdf_file)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                print(f"[OK] Converted: {pdf_file.name}")
                success_count += 1
                
            except Exception as e:
                error_msg = f"Failed to convert {pdf_file.name}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                self.conversion_errors.append(error_msg)
        
        print(f"Converted {success_count}/{len(pdf_files)} files from {folder_path}")
        return success_count == len(pdf_files)
    
    def clean_output_directory(self):
        """Remove all generated text files"""
        if self.output_base_dir.exists():
            shutil.rmtree(self.output_base_dir)
            print(f"Cleaned output directory: {self.output_base_dir}")

def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to plain text")
    parser.add_argument("path", help="Path to PDF file or folder containing PDFs")
    parser.add_argument("--clean", action="store_true", help="Clean output directory before conversion")
    
    args = parser.parse_args()
    
    converter = PDFToTextConverter()
    
    if args.clean:
        converter.clean_output_directory()
    
    path = Path(args.path)
    
    if path.is_file():
        success = converter.convert_single_file(path)
    elif path.is_dir():
        success = converter.convert_folder(path)
    else:
        print(f"Error: {path} is neither a file nor a directory")
        return 1
    
    if converter.conversion_errors:
        print(f"\n{len(converter.conversion_errors)} conversion errors occurred:")
        for error in converter.conversion_errors:
            print(f"  - {error}")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())