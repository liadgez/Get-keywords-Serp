# Keyword-Driven Competitor Discovery Tool

A lightweight tool that converts high-intent keywords into ranked competitor domains by analyzing search engine results.

## Overview

This tool helps marketers identify competitors by:
1. Taking a list of target keywords (5-15 keywords)
2. Fetching top search results for each keyword
3. Extracting and ranking competitor domains by frequency
4. Exporting results to CSV or Google Sheets

## How It Works

**Input:** Curated list of high-intent keywords
**Process:** Fetch top 20 Google/Bing results per keyword
**Output:** Ranked competitor domains based on SERP appearances

### Example Output
| Domain | Appearances | Weighted Score |
|--------|-------------|----------------|
| nike.com | 9 | 180 |
| adidas.com | 7 | 140 |
| footlocker.com | 5 | 85 |

## Benefits
- **Control:** Define competitive landscape through keyword selection
- **Accuracy:** Based on real SERP visibility
- **Cost-effective:** No paid SEO tools required

## Technical Approach

### Method
1. **Keyword Input:** Accept keywords via text file or CSV
2. **SERP Fetching:** Use SerpApi (free tier) or web scraping
3. **Domain Extraction:** Clean URLs to root domains using `tldextract`
4. **Ranking:** Weight results by SERP position (rank 1 = 20pts, rank 20 = 1pt)
5. **Export:** Output to CSV and Google Sheets

### Tech Stack
- **Python 3.11+**
- **SerpApi** (100 free searches/month) or BeautifulSoup
- **SQLite** for data storage
- **pandas** for data manipulation
- **Google Sheets API** for export

## Usage

```bash
python main.py --keywords keywords.csv --engine google --depth 20 --sheet_id <sheet_id>
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test the pipeline
python3 test_pipeline.py

# 3. Run analysis
python3 main.py analyze --keywords "nike shoes,running shoes,athletic footwear"
```

For detailed setup instructions, see [SETUP.md](SETUP.md)

## Performance
- <10 minutes per keyword batch
- <2s per SERP call (API) or <5s (scraping)
- Handles 5-15 keywords efficiently

## Limitations
- Google rate limiting may apply
- Results may vary by location/personalization
- Manual keyword curation required

---

*For detailed MVP specification and technical architecture, see [MVP_SPEC.md](MVP_SPEC.md)*