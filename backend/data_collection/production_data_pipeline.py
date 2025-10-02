"""
Production Data Pipeline for EPL Match Prediction
==================================================

Enterprise-grade data collection system with:
- Multi-source data aggregation (FBref, Understat, Football-Data.org)
- Robust error handling and retry logic
- Data validation and quality checks
- Incremental updates
- Logging and monitoring
- Cache management

Data Sources:
1. FBref: Match results, team stats, squad data
2. Understat: xG, shot data
3. Football-Data.org: Historical betting odds (optional)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import hashlib
from pathlib import Path
try:
    import sqlalchemy as sa
    from sqlalchemy.orm import Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    Session = None

import warnings
warnings.filterwarnings('ignore')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionDataPipeline:
    """
    Production-grade data pipeline for football match data

    Features:
    - Automatic retry with exponential backoff
    - Rate limiting (3 requests/second)
    - Data validation
    - Incremental updates
    - Multi-source data merging
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        cache_dir: str = "./data_cache",
        max_retries: int = 3,
        request_delay: float = 3.0
    ):
        self.db_session = db_session
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.max_retries = max_retries
        self.request_delay = request_delay

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36'
        }

        self.fbref_base = "https://fbref.com"
        self.understat_base = "https://understat.com"

        # EPL team mapping (canonical names)
        self.team_mapping = {
            'Arsenal': 'Arsenal',
            'Aston Villa': 'Aston Villa',
            'Bournemouth': 'Bournemouth',
            'Brentford': 'Brentford',
            'Brighton': 'Brighton',
            'Brighton & Hove Albion': 'Brighton',
            'Chelsea': 'Chelsea',
            'Crystal Palace': 'Crystal Palace',
            'Everton': 'Everton',
            'Fulham': 'Fulham',
            'Ipswich Town': 'Ipswich',
            'Ipswich': 'Ipswich',
            'Leicester City': 'Leicester',
            'Leicester': 'Leicester',
            'Liverpool': 'Liverpool',
            'Manchester City': 'Manchester City',
            'Manchester United': 'Manchester United',
            'Man City': 'Manchester City',
            'Man United': 'Manchester United',
            'Newcastle United': 'Newcastle',
            'Newcastle': 'Newcastle',
            "Nott'ham Forest": 'Nottingham Forest',
            'Nottingham Forest': 'Nottingham Forest',
            'Southampton': 'Southampton',
            'Tottenham': 'Tottenham',
            'Tottenham Hotspur': 'Tottenham',
            'West Ham': 'West Ham',
            'West Ham United': 'West Ham',
            'Wolverhampton': 'Wolves',
            'Wolves': 'Wolves',
            'Wolverhampton Wanderers': 'Wolves'
        }

    def _make_request(
        self,
        url: str,
        retries: int = 0,
        timeout: int = 30
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic

        Parameters:
        -----------
        url : str
            Target URL
        retries : int
            Current retry count
        timeout : int
            Request timeout in seconds

        Returns:
        --------
        Response object or None if failed
        """
        if retries >= self.max_retries:
            logger.error(f"Max retries exceeded for {url}")
            return None

        try:
            # Rate limiting
            time.sleep(self.request_delay)

            logger.debug(f"Requesting {url} (attempt {retries + 1}/{self.max_retries})")

            response = requests.get(
                url,
                headers=self.headers,
                timeout=timeout
            )
            response.raise_for_status()

            return response

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited - exponential backoff
                wait_time = (2 ** retries) * 5
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                return self._make_request(url, retries + 1, timeout)

            elif e.response.status_code in [500, 502, 503, 504]:
                # Server error - retry
                logger.warning(f"Server error {e.response.status_code}. Retrying...")
                time.sleep(2 ** retries)
                return self._make_request(url, retries + 1, timeout)

            else:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {url}. Retrying...")
            return self._make_request(url, retries + 1, timeout)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def _get_cache_path(self, cache_key: str) -> Path:
        """Generate cache file path"""
        hash_key = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"

    def _read_cache(self, cache_key: str, max_age_hours: int = 24) -> Optional[Dict]:
        """Read from cache if fresh"""
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if file_age > timedelta(hours=max_age_hours):
            logger.debug(f"Cache expired for {cache_key}")
            return None

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            logger.debug(f"Cache hit for {cache_key}")
            return data
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def _write_cache(self, cache_key: str, data: Dict):
        """Write to cache"""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, default=str)
            logger.debug(f"Cache written for {cache_key}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team names to canonical form"""
        if not team_name or not isinstance(team_name, str):
            return team_name

        team_name = team_name.strip()
        return self.team_mapping.get(team_name, team_name)

    def fetch_fbref_matches(
        self,
        season: str = "2024-2025",
        competition: str = "Premier-League",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch match results from FBref

        Parameters:
        -----------
        season : str
            Season in format "2024-2025"
        competition : str
            Competition name (URL-friendly)
        use_cache : bool
            Use cached data if available

        Returns:
        --------
        DataFrame with columns:
            - date, home_team, away_team, home_score, away_score, venue, etc.
        """
        cache_key = f"fbref_matches_{season}_{competition}"

        # Try cache first
        if use_cache:
            cached = self._read_cache(cache_key, max_age_hours=6)
            if cached:
                logger.info(f"Using cached FBref data for {season}")
                return pd.DataFrame(cached)

        url = f"{self.fbref_base}/en/comps/9/schedule/{competition}-Scores-and-Fixtures"
        logger.info(f"Fetching FBref matches: {url}")

        response = self._make_request(url)
        if not response:
            logger.error("Failed to fetch FBref data")
            return pd.DataFrame()

        try:
            soup = BeautifulSoup(response.content, 'lxml')

            # Find schedule table
            table = soup.find('table', {'id': lambda x: x and 'sched' in x})
            if not table:
                table = soup.find('table', class_='stats_table')

            if not table:
                logger.error("Could not find schedule table in FBref")
                return pd.DataFrame()

            # Parse table
            df = pd.read_html(str(table))[0]

            # Clean column names
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(0)

            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            # Extract key columns (handle variations)
            column_mapping = {
                'wk': 'week',
                'day': 'day_of_week',
                'date': 'date',
                'time': 'time',
                'home': 'home_team',
                'away': 'away_team',
                'score': 'score',
                'xg': 'home_xg',
                'xg.1': 'away_xg',
                'venue': 'venue',
                'referee': 'referee',
                'attendance': 'attendance'
            }

            df = df.rename(columns=column_mapping, errors='ignore')

            # Parse score
            if 'score' in df.columns:
                df[['home_score', 'away_score']] = df['score'].str.split('–', expand=True)
                df['home_score'] = pd.to_numeric(df['home_score'], errors='coerce')
                df['away_score'] = pd.to_numeric(df['away_score'], errors='coerce')

            # Parse date
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')

            # Normalize team names
            if 'home_team' in df.columns:
                df['home_team'] = df['home_team'].apply(self.normalize_team_name)
            if 'away_team' in df.columns:
                df['away_team'] = df['away_team'].apply(self.normalize_team_name)

            # Add season
            df['season'] = season
            df['competition'] = 'EPL'

            # Remove rows with missing teams (headers, etc.)
            df = df.dropna(subset=['home_team', 'away_team'])

            # Select final columns
            final_columns = [
                'season', 'competition', 'week', 'date', 'time',
                'home_team', 'away_team', 'home_score', 'away_score',
                'home_xg', 'away_xg', 'venue', 'referee', 'attendance'
            ]
            df = df[[col for col in final_columns if col in df.columns]]

            logger.info(f"Fetched {len(df)} matches from FBref")

            # Cache
            if use_cache:
                self._write_cache(cache_key, df.to_dict(orient='records'))

            return df

        except Exception as e:
            logger.error(f"Error parsing FBref data: {e}", exc_info=True)
            return pd.DataFrame()

    def fetch_understat_matches(
        self,
        season: int = 2024,
        league: str = "EPL",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch xG data from Understat

        Parameters:
        -----------
        season : int
            Season year (start year, e.g., 2024 for 2024-25)
        league : str
            League code
        use_cache : bool
            Use cached data

        Returns:
        --------
        DataFrame with xG data
        """
        cache_key = f"understat_{league}_{season}"

        if use_cache:
            cached = self._read_cache(cache_key, max_age_hours=12)
            if cached:
                logger.info(f"Using cached Understat data for {season}")
                return pd.DataFrame(cached)

        url = f"{self.understat_base}/league/{league}/{season}"
        logger.info(f"Fetching Understat data: {url}")

        response = self._make_request(url)
        if not response:
            logger.warning("Failed to fetch Understat data")
            return pd.DataFrame()

        try:
            # Understat data is embedded in JavaScript
            # Parse JSON from script tags
            soup = BeautifulSoup(response.content, 'lxml')
            scripts = soup.find_all('script')

            matches_data = []
            for script in scripts:
                if 'datesData' in script.text:
                    # Extract JSON data
                    start = script.text.find('JSON.parse(\'') + 12
                    end = script.text.find('\')', start)
                    json_str = script.text[start:end].encode().decode('unicode_escape')
                    matches_data = json.loads(json_str)
                    break

            if not matches_data:
                logger.warning("No Understat data found in page")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(matches_data)

            # Normalize team names
            if 'h' in df.columns:
                df['home_team'] = df['h'].apply(lambda x: x.get('title', '')).apply(self.normalize_team_name)
            if 'a' in df.columns:
                df['away_team'] = df['a'].apply(lambda x: x.get('title', '')).apply(self.normalize_team_name)

            # Extract xG
            if 'xG' in df.columns:
                df['home_xg'] = df['xG'].apply(lambda x: x.get('h', np.nan) if isinstance(x, dict) else np.nan)
                df['away_xg'] = df['xG'].apply(lambda x: x.get('a', np.nan) if isinstance(x, dict) else np.nan)

            # Extract scores
            if 'goals' in df.columns:
                df['home_score'] = df['goals'].apply(lambda x: x.get('h', np.nan) if isinstance(x, dict) else np.nan)
                df['away_score'] = df['goals'].apply(lambda x: x.get('a', np.nan) if isinstance(x, dict) else np.nan)

            # Date
            if 'datetime' in df.columns:
                df['date'] = pd.to_datetime(df['datetime'], errors='coerce')

            # Select columns
            final_columns = ['date', 'home_team', 'away_team', 'home_score', 'away_score', 'home_xg', 'away_xg']
            df = df[[col for col in final_columns if col in df.columns]]

            logger.info(f"Fetched {len(df)} matches from Understat")

            if use_cache:
                self._write_cache(cache_key, df.to_dict(orient='records'))

            return df

        except Exception as e:
            logger.error(f"Error parsing Understat data: {e}", exc_info=True)
            return pd.DataFrame()

    def merge_data_sources(
        self,
        fbref_df: pd.DataFrame,
        understat_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge data from multiple sources

        Strategy:
        - Use FBref as primary source
        - Supplement xG from Understat if missing
        - Match on (date, home_team, away_team)
        """
        if fbref_df.empty:
            return understat_df
        if understat_df.empty:
            return fbref_df

        logger.info("Merging FBref and Understat data...")

        # Merge on date + teams
        merged = fbref_df.merge(
            understat_df[['date', 'home_team', 'away_team', 'home_xg', 'away_xg']],
            on=['date', 'home_team', 'away_team'],
            how='left',
            suffixes=('', '_understat')
        )

        # Fill missing xG from Understat
        if 'home_xg_understat' in merged.columns:
            merged['home_xg'] = merged['home_xg'].fillna(merged['home_xg_understat'])
            merged['away_xg'] = merged['away_xg'].fillna(merged['away_xg_understat'])
            merged = merged.drop(columns=['home_xg_understat', 'away_xg_understat'])

        logger.info(f"Merged dataset: {len(merged)} matches")

        return merged

    def validate_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate data quality

        Checks:
        - Required columns present
        - No duplicate matches
        - Scores are valid (0-20 range)
        - Team names are known

        Returns:
        --------
        (validated_df, list of warnings)
        """
        warnings_list = []

        # Required columns
        required = ['date', 'home_team', 'away_team']
        missing = [col for col in required if col not in df.columns]
        if missing:
            warnings_list.append(f"Missing required columns: {missing}")
            return df, warnings_list

        # Remove duplicates
        initial_len = len(df)
        df = df.drop_duplicates(subset=['date', 'home_team', 'away_team'], keep='last')
        if len(df) < initial_len:
            warnings_list.append(f"Removed {initial_len - len(df)} duplicate matches")

        # Validate scores
        if 'home_score' in df.columns and 'away_score' in df.columns:
            # Convert to numeric first
            df['home_score'] = pd.to_numeric(df['home_score'], errors='coerce')
            df['away_score'] = pd.to_numeric(df['away_score'], errors='coerce')

            # Check for invalid scores (completed matches only)
            completed_matches = df[df['home_score'].notna() & df['away_score'].notna()]
            invalid_scores = completed_matches[
                (completed_matches['home_score'] < 0) | (completed_matches['home_score'] > 20) |
                (completed_matches['away_score'] < 0) | (completed_matches['away_score'] > 20)
            ]
            if len(invalid_scores) > 0:
                warnings_list.append(f"Found {len(invalid_scores)} matches with invalid scores")
                # Remove only invalid completed matches
                df = df[~df.index.isin(invalid_scores.index)]

        # Validate team names (remove NaN first)
        known_teams = set(self.team_mapping.values())
        home_teams = set(df['home_team'].dropna().unique())
        away_teams = set(df['away_team'].dropna().unique())
        unknown_home = home_teams - known_teams
        unknown_away = away_teams - known_teams
        if unknown_home or unknown_away:
            unknown = unknown_home | unknown_away
            # Filter out non-string values
            unknown = {t for t in unknown if isinstance(t, str)}
            if unknown:
                warnings_list.append(f"Unknown teams: {unknown}")

        logger.info(f"Data validation: {len(df)} matches passed, {len(warnings_list)} warnings")

        return df, warnings_list

    def collect_historical_data(
        self,
        seasons: List[str] = ["2023-2024", "2024-2025"],
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Collect complete historical data for multiple seasons

        Parameters:
        -----------
        seasons : List[str]
            List of seasons (e.g., ["2023-2024", "2024-2025"])
        use_cache : bool
            Use cached data

        Returns:
        --------
        DataFrame with all match data
        """
        logger.info(f"Collecting data for seasons: {seasons}")

        all_data = []

        for season in seasons:
            # FBref data
            fbref_df = self.fetch_fbref_matches(season, use_cache=use_cache)

            # Understat data (convert season format)
            season_year = int(season.split('-')[0])
            understat_df = self.fetch_understat_matches(season_year, use_cache=use_cache)

            # Merge
            merged_df = self.merge_data_sources(fbref_df, understat_df)

            if not merged_df.empty:
                all_data.append(merged_df)

        if not all_data:
            logger.error("No data collected")
            return pd.DataFrame()

        # Combine all seasons
        final_df = pd.concat(all_data, ignore_index=True)

        # Validate
        final_df, warnings = self.validate_data(final_df)

        for warning in warnings:
            logger.warning(warning)

        # Sort by date (ensure datetime type)
        if 'date' in final_df.columns:
            final_df['date'] = pd.to_datetime(final_df['date'], errors='coerce')
            final_df = final_df.sort_values('date')

        logger.info(f"Total matches collected: {len(final_df)}")
        logger.info(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        logger.info(f"Completed matches: {final_df['home_score'].notna().sum()}")

        return final_df


# ============================================================
# Command-line interface
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Collect EPL match data')
    parser.add_argument(
        '--seasons',
        nargs='+',
        default=['2023-2024', '2024-2025'],
        help='Seasons to collect (e.g., 2023-2024 2024-2025)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache'
    )
    parser.add_argument(
        '--output',
        default='epl_matches.csv',
        help='Output CSV file'
    )

    args = parser.parse_args()

    # Run pipeline
    pipeline = ProductionDataPipeline()
    df = pipeline.collect_historical_data(
        seasons=args.seasons,
        use_cache=not args.no_cache
    )

    # Save
    if not df.empty:
        df.to_csv(args.output, index=False)
        print(f"\n✓ Data saved to {args.output}")
        print(f"  Total matches: {len(df)}")
        print(f"  Completed: {df['home_score'].notna().sum()}")
        print(f"  Upcoming: {df['home_score'].isna().sum()}")
    else:
        print("\n✗ No data collected")
