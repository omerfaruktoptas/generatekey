#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# "SpecialWordList" terminal UI
# by Omer Faruk TOPTAS  (no Turkish diacritics on author line as requested)

import os
import sys
import time
import itertools
import shutil
import subprocess

# ---------------------- Config ----------------------
MAX_VARIANTS_PER_TOKEN = 1024
PROGRESS_PRINT_INTERVAL = 0.5
PROGRESS_PRINT_LINES = 1000
DEFAULT_OUTPUT = "wordlist.txt"

BANNER_TEXT = "SpecialWordList"  # Banner'da gosterilecek yazi
# ----------------------------------------------------

# ------------------- UI: Colors & Utils -------------
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDER = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def term_width():
    return shutil.get_terminal_size((120, 30)).columns

def strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)

def center(s: str) -> str:
    w = term_width()
    length = len(strip_ansi(s))
    pad = max(0, (w - length) // 2)
    return " " * pad + s

def draw_box(lines, title="", color=C.BRIGHT_BLUE):
    if not isinstance(lines, list):
        lines = [str(lines)]
    content_width = max([len(strip_ansi(l)) for l in lines] + [len(strip_ansi(title))], default=0)
    padding = 2
    inner_w = content_width + padding * 2
    top = f"┌─ {title} " + "─" * max(0, inner_w - len(strip_ansi(title)) - 3) + "┐"
    print(center(color + top + C.RESET))
    for l in lines:
        spaces = inner_w - len(strip_ansi(l)) - padding
        print(center(color + "│" + C.RESET + " " * padding + l + " " * spaces + color + "│" + C.RESET))
    bottom = "└" + "─" * inner_w + "┘"
    print(center(color + bottom + C.RESET))

def ask(prompt: str, default: str = "") -> str:
    msg = f"{C.BRIGHT_WHITE}{prompt}{C.RESET}"
    if default:
        msg += f" {C.DIM}[{default}]{C.RESET}"
    msg += f"{C.BRIGHT_CYAN} > {C.RESET}"
    return input(msg).strip() or default

def spinner(text: str, seconds: float = 1.0):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    start = time.time()
    i = 0
    sys.stdout.write(C.HIDE_CURSOR)
    try:
        while time.time() - start < seconds:
            sys.stdout.write("\r" + C.BRIGHT_CYAN + frames[i % len(frames)] + C.RESET + " " + text + "   ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
    finally:
        sys.stdout.write("\r" + " " * (len(strip_ansi(text)) + 6) + "\r")
        sys.stdout.write(C.SHOW_CURSOR)
        sys.stdout.flush()

# ------------------- Bigger/Nicer Banner -------------------
def _run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="ignore")
    except Exception:
        return None

def toilet_lines(text: str, font: str):
    exe = shutil.which("toilet")
    if not exe:
        return None
    # -w: genislik; buyuk fontlarin tasmamasina yardimci
    w = str(max(80, term_width()))
    # -F border ile cerceve eklenebilir; burada sade tutuyoruz
    out = _run([exe, "-w", w, "-f", font, text])
    if not out:
        return None
    return out.rstrip("\n").splitlines()

def figlet_lines(text: str, font: str):
    exe = shutil.which("figlet")
    if not exe:
        return None
    w = str(max(80, term_width()))
    out = _run([exe, "-w", w, "-f", font, text])
    if not out:
        return None
    return out.rstrip("\n").splitlines()

def banner():
    # 1) En buyuk ve sik gorunum icin once toilet fontlari
    toilet_fonts = ["big", "block", "smblock"]
    figlet_fonts = ["ANSI Shadow", "Big", "Slant", "Doh", "Banner3-D", "Larry 3D", "Cyberlarge", "Standard"]

    lines = None
    for f in toilet_fonts:
        lines = toilet_lines(BANNER_TEXT, f)
        if lines:
            break
    if not lines:
        for f in figlet_fonts:
            lines = figlet_lines(BANNER_TEXT, f)
            if lines:
                break

    print()
    if lines:
        # Cok uzun satirlar terminalden tasarsa, basit bir kisaltma uygula
        tw = term_width()
        clipped = []
        for ln in lines:
            raw = strip_ansi(ln)
            if len(raw) > tw:
                ln = raw[:tw]
            clipped.append(ln)
        for ln in clipped:
            print(center(C.BRIGHT_CYAN + ln + C.RESET))
    else:
        # Son care sade buyuk harfli tek satir
        print(center(C.BRIGHT_CYAN + C.BOLD + BANNER_TEXT + C.RESET))

    by = center(f"{C.DIM}by {C.BRIGHT_RED}Omer Faruk TOPTAS{C.RESET}")
    print("\n" + by + "\n")

# ------------------- Core: Wordlist Logic -------------------
def parse_tokens(raw: str):
    raw = raw.strip()
    if raw == "":
        return []
    parts = raw.split()
    if len(parts) == 1 and ' ' not in raw and len(raw) > 1 and not raw.isalnum():
        return list(raw)
    return parts

def case_variants(token: str, max_variants: int = MAX_VARIANTS_PER_TOKEN):
    choices = []
    for ch in token:
        if ch.isalpha():
            choices.append((ch.lower(), ch.upper()))
        else:
            choices.append((ch,))
    total = 1
    for c in choices:
        total *= len(c)
        if total > max_variants:
            fallback = []
            for cand in (token, token.lower(), token.upper(), token.title()):
                if cand not in fallback:
                    fallback.append(cand)
            return fallback
    variants = [''.join(prod) for prod in itertools.product(*choices)]
    seen = set()
    uniq = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq

def count_sequence_combinations(token_lengths, min_len, max_len):
    if max_len < 0:
        return 0
    dp = [0] * (max_len + 1)
    dp[0] = 1
    for L in range(1, max_len + 1):
        s = 0
        for tl in token_lengths:
            if tl <= L:
                s += dp[L - tl]
        dp[L] = s
    return sum(dp[min_len:max_len + 1]) if max_len >= min_len else 0

def format_mb(bytes_count):
    return f"{bytes_count / 1024**2:.3f} MB"

# ------------------- Flow -------------------
def input_form():
    clear()
    banner()
    draw_box(
        [
            f"{C.BRIGHT_GREEN}Kelimeler{C.RESET}: boslukla ayirin (orn: omer faruk toptas)",
            f"{C.BRIGHT_GREEN}Sayilar{C.RESET}: boslukla ayirin (orn: 19 90 2025)",
            f"{C.BRIGHT_GREEN}Ozel{C.RESET}: tek parca girerseniz her karakter tek tek alinabilir (orn: !@#$)",
        ],
        title="INPUT GUIDE",
        color=C.BRIGHT_BLUE
    )

    words_raw = ask("Kelimeler")
    numbers_raw = ask("Sayilar")
    specials_raw = ask("Ozel karakterler (bos birakilabilir)")

    words = parse_tokens(words_raw)
    numbers = parse_tokens(numbers_raw)
    specials = parse_tokens(specials_raw)

    print()
    draw_box(
        [
            "Uzunluk araligi icin sayi giriniz.",
            "Ornek: min=4, max=12"
        ],
        title="LENGTH",
        color=C.BRIGHT_MAGENTA
    )
    try:
        min_len = int(ask("Minimum uzunluk", "4"))
        max_len = int(ask("Maksimum uzunluk", "12"))
    except ValueError:
        print(center(C.BRIGHT_RED + "Hata: uzunluk degerleri sayi olmali." + C.RESET))
        sys.exit(1)

    print()
    draw_box(
        [
            "Tokenler icin buyuk/kucuk harf varyantlari uret?",
            "Evet icin 'E' yazin, aksi halde Enter'a basin."
        ],
        title="CASE VARIANTS",
        color=C.BRIGHT_YELLOW
    )
    case_ans = ask("Varyant uret (E/h)", "h").strip().lower()
    case_expand = case_ans.startswith("e")

    print()
    out_path = ask("Kayit yolu", DEFAULT_OUTPUT) or DEFAULT_OUTPUT

    return words, numbers, specials, min_len, max_len, case_expand, out_path

def generate_wordlist_ui(words, numbers, specials, min_len, max_len, case_expand, out_path):
    clear()
    banner()
    draw_box(
        [
            f"Kelimeler: {', '.join(words) if words else '-'}",
            f"Sayilar  : {', '.join(numbers) if numbers else '-'}",
            f"Ozel     : {''.join(specials) if specials else '-'}",
            f"Min/Max  : {min_len}/{max_len}",
            f"Varyant  : {'Evet' if case_expand else 'Hayir'}",
            f"Dosya    : {out_path}"
        ],
        title="SUMMARY",
        color=C.BRIGHT_BLUE
    )

    spinner("Hazirlaniyor...", 0.8)

    original_tokens = [t for t in (words + numbers + specials) if t != ""]
    if not original_tokens:
        print(center(C.BRIGHT_RED + "En az bir token girilmelidir." + C.RESET))
        sys.exit(1)

    expanded = []
    expansion_info = []
    if case_expand:
        for t in original_tokens:
            v = case_variants(t)
            expanded.extend(v)
            expansion_info.append((t, len(v)))
    else:
        expanded = list(original_tokens)
        for t in original_tokens:
            expansion_info.append((t, 1))

    seen_tok = set()
    tokens = []
    for t in expanded:
        if t not in seen_tok:
            seen_tok.add(t)
            tokens.append(t)

    print()
    info_lines = [f"'{orig}' -> {count} variant" for (orig, count) in expansion_info]
    draw_box(info_lines or ["(no tokens)"], title="TOKEN VARIANTS", color=C.BRIGHT_MAGENTA)
    print(center(f"{C.DIM}Pool size (unique): {len(tokens)}{C.RESET}"))
    if case_expand:
        print(center(f"{C.DIM}MAX_VARIANTS_PER_TOKEN = {MAX_VARIANTS_PER_TOKEN}{C.RESET}"))
    print()

    if any(len(t) == 0 for t in tokens):
        print(center(C.BRIGHT_RED + "Hata: bos uzunluklu token tespit edildi." + C.RESET))
        sys.exit(1)

    token_lengths = [len(t) for t in tokens]
    total_sequences = count_sequence_combinations(token_lengths, min_len, max_len)
    if total_sequences == 0:
        print(center(C.BRIGHT_YELLOW + "Uretilebilecek kombinasyon yok (min/max uyusmuyor)." + C.RESET))
        sys.exit(1)

    print(center(f"Tahmini dizilim sayisi: {C.BRIGHT_WHITE}{total_sequences:,}{C.RESET}"))
    print(center(C.DIM + "Not: Bu sayi sirali kombinasyon tahminidir; benzersiz satir sayisi daha az olabilir." + C.RESET))
    print()

    written = 0
    attempted = 0
    last_print = time.time()
    writes_since = 0
    seen = set()

    def progress_line(file_obj):
        try:
            bytes_written = file_obj.tell()
        except Exception:
            try:
                bytes_written = os.path.getsize(out_path)
            except Exception:
                bytes_written = 0
        pct = (attempted / total_sequences) * 100 if total_sequences else 100.0
        line = f"Yazilan: {written:,} | Dosya: {format_mb(bytes_written)} | Tamamlandi: {pct:.2f}%"
        print("\r" + center(C.BRIGHT_CYAN + line + C.RESET), end="", flush=True)

    def dfs(curr, f):
        nonlocal written, attempted, last_print, writes_since
        cur_len = len(curr)
        if min_len <= cur_len <= max_len:
            attempted += 1
            if curr and curr not in seen:
                f.write(curr + "\n")
                f.flush()
                seen.add(curr)
                written += 1
                writes_since += 1
        if cur_len >= max_len:
            return
        for t in tokens:
            new_len = cur_len + len(t)
            if new_len > max_len:
                continue
            dfs(curr + t, f)
            now = time.time()
            if writes_since >= PROGRESS_PRINT_LINES or (now - last_print) >= PROGRESS_PRINT_INTERVAL:
                progress_line(f)
                last_print = now
                writes_since = 0

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            dfs("", f)
            try:
                bytes_written = f.tell()
            except Exception:
                try:
                    bytes_written = os.path.getsize(out_path)
                except Exception:
                    bytes_written = 0
    except KeyboardInterrupt:
        print()
        print(center(C.BRIGHT_YELLOW + "Islem kullanici tarafindan durduruldu." + C.RESET))
        try:
            bytes_written = os.path.getsize(out_path)
        except Exception:
            bytes_written = 0
        pct = (attempted / total_sequences) * 100 if total_sequences else 100.0
        print(center(f"Yazilan: {written:,} | Dosya: {format_mb(bytes_written)} | Tamamlandi: {pct:.2f}%"))
        sys.exit(1)

    pct = (attempted / total_sequences) * 100 if total_sequences else 100.0
    print()
    print()
    draw_box(
        [
            f"Kayit: {out_path}",
            f"Toplam satir (unique): {written:,}",
            f"Dosya boyutu: {format_mb(os.path.getsize(out_path) if os.path.exists(out_path) else 0)}",
            f"Tahmini tamamlanma: {pct:.2f}%"
        ],
        title="DONE",
        color=C.BRIGHT_GREEN
    )
    print(center(C.DIM + "Ipuclari: Tokenleri akilli secin, uzunluk araligini dar tutun." + C.RESET))
    print()

def main_menu():
    while True:
        clear()
        banner()
        draw_box(
            [
                f"{C.BRIGHT_GREEN}[1]{C.RESET} SpecialWordList (wordlist olustur)",
                f"{C.BRIGHT_GREEN}[2]{C.RESET} Cikis"
            ],
            title="MENU",
            color=C.BRIGHT_BLUE
        )
        choice = ask("Seciminiz", "1")
        if choice == "1":
            params = input_form()
            generate_wordlist_ui(*params)
            input(center(C.DIM + "Devam icin Enter'a basin..." + C.RESET))
        elif choice == "2":
            clear()
            banner()
            print(center(C.BRIGHT_GREEN + "Tesekkurler! Gule gule." + C.RESET))
            print()
            break
        else:
            print(center(C.BRIGHT_YELLOW + "Gecersiz secim." + C.RESET))
            time.sleep(1.1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(C.SHOW_CURSOR)
        print()