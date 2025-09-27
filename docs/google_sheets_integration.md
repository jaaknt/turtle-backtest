# Google Sheets Integration for Trade Signals

This document explains how to set up and use the Google Sheets integration to automatically export trade signals from your backtesting runs.

## Overview

The Google Sheets integration allows you to automatically export trading signals generated during backtesting to Google Sheets. This enables you to:

- Track daily signals in a centralized location
- Share signals with team members
- Build dashboards and visualizations
- Maintain historical signal records
- Analyze signal patterns over time

## Setup Instructions

### 1. Google Cloud Project Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

### 2. Service Account Setup (Recommended)

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `turtle-backtest-sheets`
   - Description: `Service account for turtle backtest sheets integration`
4. Click "Create and Continue"
5. Grant the service account the "Editor" role (or create a custom role with Sheets access)
6. Click "Done"

### 3. Download Credentials

1. Click on the created service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Download the JSON file and save it securely (e.g., `~/.config/turtle/service_account.json`)

### 4. Create Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Copy the spreadsheet ID from the URL:
   - URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
   - The `{SPREADSHEET_ID}` is what you need

### 5. Share Spreadsheet with Service Account

1. Open your spreadsheet
2. Click "Share" button
3. Add the service account email (found in the JSON credentials file)
4. Give it "Editor" permissions
5. Click "Send"

## Code Usage

### Basic Configuration

```python
from turtle.google.models import GoogleSheetsConfig
from turtle.service.portfolio_service import PortfolioService

# Configure Google Sheets
config = GoogleSheetsConfig(
    sheet_id="your_spreadsheet_id_here",
    worksheet_name="daily_signals",
    credentials_path="path/to/service_account.json",
    auth_type="service_account",
    create_worksheet_if_missing=True,
    clear_before_export=False
)

# Use with PortfolioService
service = PortfolioService(
    trading_strategy=your_strategy,
    exit_strategy=your_exit_strategy,
    bars_history=your_bars_repo,
    start_date=start_date,
    end_date=end_date,
    google_sheets_config=config  # Add this parameter
)

# Run backtest - signals will be automatically exported
service.run_backtest(start_date, end_date, universe)
```

### Advanced Configuration

```python
config = GoogleSheetsConfig(
    sheet_id="your_spreadsheet_id",
    worksheet_name="signals",
    credentials_path="~/.config/turtle/service_account.json",
    auth_type="service_account",
    create_worksheet_if_missing=True,    # Create worksheet if it doesn't exist
    clear_before_export=False            # Append to existing data
)
```

### Manual Signal Export

```python
from turtle.google.signal_exporter import SignalExporter
from turtle.signal.models import Signal
from datetime import datetime

# Create signals (example)
signals = [
    Signal(ticker="AAPL", date=datetime.now(), ranking=85),
    Signal(ticker="GOOGL", date=datetime.now(), ranking=78),
]

# Export manually
exporter = SignalExporter(config, bars_history_repo)
success = exporter.export_signals(signals, "MyStrategy", include_price_data=True)

if success:
    print("Signals exported successfully!")
```

## Sheet Structure

The exported data includes the following columns:

| Column | Description |
|--------|-------------|
| Date | Signal date (YYYY-MM-DD) |
| Ticker | Stock symbol |
| Ranking | Signal ranking (1-100) |
| Strategy | Trading strategy name |
| Export Timestamp | When the data was exported |
| Price | Current stock price (if available) |
| Volume | Trading volume (if available) |

## Configuration Options

### GoogleSheetsConfig Parameters

- **sheet_id**: Google Sheets document ID (from URL)
- **worksheet_name**: Name of the specific worksheet/tab
- **credentials_path**: Path to service account JSON file
- **auth_type**: Authentication type (`"service_account"` or `"oauth"`)
- **create_worksheet_if_missing**: Create worksheet if it doesn't exist (default: True)
- **clear_before_export**: Clear existing data before adding new data (default: False)

### Export Options

- **include_price_data**: Include current price and volume data (requires bars_history)
- **daily_worksheets**: Automatically create date-based worksheet names
- **batch_export**: Export multiple days of signals at once

## Error Handling

The integration includes comprehensive error handling:

- **API Rate Limits**: Automatic retry with exponential backoff
- **Authentication Errors**: Clear error messages for credential issues
- **Network Issues**: Retry logic for temporary connectivity problems
- **Worksheet Errors**: Automatic worksheet creation if configured

All errors are logged but won't stop the backtesting process.

## Security Considerations

1. **Credentials Storage**: Store service account JSON files securely
2. **File Permissions**: Set appropriate file permissions (600) on credential files
3. **Environment Variables**: Consider using environment variables for sensitive paths
4. **Shared Access**: Only share spreadsheets with necessary team members

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check service account JSON file path
   - Verify service account has access to the spreadsheet
   - Ensure Google Sheets API is enabled

2. **Worksheet Not Found**
   - Set `create_worksheet_if_missing=True`
   - Check worksheet name spelling
   - Verify spreadsheet ID is correct

3. **Permission Denied**
   - Share spreadsheet with service account email
   - Check service account permissions in Google Cloud

4. **API Quota Exceeded**
   - The system automatically retries with backoff
   - Consider reducing export frequency for large datasets

### Testing Connection

```python
from turtle.google.signal_exporter import SignalExporter

exporter = SignalExporter(config)
if exporter.test_connection():
    print("Connection successful!")
else:
    print("Connection failed - check configuration")
```

## Environment Variables

You can use environment variables for configuration:

```bash
export GOOGLE_SHEETS_ID="your_spreadsheet_id"
export GOOGLE_SHEETS_CREDENTIALS="/path/to/service_account.json"
```

```python
import os

config = GoogleSheetsConfig(
    sheet_id=os.getenv("GOOGLE_SHEETS_ID"),
    worksheet_name="daily_signals",
    credentials_path=os.getenv("GOOGLE_SHEETS_CREDENTIALS")
)
```

## Best Practices

1. **Daily Worksheets**: Use date-based worksheet names for better organization
2. **Backup Credentials**: Keep backup copies of service account credentials
3. **Regular Testing**: Test the integration periodically to ensure it's working
4. **Monitor Quotas**: Monitor Google Sheets API usage to avoid hitting limits
5. **Error Monitoring**: Set up logging to monitor export success/failure rates

## Integration with Existing Workflows

The Google Sheets integration is designed to work seamlessly with existing turtle backtest workflows:

- **Automatic Export**: Signals are exported automatically during backtesting
- **Non-Blocking**: Export failures won't stop the backtesting process
- **Optional**: Can be enabled/disabled via configuration
- **Flexible**: Supports multiple export strategies and configurations