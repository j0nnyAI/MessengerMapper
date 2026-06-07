"""
Facebook Messenger Chat Timeline — Interactive HTML Exhibit Engine
Reads the same data sources and emits an interactive HTML timeline (EXHIBITS/timeline_report.html).
"""

import argparse
import sys
from pathlib import Path
from core.parse_calls import main as parse_calls_main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forensic HTML timeline exhibit builder")
    parser.add_argument("--date-from", type=str, default=None,
                        help="Filter records starting from this date in YYYY-MM-DD format")
    parser.add_argument("-f", "--file", type=str, required=True,
                        help="Path to the target raw Messenger JSON export file")
    parser.add_argument("--left-party", type=str, required=True,
                        help="Explicit name string of the outbound/left-column participant")
    parser.add_argument("--right-party", type=str, required=True,
                        help="Explicit name string of the inbound/right-column participant")
    
    args = parser.parse_args()
    
    # Run the ingestion and HTML build via parse_calls.py core logic
    try:
        parse_calls_main(
            date_from=args.date_from,
            file_path=args.file,
            left_name=args.left_party,
            right_name=args.right_party
        )
    except Exception as e:
        print(f"[ERROR] HTML timeline compilation failed: {e}")
        sys.exit(1)
