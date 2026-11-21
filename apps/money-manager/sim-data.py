#!/usr/bin/env python3
"""Simulated data for trying out the UI. Run it on the Pi.

    python3 sim-data.py add      # one year of made-up entries, up to today
    python3 sim-data.py remove   # delete every simulated entry and account, nothing else

Entries go in through the app's own JSON API (so balances, keys and transfer pairs are
built exactly like real ones). Every simulated row carries the memo "[sim]"; removal
deletes only those rows. A backup of the database is written before either step.
"""
import json
import os
import random
import shutil
import sqlite3
import sys
import time
import urllib.request
from datetime import date, timedelta

API = os.environ.get("MM_URL", "http://127.0.0.1:8888") + "/api/"
DB = os.environ.get("MM_DB", "/var/lib/money-manager/money.sqlite")
TAG = "[sim]"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def backup(label):
    dst = f"{DB}.bak-{label}-{time.strftime('%Y%m%d-%H%M%S')}"
    src = sqlite3.connect(DB)
    out = sqlite3.connect(dst)
    src.backup(out)
    out.close()
    os.chmod(dst, 0o600)
    print("backup:", dst)


def remove():
    backup("before-sim-remove")
    c = sqlite3.connect(DB, timeout=10)
    with c:
        n = c.execute("delete from ZINOUTCOME where ZMEMO=?", (TAG,)).rowcount
        a = c.execute("delete from ZASSET where ZMEMO=?", (TAG,)).rowcount
    print(f"removed {n} simulated entries and {a} simulated accounts")


def add():
    meta = call("GET", "meta")
    def plain(name):  # "🍜 Food" -> "Food"; "Gcash loan all" stays as is
        first, _, rest = name.partition(" ")
        return rest if rest and not first[0].isalnum() else name

    cats = {(kind, plain(c["name"])): c["id"] for kind in ("income", "expense") for c in meta["categories"][kind]}
    backup("before-sim-add")

    # Accounts: reuse a real Gcash account if there is one; make the rest and tag them.
    accts = {a["name"].lower(): a["id"] for a in meta["accounts"]}
    made = []

    def account(name, group):
        if name.lower() in accts:
            return accts[name.lower()]
        uid = call("POST", "accounts", {"name": name, "groupId": group})["id"]
        made.append(uid)
        return uid

    cash = account("Cash", "11")
    gcash = account("Gcash", "11")
    bpi = account("BPI Savings", "4")
    c = sqlite3.connect(DB, timeout=10)
    with c:
        c.executemany("update ZASSET set ZMEMO=? where ZUID=?", [(TAG, u) for u in made])

    rng = random.Random(2026)
    bal = {cash: 0.0, gcash: 0.0, bpi: 0.0}
    rows = 0

    def tx(kind, day, amount, account_id, category, note=""):
        nonlocal rows
        amount = round(amount, 2)
        call("POST", "transactions", {"kind": kind, "date": day.isoformat(), "amount": amount,
                                      "accountId": account_id, "categoryId": cats[(kind, category)], "note": note, "memo": TAG})
        bal[account_id] += amount if kind == "income" else -amount
        rows += 1

    def move(day, amount, src, dst, note):
        nonlocal rows
        call("POST", "transactions", {"kind": "transfer", "date": day.isoformat(), "amount": amount,
                                      "fromId": src, "toId": dst, "note": note, "memo": TAG})
        bal[src] -= amount
        bal[dst] += amount
        rows += 1

    def spend(day, amount, category, note, prefer=None):
        # Pay from cash or Gcash; top up from savings first if that wallet is running low.
        acct = prefer or (cash if rng.random() < 0.55 else gcash)
        if bal[acct] < amount + 300:
            top = 3000 if acct == cash else 5000
            move(day, top, bpi, acct, "ATM withdrawal" if acct == cash else "Cash in")
        tx("expense", day, amount, acct, category, note)

    today = date.today()
    start = date(today.year - 1, today.month, 1)
    tx("income", start, 18500, bpi, "Other", "Opening balance")
    tx("income", start, 1200, cash, "Other", "Opening balance")

    food = ["Carinderia lunch", "Jollibee", "Breakfast pandesal", "Milk tea", "7-Eleven", "Grocery, SM",
            "Mang Inasal", "Merienda", "Coffee", "Dinner, turo-turo", "Palengke"]
    ride = ["Jeep", "Jeep", "Tricycle", "MRT", "Grab", "Angkas", "Bus"]
    d = start
    while d <= today:
        dom, dow = d.day, d.weekday()
        # Pay days: 15th and the last day of the month.
        last = (d.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if dom == 15 or d == last:
            tx("income", d, 13250, bpi, "Salary", "Payroll")
        if d.month == 12 and dom == 15:
            tx("income", d, 26500, bpi, "Bonus", "13th month pay")
        if dom == 5:
            spend(d, 4000, "Household", "Rent share", gcash)
            spend(d, 1800, "Gcash loan all", "Monthly payment", gcash)
        if dom == 10:
            spend(d, rng.uniform(1100, 1900), "Household", "Meralco", gcash)
            spend(d, rng.uniform(280, 420), "Household", "Maynilad", gcash)
        if dom == 12:
            spend(d, 1299, "Household", "Fiber internet", gcash)
        if dom == 20:
            spend(d, rng.choice([1200, 1450, 1500, 1680]), "Atome CC", "Atome bill", gcash)
        if dom == 25:
            spend(d, rng.uniform(450, 750), "Pets", "Dog food")

        for _ in range(rng.choice([1, 2, 2])):
            spend(d, rng.choice([55, 75, 95, 120, 145, 180, 220, 260]) * rng.uniform(0.9, 1.15),
                  "Food", rng.choice(food))
        if dow < 5:
            spend(d, rng.choice([26, 30, 40, 52, 60, 85, 140, 190]), "Transport", rng.choice(ride), cash)
        if dow >= 4 and rng.random() < 0.3:
            spend(d, rng.uniform(250, 1100), "Social Life", rng.choice(["Inuman w/ friends", "Birthday dinner", "Movie", "Samgyup", "Videoke"]))
        if rng.random() < 0.04:
            spend(d, rng.uniform(350, 1800), "Apparel", rng.choice(["Shirt, Uniqlo", "Shoes", "Shopee haul"]))
        if rng.random() < 0.025:
            spend(d, rng.uniform(250, 1400), "Health", rng.choice(["Pharmacy", "Checkup", "Vitamins"]))
        if rng.random() < 0.02:
            spend(d, rng.uniform(150, 700), "Beauty", rng.choice(["Haircut", "Skincare"]))
        if (d.month == 12 and 15 <= dom <= 24 and rng.random() < 0.4) or (d.month == 2 and dom == 14):
            spend(d, rng.uniform(400, 1600), "Gift", "Regalo" if d.month == 12 else "Valentine's")
        if rng.random() < 0.012:
            tx("income", d, rng.choice([500, 800, 1000, 1500]), gcash, "Allowance", "From Mama")
        if rng.random() < 0.01:
            tx("income", d, rng.uniform(1500, 4000), gcash, "Other", "Sideline, graphic design")
        d += timedelta(days=1)

    print(f"added {rows} simulated entries; balances:",
          {"Cash": round(bal[cash], 2), "Gcash": round(bal[gcash], 2), "BPI Savings": round(bal[bpi], 2)})


if __name__ == "__main__":
    {"add": add, "remove": remove}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
