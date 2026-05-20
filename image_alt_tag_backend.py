import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FILTER_PREFIX = "https://static.bankbazaar.com/images/india/infographic"
EXCLUDE_URL = "https://static.bankbazaar.com/images/india/infographic/apple-store-button.svg"
OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)

def get_urls_from_user() -> List[str]:
    """Get URLs from command line input."""
    print("Paste all the URLs (separated by commas or spaces):\n")
    raw_input = input().strip()
    urls = [url.strip() for url in raw_input.replace(",", " ").split()]
    return urls

def get_urls_from_file(file_path: str) -> List[str]:
    """Get URLs from a text file (one URL per line)."""
    try:
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(urls)} URLs from {file_path}")
        return urls
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []

def extract_filtered_images(url: str) -> List[Dict]:
    """Extract images with specific prefix from a URL."""
    filtered_data = []
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')

        found = False
        for img in images:
            src = img.get('src', '')
            if src.startswith(FILTER_PREFIX) and src != EXCLUDE_URL:
                alt = img.get('alt', 'No alt text')
                filtered_data.append({
                    "Page URL": url,
                    "Image Path": src,
                    "Alt Text": alt,
                    "Timestamp": datetime.now().isoformat()
                })
                found = True

        if not found:
            filtered_data.append({
                "Page URL": url,
                "Image Path": "No images found",
                "Alt Text": "N/A",
                "Timestamp": datetime.now().isoformat()
            })

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {str(e)}")
        filtered_data.append({
            "Page URL": url,
            "Image Path": "Failed to fetch",
            "Alt Text": str(e),
            "Timestamp": datetime.now().isoformat()
        })

    return filtered_data

def save_to_excel(data: List[Dict], output_file: str = None) -> str:
    """Save data to Excel file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"filtered_image_report_{timestamp}.xlsx"
    else:
        output_file = OUTPUT_DIR / output_file

    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    logger.info(f"Report saved as {output_file}")
    return str(output_file)

def save_to_json(data: List[Dict], output_file: str = None) -> str:
    """Save data to JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"filtered_image_report_{timestamp}.json"
    else:
        output_file = OUTPUT_DIR / output_file

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Report saved as {output_file}")
    return str(output_file)

def run_filtered_image_extractor(
    urls: List[str] = None,
    output_format: str = "xlsx",
    output_file: str = None
) -> str:
    """
    Main function to run the image extractor.
    
    Args:
        urls: List of URLs to process
        output_format: Output format ('xlsx' or 'json')
        output_file: Custom output file name
    
    Returns:
        Path to the generated report
    """
    if urls is None:
        urls = get_urls_from_user()
    
    if not urls:
        logger.warning("No URLs entered.")
        return None

    logger.info(f"🔍 Extracting images that start with: {FILTER_PREFIX}")
    logger.info(f"❌ Excluding image: {EXCLUDE_URL}")

    all_data = []

    for url in urls:
        logger.info(f"Processing: {url}")
        page_data = extract_filtered_images(url)
        all_data.extend(page_data)

    # Save to specified format
    if output_format.lower() == "json":
        report_path = save_to_json(all_data, output_file)
    else:
        report_path = save_to_excel(all_data, output_file)

    logger.info(f"✅ Processing complete! Report: {report_path}")
    return report_path

def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Extract images with specific alt text from web pages"
    )
    parser.add_argument(
        '--urls',
        nargs='+',
        help='Space-separated list of URLs to process'
    )
    parser.add_argument(
        '--file',
        help='Text file containing URLs (one per line)'
    )
    parser.add_argument(
        '--output',
        default='filtered_image_report.xlsx',
        help='Output file name (default: filtered_image_report.xlsx)'
    )
    parser.add_argument(
        '--format',
        choices=['xlsx', 'json'],
        default='xlsx',
        help='Output format (default: xlsx)'
    )

    args = parser.parse_args()

    # Get URLs from different sources
    urls = []
    if args.file:
        urls = get_urls_from_file(args.file)
    elif args.urls:
        urls = args.urls
    else:
        urls = get_urls_from_user()

    # Run the extractor
    report_path = run_filtered_image_extractor(
        urls=urls,
        output_format=args.format,
        output_file=args.output
    )

    if report_path:
        print(f"\n📊 Report generated: {report_path}")

if __name__ == "__main__":
    main()
