"""
Export functionality for CSV and Google Sheets.
"""
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import typer

from .parser import CompetitorResult

try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    typer.echo("Warning: Google Sheets functionality not available. Install google-api-python-client.")


class ExportManager:
    """Manager for exporting competitor analysis results."""
    
    def __init__(self):
        """Initialize export manager."""
        self.google_sheets_scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
        self.token_file = os.getenv('GOOGLE_SHEETS_TOKEN_FILE')
    
    def export_to_csv(
        self,
        competitors: List[CompetitorResult],
        keywords: List[str],
        output_path: str = None,
        include_keyword_details: bool = True
    ) -> str:
        """
        Export competitor results to CSV file.
        
        Args:
            competitors: List of competitor results
            keywords: List of keywords analyzed
            output_path: Output file path (optional)
            include_keyword_details: Include per-keyword appearance data
            
        Returns:
            Path to created CSV file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results_{timestamp}.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        rows = []
        
        for rank, competitor in enumerate(competitors, 1):
            row = {
                'rank': rank,
                'domain': competitor.domain,
                'appearances': competitor.count,
                'weighted_score': round(competitor.weighted_score, 2)
            }
            
            # Add per-keyword data if requested
            if include_keyword_details:
                for keyword in keywords:
                    serp_rank = competitor.keyword_appearances.get(keyword, 0)
                    row[f'kw_{keyword.replace(" ", "_")}'] = serp_rank if serp_rank > 0 else ''
            
            rows.append(row)
        
        # Write CSV
        if rows:
            fieldnames = list(rows[0].keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return str(output_path)
    
    def export_summary_csv(
        self,
        competitors: List[CompetitorResult],
        keywords: List[str],
        analysis_summary: Dict,
        output_path: str = None
    ) -> str:
        """
        Export summary analysis to CSV.
        
        Args:
            competitors: List of competitor results
            keywords: List of keywords analyzed
            analysis_summary: Summary statistics
            output_path: Output file path (optional)
            
        Returns:
            Path to created CSV file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"summary_{timestamp}.csv"
        
        output_path = Path(output_path)
        
        # Create summary data
        summary_data = {
            'Analysis Date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'Keywords Analyzed': [', '.join(keywords)],
            'Total Keywords': [len(keywords)],
            'Total Competitors Found': [analysis_summary.get('total_competitors', 0)],
            'Top Competitor': [analysis_summary.get('top_competitor', 'N/A')],
            'Average Weighted Score': [round(analysis_summary.get('avg_weighted_score', 0), 2)]
        }
        
        # Write summary CSV
        pd.DataFrame(summary_data).to_csv(output_path, index=False)
        
        return str(output_path)
    
    def _get_google_sheets_service(self):
        """Get authenticated Google Sheets service."""
        if not GOOGLE_SHEETS_AVAILABLE:
            raise RuntimeError("Google Sheets API not available. Install required packages.")
        
        creds = None
        
        # Load existing token
        if self.token_file and Path(self.token_file).exists():
            creds = Credentials.from_authorized_user_file(self.token_file, self.google_sheets_scopes)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file or not Path(self.credentials_file).exists():
                    raise FileNotFoundError(
                        f"Google Sheets credentials file not found: {self.credentials_file}. "
                        "Download from Google Cloud Console and update .env file."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.google_sheets_scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            if self.token_file:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
        
        return build('sheets', 'v4', credentials=creds)
    
    def export_to_google_sheets(
        self,
        competitors: List[CompetitorResult],
        keywords: List[str],
        spreadsheet_id: str,
        sheet_name: str = None
    ) -> str:
        """
        Export competitor results to Google Sheets.
        
        Args:
            competitors: List of competitor results
            keywords: List of keywords analyzed
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Sheet name (optional, auto-generated if not provided)
            
        Returns:
            URL to the Google Sheet
        """
        if not GOOGLE_SHEETS_AVAILABLE:
            raise RuntimeError("Google Sheets functionality not available.")
        
        service = self._get_google_sheets_service()
        
        if sheet_name is None:
            sheet_name = f"SERP Analysis {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Prepare data for Google Sheets
        headers = ['Rank', 'Domain', 'Appearances', 'Weighted Score'] + \
                 [f'KW: {kw}' for kw in keywords]
        
        data = [headers]
        
        for rank, competitor in enumerate(competitors, 1):
            row = [
                rank,
                competitor.domain,
                competitor.count,
                round(competitor.weighted_score, 2)
            ]
            
            # Add per-keyword ranks
            for keyword in keywords:
                serp_rank = competitor.keyword_appearances.get(keyword, '')
                row.append(serp_rank if serp_rank > 0 else '')
            
            data.append(row)
        
        try:
            # Create new sheet
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]
            
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            # Write data to sheet
            range_name = f"'{sheet_name}'!A1"
            
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': data}
            ).execute()
            
            # Format header row
            format_requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': self._get_sheet_id(service, spreadsheet_id, sheet_name),
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': len(headers)
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                            'textFormat': {'bold': True}
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]
            
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': format_requests}
            ).execute()
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
        except Exception as e:
            typer.echo(f"Error exporting to Google Sheets: {str(e)}")
            raise
    
    def _get_sheet_id(self, service, spreadsheet_id: str, sheet_name: str) -> int:
        """Get sheet ID by name."""
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        raise ValueError(f"Sheet '{sheet_name}' not found")
    
    def create_excel_export(
        self,
        competitors: List[CompetitorResult],
        keywords: List[str],
        analysis_summary: Dict,
        output_path: str = None
    ) -> str:
        """
        Create Excel file with multiple sheets for comprehensive analysis.
        
        Args:
            competitors: List of competitor results
            keywords: List of keywords analyzed
            analysis_summary: Summary statistics
            output_path: Output file path (optional)
            
        Returns:
            Path to created Excel file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"competitor_analysis_{timestamp}.xlsx"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main results sheet
            main_data = []
            for rank, competitor in enumerate(competitors, 1):
                row = {
                    'Rank': rank,
                    'Domain': competitor.domain,
                    'Appearances': competitor.count,
                    'Weighted Score': round(competitor.weighted_score, 2)
                }
                
                # Add per-keyword data
                for keyword in keywords:
                    serp_rank = competitor.keyword_appearances.get(keyword, 0)
                    row[f'KW: {keyword}'] = serp_rank if serp_rank > 0 else ''
                
                main_data.append(row)
            
            pd.DataFrame(main_data).to_excel(writer, sheet_name='Competitors', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': ['Analysis Date', 'Keywords Analyzed', 'Total Keywords', 
                          'Total Competitors', 'Top Competitor', 'Avg Weighted Score'],
                'Value': [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ', '.join(keywords),
                    len(keywords),
                    analysis_summary.get('total_competitors', 0),
                    analysis_summary.get('top_competitor', 'N/A'),
                    round(analysis_summary.get('avg_weighted_score', 0), 2)
                ]
            }
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        return str(output_path)


def create_export_manager() -> ExportManager:
    """
    Create ExportManager instance.
    
    Returns:
        Configured ExportManager instance
    """
    return ExportManager()