from kickbase_api.user import login
from kickbase_api.league import get_league_id
from kickbase_api.manager import get_managers
from kickbase_api.others import get_achievement_reward
from kickbase_api.config import BASE_URL, get_json_with_token
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

# Settings
league_name = "Bunsenliga"
start_budget = 50_000_000
league_start_date = "2025-12-22"
output_folder = "transaction_exports"

def get_all_activities(token, league_id):
    """Fetch all activities from the league."""
    url = f"{BASE_URL}/leagues/{league_id}/activitiesFeed?max=5000"
    data = get_json_with_token(url, token)
    return data["af"]

def get_user_id_map(token, league_id):
    """Get mapping of user ID to username."""
    managers = get_managers(token, league_id)
    return {str(uid): name for name, uid in managers}

def build_user_transactions(token, league_id, activities, user_id_map, start_budget, league_start_date):
    """Build transaction history per user with running balance."""

    users = {}
    login_bonuses = []  # Collect all login bonuses
    achievements = []   # Collect all achievements

    for entry in activities:
        t = entry.get("t")
        dt = entry.get("dt")
        data = entry.get("data", {})

        # Filter by league start date
        if dt[:10] < league_start_date:
            continue

        if t == 15:  # Trade
            buyer = data.get("byr")
            seller = data.get("slr")
            player = data.get("pn", "Unknown")
            price = data.get("trp", 0)

            if buyer:
                if buyer not in users:
                    users[buyer] = []
                users[buyer].append({
                    "date": dt,
                    "type": "buy",
                    "description": f"Bought {player}" + (f" from {seller}" if seller else " (market)"),
                    "amount": -price
                })

            if seller:
                if seller not in users:
                    users[seller] = []
                users[seller].append({
                    "date": dt,
                    "type": "sell",
                    "description": f"Sold {player}" + (f" to {buyer}" if buyer else " (market)"),
                    "amount": price
                })

        elif t == 22:  # Login bonus
            bonus = data.get("bn", 0)
            if bonus:
                login_bonuses.append({"date": dt, "amount": bonus})

        elif t == 26:  # Achievement
            achievement_type = data.get("t")
            name = data.get("n", "Achievement")
            try:
                amount, reward = get_achievement_reward(token, league_id, achievement_type)
                reward_amount = amount * reward
                if reward_amount > 0:
                    achievements.append({"date": dt, "name": name, "amount": reward_amount})
            except:
                pass

    # Daily login bonus per user
    daily_login_bonus = 100_000

    # Calculate total achievement bonus and distribute equally
    total_achievement_bonus = sum(a["amount"] for a in achievements)
    num_users = len(user_id_map)
    achievement_per_user = total_achievement_bonus // num_users if num_users > 0 else 0

    # Calculate days since league start
    from datetime import datetime, timedelta
    start_date = datetime.strptime(league_start_date, "%Y-%m-%d")
    today = datetime.now()
    days_since_start = (today - start_date).days + 1

    print(f"  Daily login bonus: {daily_login_bonus:,} × {days_since_start} days = {daily_login_bonus * days_since_start:,} per user")
    print(f"  Total achievement bonus: {total_achievement_bonus:,} -> {achievement_per_user:,} per user (estimated)")

    # Ensure all users exist and add start + daily bonuses
    for username in user_id_map.values():
        if username not in users:
            users[username] = []

        # Add start budget entry
        users[username].append({
            "date": league_start_date + "T00:00:00Z",
            "type": "start",
            "description": "Starting budget",
            "amount": start_budget
        })

        # Add daily login bonus for each day
        for day in range(days_since_start):
            bonus_date = start_date + timedelta(days=day)
            users[username].append({
                "date": bonus_date.strftime("%Y-%m-%dT00:00:00Z"),
                "type": "login_bonus",
                "description": f"Daily login bonus (day {day + 1})",
                "amount": daily_login_bonus
            })

        if achievement_per_user > 0:
            users[username].append({
                "date": league_start_date + "T00:00:02Z",
                "type": "achievement_bonus",
                "description": f"Achievement bonus (estimated, {total_achievement_bonus:,} total ÷ {num_users} users)",
                "amount": achievement_per_user
            })

    # Sort transactions by date and calculate running balance
    for user in users:
        users[user].sort(key=lambda x: x["date"])

        saldo = 0  # Start from 0, first entry is the start budget
        for tx in users[user]:
            saldo += tx["amount"]
            tx["saldo"] = saldo

    return users

def export_to_csv(users, output_folder):
    """Export each user's transactions to a CSV file."""

    os.makedirs(output_folder, exist_ok=True)

    for user, transactions in users.items():
        if not transactions:
            continue

        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        df = df[["date", "type", "description", "amount", "saldo"]]

        filename = f"{output_folder}/{user}_transactions.csv"
        df.to_csv(filename, index=False)
        print(f"  Exported {len(df)} transactions for {user}")

if __name__ == "__main__":
    # Login
    USERNAME = os.getenv("KICK_USER")
    PASSWORD = os.getenv("KICK_PASS")
    token = login(USERNAME, PASSWORD)
    print("Logged in to Kickbase.")

    # Get league
    league_id = get_league_id(token, league_name)
    print(f"League: {league_name} (ID: {league_id})")

    # Get user ID mapping
    user_id_map = get_user_id_map(token, league_id)
    print(f"Found {len(user_id_map)} users")

    # Fetch activities
    print("\nFetching activities...")
    activities = get_all_activities(token, league_id)
    print(f"Found {len(activities)} total activities")

    # Build user transactions
    print("\nBuilding user transactions...")
    users = build_user_transactions(token, league_id, activities, user_id_map, start_budget, league_start_date)
    print(f"Found {len(users)} users with transactions")

    # Export to CSV
    print(f"\nExporting to {output_folder}/...")
    export_to_csv(users, output_folder)

    print("\nNote: Login/achievement bonuses are estimated (total ÷ users)")
    print("Done!")
