import logging
from pathlib import Path
import fitz  # PyMuPDF

class PDFAnnotator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def make_highlightable(self, input_file, output_file):
        """Make a single PDF copy that supports highlighting and annotations"""
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input PDF file not found: {input_path}")
        
        if input_path.suffix.lower() != '.pdf':
            raise ValueError(f"Input file is not a PDF: {input_path}")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            doc = fitz.open(str(input_path))
            doc.save(str(output_path), garbage=4, deflate=True)
            doc.close()
            
            self.logger.info(f"Highlightable PDF created: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create highlightable PDF: {e}")
            return False
    
    def process(self, input_path, output_dir):
        """Process PDF file(s) to make them highlightable"""
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input path not found: {input_path}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if input_path.is_file():
            if input_path.suffix.lower() != '.pdf':
                raise ValueError(f"Input file is not a PDF: {input_path}")
            
            output_file = output_dir / f"{input_path.stem}_highlightable.pdf"
            success = self.make_highlightable(input_path, output_file)
            return success
        
        elif input_path.is_dir():
            pdf_files = list(input_path.rglob('*.pdf'))
            
            if not pdf_files:
                self.logger.warning(f"No PDF files found in {input_path}")
                return True
            
            self.logger.info(f"Found {len(pdf_files)} PDF files to process")
            
            success_count = 0
            for pdf_file in pdf_files:
                # Maintain relative structure
                relative_path = pdf_file.relative_to(input_path)
                output_file = output_dir / relative_path.parent / f"{pdf_file.stem}_highlightable.pdf"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                if self.make_highlightable(pdf_file, output_file):
                    success_count += 1
            
            self.logger.info(f"Successfully processed {success_count}/{len(pdf_files)} PDF files")
            return success_count == len(pdf_files)
        
        else:
            raise ValueError(f"Input path is neither file nor directory: {input_path}")