#!/usr/bin/env python3
"""
Academic Paper Processing CLI Tool
"""
import argparse
import logging
import sys
from pathlib import Path

# Import subcommand modules
from commands.extract_emails import EmailExtractor
from commands.extract_references import ReferenceExtractor

from commands.pdf_converter import PDFConverter
from commands.pdf_annotator import PDFAnnotator
from commands.metadata_enricher import MetadataEnricher


def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Academic Paper Processing Tool')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract emails command
    email_parser = subparsers.add_parser('extract-emails', help='Extract emails from text files')
    email_parser.add_argument('input_dir', help='Directory containing text files')
    email_parser.add_argument('output_file', help='Output file for extracted emails')
    
    # Extract references command
    ref_parser = subparsers.add_parser('extract-references', help='Extract references from text files')
    ref_parser.add_argument('input_dir', help='Directory containing text files')
    ref_parser.add_argument('output_file', help='Output file for references')
    

    
    # Convert PDFs command
    pdf_parser = subparsers.add_parser('convert-pdf', help='Convert PDFs to text')
    pdf_parser.add_argument('input_path', help='PDF file or directory')
    pdf_parser.add_argument('output_dir', help='Output directory for text files')
    pdf_parser.add_argument('--clean', action='store_true', help='Clean output directory first')
    
    # Make PDF highlightable command
    highlight_parser = subparsers.add_parser('make-highlightable', help='Make PDF highlightable')
    highlight_parser.add_argument('input_path', help='Input PDF file or directory')
    highlight_parser.add_argument('output_dir', help='Output directory')
    
    # Enrich metadata command
    enrich_parser = subparsers.add_parser('enrich-metadata', help='Enrich paper metadata')
    enrich_parser.add_argument('input_file', help='Input references file')
    enrich_parser.add_argument('output_file', help='Output enriched file')
    enrich_parser.add_argument('--api-key', required=True, help='Google API key')
    enrich_parser.add_argument('--cse-id', required=True, help='Google CSE ID')
    enrich_parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests')
    

    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'extract-emails':
            extractor = EmailExtractor()
            extractor.extract(args.input_dir, args.output_file)
            
        elif args.command == 'extract-references':
            extractor = ReferenceExtractor()
            extractor.extract(args.input_dir, args.output_file)
            

            
        elif args.command == 'convert-pdf':
            converter = PDFConverter()
            converter.convert(args.input_path, args.output_dir, clean=args.clean)
            
        elif args.command == 'make-highlightable':
            annotator = PDFAnnotator()
            annotator.process(args.input_path, args.output_dir)
            
        elif args.command == 'enrich-metadata':
            enricher = MetadataEnricher(args.api_key, args.cse_id)
            num_papers = enricher.enrich(args.input_file, args.output_file, delay=args.delay)
            logger.info(f"Enrichment completed for {num_papers} papers with automatic analysis")
            

            
        logger.info("Command completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())