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
