# Refurbed Price Tracker 2.0

A Python project for automated price monitoring, data quality checks, data cleaning and interactive analytics.

## What the project does

The application monitors the price of a refurbished iPhone 13 and selected suggested configurations from Refurbed.

The project includes:

- automated web scraping,
- price history stored in CSV,
- price alerts,
- duplicate detection,
- invalid price detection,
- RAW and CLEAN data layers,
- data cleaning,
- analytics,
- an interactive Streamlit dashboard.

## Project architecture

```text
Refurbed website
      |
      v
refurbed_scraper.py
      |
      v
refurbed_prices.csv          <- RAW data
      |
      +--> data_quality.py
      |
      v
data_cleaning.py
      |
      v
refurbed_prices_clean.csv    <- CLEAN data
      |
      +--> analytics.py
      |
      v
app.py
      |
      v
Streamlit dashboard
```

## Data quality case

During development, the scraper detected a historical price anomaly for an iPhone 13 configuration.

A 512 GB green configuration was recorded with a price of approximately PLN 389,000, while surrounding observations were around PLN 2,000.

The issue showed that a regular expression could technically match a malformed or unrelated numeric value as a product price.

To reduce the impact of bad data, the project now:

- validates suggested configuration prices against a business range,
- excludes suspicious values from normal analytics,
- keeps RAW data for audit purposes,
- creates a separate CLEAN dataset,
- detects duplicate configuration records,
- keeps data-quality logic separate from analytics.

This prevents known bad records from distorting KPIs and charts without silently modifying the original source data.

## Main components

### `refurbed_scraper.py`

Downloads the product page and extracts:

- current main product price,
- suggested configurations,
- storage,
- condition,
- color,
- price alert status.

It also:

- deduplicates repeated configuration matches within one run,
- validates extracted prices,
- can log suspicious price candidates separately.

### `data_quality.py`

Checks RAW data for:

- full duplicates,
- duplicate records within one measurement,
- duplicate main-product records,
- duplicate suggested configurations,
- suspicious prices,
- incorrect alert values,
- invalid dates.

It also calculates an overall data-quality score.

### `data_cleaning.py`

Creates a separate cleaned dataset.

The cleaning stage:

- removes redundant duplicate records,
- excludes invalid prices,
- preserves the original RAW CSV,
- saves the cleaned result as `refurbed_prices_clean.csv`.

### `analytics.py`

Calculates:

- current and previous price,
- absolute and percentage price change,
- minimum price,
- maximum price,
- average price,
- number of measurements,
- price history.

### `app.py`

Streamlit dashboard with four sections:

- Dashboard,
- Configurations,
- Data Quality,
- Clean Data.

The analytics sections use CLEAN data, while Data Quality audits RAW data.

## Example cleaning result

One development run contained:

```text
RAW records: 637
Removed duplicate records: 108
Removed invalid price records: 1
CLEAN records: 528
```

The duplicate detection report identified historical duplicate configuration records while the main-product history remained free of duplicates.

## Tech stack

- Python
- pandas
- requests
- BeautifulSoup
- regular expressions
- CSV
- Streamlit
- Git / GitHub
- GitHub Actions

## Run locally

Install dependencies:

```bash
py -m pip install -r requirements.txt
```

Run the scraper:

```bash
py refurbed_scraper.py
```

Run the data-quality report:

```bash
py data_quality.py
```

Create the cleaned dataset:

```bash
py data_cleaning.py
```

Run the dashboard:

```bash
py -m streamlit run app.py
```

## Why I built it

The project started as a simple price-monitoring script and was expanded into a small end-to-end data application.

The goal was to practice building a working pipeline rather than isolated coding exercises:

```text
data collection -> validation -> cleaning -> analytics -> dashboard
```

The project also focuses on debugging real data problems and improving the system when unexpected records appear.

## Next steps

- deploy the Streamlit application,
- improve HTML targeting in the scraper,
- add anomaly visibility to the dashboard,
- add screenshots and a live demo link,
- improve automated testing.
