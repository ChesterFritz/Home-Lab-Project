#!/usr/bin/env python3
"""Pi Health — a tiny, dependency-free health dashboard for an Orange Pi PC (Allwinner H3).

Samples CPU, temperature, GPU clock, network, memory and an *estimated* power draw
every 2 seconds, runs periodic service checks, raises alerts, and serves a single-page
dashboard plus a small JSON API.

Standard library only, so it runs on 32-bit ARM with ~15 MB of RAM.
"""

import glob
import gzip
import http.client
import json
import os
import random
import shutil
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
CONFIG_PATH = os.environ.get("PI_HEALTH_CONFIG", "/etc/pi-health.json")
STATE_DIR = os.environ.get("STATE_DIRECTORY", os.path.join(HERE, "state"))

DEFAULTS = {
    "port": 8090,
    "bind": "0.0.0.0",
    "lan_iface": "end0",
    "vpn_iface": "tailscale0",
    "sample_seconds": 2,
    "backup_dir": "/var/backups/pi",
    "backup_max_age_hours": 26,
    "containers": ["adguardhome", "uptime-kuma"],
    "dns_server": "127.0.0.1",
    "internet_hosts": [["1.1.1.1", 443], ["8.8.8.8", 53]],
    # Push notifications (optional): e.g. "https://ntfy.sh/your-secret-topic"
    "ntfy_url": "",
    # App launcher. "{host}" becomes whatever address the dashboard was opened on, so the
    # links work both on the LAN and over Tailscale. Set "probe": false to skip the up check.
    "links": [
        {"name": "AdGuard Home", "desc": "Ad blocking and DNS", "url": "http://{host}/",
         "icon": "shield", "container": "adguardhome"},
        {"name": "Uptime Kuma", "desc": "Uptime monitors", "url": "http://{host}:3001/",
         "icon": "pulse", "container": "uptime-kuma"},
        {"name": "Router", "desc": "Home network settings", "url": "http://192.168.18.1/",
         "icon": "router"},
        {"name": "Tailscale", "desc": "Devices and exit node",
         "url": "https://login.tailscale.com/admin/machines", "icon": "mesh", "probe": False},
    ],
    "thresholds": {
        "temp_warn": 70, "temp_crit": 80,
        "cpu_warn": 90, "cpu_warn_minutes": 5,
        "mem_avail_warn_pct": 20, "mem_avail_crit_pct": 10,
        "disk_warn": 85, "disk_crit": 95,
        "swap_warn": 50,
    },
    # Power model for the Orange Pi PC. There is no current sensor on this board,
    # so watts are estimated from CPU load, clock, core voltage and GPU activity.
    "power_model": {"base_w": 1.4, "cpu_max_w": 3.0, "gpu_max_w": 0.5,
                    "ref_mhz": 1296, "ref_volt": 1.3},
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(CONFIG_PATH) as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    except FileNotFoundError:
        pass
    except Exception as e:  # bad JSON should not stop the dashboard
        print(f"config error ({CONFIG_PATH}): {e}", flush=True)
    return cfg


CFG = load_config()
LOCK = threading.Lock()


# --------------------------------------------------------------------------- readers

def read(path, default=None):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def read_int(path, default=None):
    v = read(path)
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def cpu_times():
    """Return {name: (idle, total)} for 'cpu' and each 'cpuN'."""
    out = {}
    for line in read("/proc/stat", "").splitlines():
        if not line.startswith("cpu"):
            break
        parts = line.split()
        vals = list(map(int, parts[1:]))
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        out[parts[0]] = (idle, sum(vals[:8]))
    return out


def net_bytes():
    out = {}
    for line in read("/proc/net/dev", "").splitlines()[2:]:
        name, data = line.split(":", 1)
        f = data.split()
        out[name.strip()] = (int(f[0]), int(f[8]))
    return out


def meminfo():
    m = {}
    for line in read("/proc/meminfo", "").splitlines():
        k, v = line.split(":", 1)
        m[k] = int(v.split()[0]) * 1024
    return m


def find_regulator(name):
    for r in glob.glob("/sys/class/regulator/*"):
        if read(os.path.join(r, "name")) == name:
            return r
    return None


def find_gpu_devfreq():
    for d in glob.glob("/sys/class/devfreq/*"):
        if "gpu" in os.path.basename(d):
            return d
    return None


def gpu_trans_times(devfreq):
    """Parse devfreq trans_stat: {freq_hz: time_ms}."""
    txt = read(os.path.join(devfreq, "trans_stat"), "") if devfreq else ""
    times = {}
    for line in txt.splitlines():
        line = line.strip().lstrip("*").strip()
        if ":" not in line or not line[0].isdigit():
            continue
        freq, rest = line.split(":", 1)
        nums = rest.split()
        if nums:
            try:
                times[int(freq)] = int(nums[-1])
            except ValueError:
                pass
    return times


VDD_CPU = find_regulator("vdd-cpux")
GPU_DEV = find_gpu_devfreq()
CPU_MAX_KHZ = read_int("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", 1296000)
GPU_FREQS = sorted(int(x) for x in (read(os.path.join(GPU_DEV, "available_frequencies"), "")
                                    if GPU_DEV else "").split() if x.isdigit())


def cpu_temp():
    best = None
    for z in glob.glob("/sys/class/thermal/thermal_zone*"):
        t = read_int(os.path.join(z, "temp"))
        if t is not None:
            best = max(best or -1e9, t / 1000.0)
    return round(best, 1) if best is not None else None


# --------------------------------------------------------------------------- sampler

class Sampler:
    def __init__(self):
        self.fine = deque(maxlen=int(3600 / CFG["sample_seconds"]))   # 1 h at 2 s
        self.coarse = deque(maxlen=24 * 60)                              # 24 h at 1 min
        self._bucket = []
        self._bucket_min = None
        self._prev_cpu = cpu_times()
        self._prev_net = net_bytes()
        self._prev_gpu = gpu_trans_times(GPU_DEV)
        self._prev_t = time.time()
        self.latest = None

    def sample(self):
        now = time.time()
        dt = max(now - self._prev_t, 0.001)

        cur = cpu_times()
        util = {}
        for k, (idle, total) in cur.items():
            pi, pt = self._prev_cpu.get(k, (idle, total))
            d = total - pt
            util[k] = round(100.0 * (1 - (idle - pi) / d), 1) if d > 0 else 0.0
        self._prev_cpu = cur
        cores = [util[k] for k in sorted(util) if k != "cpu"]

        n = net_bytes()

        def rate(iface):
            if iface not in n or iface not in self._prev_net:
                return 0.0, 0.0
            (rx, tx), (prx, ptx) = n[iface], self._prev_net[iface]
            return max(rx - prx, 0) / dt, max(tx - ptx, 0) / dt

        rx, tx = rate(CFG["lan_iface"])
        vrx, vtx = rate(CFG["vpn_iface"])
        self._prev_net = n

        freqs = [read_int(p) for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq")]
        freqs = [f for f in freqs if f]
        cpu_mhz = round(sum(freqs) / len(freqs) / 1000) if freqs else None
        volt = (read_int(os.path.join(VDD_CPU, "microvolts")) or 0) / 1e6 if VDD_CPU else None

        # GPU activity: share of time spent above the idle clock since the last sample.
        gpu_hz = read_int(os.path.join(GPU_DEV, "cur_freq")) if GPU_DEV else None
        gpu_busy = None
        gt = gpu_trans_times(GPU_DEV)
        if gt and self._prev_gpu and GPU_FREQS:
            deltas = {f: gt.get(f, 0) - self._prev_gpu.get(f, 0) for f in gt}
            total = sum(d for d in deltas.values() if d > 0)
            if total > 0:
                busy = sum(d for f, d in deltas.items() if f > GPU_FREQS[0] and d > 0)
                gpu_busy = round(100.0 * busy / total, 1)
        if gpu_busy is None and gpu_hz and GPU_FREQS:
            gpu_busy = 0.0 if gpu_hz <= GPU_FREQS[0] else 100.0 * gpu_hz / GPU_FREQS[-1]
        self._prev_gpu = gt

        m = meminfo()
        mem_total = m.get("MemTotal", 1)
        mem_avail = m.get("MemAvailable", 0)
        swap_total = m.get("SwapTotal", 0)
        swap_used = swap_total - m.get("SwapFree", 0)

        pm = CFG["power_model"]
        f_ratio = (cpu_mhz or pm["ref_mhz"]) / pm["ref_mhz"]
        v_ratio = ((volt or pm["ref_volt"]) / pm["ref_volt"]) ** 2
        watts = (pm["base_w"]
                 + pm["cpu_max_w"] * (util.get("cpu", 0) / 100.0) * f_ratio * v_ratio
                 + pm["gpu_max_w"] * ((gpu_busy or 0) / 100.0))

        s = {
            "t": round(now, 1),
            "cpu": util.get("cpu", 0.0),
            "cores": cores,
            "cpu_mhz": cpu_mhz,
            "volt": round(volt, 3) if volt else None,
            "temp": cpu_temp(),
            "gpu_mhz": round(gpu_hz / 1e6) if gpu_hz else None,
            "gpu": round(gpu_busy, 1) if gpu_busy is not None else None,
            "rx": round(rx), "tx": round(tx),
            "vrx": round(vrx), "vtx": round(vtx),
            "mem": round(100.0 * (mem_total - mem_avail) / mem_total, 1),
            "mem_used": mem_total - mem_avail, "mem_total": mem_total,
            "swap": round(100.0 * swap_used / swap_total, 1) if swap_total else 0.0,
            "watts": round(watts, 2),
        }
        self._prev_t = now
        with LOCK:
            self.latest = s
            self.fine.append(s)
            self._roll_minute(s)
        return s

    def _roll_minute(self, s):
        minute = int(s["t"] // 60)
        if self._bucket_min is not None and minute != self._bucket_min and self._bucket:
            b = self._bucket
            avg = lambda k: round(sum(x[k] or 0 for x in b) / len(b), 2)
            mx = lambda k: max((x[k] or 0) for x in b)
            self.coarse.append({
                "t": self._bucket_min * 60 + 30,
                "cpu": avg("cpu"), "temp": mx("temp"), "gpu": avg("gpu"),
                "gpu_mhz": mx("gpu_mhz"), "cpu_mhz": avg("cpu_mhz"),
                "rx": avg("rx"), "tx": avg("tx"), "vrx": avg("vrx"), "vtx": avg("vtx"),
                "mem": avg("mem"), "swap": avg("swap"), "watts": avg("watts"),
            })
            self._bucket = []
        self._bucket_min = minute
        self._bucket.append(s)

    def history(self, seconds):
        cutoff = time.time() - seconds
        with LOCK:
            src = self.fine if seconds <= 3600 else self.coarse
            rows = [r for r in src if r["t"] >= cutoff]
        keys = ["t", "cpu", "temp", "gpu", "gpu_mhz", "cpu_mhz", "rx", "tx", "vrx", "vtx",
                "mem", "swap", "watts"]
        return {k: [r.get(k) for r in rows] for k in keys}

    def save(self, path):
        with LOCK:
            data = {"coarse": list(self.coarse), "fine": list(self.fine)}
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)

    def restore(self, path):
        try:
            with open(path) as f:
                data = json.load(f)
            now = time.time()
            self.coarse.extend(r for r in data.get("coarse", []) if r["t"] >= now - 24 * 3600)
            self.fine.extend(r for r in data.get("fine", []) if r["t"] >= now - 3600)
        except (OSError, ValueError):
            pass


# --------------------------------------------------------------------------- checks

def docker_get(path):
    conn = http.client.HTTPConnection("docker")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect("/var/run/docker.sock")
    conn.sock = sock
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return json.loads(body)


def check_containers():
    try:
        rows = docker_get("/containers/json?all=1")
    except Exception as e:
        return None, f"Docker unreachable: {e}"
    out = []
    for c in rows:
        name = c["Names"][0].lstrip("/") if c.get("Names") else c["Id"][:12]
        status = c.get("Status", "")
        health = ("unhealthy" if "(unhealthy)" in status else
                  "healthy" if "(healthy)" in status else
                  "starting" if "(health: starting)" in status else None)
        out.append({"name": name, "state": c.get("State"), "status": status,
                    "health": health, "image": c.get("Image")})
    return sorted(out, key=lambda c: c["name"]), None


def check_dns(server, name="example.com"):
    qid = random.randint(0, 0xFFFF)
    header = struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\0"
    packet = header + qname + struct.pack(">HH", 1, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    t0 = time.time()
    try:
        s.sendto(packet, (server, 53))
        data, _ = s.recvfrom(512)
        ms = (time.time() - t0) * 1000
        rid, flags, _, ancount = struct.unpack(">HHHH", data[:8])
        ok = rid == qid and (flags & 0x000F) == 0 and ancount > 0
        return ok, round(ms, 1)
    except OSError:
        return False, None
    finally:
        s.close()


def check_internet(hosts):
    for host, port in hosts:
        t0 = time.time()
        try:
            with socket.create_connection((host, port), timeout=3):
                return True, round((time.time() - t0) * 1000, 1)
        except OSError:
            continue
    return False, None


def check_failed_units():
    try:
        out = subprocess.run(["systemctl", "--failed", "--plain", "--no-legend", "--no-pager"],
                             capture_output=True, text=True, timeout=10).stdout
        return [l.split()[0] for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def check_backup(path):
    files = glob.glob(os.path.join(path, "pi-*.tar.gz"))
    if not files:
        return None
    newest = max(files, key=os.path.getmtime)
    return {"file": os.path.basename(newest), "mtime": os.path.getmtime(newest),
            "size": os.path.getsize(newest)}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def probe_link(url):
    """Any HTTP answer (even a redirect or 401) means the app is up."""
    url = url.replace("{host}", "127.0.0.1")
    t0 = time.time()
    try:
        _OPENER.open(urllib.request.Request(url, method="GET"), timeout=3).close()
        ok = True
    except urllib.error.HTTPError:
        ok = True
    except Exception:
        ok = False
    return ok, round((time.time() - t0) * 1000) if ok else None


def check_links():
    out = []
    for i, link in enumerate(CFG.get("links", [])):
        if link.get("probe", True) is False:
            out.append({"i": i, "up": None, "ms": None})
            continue
        up, ms = probe_link(link["url"])
        out.append({"i": i, "up": up, "ms": ms})
    return out


class Checks:
    def __init__(self):
        self.data = {}

    def run(self):
        links = check_links()
        containers, derr = check_containers()
        dns_ok, dns_ms = check_dns(CFG["dns_server"])
        net_ok, net_ms = check_internet(CFG["internet_hosts"])
        du = shutil.disk_usage("/")
        load = os.getloadavg()
        data = {
            "t": time.time(),
            "containers": containers or [],
            "links": links,
            "docker_error": derr,
            "dns": {"ok": dns_ok, "ms": dns_ms, "server": CFG["dns_server"]},
            "internet": {"ok": net_ok, "ms": net_ms},
            "failed_units": check_failed_units(),
            "backup": check_backup(CFG["backup_dir"]),
            "disk": {"used": du.used, "total": du.total, "pct": round(100.0 * du.used / du.total, 1)},
            "load": [round(x, 2) for x in load],
            "uptime": float(read("/proc/uptime", "0").split()[0]),
            "link_mbps": read_int(f"/sys/class/net/{CFG['lan_iface']}/speed"),
            "vpn_up": os.path.exists(f"/sys/class/net/{CFG['vpn_iface']}"),
        }
        with LOCK:
            self.data = data
        return data


# --------------------------------------------------------------------------- alerts

SEV_ORDER = {"critical": 0, "serious": 1, "warning": 2, "info": 3}


class Alerts:
    """Each rule is evaluated every cycle; a condition must hold for `for_s` seconds to fire."""

    def __init__(self, path):
        self.path = path
        self.active = {}      # key -> alert
        self.pending = {}     # key -> first-seen time
        self.events = deque(maxlen=200)
        self._load()

    def _load(self):
        try:
            with open(self.path) as f:
                data = json.load(f)
            self.events.extend(e for e in data.get("events", []) if e.get("title") != "Pi Health started")
            self.active = {a["key"]: a for a in data.get("active", [])}
        except (OSError, ValueError):
            pass

    def save(self):
        with LOCK:
            data = {"events": list(self.events), "active": list(self.active.values())}
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, self.path)

    def event(self, severity, title, detail="", key=None):
        e = {"t": time.time(), "severity": severity, "title": title, "detail": detail,
             "key": key, "kind": "event"}
        with LOCK:
            self.events.appendleft(e)
        notify(e)

    def evaluate(self, conditions):
        """conditions: list of (key, active?, severity, title, detail, for_s)."""
        now = time.time()
        seen = set()
        changed = False
        for key, on, sev, title, detail, for_s in conditions:
            if not on:
                continue
            seen.add(key)
            first = self.pending.setdefault(key, now)
            if key in self.active:
                a = self.active[key]
                if a["severity"] != sev or a["title"] != title:
                    a.update(severity=sev, title=title)
                    changed = True
                a["detail"] = detail
            elif now - first >= for_s:
                a = {"key": key, "severity": sev, "title": title, "detail": detail, "since": now}
                with LOCK:
                    self.active[key] = a
                    self.events.appendleft(dict(a, t=now, kind="raised"))
                notify(dict(a, kind="raised"))
                changed = True
        for key in list(self.pending):
            if key not in seen:
                self.pending.pop(key, None)
        for key in list(self.active):
            if key not in seen:
                a = self.active.pop(key)
                e = dict(a, t=now, kind="resolved", duration=now - a["since"])
                with LOCK:
                    self.events.appendleft(e)
                notify(e)
                changed = True
        if changed:
            self.save()

    def snapshot(self):
        with LOCK:
            act = sorted(self.active.values(), key=lambda a: (SEV_ORDER.get(a["severity"], 9), -a["since"]))
            return act, list(self.events)[:60]


def notify(e):
    url = CFG.get("ntfy_url")
    if not url:
        return
    kind = e.get("kind")
    prefix = {"raised": "", "resolved": "Resolved: ", "event": ""}.get(kind, "")
    prio = {"critical": "urgent", "serious": "high", "warning": "default", "info": "low"}
    tags = {"critical": "rotating_light", "serious": "warning", "warning": "warning", "info": "information_source"}
    title = f"{prefix}{e['title']}"
    headers = {"Title": f"Orange Pi: {title}".encode("utf-8").decode("latin-1", "ignore"),
               "Priority": "low" if kind == "resolved" else prio.get(e["severity"], "default"),
               "Tags": "white_check_mark" if kind == "resolved" else tags.get(e["severity"], "")}

    def send():
        try:
            req = urllib.request.Request(url, data=(e.get("detail") or title).encode(), headers=headers)
            urllib.request.urlopen(req, timeout=10).read()
        except Exception as ex:
            print(f"ntfy failed: {ex}", flush=True)
    threading.Thread(target=send, daemon=True).start()


def fmt_dur(sec):
    sec = int(sec)
    if sec < 3600:
        return f"{sec // 60} min"
    if sec < 86400:
        return f"{sec // 3600} h {sec % 3600 // 60} min"
    return f"{sec // 86400} d {sec % 86400 // 3600} h"


def build_conditions(sampler, checks):
    th = CFG["thresholds"]
    s = sampler.latest or {}
    c = checks.data or {}
    conds = []

    temp = s.get("temp")
    if temp is not None:
        crit = temp >= th["temp_crit"]
        conds.append(("temp", temp >= th["temp_warn"], "critical" if crit else "warning",
                      "CPU is very hot" if crit else "CPU is running hot",
                      f"{temp:.0f} °C (warn {th['temp_warn']} °C, critical {th['temp_crit']} °C)", 30))

    # Sustained CPU: average of the last N minutes of fine samples.
    window = th["cpu_warn_minutes"] * 60
    with LOCK:
        recent = [r["cpu"] for r in sampler.fine if r["t"] >= time.time() - window]
    if len(recent) >= window / CFG["sample_seconds"] * 0.9:
        avg = sum(recent) / len(recent)
        conds.append(("cpu", avg >= th["cpu_warn"], "warning", "CPU pegged",
                      f"{avg:.0f}% average over {th['cpu_warn_minutes']} min", 0))

    if s.get("cpu_mhz") and s.get("cpu", 0) > 80 and s["cpu_mhz"] * 1000 < CPU_MAX_KHZ * 0.85:
        conds.append(("throttle", True, "warning", "CPU is throttling",
                      f"{s['cpu_mhz']} MHz under load (max {CPU_MAX_KHZ // 1000} MHz)", 60))

    if s.get("mem_total"):
        avail_pct = 100 - s["mem"]
        crit = avail_pct < th["mem_avail_crit_pct"]
        conds.append(("mem", avail_pct < th["mem_avail_warn_pct"], "critical" if crit else "warning",
                      "Memory almost full" if crit else "Memory running low",
                      f"{avail_pct:.0f}% available", 60))
    if s.get("swap") is not None:
        conds.append(("swap", s["swap"] >= th["swap_warn"], "warning", "Heavy swap use",
                      f"{s['swap']:.0f}% of swap in use", 120))

    disk = c.get("disk")
    if disk:
        crit = disk["pct"] >= th["disk_crit"]
        conds.append(("disk", disk["pct"] >= th["disk_warn"], "critical" if crit else "warning",
                      "SD card almost full" if crit else "SD card filling up",
                      f"{disk['pct']:.0f}% used", 0))

    if c:
        if c.get("docker_error"):
            conds.append(("docker", True, "critical", "Docker is not responding", c["docker_error"], 30))
        names = {x["name"]: x for x in c.get("containers", [])}
        for want in CFG["containers"]:
            x = names.get(want)
            if not x:
                conds.append((f"ct:{want}", True, "critical", f"{want} container missing", "", 30))
            elif x["state"] != "running":
                conds.append((f"ct:{want}", True, "critical", f"{want} is down", x["status"], 30))
            elif x["health"] == "unhealthy":
                # Long grace period: the nightly backup pauses Uptime Kuma briefly.
                conds.append((f"ct:{want}", True, "serious", f"{want} is unhealthy", x["status"], 180))
        dns = c.get("dns", {})
        conds.append(("dns", not dns.get("ok", True), "critical", "AdGuard DNS not answering",
                      f"No reply from {dns.get('server')}:53 — devices on your network may lose internet", 60))
        inet = c.get("internet", {})
        conds.append(("internet", not inet.get("ok", True), "serious", "Internet is down",
                      "Cannot reach 1.1.1.1 or 8.8.8.8", 60))
        fu = c.get("failed_units") or []
        conds.append(("units", bool(fu), "warning",
                      f"{len(fu)} system service{'s' if len(fu) != 1 else ''} failed", ", ".join(fu), 0))
        conds.append(("vpn", not c.get("vpn_up", True), "serious", "Tailscale is down",
                      "Remote access and the exit node are unavailable", 60))
        b = c.get("backup")
        age = (time.time() - b["mtime"]) if b else None
        conds.append(("backup", b is None or age > CFG["backup_max_age_hours"] * 3600, "warning",
                      "Backup is overdue", f"Last backup {fmt_dur(age)} ago" if b else "No backups found", 0))
    return conds


# --------------------------------------------------------------------------- loops

SAMPLER = Sampler()
CHECKS = Checks()
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(os.path.join(STATE_DIR, "custom"), exist_ok=True)
ALERTS = Alerts(os.path.join(STATE_DIR, "alerts.json"))
SAMPLER.restore(os.path.join(STATE_DIR, "history.json"))
BOOT_INFO = {
    "hostname": socket.gethostname(),
    "kernel": os.uname().release,
    "arch": os.uname().machine,
    "model": (read("/proc/device-tree/model", "") or "").rstrip("\x00"),
    "os": next((l.split("=", 1)[1].strip('"') for l in (read("/etc/os-release", "") or "").splitlines()
                if l.startswith("PRETTY_NAME=")), ""),
    "cpu_max_mhz": CPU_MAX_KHZ // 1000,
    "gpu_max_mhz": GPU_FREQS[-1] // 1_000_000 if GPU_FREQS else None,
    "gpu_name": "Mali-400 MP2 (lima)" if GPU_DEV else None,
    "cores": os.cpu_count(),
    "power_estimated": True,
    "links": [{k: l.get(k) for k in ("name", "desc", "url", "icon", "container")}
              for l in CFG.get("links", [])],
}


def sample_loop():
    while True:
        t0 = time.time()
        try:
            SAMPLER.sample()
        except Exception as e:
            print(f"sample error: {e}", flush=True)
        time.sleep(max(CFG["sample_seconds"] - (time.time() - t0), 0.2))


def check_loop():
    uptime = float(read("/proc/uptime", "0").split()[0])
    if uptime < 600:
        ALERTS.event("info", "Orange Pi restarted", f"Booted {fmt_dur(uptime)} ago")
    time.sleep(CFG["sample_seconds"] * 2)
    last_save = time.time()
    while True:
        try:
            CHECKS.run()
            ALERTS.evaluate(build_conditions(SAMPLER, CHECKS))
            if time.time() - last_save > 120:
                SAMPLER.save(os.path.join(STATE_DIR, "history.json"))
                ALERTS.save()
                last_save = time.time()
        except Exception as e:
            print(f"check error: {e}", flush=True)
        time.sleep(15)


# --------------------------------------------------------------------------- http

GZ_CACHE = {}
RANGES = {"5m": 300, "15m": 900, "1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600}
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
        ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
        ".webmanifest": "application/manifest+json", ".woff2": "font/woff2", ".ico": "image/x-icon"}


# --------------------------------------------------------------------------- custom pictures
# Pictures (and a theme song) the owner uploads for the anime themes. They live only on the Pi
# (state dir), never in the app or the repo. Fixed slot names, sniffed file types, size-capped.
CUSTOM_DIR = os.path.join(STATE_DIR, "custom")
CUSTOM_FLAVORS = ("kirino", "kuroneko", "viking")
CUSTOM_KINDS = ("main", "happy", "worried", "angry", "dizzy", "sprite", "bg", "music")
CUSTOM_SLOTS = {f"{f}-{k}" for f in CUSTOM_FLAVORS for k in CUSTOM_KINDS}
CUSTOM_MAX = 8 * 1024 * 1024
MUSIC_MAX = 20 * 1024 * 1024
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
AUDIO_TYPES = {".mp3": "audio/mpeg"}
MEDIA_TYPES = {**IMAGE_TYPES, **AUDIO_TYPES}


def sniff_image(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    return None


def sniff_audio(data):
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return ".mp3"
    return None


def custom_find(slot):
    for ext in MEDIA_TYPES:
        p = os.path.join(CUSTOM_DIR, slot + ext)
        if os.path.isfile(p):
            return p
    return None


def custom_index():
    out = {}
    for slot in sorted(CUSTOM_SLOTS):
        p = custom_find(slot)
        if p:
            out[slot] = f"custom/{os.path.basename(p)}?v={int(os.path.getmtime(p))}"
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "PiHealth/1.0"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", cache="no-store", gz_key=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, separators=(",", ":")).encode()
        elif isinstance(body, str):
            body = body.encode()
        zipped = False
        if len(body) > 1024 and "gzip" in self.headers.get("Accept-Encoding", "") and \
                not ctype.startswith(("font/", "image/", "audio/")):
            if gz_key and gz_key in GZ_CACHE:
                body = GZ_CACHE[gz_key]
            else:
                body = gzip.compress(body, 6)
                if gz_key:
                    GZ_CACHE[gz_key] = body
            zipped = True
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if zipped:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/state":
            active, events = ALERTS.snapshot()
            with LOCK:
                latest, checks = SAMPLER.latest, dict(CHECKS.data)
            return self._send(200, {"info": BOOT_INFO, "now": latest, "checks": checks,
                                    "alerts": active, "events": events, "server_time": time.time()})
        if u.path == "/api/history":
            rng = parse_qs(u.query).get("range", ["15m"])[0]
            return self._send(200, SAMPLER.history(RANGES.get(rng, 900)))
        if u.path == "/healthz":
            return self._send(200, {"ok": True})
        if u.path == "/api/custom":
            return self._send(200, custom_index())
        if u.path.startswith("/custom/"):
            name = os.path.basename(u.path)
            slot, ext = os.path.splitext(name)
            p = os.path.join(CUSTOM_DIR, name)
            if slot not in CUSTOM_SLOTS or ext not in MEDIA_TYPES or not os.path.isfile(p):
                return self._send(404, {"error": "not found"})
            with open(p, "rb") as f:
                return self._send(200, f.read(), MEDIA_TYPES[ext], "public, max-age=31536000, immutable")
        name = "index.html" if u.path in ("/", "") else u.path.lstrip("/")
        full = os.path.realpath(os.path.join(STATIC, name))
        if not full.startswith(os.path.realpath(STATIC) + os.sep) or not os.path.isfile(full):
            return self._send(404, {"error": "not found"})
        with open(full, "rb") as f:
            body = f.read()
        ext = os.path.splitext(full)[1]
        # Built assets have content hashes in their names, so they can be cached for good.
        cache = "no-cache" if ext in (".html", ".webmanifest") else \
            "public, max-age=31536000, immutable" if "/assets/" in full else "max-age=3600"
        self._send(200, body, MIME.get(ext, "application/octet-stream"), cache,
                   gz_key=(full, os.path.getmtime(full)))


    def _slot(self):
        u = urlparse(self.path)
        if not u.path.startswith("/api/custom/"):
            return None
        slot = u.path[len("/api/custom/"):]
        return slot if slot in CUSTOM_SLOTS else False

    def do_PUT(self):
        slot = self._slot()
        if slot is None:
            return self._send(404, {"error": "not found"})
        if slot is False:
            return self._send(400, {"error": "Unknown picture slot"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        music = slot.endswith("-music")
        if length <= 0 or length > (MUSIC_MAX if music else CUSTOM_MAX):
            return self._send(413, {"error": "Music must be under 20 MB" if music else "Pictures must be under 8 MB"})
        data = self.rfile.read(length)
        ext = sniff_audio(data) if music else sniff_image(data)
        if not ext:
            return self._send(415, {"error": "Use an MP3 file" if music else "Use a PNG, JPEG, WebP or GIF picture"})
        os.makedirs(CUSTOM_DIR, exist_ok=True)
        old = custom_find(slot)
        tmp = os.path.join(CUSTOM_DIR, f".{slot}{ext}.tmp")
        with open(tmp, "wb") as f:
            f.write(data)
        if old and not old.endswith(ext):
            os.remove(old)
        os.replace(tmp, os.path.join(CUSTOM_DIR, slot + ext))
        return self._send(200, custom_index())

    def do_DELETE(self):
        slot = self._slot()
        if not slot:
            return self._send(404, {"error": "not found"})
        p = custom_find(slot)
        if p:
            os.remove(p)
        return self._send(200, custom_index())


def main():
    # systemd stops us with SIGTERM; turn it into a normal exit so history is saved.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    threading.Thread(target=sample_loop, daemon=True).start()
    threading.Thread(target=check_loop, daemon=True).start()
    srv = ThreadingHTTPServer((CFG["bind"], CFG["port"]), Handler)
    srv.daemon_threads = True
    print(f"Pi Health listening on http://{CFG['bind']}:{CFG['port']}", flush=True)
    try:
        srv.serve_forever()
    finally:
        SAMPLER.save(os.path.join(STATE_DIR, "history.json"))
        ALERTS.save()


if __name__ == "__main__":
    main()
