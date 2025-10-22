import requests
import re
import time
import logging
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime

class DOIResolver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def resolve(self, doi):
        """Try to resolve DOI to publisher page"""
        if not doi or doi == "Not available" or "ISBN" in doi:
            return None, "No valid DOI"
        
        try:
            doi_url = f"https://doi.org/{doi}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(doi_url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                return response.url, "DOI resolved successfully"
            else:
                return None, f"DOI resolution failed: HTTP {response.status_code}"
        except Exception as e:
            return None, f"DOI resolution error: {str(e)}"

class GoogleSearcher:
    def __init__(self, api_key, cse_id):
        self.api_key = api_key
        self.cse_id = cse_id
        self.logger = logging.getLogger(__name__)
    
    def search(self, query, num_results=5):
        """Perform Google search using Custom Search JSON API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': num_results
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'snippet': item.get('snippet')
                })
            
            return results
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

class MetadataExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_from_url(self, url):
        """Extract metadata from a webpage"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract authors
            authors = self._extract_authors(soup)
            
            # Extract abstract
            abstract = self._extract_abstract(soup)
            
            return abstract, authors
            
        except Exception as e:
            self.logger.debug(f"Metadata extraction error from {url}: {e}")
            return "", ""
    
    def _extract_authors(self, soup):
        """Extract authors from BeautifulSoup object"""
        author_selectors = [
            '.authors', '.author-list', '[class*="author"]', 
            '.citation-authors', '.contributors'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['author', 'by ', 'et al']):
                    authors_text = re.sub(r'\s+', ' ', text)
                    return authors_text
        return ""
    
    def _extract_abstract(self, soup):
        """Extract abstract from BeautifulSoup object"""
        abstract_selectors = [
            '.abstract', '.article-abstract', '[id*="abstract"]', 
            '[class*="abstract"]', '.article-text', '.content'
        ]
        
        for selector in abstract_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 100:
                    return text[:500] + "..." if len(text) > 500 else text
        return ""

class ConfidenceCalculator:
    def calculate(self, data_type, source_method, validation_results):
        """Calculate confidence score 0-100 for extracted data"""
        base_scores = {
            'doi_direct': 90,
            'google_search': 60,
            'fallback': 30
        }
        
        score = base_scores.get(source_method, 30)
        
        # Adjust based on validation
        if validation_results.get('format_valid', False):
            score += 10
        if validation_results.get('content_relevant', False):
            score += 10
        if validation_results.get('source_reliable', False):
            score += 10
        
        return min(100, max(0, score))

class DataValidator:
    def validate(self, data, paper_title, data_type):
        """Validate extracted data and return validation results"""
        results = {
            'format_valid': False,
            'content_relevant': False,
            'source_reliable': False
        }
        
        if not data:
            return results
        
        # Format validation
        if data_type == 'authors':
            if re.search(r'[A-Z][a-z]+.*[A-Z][a-z]+', data) or 'et al' in data:
                results['format_valid'] = True
        elif data_type == 'abstract':
            if len(data) > 50 and any(word in data.lower() for word in ['study', 'research', 'analysis', 'method']):
                results['format_valid'] = True
        
        # Content relevance
        if paper_title:
            title_words = set(paper_title.lower().split())
            data_words = set(data.lower().split())
            if len(title_words.intersection(data_words)) > 0:
                results['content_relevant'] = True
        
        return results

class MetadataEnricher:
    def __init__(self, api_key, cse_id):
        self.doi_resolver = DOIResolver()
        self.google_searcher = GoogleSearcher(api_key, cse_id)
        self.metadata_extractor = MetadataExtractor()
        self.confidence_calculator = ConfidenceCalculator()
        self.data_validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        self.results_log = []
    
    def _log_result(self, message):
        """Log message to both logger and internal results log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        self.results_log.append(log_message)
        self.logger.info(message)
    
    def _process_paper_block(self, block):
        """Process one paper block with DOI-first approach"""
        lines = block.strip().split('\n')
        if not lines:
            return block
        
        # Extract DOI and Title
        doi = None
        title = None
        
        for line in lines:
            if line.startswith('DOI:'):
                doi = line[4:].strip()
            elif line.startswith('Title:'):
                title = line[6:].strip()
        
        if not title:
            self._log_result("ERROR: No title found, skipping paper")
            return block
        
        self._log_result(f"Processing: {title[:60]}...")
        self._log_result(f"DOI: {doi}")
        
        # Initialize result tracking
        result = {
            'authors': '',
            'abstract': '',
            'webpage': '',
            'author_confidence': 0,
            'abstract_confidence': 0,
            'webpage_confidence': 0,
            'source_method': '',
            'needs_review': False,
            'errors': []
        }
        
        # Try DOI resolution first
        if doi and doi != "Not available" and "ISBN" not in doi:
            self._log_result("Attempting DOI resolution...")
            resolved_url, doi_status = self.doi_resolver.resolve(doi)
            
            if resolved_url:
                self._log_result(f"DOI resolved to: {resolved_url}")
                abstract, authors = self.metadata_extractor.extract_from_url(resolved_url)
                
                if authors or abstract:
                    # Validate and calculate confidence
                    author_validation = self.data_validator.validate(authors, title, 'authors')
                    abstract_validation = self.data_validator.validate(abstract, title, 'abstract')
                    
                    result.update({
                        'authors': authors,
                        'abstract': abstract,
                        'webpage': resolved_url,
                        'author_confidence': self.confidence_calculator.calculate('authors', 'doi_direct', author_validation),
                        'abstract_confidence': self.confidence_calculator.calculate('abstract', 'doi_direct', abstract_validation),
                        'webpage_confidence': 95,
                        'source_method': 'DOI_DIRECT'
                    })
                    
                    self._log_result(f"Authors confidence: {result['author_confidence']}%")
                    self._log_result(f"Abstract confidence: {result['abstract_confidence']}%")
                else:
                    self._log_result("Failed to extract metadata from DOI page")
                    result['errors'].append('DOI page metadata extraction failed')
            else:
                self._log_result(f"DOI resolution failed: {doi_status}")
                result['errors'].append(f'DOI resolution failed: {doi_status}')
        
        # Fallback to Google search if DOI failed or no results
        if not result['authors'] and not result['abstract']:
            self._log_result("Falling back to Google search...")
            search_results = self.google_searcher.search(f'"{title}"', num_results=3)
            
            if search_results:
                for i, search_result in enumerate(search_results[:2]):
                    self._log_result(f"Trying search result {i+1}: {search_result['title'][:50]}...")
                    
                    abstract, authors = self.metadata_extractor.extract_from_url(search_result['link'])
                    if authors or abstract:
                        validation = self.data_validator.validate(authors, title, 'authors')
                        result.update({
                            'authors': authors,
                            'abstract': abstract,
                            'webpage': search_result['link'],
                            'author_confidence': self.confidence_calculator.calculate('authors', 'google_search', validation),
                            'abstract_confidence': self.confidence_calculator.calculate('abstract', 'google_search', validation),
                            'webpage_confidence': 50,
                            'source_method': 'GOOGLE_FALLBACK'
                        })
                        self._log_result("Fallback extraction successful")
                        break
            else:
                self._log_result("No search results found")
                result['errors'].append('No search results found')
        
        # Determine if needs human review
        low_confidence = (result['author_confidence'] < 70 or 
                         result['abstract_confidence'] < 70 or 
                         result['webpage_confidence'] < 70)
        
        if low_confidence or result['errors']:
            result['needs_review'] = True
            self._log_result("[REVIEW NEEDED] Low confidence or errors detected")
        
        # Log final results
        self._log_result(f"Final confidence scores - Authors: {result['author_confidence']}%, Abstract: {result['abstract_confidence']}%, Webpage: {result['webpage_confidence']}%")
        if result['errors']:
            self._log_result(f"Errors: {'; '.join(result['errors'])}")
        
        # Build enriched block
        enriched_block = block.strip()
        
        if result['authors']:
            enriched_block += f"\nAuthors: {result['authors']}"
            enriched_block += f"\nAuthor_Confidence: {result['author_confidence']}%"
        
        if result['abstract']:
            enriched_block += f"\nAbstract: {result['abstract']}"
            enriched_block += f"\nAbstract_Confidence: {result['abstract_confidence']}%"
        
        if result['webpage']:
            enriched_block += f"\nWebpage: {result['webpage']}"
            enriched_block += f"\nWebpage_Confidence: {result['webpage_confidence']}%"
        
        enriched_block += f"\nSource_Method: {result['source_method']}"
        enriched_block += f"\nNeeds_Review: {result['needs_review']}"
        
        if result['errors']:
            enriched_block += f"\nErrors: {'; '.join(result['errors'])}"
        
        return enriched_block
    
    def enrich(self, input_file, output_file, delay=1.0):
        """Enrich references with additional metadata"""
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize results log
        self.results_log = [f"PROCESSING STARTED: {datetime.now()}", "="*80, ""]
        self._log_result("Starting to enrich references with DOI-first approach...")
        
        # Read the input file
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Failed to read input file: {e}")
        
        # Split into paper blocks
        blocks = [block for block in content.split('\n\n') if block.strip()]
        enriched_blocks = []
        
        self._log_result(f"Found {len(blocks)} papers to process")
        
        for i, block in enumerate(blocks):
            self._log_result(f"\n[{i+1}/{len(blocks)}] " + "="*50)
            enriched_block = self._process_paper_block(block)
            enriched_blocks.append(enriched_block)
            time.sleep(delay)
        
        # Write enriched output
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(enriched_blocks))
        except Exception as e:
            raise IOError(f"Failed to write output file: {e}")
        
        # Write detailed log
        log_file = output_path.parent / f"{output_path.stem}_results.txt"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.results_log))
        except Exception as e:
            self.logger.warning(f"Failed to write log file: {e}")
        
        self._log_result(f"\nProcessing completed! Results saved to {output_path}")
        self._log_result(f"Detailed log available in {log_file}")
        
        self.logger.info(f"Enriched {len(blocks)} papers, results saved to {output_path}")
        
        # Automatically analyze results
        self._analyze_results(log_file)
        
        return len(blocks)
    
    def _analyze_results(self, results_file):
        """Analyze processing results from log file"""
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read results file: {e}")
            return
        
        # Count statistics
        total_papers = len(re.findall(r'\[\d+/\d+\]', content))
        doi_attempts = len(re.findall(r'Attempting DOI resolution', content))
        doi_successes = len(re.findall(r'DOI resolved to:', content))
        doi_failures = len(re.findall(r'DOI resolution failed:', content))
        
        fallback_attempts = len(re.findall(r'Falling back to Google search', content))
        fallback_successes = len(re.findall(r'Fallback extraction successful', content))
        
        no_results = len(re.findall(r'No search results found', content))
        
        # Confidence levels
        high_conf_90 = len(re.findall(r'confidence: 90%', content))
        med_conf_70 = len(re.findall(r'confidence: 70%', content))
        med_conf_60 = len(re.findall(r'confidence: 60%', content))
        zero_conf = len(re.findall(r'confidence: 0%', content))
        
        needs_review = len(re.findall(r'\[REVIEW NEEDED\]', content))
        
        # Error types
        http_403 = len(re.findall(r'HTTP 403', content))
        http_202 = len(re.findall(r'HTTP 202', content))
        
        # Print analysis
        print(f"\nCOMPLETE PROCESSING STATISTICS FOR ALL {total_papers} PAPERS")
        print("="*60)
        print(f"Total papers processed: {total_papers}")
        print()
        
        if doi_attempts > 0:
            print("DOI RESOLUTION:")
            print(f"  DOI attempts: {doi_attempts}")
            print(f"  DOI successes: {doi_successes} ({doi_successes/doi_attempts*100:.1f}%)")
            print(f"  DOI failures: {doi_failures} ({doi_failures/doi_attempts*100:.1f}%)")
            print(f"    - HTTP 403 (blocked): {http_403}")
            print(f"    - HTTP 202 (redirect): {http_202}")
            print()
        
        if fallback_attempts > 0:
            print("FALLBACK PERFORMANCE:")
            print(f"  Google fallback used: {fallback_attempts}")
            print(f"  Fallback successes: {fallback_successes} ({fallback_successes/fallback_attempts*100:.1f}%)")
            print(f"  Complete failures: {no_results} ({no_results/total_papers*100:.1f}%)")
            print()
        
        if any([high_conf_90, med_conf_70, med_conf_60, zero_conf]):
            print("CONFIDENCE DISTRIBUTION:")
            print(f"  High confidence (90%): {high_conf_90//2} papers ({high_conf_90//2/total_papers*100:.1f}%)")
            print(f"  Medium confidence (70%): {med_conf_70//2} papers ({med_conf_70//2/total_papers*100:.1f}%)")
            print(f"  Medium confidence (60%): {med_conf_60//2} papers ({med_conf_60//2/total_papers*100:.1f}%)")
            print(f"  Zero confidence: {zero_conf//2} papers ({zero_conf//2/total_papers*100:.1f}%)")
            print()
        
        if needs_review > 0:
            print("REVIEW REQUIREMENTS:")
            print(f"  Papers needing review: {needs_review} ({needs_review/total_papers*100:.1f}%)")
            print()
        
        if total_papers > 0:
            print("OVERALL SUCCESS:")
            print(f"  Some data extracted: {total_papers - no_results} ({(total_papers - no_results)/total_papers*100:.1f}%)")
            print(f"  Complete failures: {no_results} ({no_results/total_papers*100:.1f}%)")
        
        self.logger.info(f"Analysis completed for {total_papers} papers")