#!/usr/bin/env python3
"""Money Manager — self-hosted replacement for the iPhone app's "PC Manager" Wi-Fi server.

The iOS app (Realbyte Money Manager) serves an ExtJS web UI on port 8888 and answers
its API from the phone's Core Data SQLite store. This file re-implements that API
over a copy of the same SQLite file, so the original web UI runs unchanged on the
homelab. Python standard library only.

Usage:
  python3 server.py                                  # serve (env vars below)
  python3 server.py --import-from http://PHONE:8888  # copy the phone's database here

Environment:
  MM_PORT      port to listen on               (default 8888)
  MM_HOST      bind address                    (default 0.0.0.0)
  MM_DB        path of the SQLite database     (default /var/lib/money-manager/money.sqlite)
  MM_STATIC    folder with the classic UI      (default ./static next to this file)
  MM_APP       folder with the built new UI    (default ./app next to this file)
  MM_PASSWORD  if set, also require HTTP Basic auth (any username, this password)

Accounts: people register and sign in from the web app. Each account has its own private
book (a separate SQLite file). The first account registered takes over the existing
database at MM_DB; later accounts start from a clean book with the default categories.
Logins live in users.sqlite next to MM_DB.

  python3 server.py --list-users
  python3 server.py --reset-password NAME   # prints a new random password
"""
import base64
import calendar
import csv
import email.parser
import email.policy
import hashlib
import hmac
import secrets
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("MM_PORT", "8888"))
HOST = os.environ.get("MM_HOST", "0.0.0.0")
DB_PATH = os.environ.get("MM_DB", "/var/lib/money-manager/money.sqlite")
STATIC = os.environ.get("MM_STATIC", os.path.join(HERE, "static"))  # classic ExtJS UI
APP = os.environ.get("MM_APP", os.path.join(HERE, "app"))           # new web app (built from web/)
PASSWORD = os.environ.get("MM_PASSWORD", "")

CORE_DATA_EPOCH = 978307200  # 2001-01-01T00:00:00Z, Core Data's reference date
CARD_GROUP = "2"             # asset group the app reserves for credit cards
LIVE = "ifnull(ZISDEL,0)=0"

# ZDO_TYPE values, observed in the phone's own XML output
INCOME, EXPENSE, TRANSFER_OUT, TRANSFER_IN, BAL_UP, BAL_DOWN = "0", "1", "3", "4", "7", "8"
TYPE_TEXT = {INCOME: "Income", EXPENSE: "Exp.", TRANSFER_OUT: "Transfer-Out",
             TRANSFER_IN: "Transfer-In", BAL_UP: "Income Balance", BAL_DOWN: "Expense Balance"}
PLUS_TYPES = (INCOME, TRANSFER_IN, BAL_UP)
MINUS_TYPES = (EXPENSE, TRANSFER_OUT, BAL_DOWN)

write_lock = threading.Lock()
DATA_DIR = os.path.dirname(os.path.abspath(DB_PATH))
USERS_DB = os.path.join(DATA_DIR, "users.sqlite")
SESSION_DAYS = 60
COOKIE = "pitaka_session"

# The book (database file) of the account making the current request; set per request thread.
ctx = threading.local()


def db_path():
    return getattr(ctx, "db", None) or DB_PATH


# ---------------------------------------------------------------- database helpers
def connect():
    c = sqlite3.connect(db_path(), timeout=10)
    c.row_factory = sqlite3.Row
    return c


# ---------------------------------------------------------------- accounts & sessions
def users_db():
    c = sqlite3.connect(USERS_DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.executescript("""
        create table if not exists users (
          id integer primary key, username text not null unique collate nocase,
          pw text not null, book text not null, created integer not null);
        create table if not exists sessions (
          token text primary key, user_id integer not null references users(id) on delete cascade,
          created integer not null, expires integer not null);""")
    if "avatar" not in {r[1] for r in c.execute("pragma table_info(users)")}:
        c.execute("alter table users add column avatar integer not null default 0")  # photo version, 0 = none
    return c


AVATAR_DIR = os.path.join(DATA_DIR, "avatars")
AVATAR_TYPES = {b"\xff\xd8\xff": "image/jpeg", b"\x89PNG": "image/png", b"RIFF": "image/webp"}


def avatar_type(data):
    return next((t for magic, t in AVATAR_TYPES.items() if data.startswith(magic)), None)


def me_json(u):
    return {"username": u["username"], "avatar": u["avatar"] or 0}


def hash_password(pw, salt=None):
    # scrypt: memory-hard, and fast enough on a small ARM board (~16 MB, well under a second).
    salt = salt or secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode("utf-8"), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$%s$%s" % (salt.hex(), h.hex())


def check_password(pw, stored):
    try:
        _, n, r, p, salt, h = stored.split("$")
        got = hashlib.scrypt(pw.encode("utf-8"), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(got.hex(), h)
    except (ValueError, TypeError):
        return False


def token_key(token):
    return hashlib.sha256(token.encode()).hexdigest()  # only a hash of the cookie is stored


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
# Tables whose rows are someone's own money or notes; a new account's book starts without them.
PERSONAL_TABLES = ("ZINOUTCOME", "ZASSET", "ZBUDGET", "ZBUDGETAMOUNT", "ZMEMO", "ZPHOTO", "ZFAVTRANSACTION",
                   "ZREPEATTRANSACTION", "ZTAG", "ZTXTAG", "ZSMSRAWREAD", "ZCODEDATA", "ZCODELINK", "ZPROPERTY")


def make_blank_book(dst):
    """A fresh book: the schema, account groups, currency and the app's built-in categories
    (short numeric ids), copied from the original database with every personal row removed."""
    tmp = dst + ".tmp"
    src, out = sqlite3.connect(DB_PATH), sqlite3.connect(tmp)
    with out:
        src.backup(out)
    src.close()
    try:
        tables = {r[0] for r in out.execute("select name from sqlite_master where type='table'")}
        with out:
            for t in PERSONAL_TABLES:
                if t in tables:
                    out.execute('delete from "%s"' % t)
            out.execute("delete from ZCATEGORY where length(ZUID) > 4 or ZUID glob '*[^0-9]*'")
            out.execute("update ZCATEGORY set ZISDEL = 0")
            if "ZETC" in tables:
                out.execute("delete from ZETC where ZDATAYTYPEKEY is null")  # remembered notes, not settings
        out.execute("vacuum")
    finally:
        out.close()
    os.replace(tmp, dst)


class AuthError(Exception):
    pass


def register(username, password):
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        raise AuthError("Usernames are 3 to 32 letters, numbers, dots, dashes or underscores.")
    if len(password or "") < 8:
        raise AuthError("Use a password of at least 8 characters.")
    with write_lock:
        c = users_db()
        try:
            if c.execute("select 1 from users where username = ?", (username,)).fetchone():
                raise AuthError("That username is taken. Pick another, or sign in.")
            first = not c.execute("select 1 from users limit 1").fetchone()
            if first:
                book = os.path.basename(DB_PATH)  # the first account keeps the existing data
            else:
                os.makedirs(os.path.join(DATA_DIR, "books"), exist_ok=True)
                book = os.path.join("books", "u%s.sqlite" % secrets.token_hex(6))
                make_blank_book(os.path.join(DATA_DIR, book))
            with c:
                cur = c.execute("insert into users (username, pw, book, created) values (?, ?, ?, ?)",
                                (username, hash_password(password), book, int(time.time())))
            return cur.lastrowid
        finally:
            c.close()


def new_session(user_id):
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    c = users_db()
    try:
        with c:
            c.execute("delete from sessions where expires < ?", (now,))
            c.execute("insert into sessions values (?, ?, ?, ?)", (token_key(token), user_id, now, now + SESSION_DAYS * 86400))
    finally:
        c.close()
    return token


def session_user(token):
    if not token:
        return None
    c = users_db()
    try:
        return c.execute("select u.* from sessions s join users u on u.id = s.user_id "
                         "where s.token = ? and s.expires > ?", (token_key(token), int(time.time()))).fetchone()
    finally:
        c.close()


# Sign-in throttle: after 5 wrong passwords from one address, wait 30 s per further try.
failures = {}


def throttled(ip):
    n, last = failures.get(ip, (0, 0))
    return n >= 5 and time.time() - last < 30


def note_failure(ip, ok):
    if ok:
        failures.pop(ip, None)
    else:
        n, _ = failures.get(ip, (0, 0))
        failures[ip] = (n + 1, time.time())


def money(x):
    return "%.2f" % (x or 0)


def tx_date(row):
    """The app stores a YYYY-MM-DD string; very old rows may only carry ZDATE."""
    s = row["ZTXDATESTR"]
    if s:
        return s
    if row["ZDATE"] is None:
        return ""
    return datetime.fromtimestamp(row["ZDATE"] + CORE_DATA_EPOCH).strftime("%Y-%m-%d")


def to_core_data(day):
    """Local midnight of a YYYY-MM-DD date, as Core Data seconds."""
    d = datetime.strptime(day, "%Y-%m-%d")
    return time.mktime(d.timetuple()) - CORE_DATA_EPOCH


def now_ms():
    return int(time.time() * 1000)


def new_uid():
    return str(uuid.uuid4()).upper()


def parse_day(v):
    """ExtJS sends dates as 2026-11-21T00:00:00, plain 2026-11-21, or a JS Date string."""
    v = (v or "").strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", v)
    if m:
        return m.group(1)
    for fmt in ("%a %b %d %Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v[:15] if fmt.startswith("%a") else v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return date.today().isoformat()


def num(v, default=0.0):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return default


def next_pk(c, table, fallback_ent):
    """Allocate Z_PK the way Core Data does, keeping Z_PRIMARYKEY in step so the
    file can be restored to the phone without primary-key collisions."""
    r = c.execute(f"select Z_ENT from {table} limit 1").fetchone()
    ent = r[0] if r else fallback_ent
    row = c.execute("select Z_MAX from Z_PRIMARYKEY where Z_ENT=?", (ent,)).fetchone()
    top = max(row[0] if row and row[0] else 0,
              c.execute(f"select ifnull(max(Z_PK),0) from {table}").fetchone()[0])
    if row:
        c.execute("update Z_PRIMARYKEY set Z_MAX=? where Z_ENT=?", (top + 1, ent))
    return ent, top + 1


def main_currency(c):
    r = c.execute(f"select ZUID from ZCURRENCY where ZISMAINCURRENCY=1 and {LIVE} limit 1").fetchone()
    return r[0] if r else ""


def assets(c):
    """Live assets in the app's display order: by asset group, then position in the group."""
    return c.execute(f"select a.* from ZASSET a left join ZASSETGROUP g on g.ZUID=a.ZGROUPUID "
                     f"where ifnull(a.ZISDEL,0)=0 order by ifnull(g.ZORDER,999999), a.ZORDER").fetchall()


def asset_names(c):
    """Names for every asset, deleted ones included (old transactions still point at them)."""
    return {r["ZUID"]: r["ZNICNAME"] or "" for r in c.execute("select ZUID,ZNICNAME from ZASSET")}


def categories(c):
    return {r["ZUID"]: r for r in c.execute("select * from ZCATEGORY")}


def balances(c, through=None):
    """Signed balance per asset uid over live transactions, optionally up to a date."""
    out = {}
    for r in c.execute(f"select ZASSETUID,ZDO_TYPE,ZAMOUNT,ZTXDATESTR,ZDATE from ZINOUTCOME where {LIVE}"):
        if through and tx_date(r) > through:
            continue
        sign = 1 if r["ZDO_TYPE"] in PLUS_TYPES else -1 if r["ZDO_TYPE"] in MINUS_TYPES else 0
        out[r["ZASSETUID"]] = out.get(r["ZASSETUID"], 0.0) + sign * (r["ZAMOUNT"] or 0)
    return {k: round(v, 2) for k, v in out.items()}  # float sums drift (1e-12 is not "positive")


def split_category(cats, uid):
    """(parent id, parent name, sub id, sub name) for a transaction's category uid."""
    cat = cats.get(uid)
    if not cat:
        return uid or "", "", uid or "", ""
    puid = cat["ZPUID"]
    if puid not in (None, "", "0") and puid in cats:
        return puid, cats[puid]["ZNAME"] or "", uid, cat["ZNAME"] or ""
    return uid, cat["ZNAME"] or "", uid, ""


# ---------------------------------------------------------------- read endpoints
def get_init_data(c, p):
    today = date.today()
    start = today.replace(day=1)
    end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    cats = c.execute(f"select * from ZCATEGORY where {LIVE} and ifnull(ZSTATUS,0)!=2 order by ZORDER").fetchall()

    def cat_list(dotype):
        top = [r for r in cats if r["ZDOTYPE"] == dotype and r["ZPUID"] in (None, "", "0")]
        return [{"mcid": r["ZUID"], "mcname": r["ZNAME"] or "",
                 "mcsc": [{"mcscid": s["ZUID"], "mcscname": s["ZNAME"] or ""}
                          for s in cats if s["ZPUID"] == r["ZUID"]]} for r in top]

    live = assets(c)
    groups = c.execute(f"select * from ZASSETGROUP where {LIVE} and ZUID!=? order by ZORDER", (CARD_GROUP,)).fetchall()
    return {
        "initData": {"initStartDate": start.isoformat(), "initEndDate": end.isoformat(),
                     "mbid": "1", "mbName": "Money Manager"},
        "multiBooks": [{"mbid": "1", "mbname": "Money Manager", "baseDate": "1"}],
        "category_1": cat_list(1),
        "category_0": cat_list(0),
        "payType": [{"ptid": a["ZUID"], "ptname": a["ZNICNAME"] or ""} for a in live],
        "inOutText": [["Exp."], ["Income"]],
        "assetGroups": [{"assetGroupId": g["ZUID"], "assetType": "group", "assetName": g["ZASSETGROUPNAME"] or ""}
                        for g in groups],
        "assetNames": [{"assetType": "item", "assetId": a["ZUID"], "assetName": a["ZNICNAME"] or ""} for a in live],
    }


def asset_tree(c, cards):
    bal = balances(c)
    live = assets(c)
    groups = c.execute(f"select * from ZASSETGROUP where {LIVE} order by ZORDER").fetchall()
    tree = []
    for g in groups:
        if (g["ZUID"] == CARD_GROUP) != cards:
            continue
        items = []
        for a in live:
            if a["ZGROUPUID"] != g["ZUID"]:
                continue
            m = bal.get(a["ZUID"], 0.0)
            item = {"assetType": "item", "assetId": a["ZUID"], "assetName": a["ZNICNAME"] or "",
                    "color": "#4169e1" if m > 0 else "#dc143c",
                    "linkAssetId": a["ZCARDASSETUID"] or "-1", "assetMoney": money(m),
                    "leaf": True, "iconCls": "task"}
            if cards:
                item.update(notPayMoney=money(m), jungsanDay=a["ZCARD_DAYFIN"] or "",
                            paymentDay=a["ZCARD_DAYPAY"] or "")
            items.append(item)
        if items:
            total = sum(num(i["assetMoney"]) for i in items)
            node = {"assetName": g["ZASSETGROUPNAME"] or "", "assetGroupId": g["ZUID"], "assetType": "group",
                    "assetMoney": money(total), "iconCls": "task-folder", "expanded": True, "children": items}
            if cards:
                node["notPayMoney"] = money(total)
            tree.append(node)
    return tree


def get_data_by_period(c, p):
    start = parse_day(p.get("startDate"))
    end = parse_day(p.get("endDate"))
    asset = p.get("assetId", "")
    types = [INCOME, EXPENSE, TRANSFER_OUT, BAL_UP, BAL_DOWN] + ([TRANSFER_IN] if asset else [])
    q = f"select * from ZINOUTCOME where {LIVE} and ZDO_TYPE in ({','.join('?' * len(types))})"
    args = list(types)
    if asset:
        q += " and ZASSETUID=?"
        args.append(asset)
    rows = [r for r in c.execute(q, args) if start <= tx_date(r) <= end]
    rows.sort(key=lambda r: (r["ZDATE"] or 0, r["ZUTIME"] or 0), reverse=True)  # the phone's order
    names, cats = asset_names(c), categories(c)
    out = ["<?xml version='1.0' encoding='UTF-8'?><dataset><results>%d</results>" % len(rows)]

    def cdata(s):
        return "<![CDATA[%s]]>" % (s or "").replace("]]>", "]]]]><![CDATA[>")

    for r in rows:
        t = r["ZDO_TYPE"]
        if t in (TRANSFER_OUT, TRANSFER_IN):
            mcid = mbcat = mcscid = sub = ""
        elif t in (BAL_UP, BAL_DOWN):
            mcid, mbcat, mcscid, sub = "(null)", "Modified Bal.", "-4", ""
        else:
            mcid, mbcat, mcscid, sub = split_category(cats, r["ZCATEGORYUID"])
        amount = -(r["ZAMOUNT"] or 0) if t == TRANSFER_OUT else (r["ZAMOUNT"] or 0)
        out.append("<row><id>%s</id><mbDate>%s</mbDate><inOutCode>%s</inOutCode><assetId>%s</assetId>"
                   "<payType>%s</payType><inOutType>%s</inOutType>" % (
                       escape(r["ZUID"] or ""), tx_date(r), t, escape(r["ZASSETUID"] or ""),
                       cdata(names.get(r["ZASSETUID"], "")), TYPE_TEXT.get(t, "")))
        if t in (TRANSFER_OUT, TRANSFER_IN):
            out.append("<toAssetId>%s</toAssetId>" % escape(r["ZTOASSETUID"] or ""))
        out.append("<mcid>%s</mcid><mbCategory>%s</mbCategory><mcscid>%s</mcscid><subCategory>%s</subCategory>"
                   "<mbContent>%s</mbContent><mbDetailContent>%s</mbDetailContent><mbCash>%.6f</mbCash></row>" % (
                       escape(mcid), cdata(mbcat), escape(mcscid), cdata(sub),
                       cdata(r["ZCONTENT"]), cdata(r["ZMEMO"]), amount))
    out.append("</dataset>")
    return "".join(out)


def get_summary(c, p):
    start = parse_day(p.get("startDate"))
    end = parse_day(p.get("endDate"))
    cats = categories(c)
    card_assets = {a["ZUID"] for a in c.execute("select ZUID,ZGROUPUID from ZASSET") if a["ZGROUPUID"] == CARD_GROUP}
    inc, out, card = 0.0, 0.0, 0.0
    by_cat = {INCOME: {}, EXPENSE: {}}
    for r in c.execute(f"select * from ZINOUTCOME where {LIVE} and ZDO_TYPE in (?,?)", (INCOME, EXPENSE)):
        if not (start <= tx_date(r) <= end):
            continue
        amt = r["ZAMOUNT"] or 0
        t = r["ZDO_TYPE"]
        if t == INCOME:
            inc += amt
        else:
            out += amt
            if r["ZASSETUID"] in card_assets:
                card += amt
        pid, pname, _, _ = split_category(cats, r["ZCATEGORYUID"])
        slot = by_cat[t].setdefault(pid, [pname, 0.0])
        slot[1] += amt

    def rows(d):
        return [{"mcname": n, "mcSum": money(s), "budget": "0.00"}
                for n, s in sorted(d.values(), key=lambda x: -x[1])]

    return {"summary": {"startDate": start, "endDate": end, "income": money(inc), "outcome": money(out),
                        "cash": money(out - card), "card": money(card), "etcExpenseOpt": False,
                        "etcExpense": "0.00", "sum": money(inc - out)},
            "income": rows(by_cat[INCOME]), "outcome": rows(by_cat[EXPENSE])}


def get_dashboard(c, p):
    live = {a["ZUID"]: a for a in assets(c)}
    today = date.today()
    line = []
    for k in range(-13, 3):  # the phone shows 13 months back through 2 ahead
        y, m = divmod(today.year * 12 + today.month - 1 + k, 12)
        m += 1
        last = date(y, m, calendar.monthrange(y, m)[1]).isoformat()
        b = {u: v for u, v in balances(c, last).items() if u in live}
        pos = sum(v for v in b.values() if v > 0)
        neg = sum(v for v in b.values() if v < 0)
        line.append({"month": "%04d-%02d" % (y, m), "total": money(pos + neg),
                     "asset": "%.6f" % pos, "debt": "%.6f" % neg})
    b = {u: v for u, v in balances(c).items() if u in live}
    pos = sum(v for v in b.values() if v > 0)
    neg = sum(v for v in b.values() if v < 0)
    return {"assetLine": line,
            "assetRatio": [{"assetName": live[u]["ZNICNAME"], "assetMoney": money(v)} for u, v in b.items() if v > 0],
            "debtRatio": [{"assetName": live[u]["ZNICNAME"], "assetMoney": money(v)} for u, v in b.items() if v < 0],
            "assetSummary": {"totalAsset": "%.6f" % (pos + neg), "asset": "%.6f" % pos, "debt": "%.6f" % neg}}


def get_asset_chart(c, p):
    asset = p.get("assetId", "")
    today = date.today()
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)  # Sunday-start weeks
    points = []
    for k in range(19, -1, -1):
        start = week_start - timedelta(weeks=k)
        through = (start + timedelta(days=6)).isoformat()
        points.append({"month": start.isoformat(), "assetMoney": money(balances(c, through).get(asset, 0.0))})
    return {"assetChartData": points}


# ---------------------------------------------------------------- write endpoints
def insert_tx(c, **f):
    ent, pk = next_pk(c, "ZINOUTCOME", 11)
    day = f.pop("day")
    row = dict(Z_PK=pk, Z_ENT=ent, Z_OPT=1, ZISSYNCED=0, ZMARK=0, ZUTIME=now_ms(), ZDATE=to_core_data(day),
               ZTXDATESTR=day, ZCARDDIVIDEMONTH="0", ZCURRENCYUID=main_currency(c), ZUID=new_uid())
    for k in ("ZASSET_GROUP", "ZASSET_ID", "ZCATEGORY_ID", "ZOPPOSITEAID", "ZAID", "ZCATEGORYID",
              "ZCURRENCYID", "ZFEE_ID", "ZSYNCCHECK", "ZSYNCVERSION"):
        row[k] = 0
    amt = f.pop("amount")
    row.update(ZAMOUNT=amt, ZAMOUNTACCOUNT=amt, ZAMOUNTSUB=amt)
    row.update(f)
    c.execute("insert into ZINOUTCOME (%s) values (%s)" % (",".join(row), ",".join("?" * len(row))),
              list(row.values()))
    return row["ZUID"]


def save_tx(c, p, create):
    code = p.get("inOutCode", EXPENSE)
    cat = p.get("mcscid") or p.get("mcid") or ""
    fields = dict(day=parse_day(p.get("mbDate")), amount=abs(num(p.get("mbCash"))),
                  ZASSETUID=p.get("assetId", ""), ZCONTENT=p.get("mbContent", ""),
                  ZMEMO=p.get("mbDetailContent", ""))
    if code in (INCOME, EXPENSE):
        fields["ZCATEGORYUID"] = cat
    existing = None if create else c.execute("select * from ZINOUTCOME where ZUID=?", (p.get("id", ""),)).fetchone()
    if existing is None:
        insert_tx(c, ZDO_TYPE=code, **fields)
        return
    day = fields.pop("day")
    amt = fields.pop("amount")
    if existing["ZDO_TYPE"] in (BAL_UP, BAL_DOWN):  # the UI locks account/category on these
        fields.pop("ZASSETUID", None)
    fields.update(ZDATE=to_core_data(day), ZTXDATESTR=day, ZAMOUNT=amt, ZAMOUNTACCOUNT=amt, ZAMOUNTSUB=amt,
                  ZUTIME=now_ms(), ZISSYNCED=0, Z_OPT=(existing["Z_OPT"] or 0) + 1)
    c.execute("update ZINOUTCOME set %s where Z_PK=?" % ",".join(k + "=?" for k in fields),
              list(fields.values()) + [existing["Z_PK"]])


def delete_tx(c, p):
    for uid in filter(None, (p.get("ids") or "").split(":")):
        r = c.execute("select ZTXUIDTRANS from ZINOUTCOME where ZUID=?", (uid,)).fetchone()
        c.execute("update ZINOUTCOME set ZISDEL=1, ZUTIME=?, ZISSYNCED=0 where ZUID=?", (now_ms(), uid))
        if r and r[0]:  # take the other leg of a transfer with it
            c.execute("update ZINOUTCOME set ZISDEL=1, ZUTIME=?, ZISSYNCED=0 where ZTXUIDTRANS=?", (now_ms(), r[0]))


def move_asset(c, p, modify):
    day = parse_day(p.get("moveDate"))
    amt = abs(num(p.get("moveMoney")))
    src, dst = p.get("fromAssetId", ""), p.get("toAssetId", "")
    content, memo = p.get("moneyContent", ""), p.get("mbDetailContent", "")
    if modify:
        r = c.execute("select ZTXUIDTRANS from ZINOUTCOME where ZUID=?", (p.get("id", ""),)).fetchone()
        if r and r[0]:
            c.execute("update ZINOUTCOME set ZISDEL=1, ZUTIME=? where ZTXUIDTRANS=?", (now_ms(), r[0]))
        else:
            c.execute("update ZINOUTCOME set ZISDEL=1, ZUTIME=? where ZUID=?", (now_ms(), p.get("id", "")))
    link = new_uid()
    insert_tx(c, day=day, amount=amt, ZDO_TYPE=TRANSFER_OUT, ZASSETUID=src, ZTOASSETUID=dst,
              ZTXUIDTRANS=link, ZCONTENT=content, ZMEMO=memo)
    insert_tx(c, day=day, amount=amt, ZDO_TYPE=TRANSFER_IN, ZASSETUID=dst, ZTOASSETUID=src,
              ZTXUIDTRANS=link, ZCONTENT=content, ZMEMO=memo)


def adjust_balance(c, asset_uid, target):
    """The app records a balance edit as a 'Difference' transaction (types 7/8)."""
    diff = round(target - balances(c).get(asset_uid, 0.0), 2)
    if diff:
        insert_tx(c, day=date.today().isoformat(), amount=abs(diff), ZDO_TYPE=BAL_UP if diff > 0 else BAL_DOWN,
                  ZASSETUID=asset_uid, ZCATEGORYUID="-4", ZCONTENT="Difference", ZMEMO="")


def insert_asset(c, name, group, **extra):
    ent, pk = next_pk(c, "ZASSET", 1)
    order = c.execute("select ifnull(max(ZORDER),0)+1 from ZASSET").fetchone()[0]
    row = dict(Z_PK=pk, Z_ENT=ent, Z_OPT=1, ZORDER=order, ZTYPE=0, ZISSYNCED=0, ZUTIME=now_ms(),
               ZNICNAME=name, ZGROUPUID=group, ZCURRENCYUID=main_currency(c), ZUID=new_uid(), ZCARDASSETUID="")
    for k in ("ZCARD_ACCOUNT_ID", "ZGROUP_ID", "ZLEFTMONEY", "ZAID", "ZCARD_USAGE_HURDLE_START_DATE",
              "ZCARD_USAGE_HURDLE_TYPE", "ZCURRENCYID", "ZISCARDAUTOPAY", "ZISREFLECT", "ZSYNCCHECK",
              "ZSYNCVERSION", "ZTRANSFEREXPENSE"):
        row[k] = 0
    row.update(extra)
    c.execute("insert into ZASSET (%s) values (%s)" % (",".join(row), ",".join("?" * len(row))), list(row.values()))
    return row["ZUID"]


def asset_add(c, p):
    uid = insert_asset(c, p.get("assetName", ""), p.get("assetGroupId", ""),
                       ZCARDASSETUID=p.get("linkAssetId", "") or "")
    adjust_balance(c, uid, num(p.get("assetMoney")))


def asset_modify(c, p):
    uid = p.get("assetId", "")
    sets = {"ZNICNAME": p.get("assetName", ""), "ZUTIME": now_ms(), "ZISSYNCED": 0}
    if p.get("assetGroupId"):
        sets["ZGROUPUID"] = p["assetGroupId"]
    if p.get("linkAssetId"):
        sets["ZCARDASSETUID"] = p["linkAssetId"]
    c.execute("update ZASSET set %s where ZUID=?" % ",".join(k + "=?" for k in sets), list(sets.values()) + [uid])
    if "assetMoney" in p:
        adjust_balance(c, uid, num(p.get("assetMoney")))


def card_add(c, p):
    insert_asset(c, p.get("cardName", ""), CARD_GROUP, ZCARDASSETUID=p.get("linkAssetId", "") or "",
                 ZCARD_DAYFIN=p.get("jungsanDay", ""), ZCARD_DAYPAY=p.get("paymentDay", ""))


def card_modify(c, p):
    sets = {"ZUTIME": now_ms(), "ZISSYNCED": 0, "ZCARD_DAYFIN": p.get("jungsanDay", ""),
            "ZCARD_DAYPAY": p.get("paymentDay", "")}
    if p.get("cardName"):
        sets["ZNICNAME"] = p["cardName"]
    if p.get("linkAssetId"):
        sets["ZCARDASSETUID"] = p["linkAssetId"]
    c.execute("update ZASSET set %s where ZUID=?" % ",".join(k + "=?" for k in sets),
              list(sets.values()) + [p.get("assetId", "")])


def remove_asset(c, p):
    c.execute("update ZASSET set ZISDEL=1, ZUTIME=?, ZISSYNCED=0 where ZUID=?", (now_ms(), p.get("assetId", "")))


def excel_csv(c, p):
    xml = get_data_by_period(c, p)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Account", "Type", "Category", "Subcategory", "Note", "Description", "Amount"])
    for row in re.findall(r"<row>(.*?)</row>", xml, re.S):
        def g(tag):
            m = re.search(r"<%s>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (tag, tag), row, re.S)
            return m.group(1) if m else ""
        w.writerow([g("mbDate"), g("payType"), g("inOutType"), g("mbCategory"), g("subCategory"),
                    g("mbContent"), g("mbDetailContent"), "%.2f" % num(g("mbCash"))])
    return "﻿" + buf.getvalue()  # BOM so Excel reads UTF-8 (emoji category names)


# ---------------------------------------------------------------- database import/export
def validate_db(path):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    finally:
        c.close()
    missing = {"ZINOUTCOME", "ZASSET", "ZASSETGROUP", "ZCATEGORY"} - tables
    if missing:
        raise ValueError("not a Money Manager database (missing %s)" % ", ".join(sorted(missing)))


def install_db(src):
    """Validate an uploaded/downloaded file, keep the current DB as a timestamped backup, swap in."""
    validate_db(src)
    with write_lock:
        dst = db_path()
        if os.path.exists(dst):
            bak = "%s.bak-%s" % (dst, datetime.now().strftime("%Y%m%d-%H%M%S"))
            shutil.copy2(dst, bak)
        os.replace(src, dst)


def snapshot_bytes():
    """A consistent copy of the live database (safe even while it's being written)."""
    fd, tmp = tempfile.mkstemp(suffix=".sqlite", dir=os.path.dirname(db_path()))
    os.close(fd)
    try:
        src, dst = sqlite3.connect(db_path()), sqlite3.connect(tmp)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        with open(tmp, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp)


def import_from(phone_url):
    url = phone_url.rstrip("/") + "/moneyBook/money.sqlite"
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".sqlite", dir=os.path.dirname(DB_PATH) or ".")
    with os.fdopen(fd, "wb") as f, urllib.request.urlopen(url, timeout=60) as r:
        shutil.copyfileobj(r, f)
    install_db(tmp)
    print("imported %s -> %s" % (url, DB_PATH))


# ---------------------------------------------------------------- JSON API (new web app, /api/*)
KIND = {INCOME: "income", EXPENSE: "expense", TRANSFER_OUT: "transfer", TRANSFER_IN: "transfer",
        BAL_UP: "adjust", BAL_DOWN: "adjust"}


class ApiError(Exception):
    pass


def month_bounds(ym):
    y, m = (int(x) for x in ym.split("-"))
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def shift_month(y, m, k):
    y2, m2 = divmod(y * 12 + m - 1 + k, 12)
    return y2, m2 + 1


def live_categories(c):
    return c.execute(f"select * from ZCATEGORY where {LIVE} and ifnull(ZSTATUS,0)!=2 order by ZORDER").fetchall()


def api_meta(c, q):
    cats = live_categories(c)

    def tree(dotype):
        top = [r for r in cats if r["ZDOTYPE"] == dotype and r["ZPUID"] in (None, "", "0")]
        return [{"id": r["ZUID"], "name": r["ZNAME"] or "",
                 "subs": [{"id": s["ZUID"], "name": s["ZNAME"] or ""} for s in cats if s["ZPUID"] == r["ZUID"]]}
                for r in top]

    bal = balances(c)
    cur = c.execute(f"select ZISO,ZSYMBOL from ZCURRENCY where ZISMAINCURRENCY=1 and {LIVE} limit 1").fetchone()
    groups = c.execute(f"select * from ZASSETGROUP where {LIVE} order by ZORDER").fetchall()
    accts = [{"id": a["ZUID"], "name": a["ZNICNAME"] or "", "groupId": a["ZGROUPUID"],
              "balance": bal.get(a["ZUID"], 0.0), "isCard": a["ZGROUPUID"] == CARD_GROUP,
              "statementDay": a["ZCARD_DAYFIN"] or "", "paymentDay": a["ZCARD_DAYPAY"] or "",
              "linkId": a["ZCARDASSETUID"] or ""} for a in assets(c)]
    return {"currency": {"iso": cur["ZISO"] if cur else "PHP", "symbol": cur["ZSYMBOL"] if cur else "₱"},
            "categories": {"income": tree(0), "expense": tree(1)},
            "groups": [{"id": g["ZUID"], "name": g["ZASSETGROUPNAME"] or "", "isCard": g["ZUID"] == CARD_GROUP}
                       for g in groups],
            "accounts": accts,
            "netWorth": round(sum(a["balance"] for a in accts), 2),
            "today": date.today().isoformat()}


def tx_json(r, names, cats):
    t = r["ZDO_TYPE"]
    out = {"id": r["ZUID"], "date": tx_date(r), "code": t, "kind": KIND.get(t, "other"),
           "amount": round(r["ZAMOUNT"] or 0, 2), "accountId": r["ZASSETUID"] or "",
           "account": names.get(r["ZASSETUID"], ""), "note": r["ZCONTENT"] or "", "memo": r["ZMEMO"] or "",
           "categoryId": "", "category": "", "subcategoryId": "", "subcategory": ""}
    if t in (TRANSFER_OUT, TRANSFER_IN):
        out.update(toAccountId=r["ZTOASSETUID"] or "", toAccount=names.get(r["ZTOASSETUID"], ""),
                   direction="out" if t == TRANSFER_OUT else "in")
    elif t in (BAL_UP, BAL_DOWN):
        out.update(category="Balance adjustment", direction="up" if t == BAL_UP else "down")
    else:
        pid, pname, sid, sname = split_category(cats, r["ZCATEGORYUID"])
        out.update(categoryId=pid, category=pname, subcategoryId=sid if sname else "", subcategory=sname)
    return out


def api_transactions(c, q):
    start, end = parse_day(q.get("from")), parse_day(q.get("to"))
    acct = q.get("account", "")
    types = [INCOME, EXPENSE, TRANSFER_OUT, BAL_UP, BAL_DOWN] + ([TRANSFER_IN] if acct else [])
    sql = f"select * from ZINOUTCOME where {LIVE} and ZDO_TYPE in ({','.join('?' * len(types))})"
    args = list(types)
    if acct:
        sql += " and ZASSETUID=?"
        args.append(acct)
    rows = [r for r in c.execute(sql, args) if start <= tx_date(r) <= end]
    rows.sort(key=lambda r: (tx_date(r), r["ZDATE"] or 0, r["ZUTIME"] or 0), reverse=True)
    names, cats = asset_names(c), categories(c)
    return [tx_json(r, names, cats) for r in rows]


def api_summary(c, q):
    start, end = parse_day(q.get("from")), parse_day(q.get("to"))
    cats = categories(c)
    total = {INCOME: 0.0, EXPENSE: 0.0}
    by_cat = {INCOME: {}, EXPENSE: {}}
    daily = {}
    for r in c.execute(f"select * from ZINOUTCOME where {LIVE} and ZDO_TYPE in (?,?)", (INCOME, EXPENSE)):
        d = tx_date(r)
        if not (start <= d <= end):
            continue
        t, amt = r["ZDO_TYPE"], r["ZAMOUNT"] or 0
        total[t] += amt
        pid, pname, _, _ = split_category(cats, r["ZCATEGORYUID"])
        slot = by_cat[t].setdefault(pid, {"id": pid, "name": pname or "Uncategorized", "amount": 0.0, "count": 0})
        slot["amount"] += amt
        slot["count"] += 1
        day = daily.setdefault(d, {"date": d, "income": 0.0, "expense": 0.0})
        day["income" if t == INCOME else "expense"] += amt

    def ranked(d):
        return [dict(v, amount=round(v["amount"], 2)) for v in sorted(d.values(), key=lambda v: -v["amount"])]

    return {"from": start, "to": end, "income": round(total[INCOME], 2), "expense": round(total[EXPENSE], 2),
            "net": round(total[INCOME] - total[EXPENSE], 2),
            "income_by_category": ranked(by_cat[INCOME]), "expense_by_category": ranked(by_cat[EXPENSE]),
            "daily": [{k: (round(v, 2) if k != "date" else v) for k, v in x.items()}
                      for x in sorted(daily.values(), key=lambda x: x["date"])]}


def api_trend(c, q):
    """Income and expense per month for the N months ending at `end` (YYYY-MM)."""
    n = max(1, min(int(q.get("months") or 12), 60))
    ey, em = (int(x) for x in (q.get("end") or date.today().strftime("%Y-%m")).split("-"))
    months = [shift_month(ey, em, -k) for k in range(n - 1, -1, -1)]
    data = {"%04d-%02d" % ym: {"month": "%04d-%02d" % ym, "income": 0.0, "expense": 0.0} for ym in months}
    for r in c.execute(f"select * from ZINOUTCOME where {LIVE} and ZDO_TYPE in (?,?)", (INCOME, EXPENSE)):
        slot = data.get(tx_date(r)[:7])
        if slot:
            slot["income" if r["ZDO_TYPE"] == INCOME else "expense"] += r["ZAMOUNT"] or 0
    return [{k: (round(v, 2) if k != "month" else v) for k, v in x.items()} for x in data.values()]


def api_networth(c, q):
    n = max(1, min(int(q.get("months") or 12), 60))
    today = date.today()
    live = {a["ZUID"] for a in assets(c)}
    rows = c.execute(f"select ZASSETUID,ZDO_TYPE,ZAMOUNT,ZTXDATESTR,ZDATE from ZINOUTCOME where {LIVE}").fetchall()
    out = []
    for k in range(n - 1, -1, -1):
        y, m = shift_month(today.year, today.month, -k)
        last = min(date(y, m, calendar.monthrange(y, m)[1]), today).isoformat()
        b = {}
        for r in rows:
            if r["ZASSETUID"] in live and tx_date(r) <= last:
                sign = 1 if r["ZDO_TYPE"] in PLUS_TYPES else -1 if r["ZDO_TYPE"] in MINUS_TYPES else 0
                b[r["ZASSETUID"]] = b.get(r["ZASSETUID"], 0.0) + sign * (r["ZAMOUNT"] or 0)
        pos = sum(v for v in b.values() if v > 0.004)
        neg = sum(v for v in b.values() if v < -0.004)
        out.append({"month": "%04d-%02d" % (y, m), "assets": round(pos, 2), "debts": round(neg, 2),
                    "total": round(pos + neg, 2)})
    return out


def api_account_history(c, q):
    acct, n = q.get("id", ""), max(4, min(int(q.get("weeks") or 26), 104))
    today = date.today()
    rows = c.execute(f"select ZDO_TYPE,ZAMOUNT,ZTXDATESTR,ZDATE from ZINOUTCOME where {LIVE} and ZASSETUID=?",
                     (acct,)).fetchall()
    out = []
    for k in range(n - 1, -1, -1):
        day = (today - timedelta(weeks=k)).isoformat()
        total = 0.0
        for r in rows:
            if tx_date(r) <= day:
                total += (1 if r["ZDO_TYPE"] in PLUS_TYPES else -1 if r["ZDO_TYPE"] in MINUS_TYPES else 0) \
                    * (r["ZAMOUNT"] or 0)
        out.append({"date": day, "balance": round(total, 2)})
    return out


def need(body, *keys):
    for k in keys:
        if body.get(k) in (None, ""):
            raise ApiError("%s is required" % k)


def api_save_transaction(c, body):
    kind = body.get("kind")
    if kind == "transfer":
        need(body, "date", "amount", "fromId", "toId")
        if body["fromId"] == body["toId"]:
            raise ApiError("Pick two different accounts")
        move_asset(c, {"id": body.get("id", ""), "moveDate": body["date"], "moveMoney": body["amount"],
                       "fromAssetId": body["fromId"], "toAssetId": body["toId"],
                       "moneyContent": body.get("note", ""), "mbDetailContent": body.get("memo", "")},
                   modify=bool(body.get("id")))
        return {"ok": True}
    if kind not in ("income", "expense"):
        raise ApiError("kind must be income, expense or transfer")
    need(body, "date", "amount", "accountId", "categoryId")
    if num(body["amount"]) <= 0:
        raise ApiError("Amount must be more than zero")
    p = {"id": body.get("id", ""), "mbDate": body["date"], "mbCash": body["amount"],
         "assetId": body["accountId"], "mcid": body["categoryId"], "mcscid": body.get("subcategoryId") or "",
         "inOutCode": INCOME if kind == "income" else EXPENSE, "mbContent": body.get("note", ""),
         "mbDetailContent": body.get("memo", "")}
    save_tx(c, p, create=not body.get("id"))
    return {"ok": True}


def api_delete_transaction(c, tx_id):
    delete_tx(c, {"ids": ":" + tx_id})
    return {"ok": True}


def api_save_account(c, body):
    need(body, "name", "groupId")
    if body.get("id"):
        asset_modify(c, {"assetId": body["id"], "assetName": body["name"], "assetGroupId": body["groupId"],
                         **({"assetMoney": body["balance"]} if body.get("balance") not in (None, "") else {})})
        return {"ok": True}
    uid = insert_asset(c, body["name"], body["groupId"])
    if body.get("balance") not in (None, ""):
        adjust_balance(c, uid, num(body["balance"]))
    return {"ok": True, "id": uid}


def api_delete_account(c, acct_id):
    remove_asset(c, {"assetId": acct_id})
    return {"ok": True}


API_GET = {"meta": api_meta, "transactions": api_transactions, "summary": api_summary,
           "trend": api_trend, "networth": api_networth, "account-history": api_account_history}


# ---------------------------------------------------------------- HTTP
READS = {"getinitdata": get_init_data, "getdatabyperiod": get_data_by_period,
         "getsummarydatabyperiod": get_summary, "getdashboarddata": get_dashboard,
         "geteachassetchartdata": get_asset_chart,
         "getassetdata": lambda c, p: asset_tree(c, cards=False),
         "getcarddata": lambda c, p: asset_tree(c, cards=True)}
WRITES = {"create": lambda c, p: save_tx(c, p, True), "update": lambda c, p: save_tx(c, p, False),
          "delete": delete_tx, "moveasset": lambda c, p: move_asset(c, p, False),
          "modifymoveasset": lambda c, p: move_asset(c, p, True), "assetadd": asset_add,
          "assetmodify": asset_modify, "removeasset": remove_asset, "addassetcard": card_add,
          "modifycard": card_modify}
TYPES = {".js": "application/javascript", ".css": "text/css", ".woff2": "font/woff2", ".woff": "font/woff",
         ".webmanifest": "application/manifest+json", ".gif": "image/gif", ".png": "image/png",
         ".jpg": "image/jpeg", ".html": "text/html; charset=utf-8", ".svg": "image/svg+xml"}


class Handler(BaseHTTPRequestHandler):
    server_version = "MoneyManager/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def send(self, body, ctype="text/plain; charset=UTF-8", code=200, headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        p = self.path.lower()
        cache = "no-store" if ("moneybook" in p or p.startswith("/api/") or ctype.startswith("text/html")) else \
            "public, max-age=31536000, immutable" if p.startswith("/assets/") else "public, max-age=86400"
        if p.startswith("/auth/"):
            cache = "no-store"
        headers = dict(headers or {})
        self.send_header("Cache-Control", headers.pop("Cache-Control", cache))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def authorized(self):
        if not PASSWORD:
            return True
        h = self.headers.get("Authorization", "")
        if h.startswith("Basic "):
            try:
                _, _, pw = base64.b64decode(h[6:]).decode("utf-8").partition(":")
                if hmac.compare_digest(pw.encode(), PASSWORD.encode()):
                    return True
            except ValueError:
                pass
        self.send("Login required", code=401, headers={"WWW-Authenticate": 'Basic realm="Money Manager"'})
        return False

    def params(self):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query, keep_blank_values=True))
        if self.command == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            ctype = self.headers.get("Content-Type", "")
            if ctype.startswith("multipart/form-data"):
                msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(
                    b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + raw)
                for part in msg.iter_parts():
                    name = part.get_param("name", header="content-disposition")
                    if name:
                        q[name] = part.get_payload(decode=True) if part.get_filename() else \
                            part.get_payload(decode=True).decode("utf-8", "replace")
            else:
                q.update(urllib.parse.parse_qsl(raw.decode("utf-8", "replace"), keep_blank_values=True))
        return q

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.route()

    def do_POST(self):
        self.route()

    def do_DELETE(self):
        self.route()

    def client_ip(self):
        ip = self.client_address[0]
        if ip in ("127.0.0.1", "::1"):  # behind the local reverse proxy (Caddy)
            ip = (self.headers.get("X-Forwarded-For") or ip).split(",")[0].strip()
        return ip

    def session_token(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == COOKIE:
                return v
        return None

    def read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        if not isinstance(body, dict):
            raise ApiError("Expected a JSON object")
        return body

    def cookie(self, token, max_age):
        return {"Set-Cookie": "%s=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (COOKIE, token, max_age)}

    def auth_api(self, name):
        """/auth/register, /auth/login, /auth/logout, /auth/me, /auth/password."""
        try:
            if name == "me" and self.command == "GET":
                u = session_user(self.session_token())
                if not u:
                    return self.send_json({"error": "Sign in to continue."}, 401)
                return self.send_json(me_json(u))
            if name == "avatar" and self.command == "GET":
                u = session_user(self.session_token())
                f = u and os.path.join(AVATAR_DIR, "u%d" % u["id"])
                if not u or not u["avatar"] or not os.path.isfile(f):
                    return self.send_json({"error": "No photo"}, 404)
                with open(f, "rb") as fh:
                    data = fh.read()
                return self.send(data, avatar_type(data) or "application/octet-stream",
                                 headers={"Cache-Control": "private, max-age=31536000"})
            if self.command != "POST":
                return self.send_json({"error": "Unknown call"}, 404)
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self.send_json({"error": "Expected JSON"}, 415)  # forms from other sites can't send this
            body = self.read_json()
            if name == "register":
                uid = register(body.get("username"), body.get("password"))
                return self.send(json.dumps({"username": body["username"].strip(), "avatar": 0}), "application/json; charset=utf-8", 201,
                                 self.cookie(new_session(uid), SESSION_DAYS * 86400))
            if name == "login":
                ip = self.client_ip()
                if throttled(ip):
                    return self.send_json({"error": "Too many wrong passwords. Wait 30 seconds, then try again."}, 429)
                c = users_db()
                try:
                    u = c.execute("select * from users where username = ?", ((body.get("username") or "").strip(),)).fetchone()
                finally:
                    c.close()
                ok = bool(u) and check_password(body.get("password") or "", u["pw"])
                note_failure(ip, ok)
                if not ok:
                    return self.send_json({"error": "That username and password don't match."}, 401)
                return self.send(json.dumps(me_json(u)), "application/json; charset=utf-8", 200,
                                 self.cookie(new_session(u["id"]), SESSION_DAYS * 86400))
            if name == "logout":
                tok = self.session_token()
                if tok:
                    c = users_db()
                    try:
                        with c:
                            c.execute("delete from sessions where token = ?", (token_key(tok),))
                    finally:
                        c.close()
                return self.send(json.dumps({"ok": True}), "application/json; charset=utf-8", 200, self.cookie("", 0))
            if name == "avatar":
                # body: {"image": "data:image/jpeg;base64,..."} to set (already cropped and shrunk
                # by the browser), or {"image": null} to remove.
                u = session_user(self.session_token())
                if not u:
                    return self.send_json({"error": "Sign in to continue."}, 401)
                path = os.path.join(AVATAR_DIR, "u%d" % u["id"])
                version = 0
                if body.get("image"):
                    head, _, b64 = str(body["image"]).partition(",")
                    data = base64.b64decode(b64, validate=True)
                    if not avatar_type(data):
                        raise ApiError("Use a JPEG, PNG or WebP photo.")
                    if len(data) > 400_000:
                        raise ApiError("That photo is too large.")
                    os.makedirs(AVATAR_DIR, exist_ok=True)
                    with open(path + ".tmp", "wb") as fh:
                        fh.write(data)
                    os.replace(path + ".tmp", path)
                    version = int(time.time())
                elif os.path.exists(path):
                    os.unlink(path)
                c = users_db()
                try:
                    with c:
                        c.execute("update users set avatar = ? where id = ?", (version, u["id"]))
                finally:
                    c.close()
                return self.send_json({"avatar": version})
            if name == "password":
                u = session_user(self.session_token())
                if not u:
                    return self.send_json({"error": "Sign in to continue."}, 401)
                if not check_password(body.get("current") or "", u["pw"]):
                    return self.send_json({"error": "Your current password isn't right."}, 400)
                if len(body.get("new") or "") < 8:
                    return self.send_json({"error": "Use a new password of at least 8 characters."}, 400)
                c = users_db()
                try:
                    with c:
                        c.execute("update users set pw = ? where id = ?", (hash_password(body["new"]), u["id"]))
                        # sign out every other device
                        c.execute("delete from sessions where user_id = ? and token != ?", (u["id"], token_key(self.session_token())))
                finally:
                    c.close()
                return self.send_json({"ok": True})
            return self.send_json({"error": "Unknown call"}, 404)
        except AuthError as e:
            return self.send_json({"error": str(e)}, 400)
        except (ApiError, ValueError, json.JSONDecodeError) as e:
            return self.send_json({"error": str(e)}, 400)

    def route(self):
        if not self.authorized():
            return
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        low = path.lower()
        ctx.db = None
        try:
            if low.startswith("/auth/"):
                return self.auth_api(low[len("/auth/"):].strip("/"))
            public = low in ("/", "/index.html", "/favicon.svg", "/manifest.webmanifest", "/icon.svg") or low.startswith("/assets/")
            if not public:
                u = session_user(self.session_token())
                if not u:
                    if low.startswith("/api/") or low.startswith("/moneybook/"):
                        return self.send_json({"error": "Sign in to continue."}, 401)
                    return self.send("", code=302, headers={"Location": "/"})  # the app shows sign-in
                ctx.db = os.path.join(DATA_DIR, u["book"])
            if low.startswith("/api/"):
                return self.json_api(path[len("/api/"):])
            if low in ("/", "/index.html"):
                return self.static_file("index.html", APP)
            if low.startswith("/assets/") or low in ("/favicon.svg", "/manifest.webmanifest", "/icon.svg"):
                return self.static_file(path[1:], APP)
            if low == "/classic":
                return self.send("", code=301, headers={"Location": "/classic/"})
            if low.startswith("/classic/"):  # the original ExtJS UI, unchanged, under /classic/
                path = path[len("/classic"):]
                low = path.lower()
                if low in ("/", "/index.html"):
                    return self.static_file("index.html")
            if low == "/print.html":
                return self.static_file("print.html")
            if low.startswith("/static/"):
                return self.static_file(path[len("/static/"):])
            if low.startswith("/js/"):  # realbyte-lang.js loads js/locale/ext-lang-*.js page-relative
                return self.static_file(path[1:])
            if low.startswith("/moneybook/"):
                return self.api(low[len("/moneybook/"):])
            self.send("Not found", code=404)
        except Exception as e:  # keep the server up; the UI shows its own error
            self.log_message("error on %s: %r", path, e)
            self.send(json.dumps({"success": False, "msg": str(e)}), code=500)

    def static_file(self, rel, root=None):
        root = root or STATIC
        full = os.path.realpath(os.path.join(root, rel))
        if not full.startswith(os.path.realpath(root) + os.sep) or not os.path.isfile(full):
            return self.send("Not found", code=404)
        with open(full, "rb") as f:
            self.send(f.read(), TYPES.get(os.path.splitext(full)[1].lower(), "application/octet-stream"))

    def json_api(self, name):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query, keep_blank_values=True))
        parts = name.strip("/").split("/")
        try:
            if self.command == "GET" and parts[0] in API_GET and len(parts) == 1:
                c = connect()
                try:
                    return self.send_json(API_GET[parts[0]](c, q))
                finally:
                    c.close()
            body = {}
            if self.command == "POST":
                if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                    raise ApiError("Expected JSON")
                body = self.read_json()
            routes = {("POST", "transactions"): lambda c: api_save_transaction(c, body),
                      ("POST", "accounts"): lambda c: api_save_account(c, body)}
            if self.command == "DELETE" and len(parts) == 2 and parts[0] in ("transactions", "accounts"):
                fn = (api_delete_transaction if parts[0] == "transactions" else api_delete_account)
                op = lambda c: fn(c, parts[1])  # noqa: E731
            else:
                op = routes.get((self.command, parts[0])) if len(parts) == 1 else None
            if not op:
                return self.send_json({"error": "Unknown API call"}, 404)
            with write_lock:
                c = connect()
                try:
                    with c:
                        return self.send_json(op(c))
                finally:
                    c.close()
        except (ApiError, ValueError, json.JSONDecodeError) as e:
            return self.send_json({"error": str(e)}, 400)

    def send_json(self, obj, code=200):
        self.send(json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8", code)

    def api(self, name):
        if name == "initvar.js":
            return self.send("Realbyte.lang = 'en';Realbyte.moneyFormat='0,000.00';Realbyte.uri='moneyBook';",
                             "application/javascript")
        if name == "money.sqlite":
            return self.send(snapshot_bytes(), "application/x-sqlite3",
                             headers={"Content-Disposition": 'attachment; filename="money.sqlite"'})
        p = self.params()
        if name == "uploadsqlfile":
            data = p.get("file")
            if not isinstance(data, bytes) or not data.startswith(b"SQLite format 3\x00"):
                return self.send(json.dumps({"success": False, "msg": "Not a SQLite file"}), "text/html")
            fd, tmp = tempfile.mkstemp(suffix=".sqlite", dir=os.path.dirname(db_path()))
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            try:
                install_db(tmp)
            except Exception:
                os.path.exists(tmp) and os.unlink(tmp)
                raise
            return self.send(json.dumps({"success": True}), "text/html")  # ExtJS reads uploads via iframe
        if name == "getexcelfile":
            c = connect()
            try:
                body = excel_csv(c, p)
            finally:
                c.close()
            fname = "MoneyManager_%s_%s.csv" % (parse_day(p.get("startDate")), parse_day(p.get("endDate")))
            return self.send(body, "text/csv; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="%s"' % fname})
        if name in READS:
            c = connect()
            try:
                result = READS[name](c, p)
            finally:
                c.close()
            if name == "getdatabyperiod":
                return self.send(result, "application/xml; charset=UTF-8")
            return self.send(json.dumps(result, ensure_ascii=False))
        if name in WRITES:
            with write_lock:
                c = connect()
                try:
                    with c:
                        WRITES[name](c, p)
                finally:
                    c.close()
            return self.send(json.dumps({"success": True}))
        self.send("Not found", code=404)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--import-from":
        return import_from(sys.argv[2])
    if len(sys.argv) == 2 and sys.argv[1] == "--list-users":
        c = users_db()
        for r in c.execute("select id, username, book, created from users order by id"):
            print("%3d  %-24s %s  (since %s)" % (r["id"], r["username"], r["book"], datetime.fromtimestamp(r["created"]).date()))
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--reset-password":
        pw = secrets.token_urlsafe(9)
        c = users_db()
        with c:
            n = c.execute("update users set pw = ? where username = ?", (hash_password(pw), sys.argv[2])).rowcount
            if n:
                c.execute("delete from sessions where user_id = (select id from users where username = ?)", (sys.argv[2],))
        sys.exit("No account named %s" % sys.argv[2]) if not n else print("New password for %s: %s" % (sys.argv[2], pw))
        return
    if not os.path.exists(DB_PATH):
        sys.exit("No database at %s. Import one first:\n  python3 %s --import-from http://<phone-ip>:8888"
                 % (DB_PATH, sys.argv[0]))
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print("Money Manager on http://%s:%d  (db %s)" % (HOST, PORT, DB_PATH), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
