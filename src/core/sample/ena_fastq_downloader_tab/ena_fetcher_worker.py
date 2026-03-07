"""Worker thread for fetching accession data from ENA API."""

import requests
import json
from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

BASE_URL = "https://www.ebi.ac.uk/ena/portal/api/filereport"
FIELDS = "study_accession,sample_accession,experiment_accession,run_accession,tax_id,scientific_name,fastq_ftp,submitted_ftp,sra_ftp,bam_ftp"


class ENAFetcherWorker(QObject):
    """Worker thread to fetch accession data from ENA API without blocking UI."""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    fetch_progress = pyqtSignal(int, int)  # current, total
    result_ready = pyqtSignal(list, list)  # successful_results, failed_accessions
    
    def __init__(self, accessions):
        """Initialize the fetcher worker with accession list.
        
        Parameters
        ----------
        accessions : list
            List of accession numbers (e.g., ['SRR10376955', 'SRR10376956'])
        """
        super().__init__()
        self.accessions = [acc.strip() for acc in accessions if acc.strip()]
    
    def run(self):
        """Fetch data for all accessions from ENA API."""
        try:
            successful_results = []
            failed_accessions = []
            
            total = len(self.accessions)
            
            for idx, accession in enumerate(self.accessions):
                try:
                    self.fetch_progress.emit(idx + 1, total)
                    
                    # Build URL with single accession
                    url = f"{BASE_URL}?accession={accession}&result=read_run&fields={FIELDS}&format=json&download=true&limit=0"
                    
                    logger.info(f"Fetching data for accession: {accession}")
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Parse JSON response
                    data = response.json()
                    
                    if data and isinstance(data, list) and len(data) > 0:
                        # Extract FTP URLs
                        for record in data:
                            successful_results.append({
                                'accession': accession,
                                'data': record,
                                'fastq_urls': self._extract_ftp_urls(record)
                            })
                        logger.info(f"Successfully fetched data for {accession}")
                    else:
                        logger.warning(f"No data returned for accession: {accession}")
                        failed_accessions.append((accession, "No data returned from API"))
                        
                except requests.exceptions.Timeout:
                    error_msg = f"Request timeout for {accession}"
                    logger.warning(error_msg)
                    failed_accessions.append((accession, error_msg))
                    
                except requests.exceptions.HTTPError as e:
                    error_msg = f"HTTP Error {e.response.status_code} for {accession}"
                    logger.warning(error_msg)
                    failed_accessions.append((accession, error_msg))
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON response for {accession}"
                    logger.warning(error_msg)
                    failed_accessions.append((accession, error_msg))
                    
                except Exception as e:
                    error_msg = f"Error fetching {accession}: {str(e)}"
                    logger.error(error_msg)
                    failed_accessions.append((accession, error_msg))
            
            self.result_ready.emit(successful_results, failed_accessions)
            
        except Exception as e:
            logger.error(f"Fatal error in fetcher worker: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
    
    def _extract_ftp_urls(self, record):
        """Extract FTP URLs from a record.
        
        Parameters
        ----------
        record : dict
            A single record from ENA API response
            
        Returns
        -------
        list
            List of FTP URLs (fastq_ftp takes priority)
        """
        urls = []
        
        # Priority: fastq_ftp > submitted_ftp > sra_ftp > bam_ftp
        ftp_field = None
        
        if record.get('fastq_ftp'):
            ftp_field = record.get('fastq_ftp')
        elif record.get('submitted_ftp'):
            ftp_field = record.get('submitted_ftp')
        elif record.get('sra_ftp'):
            ftp_field = record.get('sra_ftp')
        elif record.get('bam_ftp'):
            ftp_field = record.get('bam_ftp')
        
        if ftp_field:
            # FTP URLs are semicolon-separated
            urls = [url.strip() for url in ftp_field.split(';') if url.strip()]
        
        # Convert FTP URLs to HTTP URLs (EBI supports both)
        http_urls = []
        for url in urls:
            if url.startswith('ftp://'):
                http_url = url.replace('ftp://', 'https://')
            else:
                http_url = 'https://' + url if not url.startswith('https://') else url
            http_urls.append(http_url)
        
        return http_urls
