#!/usr/bin/env python3
"""
Daily rate scheduler for Frankie mortgage rate ingestion.
Runs automatically to pull rates and store them for Gemini analysis.
"""

import schedule
import time
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List
import logging
from pathlib import Path

# Import our rate modules
from zillow_scraper import scrape_zillow_rates
from parser import normalize_zillow_rates, calculate_rate_stats


class RateScheduler:
    """Manages daily rate collection and storage for Gemini analysis."""
    
    def __init__(self, data_dir: str = "rate_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.data_dir / 'rate_scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create subdirectories
        (self.data_dir / 'raw').mkdir(exist_ok=True)
        (self.data_dir / 'normalized').mkdir(exist_ok=True)
        (self.data_dir / 'daily').mkdir(exist_ok=True)
        (self.data_dir / 'historical').mkdir(exist_ok=True)
    
    def collect_daily_rates(self) -> Dict:
        """
        Collect rates from all sources and store them.
        This is the main function that runs daily.
        """
        timestamp = datetime.now(timezone.utc)
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%Y-%m-%d_%H-%M-%S')
        
        self.logger.info(f"Starting daily rate collection for {date_str}")
        
        try:
            # Step 1: Scrape rates from Zillow
            self.logger.info("Scraping rates from Zillow...")
            raw_rates = scrape_zillow_rates()
            self.logger.info(f"Found {len(raw_rates)} raw rates from Zillow")
            
            # Step 2: Normalize rates
            self.logger.info("Normalizing rates...")
            normalized_rates = normalize_zillow_rates(raw_rates)
            self.logger.info(f"Normalized {len(normalized_rates)} rates")
            
            # Step 3: Calculate statistics
            stats = calculate_rate_stats(normalized_rates)
            
            # Step 4: Create daily summary
            daily_summary = {
                "date": date_str,
                "timestamp": timestamp.isoformat(),
                "raw_rates_count": len(raw_rates),
                "normalized_rates_count": len(normalized_rates),
                "statistics": stats,
                "sources": list(set(rate.get('source', 'unknown') for rate in normalized_rates)),
                "loan_types": list(set(rate.get('loan_type', 'unknown') for rate in normalized_rates))
            }
            
            # Step 5: Save all data
            self._save_daily_data(raw_rates, normalized_rates, daily_summary, date_str, time_str)
            
            # Step 6: Update current rates file (latest)
            self._update_current_rates(normalized_rates, timestamp)
            
            # Step 7: Clean up old data (keep last 30 days)
            self._cleanup_old_data()
            
            self.logger.info(f"Daily rate collection completed successfully for {date_str}")
            
            return {
                "success": True,
                "date": date_str,
                "rates_collected": len(normalized_rates),
                "summary": daily_summary
            }
            
        except Exception as e:
            self.logger.error(f"Error in daily rate collection: {e}")
            return {
                "success": False,
                "date": date_str,
                "error": str(e)
            }
    
    def _save_daily_data(self, raw_rates: List[Dict], normalized_rates: List[Dict], 
                        daily_summary: Dict, date_str: str, time_str: str):
        """Save daily rate data to files."""
        
        # Save raw rates
        raw_file = self.data_dir / 'raw' / f'raw_rates_{date_str}_{time_str}.json'
        with open(raw_file, 'w') as f:
            json.dump(raw_rates, f, indent=2)
        
        # Save normalized rates
        normalized_file = self.data_dir / 'normalized' / f'normalized_rates_{date_str}_{time_str}.json'
        with open(normalized_file, 'w') as f:
            json.dump(normalized_rates, f, indent=2)
        
        # Save daily summary
        summary_file = self.data_dir / 'daily' / f'daily_summary_{date_str}.json'
        with open(summary_file, 'w') as f:
            json.dump(daily_summary, f, indent=2)
        
        # Save to historical (append to daily file)
        historical_file = self.data_dir / 'historical' / f'rates_{date_str}.json'
        historical_data = {
            "date": date_str,
            "timestamp": time_str,
            "raw_rates": raw_rates,
            "normalized_rates": normalized_rates,
            "summary": daily_summary
        }
        
        with open(historical_file, 'w') as f:
            json.dump(historical_data, f, indent=2)
        
        self.logger.info(f"Saved daily data: {raw_file}, {normalized_file}, {summary_file}")
    
    def _update_current_rates(self, normalized_rates: List[Dict], timestamp: datetime):
        """Update the current rates file with latest data."""
        
        current_rates_file = self.data_dir / 'current_rates.json'
        current_data = {
            "last_updated": timestamp.isoformat(),
            "rates": normalized_rates,
            "rate_count": len(normalized_rates)
        }
        
        with open(current_rates_file, 'w') as f:
            json.dump(current_data, f, indent=2)
        
        self.logger.info(f"Updated current rates file: {current_rates_file}")
    
    def _cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data files, keeping only the specified number of days."""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        # Clean up raw rates
        raw_dir = self.data_dir / 'raw'
        for file in raw_dir.glob('raw_rates_*.json'):
            file_date_str = file.stem.split('_')[2]  # Extract date from filename
            try:
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                if file_date < cutoff_date:
                    file.unlink()
                    self.logger.info(f"Deleted old raw rates file: {file}")
            except ValueError:
                continue
        
        # Clean up normalized rates
        normalized_dir = self.data_dir / 'normalized'
        for file in normalized_dir.glob('normalized_rates_*.json'):
            file_date_str = file.stem.split('_')[2]
            try:
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                if file_date < cutoff_date:
                    file.unlink()
                    self.logger.info(f"Deleted old normalized rates file: {file}")
            except ValueError:
                continue
    
    def get_current_rates(self) -> List[Dict]:
        """Get the most recent rates for Gemini analysis."""
        
        current_rates_file = self.data_dir / 'current_rates.json'
        
        if not current_rates_file.exists():
            self.logger.warning("No current rates file found, collecting rates now...")
            self.collect_daily_rates()
        
        try:
            with open(current_rates_file, 'r') as f:
                data = json.load(f)
                return data.get('rates', [])
        except Exception as e:
            self.logger.error(f"Error reading current rates: {e}")
            return []
    
    def get_rates_for_gemini(self, loan_types: List[str] = None) -> Dict:
        """
        Get formatted rates data specifically for Gemini analysis.
        
        Args:
            loan_types: Optional list of loan types to filter by
            
        Returns:
            Dict: Formatted rates data for Gemini
        """
        
        rates = self.get_current_rates()
        
        if loan_types:
            rates = [rate for rate in rates if rate.get('loan_type') in loan_types]
        
        # Format for Gemini analysis
        gemini_data = {
            "current_rates": rates,
            "rate_summary": {
                "total_rates": len(rates),
                "loan_types": list(set(rate.get('loan_type') for rate in rates)),
                "rate_range": {
                    "min": min([rate.get('rate', 0) for rate in rates]) if rates else 0,
                    "max": max([rate.get('rate', 0) for rate in rates]) if rates else 0
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "rate_breakdown": {}
        }
        
        # Add breakdown by loan type
        for rate in rates:
            loan_type = rate.get('loan_type')
            if loan_type not in gemini_data["rate_breakdown"]:
                gemini_data["rate_breakdown"][loan_type] = []
            gemini_data["rate_breakdown"][loan_type].append(rate)
        
        return gemini_data
    
    def start_scheduler(self, run_time: str = "09:00"):
        """
        Start the daily scheduler.
        
        Args:
            run_time: Time to run daily (24-hour format, e.g., "09:00")
        """
        
        self.logger.info(f"Starting rate scheduler, will run daily at {run_time}")
        
        # Schedule daily rate collection
        schedule.every().day.at(run_time).do(self.collect_daily_rates)
        
        # Run once immediately if no current rates exist
        if not (self.data_dir / 'current_rates.json').exists():
            self.logger.info("No current rates found, running initial collection...")
            self.collect_daily_rates()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_once(self):
        """Run rate collection once (for testing or manual execution)."""
        return self.collect_daily_rates()


if __name__ == "__main__":
    import argparse
    from datetime import timedelta
    
    parser = argparse.ArgumentParser(description='Frankie Rate Scheduler')
    parser.add_argument('--run-time', default='09:00', help='Daily run time (HH:MM)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--data-dir', default='rate_data', help='Data directory')
    
    args = parser.parse_args()
    
    scheduler = RateScheduler(args.data_dir)
    
    if args.once:
        print("Running rate collection once...")
        result = scheduler.run_once()
        print(f"Result: {result}")
    else:
        print(f"Starting scheduler, will run daily at {args.run_time}")
        scheduler.start_scheduler(args.run_time) 