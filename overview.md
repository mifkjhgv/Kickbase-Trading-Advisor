## Konsti Repository Overview

This is **KickAdvisor** - a Python-based trading advisor for **Kickbase** (a fantasy football/soccer game).

### What It Does

1. **Estimates manager budgets** - Tracks buy/sell activity to reverse-engineer how much money competitors have
2. **Predicts player market values** - Uses machine learning (RandomForest) to forecast 1-day ahead price changes
3. **Sends daily email recommendations** - Automated HTML reports with actionable trading advice

### Architecture

```
├── daily_predictions.py     # Main entry point/orchestrator
├── kickbase_api/            # API wrapper for Kickbase
│   ├── user.py              # Auth, squads, budgets
│   ├── league.py            # League data, market, activities
│   ├── player.py            # Player stats & market values
│   └── manager.py           # Manager info
├── features/
│   ├── budgets.py           # Budget estimation logic
│   ├── notifier.py          # Email delivery
│   └── predictions/         # ML pipeline
│       ├── data_handler.py  # SQLite caching, API fetching
│       ├── preprocessing.py # Feature engineering
│       ├── modeling.py      # RandomForest training
│       └── predictions.py   # Live predictions
└── player_data_total.db     # Local SQLite cache
```

### Tech Stack

- **Python** with pandas, scikit-learn, numpy
- **SQLite** for local data caching
- **Gmail SMTP** for notifications
- **GitHub Actions** for daily automated runs

### Key Features

- Parallel API fetching (ThreadPoolExecutor)
- Smart caching to minimize API calls
- Configurable for Bundesliga, 2.Bundesliga, or La Liga
- Works locally with `.env` or via GitHub Secrets

### Database Schema: `player_data_1d`

SQLite table in `player_data_total.db`:

| Column | Type | API Source | Description |
|--------|------|------------|-------------|
| `player_id` | INTEGER | `i` | Unique Kickbase player ID |
| `team_id` | INTEGER | `tid` | Team ID |
| `team_name` | TEXT | `tn` | Team name |
| `first_name` | TEXT | `fn` | Player's first name |
| `last_name` | TEXT | `ln` | Player's last name |
| `position` | TEXT | `pos` | Position (1=GK, 2=DEF, 3=MID, 4=FWD) |
| `md` | DATE | `md` | Matchday date |
| `date` | DATE | merged | Row date (mv or matchday) |
| `p` | REAL | `p` | Points scored |
| `mp` | INTEGER | `mp` | Minutes played |
| `ppm` | REAL | calculated | Points per minute |
| `t1` | INTEGER | `t1` | Home team ID |
| `t2` | INTEGER | `t2` | Away team ID |
| `t1g` | INTEGER | `t1g` | Home team goals |
| `t2g` | INTEGER | `t2g` | Away team goals |
| `won` | INTEGER | calculated | 1=win, 0=loss, NULL=draw |
| `k` | TEXT | `k` | Event keys (goals, assists, cards) as CSV |
| `mv` | REAL | `mv` | Market value |

**API Endpoints:**
- `/competitions/{id}/players/{playerId}` → player info
- `/competitions/{id}/players/{playerId}/marketvalue/{timeframe}` → market values
- `/competitions/{id}/players/{playerId}/performance` → match performance

**Data Merge:** `merge_asof` joins market values with most recent performance data

### Feature Engineering

Computed features in `preprocessing.py`:

| Feature | Description |
|---------|-------------|
| `mv_change_1d` | MV difference from yesterday |
| `mv_trend_1d` | MV % change from yesterday |
| `mv_change_3d` | MV difference from 3 days ago |
| `mv_vol_3d` | 3-day rolling std of MV |
| `mv_trend_7d` | MV % change over 7 days |
| `market_divergence` | Player MV vs league avg (3-day rolling) |
| `days_to_next` | Days until next matchday |

**Target:** `mv_target_clipped` — next day MV change, with outliers clipped at 2.5×IQR

### Model Configuration

RandomForestRegressor (`modeling.py`):
- `n_estimators`: 500
- `max_depth`: 20
- `min_samples_split`: 5
- `min_samples_leaf`: 2
- `max_features`: sqrt

**Train/Test Split:** 75/25 time-based (no shuffle, avoids data leakage)

### Important Constants

| Value | Usage |
|-------|-------|
| **22:15 Berlin** | MV update cutoff — before this, "today" means yesterday's data |
| **5000** | Min predicted MV gain to show in market recommendations |
| **365 days** | Max MV history fetched |
| **50 matchdays** | Max performance history fetched |

### Output DataFrames

**Market Recommendations:** Players on market with predicted MV gain >5000
- `hours_to_exp`: Hours until auction ends
- `expiring_today`: True if expires before next 22:00

**Squad Recommendations:** Your players ranked by predicted MV change
- `s_11_prob`: Starting XI probability (Pro users only)
