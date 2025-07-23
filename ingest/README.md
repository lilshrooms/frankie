# Frankie Rate Ingestion System

This system automatically collects, normalizes, and stores mortgage rates for use in Gemini analysis of prospective homeowners.

## Overview

The rate ingestion system consists of several components:

1. **Zillow Scraper** (`zillow_scraper.py`) - Scrapes current mortgage rates from Zillow
2. **Rate Parser** (`parser.py`) - Normalizes and standardizes rate data
3. **Quote Engine** (`engine/quote_engine.py`) - Generates personalized rate quotes with LLPAs
4. **Rate Scheduler** (`rate_scheduler.py`) - Manages daily rate collection and storage
5. **Gemini Integration** (`gemini_rate_integration.py`) - Provides rates to Gemini for analysis

## Quick Start

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Test the System

```bash
# Test the complete workflow
python test_workflow.py

# Test the quote engine
cd ../engine && python quote_engine.py

# Test with real rates
python test_with_real_rates.py
```

### 3. Run Daily Rate Collection

```bash
# Run once manually
python rate_scheduler.py --once

# Start the scheduler (runs daily at 9:00 AM)
python rate_scheduler.py --run-time 09:00
```

## Setup for Production

### Option 1: Cron Job (Recommended)

```bash
# Make the setup script executable
chmod +x ../scripts/setup_cron.sh

# Edit the script to set the correct Frankie directory path
nano ../scripts/setup_cron.sh

# Run the setup script
sudo ../scripts/setup_cron.sh
```

### Option 2: Systemd Service

```bash
# Edit the service file to set correct paths
nano ../scripts/frankie_rate_scheduler.service

# Install the service
sudo cp ../scripts/frankie_rate_scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable frankie_rate_scheduler
sudo systemctl start frankie_rate_scheduler
```

## Data Structure

The system creates the following directory structure:

```
rate_data/
├── current_rates.json          # Latest rates (used by Gemini)
├── rate_scheduler.log          # Scheduler logs
├── raw/                        # Raw scraped data
│   └── raw_rates_YYYY-MM-DD_HH-MM-SS.json
├── normalized/                 # Normalized rate data
│   └── normalized_rates_YYYY-MM-DD_HH-MM-SS.json
├── daily/                      # Daily summaries
│   └── daily_summary_YYYY-MM-DD.json
└── historical/                 # Historical data
    └── rates_YYYY-MM-DD.json
```

## API Usage

### Get Current Rates for Gemini

```python
from gemini_rate_integration import GeminiRateIntegration

integration = GeminiRateIntegration()

# Get formatted rates context for Gemini
context = integration.get_current_rates_context()

# Generate quote for specific borrower
borrower_info = {
    "loan_amount": 500000,
    "credit_score": 720,
    "ltv": 85
}
quote = integration.generate_rate_quote_for_borrower(borrower_info)

# Format for Gemini analysis
email_body = "Hi, I'm looking to refinance..."
formatted = integration.format_for_gemini_analysis(email_body, borrower_info)
```

### Quote Engine Usage

```python
from engine.quote_engine import quote_rate, get_quote_comparison

# Single quote
quote = quote_rate(500000, 720, 85, "30yr_fixed", rates_data)

# Compare all loan types
comparison = get_quote_comparison(500000, 720, 85, rates_data)
```

## Rate Sources

Currently supported:
- **Zillow** - Primary source for current market rates

Future sources planned:
- Freddie Mac
- Fannie Mae
- Bankrate
- Mortgage News Daily

## Loan Types Supported

- `30yr_fixed` - 30-year fixed rate mortgage
- `15yr_fixed` - 15-year fixed rate mortgage
- `fha_30yr` - FHA 30-year fixed
- `va_30yr` - VA 30-year fixed
- `jumbo_30yr` - Jumbo 30-year fixed
- `5_1_arm` - 5/1 Adjustable Rate Mortgage
- `7_1_arm` - 7/1 Adjustable Rate Mortgage
- `10_1_arm` - 10/1 Adjustable Rate Mortgage

## LLPAs (Loan Level Price Adjustments)

The system applies realistic LLPAs based on:

### Credit Score Adjustments
- < 680: +0.125%
- 680-719: +0.0625%
- 720-759: +0.0%
- 760+: -0.0625% (premium for excellent credit)

### LTV Adjustments
- > 80%: +0.25%
- 70-80%: +0.125%
- 60-70%: +0.0625%
- < 60%: +0.0%

### Loan Type Adjustments
- FHA: +0.375% (typically higher)
- VA: +0.125% (typically lower)
- Jumbo: +0.25% (typically higher)
- ARMs: -0.125% (typically lower)

## Monitoring

### Check Scheduler Status

```bash
# View logs
tail -f rate_data/rate_scheduler.log

# Check cron job
crontab -l

# Check systemd service
sudo systemctl status frankie_rate_scheduler
```

### Data Validation

```bash
# Check current rates
cat rate_data/current_rates.json

# View daily summary
cat rate_data/daily/daily_summary_$(date +%Y-%m-%d).json

# Check rate trends
python gemini_rate_integration.py
```

## Troubleshooting

### Common Issues

1. **No rates found**: Check if Zillow scraper is working
2. **Import errors**: Ensure all dependencies are installed
3. **Permission errors**: Check file permissions for data directory
4. **Timezone issues**: Ensure system timezone is set correctly

### Debug Mode

```bash
# Run with verbose logging
python rate_scheduler.py --once --debug

# Test individual components
python zillow_scraper.py
python parser.py
```

## Integration with Frankie

The rate data is automatically available to:

1. **Gemini Analyzer** - For analyzing borrower emails with current rates
2. **Email Response System** - For including rate quotes in responses
3. **Admin Dashboard** - For displaying current market conditions
4. **Quote Generation** - For providing personalized rate quotes

## Configuration

### Environment Variables

```bash
# Optional: Set custom data directory
export FRANKIE_RATE_DATA_DIR="/custom/path/to/rate_data"

# Optional: Set custom run time
export FRANKIE_RATE_RUN_TIME="10:00"
```

### Customization

- **Rate Sources**: Add new scrapers in `zillow_scraper.py`
- **LLPAs**: Modify adjustment logic in `engine/quote_engine.py`
- **Storage**: Change data format in `rate_scheduler.py`
- **Schedule**: Adjust timing in cron or systemd configuration

## Security Considerations

- Rate data is stored locally by default
- No sensitive borrower information is stored
- Logs may contain rate information (non-sensitive)
- Consider encryption for production deployments

## Performance

- Daily collection takes ~30 seconds
- Data storage: ~1MB per month
- Memory usage: < 50MB
- CPU usage: Minimal (mostly I/O)

## Support

For issues or questions:
1. Check the logs in `rate_data/rate_scheduler.log`
2. Review this README
3. Test individual components
4. Check system resources and permissions 