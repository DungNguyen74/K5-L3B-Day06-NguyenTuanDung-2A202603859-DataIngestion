"""Download World Bank Annual Report 2023 to complete the 2-document corpus."""
import json
import requests
from pathlib import Path
from pypdf import PdfReader

DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
DATA_DIR.mkdir(exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# 1. Query handle 10986/40219 for World Bank Annual Report 2023 bitstream
handle_url = 'https://openknowledge.worldbank.org/server/api/pid/find?id=10986/40219'
print(f"Resolving handle 10986/40219...")
r_handle = requests.get(handle_url, headers=headers, timeout=15)
if r_handle.status_code == 200:
    item_data = r_handle.json()
    item_uuid = item_data.get('id')
    print(f"Item UUID: {item_uuid}")
    
    # Get bundles/bitstreams
    bitstreams_url = f"https://openknowledge.worldbank.org/server/api/core/items/{item_uuid}/bundles"
    r_bundles = requests.get(bitstreams_url, headers=headers, timeout=15)
    bundles = r_bundles.json().get('_embedded', {}).get('bundles', [])
    
    pdf_url = None
    for b in bundles:
        if b.get('name') == 'ORIGINAL':
            bs_link = b.get('_links', {}).get('bitstreams', {}).get('href')
            r_bs = requests.get(bs_link, headers=headers, timeout=15)
            bitstreams = r_bs.json().get('_embedded', {}).get('bitstreams', [])
            for bs in bitstreams:
                name = bs.get('name', '')
                if name.endswith('.pdf') and 'en' in name.lower() or name.endswith('.pdf'):
                    pdf_url = bs.get('_links', {}).get('content', {}).get('href')
                    print(f"Found PDF bitstream: {name} -> {pdf_url}")
                    break
            if pdf_url:
                break
    
    if pdf_url:
        wb_2023_path = DATA_DIR / 'world_bank_annual_report_2023.pdf'
        print(f"Downloading World Bank Annual Report 2023 to {wb_2023_path}...")
        r_pdf = requests.get(pdf_url, headers=headers, stream=True, timeout=60)
        with open(wb_2023_path, 'wb') as f:
            for chunk in r_pdf.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded World Bank 2023 PDF ({wb_2023_path.stat().st_size} bytes)")
        
        # Verify text extraction
        reader = PdfReader(wb_2023_path)
        print(f"Total pages in WB 2023: {len(reader.pages)}")
        t = reader.pages[4].extract_text() or ''
        print(f"Sample text page 5 (length {len(t)}): {repr(t[:150])}")
else:
    print(f"Handle lookup failed: {r_handle.status_code}")
