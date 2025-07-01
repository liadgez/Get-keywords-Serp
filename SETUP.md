# Setup Guide - Keyword-Driven Competitor Discovery Tool

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the Pipeline
```bash
# Test with mock data to verify everything works
python3 test_pipeline.py

# Test database functionality
python3 test_database.py
```

### 3. Set Up API Key (Optional but Recommended)
1. Sign up for SerpApi at https://serpapi.com/ (100 free searches/month)
2. Copy `.env.example` to `.env`
3. Add your API key to `.env`:
   ```
   SERPAPI_KEY=your_api_key_here
   ```

### 4. Run Analysis
```bash
# With API key (recommended)
python3 main.py analyze --keywords "nike shoes,running shoes,athletic footwear"

# Without API key (uses web scraping, may be blocked)
python3 main.py analyze --keywords-file keywords_sample.csv --output-csv results.csv
```

## Usage Examples

### Basic Analysis
```bash
python3 main.py analyze --keywords "nike shoes,running shoes"
```

### Advanced Analysis with Export
```bash
python3 main.py analyze \
  --keywords-file keywords_sample.csv \
  --output-csv results.csv \
  --output-excel analysis.xlsx \
  --depth 20 \
  --min-appearances 2 \
  --verbose
```

### View Results History
```bash
# Show recent analysis runs
python3 main.py history

# Show detailed results for a specific run
python3 main.py show 1

# Show database statistics
python3 main.py stats
```

## Google Sheets Integration (Optional)

### 1. Set Up Google Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create credentials (Desktop Application)
5. Download credentials JSON file

### 2. Install Google Sheets Dependencies
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. Configure Environment
Update `.env` file:
```
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_SHEETS_TOKEN_FILE=path/to/token.json
```

### 4. Export to Google Sheets
```bash
python3 main.py analyze \
  --keywords "your keywords" \
  --sheet-id "your_google_sheet_id"
```

## Project Structure

```
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── keywords_sample.csv    # Sample keywords
├── test_pipeline.py       # Pipeline test with mock data
├── test_database.py       # Database functionality test
├── src/
│   ├── input.py           # Keyword validation
│   ├── serp.py            # SERP fetching
│   ├── parser.py          # Domain parsing
│   ├── db.py              # Database operations
│   └── export.py          # Export functionality
├── data/                  # Database storage
└── logs/                  # Application logs
```

## Troubleshooting

### Web Scraping Issues
- **Problem**: Getting 0 results without API key
- **Solution**: Google blocks automated requests. Use SerpApi or try with different keywords

### SSL Warnings
- **Problem**: urllib3 SSL warnings on macOS
- **Solution**: These are harmless warnings, functionality is not affected

### Import Errors
- **Problem**: Module not found errors
- **Solution**: Ensure all dependencies are installed with `pip install -r requirements.txt`

### Google Sheets Errors
- **Problem**: Authentication issues
- **Solution**: 
  1. Verify credentials file path in `.env`
  2. Delete `token.json` and re-authenticate
  3. Check API is enabled in Google Cloud Console

## Performance Tips

1. **Use SerpApi**: Much more reliable than web scraping
2. **Limit keywords**: 5-15 keywords work best for performance
3. **Use depth wisely**: 20 results per keyword is usually sufficient
4. **Filter results**: Use `--min-appearances` to focus on frequent competitors

## API Limits

- **SerpApi Free Tier**: 100 searches/month
- **Google Sheets API**: 100 requests/100 seconds per user
- **Web Scraping**: May be blocked by search engines

## File Formats

### Keywords Input
- **CSV**: First column contains keywords, header row automatically skipped
- **Text**: One keyword per line
- **String**: Comma-separated keywords

### Output Formats
- **CSV**: Basic tabular format
- **Excel**: Multi-sheet with summary
- **Google Sheets**: Live collaborative format

## Next Steps

1. Run `python3 test_pipeline.py` to verify installation
2. Set up SerpApi key for reliable data
3. Create your own keywords file
4. Run analysis and export results
5. Set up Google Sheets for team collaboration