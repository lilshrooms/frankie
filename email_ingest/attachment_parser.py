import io
import re
import pdfplumber
from PIL import Image, ImageEnhance
import pytesseract
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional

def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    """Enhance image for better OCR accuracy"""
    # Convert to grayscale if not already
    if image.mode != 'L':
        image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    
    return image

def extract_tables_from_pdf(data: bytes) -> List[Dict]:
    """Extract tables from PDF using pdfplumber's table detection"""
    tables = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table_num, table in enumerate(page_tables):
                if table and len(table) > 1:  # Ensure table has content
                    tables.append({
                        'page': page_num + 1,
                        'table_num': table_num + 1,
                        'data': table
                    })
    return tables

def detect_document_type(filename: str, text: str) -> str:
    """Detect document type based on filename and content"""
    filename_lower = filename.lower()
    text_lower = text.lower()
    
    # W2 detection
    if 'w2' in filename_lower or 'w-2' in filename_lower or 'w2' in text_lower:
        return 'w2'
    
    # 1099 detection
    if '1099' in filename_lower or '1099' in text_lower:
        return '1099'
    
    # Bank statement detection
    if any(word in filename_lower for word in ['bank', 'statement', 'account']) or \
       any(word in text_lower for word in ['account balance', 'bank statement', 'deposits', 'withdrawals']):
        return 'bank_statement'
    
    # Pay stub detection
    if any(word in filename_lower for word in ['pay', 'stub', 'paycheck', 'payslip', 'salary']) or \
       any(word in text_lower for word in ['pay period', 'gross pay', 'net pay', 'deductions', 'earnings statement', 'payroll']):
        return 'pay_stub'
    
    # Tax return detection
    if any(word in filename_lower for word in ['tax', 'return', '1040']) or \
       any(word in text_lower for word in ['form 1040', 'tax return', 'adjusted gross income']):
        return 'tax_return'
    
    # Credit card statement detection
    if any(word in filename_lower for word in ['credit', 'card', 'statement', 'visa', 'mastercard', 'amex', 'discover']) or \
       any(word in text_lower for word in ['credit card', 'card statement', 'minimum payment', 'credit limit', 'available credit', 'new balance', 'previous balance']):
        return 'credit_card_statement'
    
    return 'unknown'

def extract_structured_data_from_text(text: str, doc_type: str) -> Dict:
    """Extract structured data based on document type"""
    structured_data = {}
    
    if doc_type == 'w2':
        # Extract W2 specific fields
        patterns = {
            'employer_name': r'employer.*?name.*?([A-Za-z\s&.,]+)',
            'wages': r'wages.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'federal_tax': r'federal.*?income.*?tax.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'ssn': r'(\b\d{3}-\d{2}-\d{4}\b)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured_data[field] = match.group(1).strip()
    
    elif doc_type == 'bank_statement':
        # Extract comprehensive bank statement fields
        patterns = {
            'account_number': r'(?:account|acct).*?(?:number|#|no).*?(\d{4,})',
            'account_holder': r'(?:account holder|customer name|name).*?([A-Za-z\s]+)',
            'statement_date': r'(?:statement date|as of|period ending).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'beginning_balance': r'(?:beginning|opening|previous).*?balance.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'ending_balance': r'(?:ending|closing|current|new).*?balance.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'total_deposits': r'(?:total|sum of).*?deposits.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'total_withdrawals': r'(?:total|sum of).*?(?:withdrawals|debits).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'minimum_balance': r'(?:minimum|lowest).*?balance.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'average_balance': r'(?:average|avg).*?balance.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'interest_earned': r'(?:interest|int).*?(?:earned|paid).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'service_charges': r'(?:service|maintenance|monthly).*?(?:charge|fee).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured_data[field] = match.group(1).strip()
        
        # Extract individual transactions (up to 10 most recent)
        transaction_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([A-Za-z\s]+)\s+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        transactions = re.findall(transaction_pattern, text)
        if transactions:
            structured_data['recent_transactions'] = transactions[:10]  # Limit to 10 most recent
    
    elif doc_type == 'pay_stub':
        # Extract comprehensive pay stub fields
        patterns = {
            'employee_name': r'(?:employee|name).*?([A-Za-z\s]+)',
            'employer_name': r'(?:employer|company).*?([A-Za-z\s&.,]+)',
            'pay_period': r'(?:pay period|period ending|for period).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'pay_date': r'(?:pay date|date paid|check date).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'gross_pay': r'(?:gross|total).*?(?:pay|earnings).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'net_pay': r'(?:net|take home|final).*?(?:pay|earnings).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'hourly_rate': r'(?:hourly|rate|per hour).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'hours_worked': r'(?:hours|hrs).*?(?:worked|regular).*?(\d{1,3}(?:\.\d{1,2})?)',
            'overtime_hours': r'(?:overtime|ot).*?(?:hours|hrs).*?(\d{1,3}(?:\.\d{1,2})?)',
            'overtime_rate': r'(?:overtime|ot).*?(?:rate|pay).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'year_to_date_gross': r'(?:ytd|year to date).*?(?:gross|total).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'year_to_date_net': r'(?:ytd|year to date).*?(?:net|take home).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'federal_tax': r'(?:federal|fed).*?(?:tax|withholding).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'state_tax': r'(?:state|st).*?(?:tax|withholding).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'social_security': r'(?:social security|ss|fica).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'medicare': r'(?:medicare|med).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'retirement': r'(?:retirement|401k|403b|pension).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'health_insurance': r'(?:health|medical|insurance).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'other_deductions': r'(?:other|additional|misc).*?(?:deductions|deduct).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured_data[field] = match.group(1).strip()
        
        # Extract deduction breakdown
        deduction_pattern = r'([A-Za-z\s]+)\s+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        deductions = re.findall(deduction_pattern, text)
        if deductions:
            # Filter for likely deduction entries
            valid_deductions = []
            for desc, amount in deductions:
                if any(keyword in desc.lower() for keyword in ['tax', 'insurance', 'retirement', '401k', '403b', 'pension', 'health', 'medical', 'dental', 'vision', 'life', 'disability', 'union', 'garnishment']):
                    valid_deductions.append((desc.strip(), amount))
            if valid_deductions:
                structured_data['deduction_breakdown'] = valid_deductions[:10]  # Limit to 10
    
    elif doc_type == '1099':
        # Extract 1099 specific fields
        patterns = {
            'payer_name': r'(?:payer|company).*?name.*?([A-Za-z\s&.,]+)',
            'recipient_name': r'(?:recipient|your).*?name.*?([A-Za-z\s]+)',
            'ssn': r'(\b\d{3}-\d{2}-\d{4}\b)',
            'ein': r'(\b\d{2}-\d{7}\b)',
            'non_employee_compensation': r'(?:non.?employee|nonemployee).*?compensation.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'federal_tax_withheld': r'(?:federal|fed).*?tax.*?withheld.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'state_tax_withheld': r'(?:state|st).*?tax.*?withheld.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'local_tax_withheld': r'(?:local|loc).*?tax.*?withheld.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'state_income': r'(?:state|st).*?income.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'local_income': r'(?:local|loc).*?income.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured_data[field] = match.group(1).strip()
    
    elif doc_type == 'tax_return':
        # Extract tax return specific fields
        patterns = {
            'filing_status': r'(?:filing status|status).*?([A-Za-z\s]+)',
            'adjusted_gross_income': r'(?:adjusted gross income|agi).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'total_income': r'(?:total income|gross income).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'taxable_income': r'(?:taxable income).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'total_tax': r'(?:total tax|tax due).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'refund_amount': r'(?:refund|overpayment).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'amount_owed': r'(?:amount owed|balance due).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'wages_salaries': r'(?:wages|salaries).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'business_income': r'(?:business|self.?employment).*?income.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'interest_income': r'(?:interest|dividends).*?income.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'rental_income': r'(?:rental|real estate).*?income.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured_data[field] = match.group(1).strip()
    
    elif doc_type == 'credit_card_statement':
        # Extract comprehensive credit card statement fields
        patterns = {
            'cardholder_name': r'(?:cardholder|account holder|customer).*?name.*?([A-Za-z\s]+)',
            'account_number': r'(?:account|card).*?(?:number|#|no).*?(\d{4,})',
            'statement_date': r'(?:statement date|closing date|billing date).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'payment_due_date': r'(?:payment due|due date).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'previous_balance': r'(?:previous|prior).*?balance.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'new_balance': r'(?:new|current|ending).*?balance.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'minimum_payment': r'(?:minimum|min).*?payment.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'credit_limit': r'(?:credit|available).*?limit.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'available_credit': r'(?:available|remaining).*?credit.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'total_purchases': r'(?:total|sum of).*?(?:purchases|charges).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'total_payments': r'(?:total|sum of).*?(?:payments|credits).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'finance_charges': r'(?:finance|interest).*?(?:charges|fees).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'late_fees': r'(?:late|delinquency).*?(?:fees|charges).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'annual_fee': r'(?:annual|yearly).*?(?:fee|charge).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'cash_advance_fee': r'(?:cash advance|advance).*?(?:fee|charge).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'balance_transfer_fee': r'(?:balance transfer|transfer).*?(?:fee|charge).*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'apr_rate': r'(?:apr|annual percentage rate).*?(\d{1,2}(?:\.\d{1,2})?%)',
            'cash_advance_apr': r'(?:cash advance|advance).*?apr.*?(\d{1,2}(?:\.\d{1,2})?%)',
            'balance_transfer_apr': r'(?:balance transfer|transfer).*?apr.*?(\d{1,2}(?:\.\d{1,2})?%)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured_data[field] = match.group(1).strip()
        
        # Extract individual transactions (up to 20 most recent for spending analysis)
        transaction_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([A-Za-z\s&.,]+)\s+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        transactions = re.findall(transaction_pattern, text)
        if transactions:
            structured_data['recent_transactions'] = transactions[:20]  # Limit to 20 most recent
        
        # Calculate utilization ratio if we have the data
        if 'new_balance' in structured_data and 'credit_limit' in structured_data:
            try:
                balance = float(structured_data['new_balance'].replace('$', '').replace(',', ''))
                limit = float(structured_data['credit_limit'].replace('$', '').replace(',', ''))
                if limit > 0:
                    utilization = (balance / limit) * 100
                    structured_data['credit_utilization_percent'] = f"{utilization:.1f}%"
            except (ValueError, AttributeError):
                pass
        
        # Extract spending categories if available
        category_pattern = r'([A-Za-z\s]+):\s+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        categories = re.findall(category_pattern, text)
        if categories:
            # Filter for likely spending categories
            valid_categories = []
            for category, amount in categories:
                if any(keyword in category.lower() for keyword in ['dining', 'gas', 'groceries', 'entertainment', 'travel', 'utilities', 'insurance', 'medical', 'shopping', 'transportation', 'home', 'auto']):
                    valid_categories.append((category.strip(), amount))
            if valid_categories:
                structured_data['spending_categories'] = valid_categories
    
    return structured_data

def parse_pdf(data: bytes) -> Dict:
    """Enhanced PDF parsing with OCR fallback for image-based PDFs"""
    text = ""
    tables = []
    used_ocr = False
    
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            # Try to extract text first (for text-based PDFs)
            page_text = page.extract_text() or ""
            
            # If no text extracted, convert page to image and use OCR
            if not page_text.strip():
                try:
                    # Convert PDF page to image using pdf2image approach
                    import fitz  # PyMuPDF
                    import tempfile
                    
                    # Create a temporary PDF file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                        tmp_file.write(data)
                        tmp_file_path = tmp_file.name
                    
                    # Open with PyMuPDF and convert to image
                    doc = fitz.open(tmp_file_path)
                    if len(doc) > 0:
                        page_pdf = doc[0]  # Get first page
                        mat = fitz.Matrix(2, 2)  # Scale factor for better OCR
                        pix = page_pdf.get_pixmap(matrix=mat)
                        
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Enhance image for better OCR
                        enhanced_image = enhance_image_for_ocr(pil_image)
                        # Use OCR to extract text
                        page_text = pytesseract.image_to_string(enhanced_image)
                        used_ocr = True
                        print(f"Used OCR for page with no extractable text")
                    
                    doc.close()
                    
                    # Clean up temporary file
                    import os
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    print(f"OCR failed for page: {e}")
                    page_text = ""
            
            text += page_text + "\n"
            
            # Extract tables from this page
            page_tables = page.extract_tables()
            for table in page_tables:
                if table and len(table) > 1:
                    tables.append(table)
    
    return {
        'text': text,
        'tables': tables,
        'raw_tables': extract_tables_from_pdf(data),
        'used_ocr': used_ocr
    }

def parse_image(data: bytes) -> Dict:
    """Enhanced image parsing with preprocessing for better OCR"""
    image = Image.open(io.BytesIO(data))
    
    # Enhance image for better OCR
    enhanced_image = enhance_image_for_ocr(image)
    
    # Try different OCR configurations for better accuracy
    ocr_configs = [
        '--oem 3 --psm 6',  # Default
        '--oem 3 --psm 3',  # Fully automatic page segmentation
        '--oem 3 --psm 4',  # Assume single column of text
        '--oem 1 --psm 6'   # Legacy engine
    ]
    
    best_text = ""
    best_confidence = 0
    
    for config in ocr_configs:
        try:
            # Get text with confidence scores
            ocr_data = pytesseract.image_to_data(enhanced_image, config=config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_text = pytesseract.image_to_string(enhanced_image, config=config)
        except Exception:
            continue
    
    # Fallback to default if all configs fail
    if not best_text:
        best_text = pytesseract.image_to_string(enhanced_image)
    
    return {
        'text': best_text,
        'confidence': best_confidence,
        'tables': []  # Images typically don't have structured tables
    }

def parse_attachments(attachments) -> List[Dict]:
    """Enhanced attachment parsing with document type detection and structured data"""
    results = []
    
    for att in attachments:
        filename = att['filename']
        data = att['data']
        
        if filename.lower().endswith('.pdf'):
            parsed_data = parse_pdf(data)
            text = parsed_data['text']
            tables = parsed_data['tables']
            used_ocr = parsed_data.get('used_ocr', False)
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            parsed_data = parse_image(data)
            text = parsed_data['text']
            tables = parsed_data['tables']
            used_ocr = True  # Images always use OCR
        else:
            text = None
            tables = []
            used_ocr = False
        
        if text:
            # Detect document type
            doc_type = detect_document_type(filename, text)
            
            # Extract structured data
            structured_data = extract_structured_data_from_text(text, doc_type)
            
            results.append({
                'filename': filename,
                'text': text,
                'tables': tables,
                'document_type': doc_type,
                'structured_data': structured_data,
                'used_ocr': used_ocr
            })
        else:
            results.append({
                'filename': filename,
                'text': None,
                'tables': [],
                'document_type': 'unknown',
                'structured_data': {}
            })
    
    return results 