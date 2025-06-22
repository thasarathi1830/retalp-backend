import chardet
import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

def detect_encoding(contents, min_confidence=0.7):
    """Detect file encoding with confidence threshold"""
    result = chardet.detect(contents)
    logger.info(f"Encoding detection: {result['encoding']} (confidence: {result['confidence']})")
    return result['encoding'] if result['confidence'] > min_confidence else 'utf-8'

def read_csv_with_fallback(contents, encodings=None):
    """Robust CSV reader with multiple fallback strategies"""
    # Default encoding priority
    encodings = encodings or ['utf-8', 'ISO-8859-1', 'cp1252', 'latin1']
    
    # Try detected encoding first
    primary_enc = detect_encoding(contents)
    if primary_enc not in encodings:
        encodings.insert(0, primary_enc)
    
    # Attempt reading with each encoding
    for encoding in encodings:
        try:
            return pd.read_csv(io.BytesIO(contents), encoding=encoding)
        except Exception as e:
            logger.debug(f"Failed with {encoding}: {str(e)}")
    
    # Fallback with error tolerance
    try:
        return pd.read_csv(io.BytesIO(contents), encoding='utf-8', on_bad_lines='skip', engine='python')
    except Exception as e:
        logger.error(f"Final CSV fallback failed: {str(e)}")
        raise ValueError(f"Could not read CSV file: {str(e)}")
