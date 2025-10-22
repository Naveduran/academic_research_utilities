import logging
import shutil
from pathlib import Path
import PyPDF2
import pdfplumber

class PDFConverter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conversion_errors = []
    
    def extract_text_pypdf2(self, pdf_path):
        """Extract text using PyPDF2"""
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
        """Extract text using pdfplumber"""
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
        # Try pdfplumber first
        try:
            text = self.extract_text_pdfplumber(pdf_path)
            if text and len(text.strip()) > 100:
                return text
        except Exception as e:
            self.logger.debug(f"pdfplumber failed for {pdf_path.name}: {e}")
        
        # Fallback to PyPDF2
        try:
            text = self.extract_text_pypdf2(pdf_path)
            if text and len(text.strip()) > 100:
                return text
        except Exception as e:
            self.logger.debug(f"PyPDF2 failed for {pdf_path.name}: {e}")
        
        raise Exception("All extraction methods failed")
    
    def get_output_path(self, pdf_path, output_dir, source_folder=None):
        """Generate output path maintaining folder structure"""
        output_base = Path(output_dir)
        
        if source_folder:
            # Batch processing - maintain folder structure
            relative_folder = Path(source_folder).name
            output_dir_final = output_base / relative_folder
        else:
            # Single file processing
            output_dir_final = output_base / "single_files"
        
        output_dir_final.mkdir(parents=True, exist_ok=True)
        return output_dir_final / f"{pdf_path.stem}.txt"
    
    def convert_single_file(self, pdf_path, output_dir):
        """Convert a single PDF file"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        output_path = self.get_output_path(pdf_path, output_dir)
        
        # Skip if already converted
        if output_path.exists():
            self.logger.info(f"Skipping {pdf_path.name} - already converted")
            return True
        
        try:
            self.logger.info(f"Converting {pdf_path.name}...")
            text = self.convert_pdf_to_text(pdf_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.logger.info(f"Converted: {pdf_path.name} -> {output_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to convert {pdf_path.name}: {str(e)}"
            self.logger.error(error_msg)
            self.conversion_errors.append(error_msg)
            return False
    
    def convert_folder(self, folder_path, output_dir):
        """Convert all PDFs in a folder"""
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")
        
        pdf_files = list(folder_path.glob("*.pdf"))
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {folder_path}")
            return True
        
        self.logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")
        
        success_count = 0
        for pdf_file in pdf_files:
            output_path = self.get_output_path(pdf_file, output_dir, folder_path)
            
            # Skip if already converted
            if output_path.exists():
                self.logger.info(f"Skipping {pdf_file.name} - already converted")
                success_count += 1
                continue
            
            try:
                self.logger.info(f"Converting {pdf_file.name}...")
                text = self.convert_pdf_to_text(pdf_file)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                self.logger.info(f"Converted: {pdf_file.name}")
                success_count += 1
                
            except Exception as e:
                error_msg = f"Failed to convert {pdf_file.name}: {str(e)}"
                self.logger.error(error_msg)
                self.conversion_errors.append(error_msg)
        
        self.logger.info(f"Converted {success_count}/{len(pdf_files)} files from {folder_path}")
        return success_count == len(pdf_files)
    
    def convert(self, input_path, output_dir, clean=False):
        """Convert PDF(s) to text"""
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        if clean and output_dir.exists():
            shutil.rmtree(output_dir)
            self.logger.info(f"Cleaned output directory: {output_dir}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if input_path.is_file():
            success = self.convert_single_file(input_path, output_dir)
        elif input_path.is_dir():
            success = self.convert_folder(input_path, output_dir)
        else:
            raise ValueError(f"Input path is neither file nor directory: {input_path}")
        
        if self.conversion_errors:
            self.logger.warning(f"{len(self.conversion_errors)} conversion errors occurred")
            for error in self.conversion_errors:
                self.logger.warning(f"  - {error}")
        
        return success