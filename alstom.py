from __future__ import annotations

import re
import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Iterable, Tuple
import bisect
import sys
import os
from collections import deque
from math import isnan
import csv  # added for CSV exports

# GUI file picker (optional)
def pick_files_gui() -> List[str]:
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        return list(filedialog.askopenfilenames(title="Select DRU/JRU log files"))
    except Exception as e:
        print(f"[WARN] GUI file selection failed: {e}")
        return []

def gui_select_files_and_output():
    """
    GUI dialog allowing user to:
      - Select multiple input files
      - Select (optional) output directory
      - Press Run to proceed
    Returns (files_list, out_dir_or_None)
    """
    try:
        from tkinter import Tk, Button, Label, Listbox, END, filedialog, SINGLE
    except Exception as e:
        print(f"[WARN] Tkinter not available for GUI: {e}")
        return [], None

    files: List[str] = []
    out_dir: Optional[str] = None
    done = {"value": False}

    def pick_files():
        nonlocal files
        sel = filedialog.askopenfilenames(title="Select input log files")
        if sel:
            files = list(sel)
            lb.delete(0, END)
            for fp in files:
                lb.insert(END, os.path.basename(fp))

    def pick_out_dir():
        nonlocal out_dir
        d = filedialog.askdirectory(title="Select output directory")
        if d:
            out_dir = d
            lbl_out_dir.config(text=f"Output dir: {out_dir}")

    def run():
        done["value"] = True
        root.destroy()

    def cancel():
        files.clear()
        done["value"] = True
        root.destroy()

    root = Tk()
    root.title("DRU/JRU Reporter")
    Button(root, text="Browse Input Files", command=pick_files, width=25).pack(pady=4)
    lb = Listbox(root, height=8, selectmode=SINGLE, width=60)
    lb.pack(padx=6, pady=4)
    Button(root, text="Browse Output Directory", command=pick_out_dir, width=25).pack(pady=4)
    lbl_out_dir = Label(root, text="Output dir: (will fallback to first file directory)")
    lbl_out_dir.pack(padx=6, pady=4)
    Button(root, text="Run", command=run, width=12).pack(pady=4)
    Button(root, text="Cancel", command=cancel, width=12).pack(pady=2)
    try:
        root.mainloop()
    except Exception as e:
        print(f"[WARN] GUI mainloop failed: {e}")
        return [], None
    return files, out_dir

@dataclass
class JRUMessage:
    dt: datetime
    m_level: Optional[int]
    m_mode: Optional[int]
    current_speed_1kph: Optional[int]
    stm_mode: Optional[int]  # added STM mode

@dataclass
class AntennaTestRecord:
    dt: datetime
    antenna: str   # 'A' or 'B' (or '0'/'1' mapped)
    flag: str
    value: int

# New dataclass to hold Q_BTM_ALARM events
@dataclass
class BTMAlarmRecord:
    dt: datetime
    value: int

ANTENNA_COUNTER_FLAGS = [
    "PERFORMED",
    "FAILED",
    "FAILED_BALISE_VICINITY",
    "FAILED_NOISE_SUSPICION",
    "INCORRECT_PAM",
    "INCORRECT_LEVEL",
]

class DRUJRUReporter:
    def __init__(self, max_delta_time_s: int = 30, max_delta_stat_counters_min: int = 11):
        self.jru_messages: List[JRUMessage] = []
        self.jru_timestamps: List[datetime] = []  # parallel list for bisect
        self.antenna_tests: List[AntennaTestRecord] = []
        # storage for parsed Q_BTM_ALARM events
        self.q_btm_alarms: List[BTMAlarmRecord] = []
        self.q_btm_alarm_timestamps: List[datetime] = []
        self.m_level_remap: Dict[int, str] = {}
        self.m_mode_remap: Dict[int, str] = {}
        # Buffer & regex for antenna stats (multi‑line, like BTMAntennaTestStatsParser)
        self._antenna_buffer: deque[str] = deque(maxlen=80)  # reduced from 120 for performance
        self._antenna_stats_re = re.compile(
            r"STAT_TYPE\s*:\s*2.*?CHANNEL_ID\s*\(0\)\s*:\s*0.*?ANTENNA_ID\s*\(0\)\s*:\s*(\d).*?"
            r"NB_ANTENNA_TESTS_PERFORMED\s*\(0\)\s*:\s*(\d+).*?"
            r"NB_ANTENNA_TESTS_FAILED\s*\(0\)\s*:\s*(\d+).*?"
            r"NB_ANTENNA_TESTS_FAILED_BALISE_VICINITY\s*\(0\)\s*:\s*(\d+).*?"
            r"NB_ANTENNA_TESTS_FAILED_NOISE_SUSPICION\s*\(0\)\s*:\s*(\d+).*?"
            r"NB_ANTENNA_TESTS_INCORRECT_PAM\s*\(0\)\s*:\s*(\d+).*?"
            r"NB_ANTENNA_TESTS_INCORRECT_LEVEL\s*\(0\)\s*:\s*(\d+)",
            re.DOTALL
        )
        self._antenna_ts_date_re = re.compile(r"DATE\.YEAR\s*:\s*(\d+).*?DATE\.MONTH\s*:\s*(\d+).*?DATE\.DAY\s*:\s*(\d+)", re.DOTALL)
        self._antenna_ts_time_re = re.compile(r"TIME\.HOUR\s*:\s*(\d+).*?TIME\.MINUTES\s*:\s*(\d+).*?TIME\.SECONDS\s*:\s*(\d+).*?TIME\.MILLI(?:SECONDS|SECONDES)\s*:\s*(\d+)",
            re.DOTALL
        )
        self._antenna_stats_seen: set[tuple[datetime, int]] = set()
        # Precompile key/value pattern once (moved out of per-block parsing)
        self._kv_pattern = re.compile(r'^\s*([A-Z0-9_.]+)\s*:\s*([^-\n\r]+?)(?:-->(.*))?$', re.IGNORECASE)
        # Metrics configuration
        self.max_delta_time_s = max_delta_time_s
        # Will hold computed metrics after produce_metrics()
        self.metrics: Dict[str, float] = {}
        # 5b configuration
        self.max_delta_stat_counters_s = max_delta_stat_counters_min * 60
        # Antenna aggregated snapshots (list aligned with timestamps)
        self._antenna_full_entries: List[Tuple[datetime, str, Dict[str, int]]] = []
        self._antenna_full_timestamps: List[datetime] = []
        # 5b results
        self.btm_alarm_context: List[Dict[str, object]] = []
        # 5c results: per antenna snapshot deltas
        self.antenna_flag_deltas: List[Dict[str, object]] = []
        # Monthly aggregation containers
        self.monthly_time_distance: Dict[tuple[int, int], Dict[str, float]] = {}  # (year, month) -> accumulators
        self.monthly_alarm_counts: Dict[tuple[int, int], Dict[str, int]] = {}     # (year, month) -> alarm counts
        self.metrics_monthly: List[Dict[str, object]] = []  # finalized monthly rows for export
        # Carry-forward caches for JRU fields (reset per file)
        self._last_m_level: Optional[int] = None
        self._last_m_mode: Optional[int] = None
        self._last_stm_mode: Optional[int] = None
        self._last_speed: Optional[int] = None  # propagate last speed
        # NEW: cumulative distance (km) aligned with self.jru_timestamps
        self._cumulative_distance_km: List[float] = []

    @staticmethod
    def _digits_int(s: str, default: int = 0) -> int:
        """Fast extraction of integer digits without regex."""
        digits = ''.join(ch for ch in s if ch.isdigit())
        if not digits:
            return default
        try:
            return int(digits)
        except Exception as e:
            print(f"[WARN] int conversion failed: {e}")
            return default

    # -------- Parsing Entry --------
    def parse_files(self, filepaths: Iterable[str]) -> None:
        for fp in filepaths:
            # Reset carry-forward fields for each new file
            self._last_m_level = None
            self._last_m_mode = None
            self._last_stm_mode = None
            self._last_speed = None  # reset last speed per file
            print(f"[INFO] Parsing {fp}")
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    self._parse_stream(f)
            except Exception as e:
                print(f"[ERROR] Failed parsing {fp}: {e}")
        # Sort after all files parsed (ascending)
        self._finalize_sort()

    # -------- Stream Parsing --------
    def _parse_stream(self, lines: Iterable[str]) -> None:
        # State for block accumulation
        in_block = False
        block_buffer = []
        append_block = block_buffer.append
        for line in lines:
            # Antenna test quick pass
            self._try_parse_antenna_line(line)
            # Fast block start detection (replaces regex search)
            if not in_block and 'JRU' in line and '(' in line:
                in_block = True
                block_buffer = [line]
                append_block = block_buffer.append
                continue
            if in_block:
                append_block(line)
                if line.strip() == ')':
                    try:
                        self._parse_jru_msg3_block(block_buffer)
                    except Exception as e:
                        print(f"[WARN] Failed to parse Msg 3 block: {e}")
                    # Removed duplicate _try_parse_q_btm_alarm_block call (optimization)
                    in_block = False
                    block_buffer = []
                    append_block = block_buffer.append
                    continue

    # -------- Specific Parsers --------
    def _parse_jru_msg3_block(self, block_lines: List[str]) -> None:
        # Extract needed fields (optimized: reuse precompiled pattern)
        fields = {}
        kv_pattern = self._kv_pattern
        for ln in block_lines:
            m = kv_pattern.match(ln)
            if not m:
                continue
            key = m.group(1).strip()
            raw_val = m.group(2).strip()
            desc = (m.group(3) or "").strip()
            fields[key] = (raw_val, desc)

        # Timestamp attempt (allow Q_BTM_ALARM parsing even if other fields missing)
        # Robust to both TIME.MILLISECONDS and TIME.MILLISECONDES
        millis_key = None
        for k in ("TIME.MILLISECONDS", "TIME.MILLISECONDES"):
            if k in fields:
                millis_key = k
                break
        have_dt_parts = all(k in fields for k in ("DATE.YEAR","DATE.MONTH","DATE.DAY",
                                                  "TIME.HOUR","TIME.MINUTES","TIME.SECONDS")) and millis_key is not None
        dt = None
        if have_dt_parts:
            try:
                year  = self._digits_int(fields["DATE.YEAR"][0])
                month = self._digits_int(fields["DATE.MONTH"][0])
                day   = self._digits_int(fields["DATE.DAY"][0])
                hour  = self._digits_int(fields["TIME.HOUR"][0])
                minute= self._digits_int(fields["TIME.MINUTES"][0])
                second= self._digits_int(fields["TIME.SECONDS"][0])
                millis= self._digits_int(fields[millis_key][0])
                dt = datetime(year, month, day, hour, minute, second, millis * 1000)
            except Exception as e:
                print(f"[WARN] Invalid datetime in Msg 3: {e}")
                dt = None

        # Parse Q_BTM_ALARM early (so we don't lose it after optimization removing secondary parser)
        if "Q_BTM_ALARM" in fields and dt is not None:
            try:
                q_val = self._digits_int(fields["Q_BTM_ALARM"][0])
                self.q_btm_alarms.append(BTMAlarmRecord(dt=dt, value=q_val))
                self.q_btm_alarm_timestamps.append(dt)
            except Exception as e:
                print(f"[WARN] Q_BTM_ALARM parse: {e}")

        # Required keys for constructing a full JRU message
        required_keys = ["M_LEVEL","M_MODE","V_TRAIN"]

        # New: abort message parsing (but keep earlier Q_BTM_ALARM capture) if any mandatory value is 'Unknown'
        unknown_fields = []
        for k in ("M_LEVEL", "M_MODE", "V_TRAIN"):
            if k in fields:
                try:
                    if 'unknown' in fields[k][0].strip().lower():
                        unknown_fields.append(k)
                except Exception as e:
                    print(f"[WARN] Unknown detection failed for {k}: {e}")

        # M_LEVEL with carry-forward
        m_level = None
        try:
            if "M_LEVEL" in fields and 'unknown' not in fields["M_LEVEL"][0].strip().lower():
                m_level = self._digits_int(fields["M_LEVEL"][0])
                desc = fields["M_LEVEL"][1]
                if desc and m_level not in self.m_level_remap:
                    self.m_level_remap[m_level] = desc
                self._last_m_level = m_level
            else:
                m_level = self._last_m_level
        except Exception as e:
            print(f"[WARN] M_LEVEL parse: {e}")
            m_level = self._last_m_level

        # M_MODE with carry-forward
        m_mode = None
        try:
            if "M_MODE" in fields and 'unknown' not in fields["M_MODE"][0].strip().lower():
                m_mode = self._digits_int(fields["M_MODE"][0])
                desc = fields["M_MODE"][1]
                if desc and m_mode not in self.m_mode_remap:
                    self.m_mode_remap[m_mode] = desc
                self._last_m_mode = m_mode
            else:
                m_mode = self._last_m_mode
        except Exception as e:
            print(f"[WARN] M_MODE parse: {e}")
            m_mode = self._last_m_mode

        # STM_MODE (optional) with carry-forward (no mapping dict)
        stm_mode = None
        try:
            if "STM_MODE" in fields and 'unknown' not in fields["STM_MODE"][0].strip().lower():
                stm_mode = self._digits_int(fields["STM_MODE"][0])
                self._last_stm_mode = stm_mode
            else:
                stm_mode = self._last_stm_mode
        except Exception as e:
            print(f"[WARN] STM_MODE parse: {e}")
            stm_mode = self._last_stm_mode

        # CURRENT_SPEED_1KPH with carry-forward
        speed = None
        try:
            if "V_TRAIN" in fields and 'unknown' not in fields["V_TRAIN"][0].strip().lower():
                speed = self._digits_int(fields["V_TRAIN"][0])
                if speed in (1022, 1023):
                    speed = 0
                self._last_speed = speed
            else:
                speed = self._last_speed
        except Exception as e:
            print(f"[WARN] Speed parse: {e}")
            speed = self._last_speed

        # Require timestamp; other fields may be None now (still store message)
        if dt is None:
            return

        msg = JRUMessage(dt=dt, m_level=m_level, m_mode=m_mode, current_speed_1kph=speed, stm_mode=stm_mode)
        self.jru_messages.append(msg)
        self.jru_timestamps.append(dt)

    def _try_parse_antenna_line(self, line: str) -> None:
        # Append current line into sliding buffer for multi-line antenna stats detection
        self._antenna_buffer.append(line)

        # Optimization: only attempt heavy multi-line regex after the last expected counter line arrives
        if 'NB_ANTENNA_TESTS_INCORRECT_LEVEL' in line:
            block_text = ''.join(self._antenna_buffer)
            m = self._antenna_stats_re.search(block_text)
            if m:
                try:
                    date_m = self._antenna_ts_date_re.search(block_text)
                    time_m = self._antenna_ts_time_re.search(block_text)
                    if date_m and time_m:
                        year, month, day = map(int, date_m.groups())
                        hour, minute, second, ms = map(int, time_m.groups())
                        ts = datetime(year, month, day, hour, minute, second, ms * 1000)
                    else:
                        ts = None
                        print("[WARN] Antenna stats matched but timestamp fields missing; skipping timestamped emit.")
                    if ts is not None:
                        antenna_id = int(m.group(1))
                        key = (ts, antenna_id)
                        if key not in self._antenna_stats_seen:
                            self._antenna_stats_seen.add(key)
                            performed = int(m.group(2))
                            failed = int(m.group(3))
                            failed_balise_vicinity = int(m.group(4))
                            failed_noise_suspicion = int(m.group(5))
                            incorrect_pam = int(m.group(6))
                            incorrect_level = int(m.group(7))
                            antenna_letter = 'A' if antenna_id == 0 else 'B'
                            records = [
                                ("PERFORMED", performed),
                                ("FAILED", failed),
                                ("FAILED_BALISE_VICINITY", failed_balise_vicinity),
                                ("FAILED_NOISE_SUSPICION", failed_noise_suspicion),
                                ("INCORRECT_PAM", incorrect_pam),
                                ("INCORRECT_LEVEL", incorrect_level),
                            ]
                            for flag, val in records:
                                self.antenna_tests.append(
                                    AntennaTestRecord(dt=ts, antenna=antenna_letter, flag=flag, value=val)
                                )
                        else:
                            print(f"[WARN] Duplicate antenna-stats block skipped for antenna_id={antenna_id} at {ts}")
                    # Clear buffer after processing to avoid repeated large searches
                    self._antenna_buffer.clear()
                except Exception as e:
                    print(f"[WARN] Antenna stats parse: {e}")
        # --- Legacy single-line placeholder parser retained as fallback ---
        try:
            pattern = re.compile(
                r'(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}).*?\bANT(?:ENNA)?\s*(?P<ant>[AB01])\b.*?\b(?P<flag>[A-Z0-9_]+)\s*=\s*(?P<val>\d+)',
                re.IGNORECASE
            )
            lm = pattern.search(line)
            if lm:
                print("[WARN] Antenna fallback parser used for single line (simple regex matched).")
                try:
                    dt = datetime.strptime(lm.group('ts'), "%Y-%m-%d %H:%M:%S.%f")
                    ant_raw = lm.group('ant').upper()
                    antenna = 'A' if ant_raw in ('A', '0') else 'B'
                    flag = lm.group('flag').upper()
                    val = int(lm.group('val'))
                    self.antenna_tests.append(AntennaTestRecord(dt=dt, antenna=antenna, flag=flag, value=val))
                except Exception as inner_e:
                    print(f"[WARN] Antenna (line) parse failed: {inner_e}")
        except Exception as e:
            print(f"[WARN] Antenna fallback regex error: {e}")

    # -------- Sorting / Finalization --------
    def _finalize_sort(self):
        if not self.jru_messages:
            # still sort alarms if present
            if self.q_btm_alarms:
                paired_alarm = list(zip(self.q_btm_alarm_timestamps, self.q_btm_alarms))
                paired_alarm.sort(key=lambda x: x[0])
                self.q_btm_alarm_timestamps = [p[0] for p in paired_alarm]
                self.q_btm_alarms = [p[1] for p in paired_alarm]
            return
        # If already appended in chronological order per file could be mostly sorted; still sort
        paired = list(zip(self.jru_timestamps, self.jru_messages))
        paired.sort(key=lambda x: x[0])
        self.jru_timestamps = [p[0] for p in paired]
        self.jru_messages = [p[1] for p in paired]

        # Also sort Q_BTM_ALARM records if any
        if self.q_btm_alarms:
            paired_alarm = list(zip(self.q_btm_alarm_timestamps, self.q_btm_alarms))
            paired_alarm.sort(key=lambda x: x[0])
            self.q_btm_alarm_timestamps = [p[0] for p in paired_alarm]
            self.q_btm_alarms = [p[1] for p in paired_alarm]

        # Build aggregated antenna snapshots per (timestamp, antenna)
        try:
            if self.antenna_tests:
                grouped: Dict[Tuple[datetime, str], Dict[str, int]] = {}
                for rec in self.antenna_tests:
                    key = (rec.dt, rec.antenna)
                    d = grouped.setdefault(key, {})
                    # keep last value per flag (overwrite if duplicates)
                    d[rec.flag] = rec.value
                # Convert to list
                entries = []
                for (dt, ant), flags in grouped.items():
                    entries.append((dt, ant, flags))
                entries.sort(key=lambda x: x[0])
                self._antenna_full_entries = entries
                self._antenna_full_timestamps = [e[0] for e in entries]
                # --- 5c) Compute per-antenna deltas ---
                try:
                    per_ant: Dict[str, List[Tuple[datetime, Dict[str, int]]]] = {}
                    for dt, ant, flags in self._antenna_full_entries:
                        per_ant.setdefault(ant, []).append((dt, flags))
                    deltas_out: List[Dict[str, object]] = []
                    for ant, snapshots in per_ant.items():
                        prev_flags = None
                        for dt, flags in snapshots:
                            row = {"dt": dt, "antenna": ant}
                            # First, check if any flag has a negative delta (reset case)
                            reset_case = False
                            if prev_flags is not None:
                                for flag in ANTENNA_COUNTER_FLAGS:
                                    cur = flags.get(flag, 0)
                                    prev = prev_flags.get(flag, 0)
                                    if cur - prev < 0:
                                        reset_case = True
                                        break
                            for flag in ANTENNA_COUNTER_FLAGS:
                                cur = flags.get(flag, 0)
                                if prev_flags is None or reset_case:
                                    delta = cur  # first snapshot or reset: treat as reset/start
                                else:
                                    prev = prev_flags.get(flag, 0)
                                    raw_delta = cur - prev
                                    delta = raw_delta
                                row[f"delta_{flag}"] = delta
                                row[f"delta_{flag}"] = delta
                            deltas_out.append(row)
                            prev_flags = flags
                    self.antenna_flag_deltas = deltas_out
                except Exception as e:
                    print(f"[WARN] Antenna delta computation failed: {e}")
        except Exception as e:
            print(f"[WARN] Antenna aggregation failed: {e}")

    # -------- Search API --------
    def find_message_at_or_before(self, dt: datetime) -> Optional[JRUMessage]:
        idx = bisect.bisect_right(self.jru_timestamps, dt) - 1
        if idx >= 0:
            return self.jru_messages[idx]
        return None

    # New: finder for Q_BTM_ALARM at or before a datetime
    def find_btm_alarm_at_or_before(self, dt: datetime) -> Optional[BTMAlarmRecord]:
        idx = bisect.bisect_right(self.q_btm_alarm_timestamps, dt) - 1
        if idx >= 0:
            return self.q_btm_alarms[idx]
        return None

    # -------- Metrics (To Be Implemented) --------
    def produce_metrics(self):
        # 5a moving / standstill
        total_moving_time_s = 0.0
        total_standstill_time_s = 0.0
        total_moving_distance_raw = 0.0
        total_standstill_distance_raw = 0.0
        if not self.jru_messages or len(self.jru_messages) < 2:
            self.metrics = {
                "moving_time_s": 0.0,
                "standstill_time_s": 0.0,
                "moving_distance_raw": 0.0,
                "standstill_distance_raw": 0.0,
                "moving_distance_km": 0.0,
                "standstill_distance_km": 0.0,
                "total_time_s": 0.0,
                "total_distance_raw": 0.0,
                "total_distance_km": 0.0,
                "segments": 0,
                "btm_alarm_speed_zero": 0,
                "btm_alarm_speed_moving": 0
            }
            # Ensure cumulative distance list still initialized
            self._cumulative_distance_km = [0.0] * len(self.jru_messages)
        else:
            # Initialize cumulative distance list
            self._cumulative_distance_km = [0.0] * len(self.jru_messages)
            last_dt = self.jru_messages[0].dt
            segments = 0
            cumulative_km = 0.0
            for i in range(1, len(self.jru_messages)):
                msg = self.jru_messages[i]
                dt = msg.dt
                delta_t = (dt - last_dt).total_seconds()
                if delta_t < 0:
                    print(f"[WARN] Negative delta_t detected at index {i}; skipping interval.")
                    last_dt = dt
                    continue
                if delta_t > self.max_delta_time_s:
                    print(f"[INFO] Reset detected (delta_t={delta_t:.2f}s > {self.max_delta_time_s}s) at {dt}; skipping interval.")
                    last_dt = dt
                    continue
                speed = msg.current_speed_1kph
                if speed is None:
                    # carry forward cumulative distance value
                    self._cumulative_distance_km[i] = cumulative_km
                    last_dt = dt
                    continue
                delta_distance_raw = delta_t * speed
                # Monthly key based on start of interval (last_dt)
                mk = (last_dt.year, last_dt.month)
                agg = self.monthly_time_distance.setdefault(mk, {
                    "moving_time_s": 0.0,
                    "standstill_time_s": 0.0,
                    "moving_distance_raw": 0.0,
                    "standstill_distance_raw": 0.0
                })
                if speed > 0:
                    total_moving_time_s += delta_t
                    total_moving_distance_raw += delta_distance_raw
                    agg["moving_time_s"] += delta_t
                    agg["moving_distance_raw"] += delta_distance_raw
                else:
                    total_standstill_time_s += delta_t
                    total_standstill_distance_raw += delta_distance_raw
                    agg["standstill_time_s"] += delta_t
                    agg["standstill_distance_raw"] += delta_distance_raw
                delta_km = delta_distance_raw / 3600.0
                cumulative_km += delta_km
                self._cumulative_distance_km[i] = cumulative_km
                segments += 1
                last_dt = dt
            moving_distance_km = total_moving_distance_raw / 3600.0
            standstill_distance_km = total_standstill_distance_raw / 3600.0
            self.metrics = {
                "moving_time_s": total_moving_time_s,
                "standstill_time_s": total_standstill_time_s,
                "moving_distance_raw": total_moving_distance_raw,
                "standstill_distance_raw": total_standstill_distance_raw,
                "moving_distance_km": moving_distance_km,
                "standstill_distance_km": standstill_distance_km,
                "total_time_s": total_moving_time_s + total_standstill_time_s,
                "total_distance_raw": total_moving_distance_raw + total_standstill_distance_raw,
                "total_distance_km": moving_distance_km + standstill_distance_km,
                "segments": segments,
                "btm_alarm_speed_zero": 0,
                "btm_alarm_speed_moving": 0
            }
        # 5b context
        try:
            self._compute_btm_alarm_context()
        except Exception as e:
            print(f"[WARN] BTM alarm context computation failed: {e}")
        # NEW: augment antenna deltas with speed + cumulative distance
        try:
            self._augment_antenna_deltas_speed_distance()
        except Exception as e:
            print(f"[WARN] Antenna delta augmentation failed: {e}")
        # Finalize monthly metrics (merge time/distance + alarm counts)
        try:
            months = set(self.monthly_time_distance.keys()) | set(self.monthly_alarm_counts.keys())
            rows = []
            for (y, mth) in sorted(months):
                td = self.monthly_time_distance.get((y, mth), {})
                ac = self.monthly_alarm_counts.get((y, mth), {})
                moving_time_s = td.get("moving_time_s", 0.0)
                standstill_time_s = td.get("standstill_time_s", 0.0)
                moving_distance_raw = td.get("moving_distance_raw", 0.0)
                standstill_distance_raw = td.get("standstill_distance_raw", 0.0)
                row = {
                    "month": f"{y:04d}-{mth:02d}",
                    "total_distance_km": (moving_distance_raw + standstill_distance_raw) / 3600.0,
                    "total_time_min": (moving_time_s + standstill_time_s) / 60.0,
                    "moving_time_min": moving_time_s / 60.0,
                    "standstill_time_min": standstill_time_s / 60.0,
                    "btm_alarm_speed_zero": ac.get("btm_alarm_speed_zero", 0),
                    "btm_alarm_speed_moving": ac.get("btm_alarm_speed_moving", 0),
                    "moving_distance_km": moving_distance_raw / 3600.0
                }
                rows.append(row)
            self.metrics_monthly = rows
        except Exception as e:
            print(f"[WARN] Monthly metrics finalization failed: {e}")

    def _compute_btm_alarm_context(self):
        # Refactored: use self.antenna_flag_deltas (already contains per-snapshot deltas).
        if not self.q_btm_alarms:
            return

        # Prepare sorted antenna delta snapshots by timestamp (global order, ignoring antenna separation)
        if self.antenna_flag_deltas:
            deltas_sorted = sorted(self.antenna_flag_deltas, key=lambda r: r["dt"])
            delta_timestamps = [r["dt"] for r in deltas_sorted]
        else:
            deltas_sorted = []
            delta_timestamps = []

        contexts = []
        speed_zero = 0
        speed_moving = 0

        for alarm in self.q_btm_alarms:
            if alarm.value != 1:
                continue  # Only alarms with value 1
            ts_alarm = alarm.dt

            # Get latest Msg 3 at or before alarm for speed / mode / level context
            msg = self.find_message_at_or_before(ts_alarm)
            m_level = msg.m_level if msg else None
            m_mode = msg.m_mode if msg else None
            speed = msg.current_speed_1kph if msg else None
            stm_mode = msg.stm_mode if msg else None  # added

            if speed is not None:
                if speed == 0:
                    speed_zero += 1
                    mk = (ts_alarm.year, ts_alarm.month)
                    self.monthly_alarm_counts.setdefault(mk, {
                        "btm_alarm_speed_zero": 0,
                        "btm_alarm_speed_moving": 0
                    })["btm_alarm_speed_zero"] += 1
                else:
                    speed_moving += 1
                    mk = (ts_alarm.year, ts_alarm.month)
                    self.monthly_alarm_counts.setdefault(mk, {
                        "btm_alarm_speed_zero": 0,
                        "btm_alarm_speed_moving": 0
                    })["btm_alarm_speed_moving"] += 1

            # Find nearest upper antenna delta snapshot (dt >= alarm)
            deltas_row = None
            valid = True
            if not delta_timestamps:
                valid = False
            else:
                idx = bisect.bisect_left(delta_timestamps, ts_alarm)
                if idx >= len(delta_timestamps):
                    # No upper snapshot
                    valid = False
                else:
                    upper_row = deltas_sorted[idx]
                    gap_s = (upper_row["dt"] - ts_alarm).total_seconds()
                    if gap_s < 0 or gap_s > self.max_delta_stat_counters_s:
                        valid = False
                    else:
                        deltas_row = upper_row  # Use its already computed deltas

            ctx_row = {
                "btm_alarm_timestamp": ts_alarm,
                "m_level": m_level,
                "m_mode": m_mode,
                "current_speed_1kph": speed,
                "stm_mode": stm_mode,  # added
            }

            # Populate delta fields
            for flag in ANTENNA_COUNTER_FLAGS:
                key_source = f"delta_{flag}"
                key_target = f"delta_{flag.lower()}"
                if valid and deltas_row and key_source in deltas_row:
                    ctx_row[key_target] = deltas_row[key_source]
                else:
                    ctx_row[key_target] = float('nan')

            if valid and deltas_row:
                print(f"[INFO] BTM alarm context deltas @ {ts_alarm} using snapshot {deltas_row['dt']}: {ctx_row}")
            elif not valid:
                print(f"[WARN] No valid antenna delta snapshot for BTM alarm @ {ts_alarm}")

            contexts.append(ctx_row)

        self.btm_alarm_context = contexts
        # Update metrics counts (metrics dict already initialized in produce_metrics)
        self.metrics["btm_alarm_speed_zero"] = speed_zero
        self.metrics["btm_alarm_speed_moving"] = speed_moving

    def _augment_antenna_deltas_speed_distance(self):
        """
        For each antenna delta snapshot, sample:
          - speed_1kph : speed from nearest JRU message timestamp
          - cum_distance_km : cumulative distance (km) at that nearest timestamp
        Nearest = closest absolute time difference (prefers earlier on tie).
        """
        if not self.antenna_flag_deltas or not self.jru_timestamps:
            return
        for row in self.antenna_flag_deltas:
            dt = row["dt"]
            speed, cum_km = self._get_speed_and_cumulative_distance_nearest(dt)
            row["speed_1kph"] = speed
            row["cum_distance_km"] = cum_km
        print("[INFO] Augmented antenna deltas with speed and cumulative distance.")

    def _get_speed_and_cumulative_distance_nearest(self, dt: datetime) -> Tuple[Optional[int], Optional[float]]:
        """
        Return (speed, cumulative_distance_km) for nearest JRU message timestamp.
        """
        if not self.jru_timestamps:
            return None, None
        idx = bisect.bisect_left(self.jru_timestamps, dt)
        candidates = []
        if idx < len(self.jru_timestamps):
            candidates.append(idx)
        if idx > 0:
            candidates.append(idx - 1)
        if not candidates:
            return None, None
        # choose nearest (tie -> earlier)
        best_i = candidates[0]
        best_diff = abs((self.jru_timestamps[best_i] - dt).total_seconds())
        for i in candidates[1:]:
            diff = abs((self.jru_timestamps[i] - dt).total_seconds())
            if diff < best_diff or (diff == best_diff and self.jru_timestamps[i] <= self.jru_timestamps[best_i]):
                best_i = i
                best_diff = diff
        msg = self.jru_messages[best_i]
        cum_km = self._cumulative_distance_km[best_i] if best_i < len(self._cumulative_distance_km) else None
        return msg.current_speed_1kph, cum_km

    def export_metrics_to_csv(self, out_dir: str):
        # Implements point 6: 6a summary csv, 6b antenna deltas csv, 6c BTM alarm context csv
        try:
            if not out_dir:
                print("[WARN] Output directory not provided.")
                return
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            print(f"[WARN] Cannot create output directory '{out_dir}': {e}")
            return

        # 6a) Summary CSV
        try:
            summary_path = os.path.join(out_dir, "summary.csv")
            headers = [
                "Month",
                "Total distance (km)",
                "Total time (min)",
                "Moving time (min)",
                "Standstill time (min)",
                "BTM alarms (standstill)",
                "BTM alarms (moving)",
                "BTM alarms per 1000 km"
            ]
            if not self.metrics_monthly:
                print("[WARN] No monthly metrics computed; writing empty summary.")
            with open(summary_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                total_distance_km = 0.0
                total_time_min = 0.0
                total_moving_time_min = 0.0
                total_standstill_time_min = 0.0
                total_btm_alarm_speed_zero = 0
                total_btm_alarm_speed_moving = 0
                total_moving_distance_km = 0.0
                for row in self.metrics_monthly:
                    moving_distance_km = row.get("moving_distance_km", 0.0)
                    btm_alarms_moving = row.get("btm_alarm_speed_moving", 0)
                    alarms_per_1000km = 1000 * (btm_alarms_moving / moving_distance_km) if moving_distance_km > 0 else 0.0
                    writer.writerow([
                        row["month"],
                        f"{row['total_distance_km']:.0f}",
                        f"{row['total_time_min']:.0f}",
                        f"{row['moving_time_min']:.0f}",
                        f"{row['standstill_time_min']:.0f}",
                        row["btm_alarm_speed_zero"],
                        row["btm_alarm_speed_moving"],
                        f"{alarms_per_1000km:.0f}"
                    ])
                    # Accumulate totals
                    total_distance_km += moving_distance_km
                    total_time_min += row["total_time_min"]
                    total_moving_time_min += row["moving_time_min"]
                    total_standstill_time_min += row["standstill_time_min"]
                    total_btm_alarm_speed_zero += row["btm_alarm_speed_zero"]
                    total_btm_alarm_speed_moving += row["btm_alarm_speed_moving"]
                    total_moving_distance_km += moving_distance_km
                # Write totals row if any data
                if self.metrics_monthly:
                    total_alarms_per_1000km = 1000 * (total_btm_alarm_speed_moving / total_moving_distance_km) if total_moving_distance_km > 0 else 0.0
                    writer.writerow([
                        "TOTAL",
                        f"{total_distance_km:.0f}",
                        f"{total_time_min:.0f}",
                        f"{total_moving_time_min:.0f}",
                        f"{total_standstill_time_min:.0f}",
                        total_btm_alarm_speed_zero,
                        total_btm_alarm_speed_moving,
                        f"{total_alarms_per_1000km:.0f}"
                    ])
            print(f"[INFO] Summary (monthly) CSV written: {summary_path}")
        except Exception as e:
            print(f"[WARN] Failed writing summary csv: {e}")

        # Helper for NaN
        def _csv_safe(v):
            if v is None:
                return ""
            if isinstance(v, float) and isnan(v):
                return ""
            return v

        # 6b) Antenna deltas CSV
        try:
            if self.antenna_flag_deltas:
                deltas_path = os.path.join(out_dir, "antenna_deltas.csv")
                # Collect header preserving order: dt, antenna, speed_1kph, cum_distance_km, then delta_* flags
                base_fields = ["dt", "antenna", "speed_kph", "cum_distance"]
                delta_cols = []
                for flag in ANTENNA_COUNTER_FLAGS:
                    col = f"delta_{flag}"
                    delta_cols.append(col)
                header = base_fields + delta_cols
                with open(deltas_path, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(header)
                    for row in sorted(self.antenna_flag_deltas, key=lambda r: r["dt"]):
                        w.writerow([
                            row["dt"].isoformat(),
                            row["antenna"],
                            _csv_safe(row.get("speed_1kph")),
                            _csv_safe(f"{row.get('cum_distance_km', 0.0):.3f}" if row.get("cum_distance_km") is not None else ""),
                            *[_csv_safe(row.get(f"delta_{flag}", "")) for flag in ANTENNA_COUNTER_FLAGS]
                        ])
                print(f"[INFO] Antenna deltas CSV written: {deltas_path}")
            else:
                print("[WARN] No antenna_flag_deltas to export.")
        except Exception as e:
            print(f"[WARN] Failed writing antenna deltas csv: {e}")

        # 6c) BTM alarm context CSV
        try:
            if self.btm_alarm_context:
                ctx_path = os.path.join(out_dir, "btm_alarm_context.csv")
                # Build header (STM_MODE column now string, no legend)
                base_cols = [
                    "btm_alarm_timestamp",
                    "m_mode", "m_mode_str",
                    "STM_MODE",
                    "current_speed_1kph"
                ]
                delta_cols = [f"delta_{flag.lower()}" for flag in ANTENNA_COUNTER_FLAGS]
                header = base_cols + delta_cols
                stm_mode_map = {3: "CS", 4: "HS", 5: "DA"}
                with open(ctx_path, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(header)
                    for row in sorted(self.btm_alarm_context, key=lambda r: r["btm_alarm_timestamp"]):
                        m_mode = row.get("m_mode", "")
                        m_mode_str = ""
                        try:
                            if m_mode != "" and m_mode is not None:
                                m_mode_str = self.m_mode_remap.get(m_mode, "")
                        except Exception as e:
                            print(f"[WARN] M_MODE lookup failed: {e}")
                        stm_mode_val = row.get("stm_mode", None)
                        if stm_mode_val is not None and stm_mode_val in stm_mode_map:
                            stm_mode_str = stm_mode_map[stm_mode_val]
                        else:
                            stm_mode_str = "unknown"
                        w.writerow([
                            row["btm_alarm_timestamp"].isoformat(),
                            m_mode,
                            m_mode_str,
                            stm_mode_str,
                            row.get("current_speed_1kph", ""),
                            *[_csv_safe(row.get(f"delta_{flag.lower()}", "")) for flag in ANTENNA_COUNTER_FLAGS]
                        ])
                print(f"[INFO] BTM alarm context CSV written: {ctx_path}")
            else:
                print("[INFO] No BTM alarm context data to export.")
        except Exception as e:
            print(f"[WARN] Failed writing BTM alarm context csv: {e}")

# -------- CLI / Main --------
def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DRU/JRU Reporter (skeleton for metrics).")
    p.add_argument("files", nargs="*", help="Input log files (optional if GUI used).")
    p.add_argument("--no-gui", action="store_true", help="Disable GUI file picker.")
    p.add_argument("--max-delta-time", type=int, default=30, help="Max delta (s) between Msg 3 entries before considering a reset (default 30).")
    p.add_argument("--max-delta-stat-counters-min", type=int, default=11,
                   help="Max minutes between lower/upper antenna stats snapshots for delta (default 11).")
    p.add_argument("--out-dir", help="Directory to write output files (summary + CSVs).")
    return p.parse_args(argv)

def main(argv: List[str]) -> int:
    args = parse_args(argv)
    files = list(args.files)
    gui_chosen_out_dir = None  # track GUI-selected out dir
    if not files and not args.no_gui:
        try:
            gui_files, gui_out = gui_select_files_and_output()
            if gui_files:
                files = list(gui_files)
            gui_chosen_out_dir = gui_out
        except Exception as e:
            print(f"[WARN] GUI selection failed: {e}")
    if not files:
        print("No input files provided.")
        return 1
    reporter = DRUJRUReporter(max_delta_time_s=args.max_delta_time,
                              max_delta_stat_counters_min=args.max_delta_stat_counters_min)
    reporter.parse_files(files)
    # Compute metrics 5a
    try:
        reporter.produce_metrics()
    except Exception as e:
        print(f"[WARN] Metrics computation failed: {e}")
    # Skeleton summary
    print(f"[SUMMARY] Parsed {len(reporter.jru_messages)} JRU Msg 3 entries")
    print(f"[SUMMARY] Parsed {len(reporter.antenna_tests)} antenna test records (placeholder logic)")
    print(f"[SUMMARY] Parsed {len(reporter.q_btm_alarms)} Q_BTM_ALARM records")
    print(f"[SUMMARY] M_LEVEL map: {reporter.m_level_remap}")
    print(f"[SUMMARY] M_MODE map: {reporter.m_mode_remap}")
    if reporter.metrics:
        m = reporter.metrics
        print("[METRICS 5a] Moving time (s):", f"{m['moving_time_s']:.2f}")
        print("[METRICS 5a] Standstill time (s):", f"{m['standstill_time_s']:.2f}")
        print("[METRICS 5a] Total time (m):", f"{m['total_time_s'] / 60.:.2f}")
        print("[METRICS 5a] Total distance (km):", f"{m['total_distance_km']:.3f}")
        print("[METRICS 5a] Segments counted:", m['segments'])
        print("[METRICS 5b] BTM alarms at standstill:", m.get("btm_alarm_speed_zero", 0))
        print("[METRICS 5b] BTM alarms in movement:", m.get("btm_alarm_speed_moving", 0))
        print(f"[METRICS 5b] Context rows: {len(reporter.btm_alarm_context)}")

    # Determine export directory priority: CLI --out-dir > GUI selection > first input file dir
    export_dir = args.out_dir or gui_chosen_out_dir
    if not export_dir and files:
        try:
            export_dir = os.path.dirname(os.path.abspath(files[0]))
            print(f"[INFO] Output directory fallback to: {export_dir}")
        except Exception as e:
            print(f"[WARN] Failed to derive fallback output directory: {e}")
            export_dir = None

    if export_dir:
        try:
            reporter.export_metrics_to_csv(export_dir)
        except Exception as e:
            print(f"[WARN] Export failed: {e}")
    else:
        print("[WARN] No output directory resolved; skipping exports.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        print(f"Unhandled error: {e}")
        sys.exit(2)

