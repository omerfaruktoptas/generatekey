#!/usr/bin/env python3
# wordlist_blocks_case_prompt_with_progress.py
# Blok bazlı wordlist üretici. Kullanıcıya büyük/küçük harf varyantı isteyip istemediğini sorar.
# Üretim sırasında dosya boyutunu (MB) ve tamamlanma yüzdesini (tahmini) gösterir.

import sys
import itertools
import os
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel

MAX_VARIANTS_PER_TOKEN = 1024  # Güvenlik limiti; gerekirse artırılabilir
PROGRESS_PRINT_INTERVAL = 0.5  # saniye, ilerleme güncellemeleri arasındaki minimum süre
PROGRESS_PRINT_LINES = 1000    # veya bu kadar satır yazıldığında zorla güncelle

# Konsol oluşturuluyor
console = Console()

def read_tokens(prompt):
    raw = input(prompt).strip()
    if raw == "":
        return []
    parts = raw.split()
    # Eğer tek parça ve özel karakter dizisi ise her karakter ayrı token olsun
    if len(parts) == 1 and ' ' not in raw and len(raw) > 1 and not raw.isalnum():
        return list(raw)
    return parts

def case_variants(token, max_variants=MAX_VARIANTS_PER_TOKEN):
    """
    Bir token için tüm büyük/küçük harf kombinasyonlarını üretir.
    Eğer kombinasyon sayısı max_variants'ı geçerse, fallback olarak
    [original, lower, upper, title] kombinasyonlarını döner.
    """
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
    # Benzersizleştir ve sırayı koru
    seen = set()
    unique = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique

def count_sequence_combinations(token_lengths, min_len, max_len):
    """
    Token uzunluklarına göre sırayla (tekrar izinli) oluşturulabilecek dizilim sayısını (kombinasyon sırası önemli)
    dinamik programlama ile hesaplar. Bu sayı, üretilmesi planlanan "deneme" sayısının bir tahminidir.
    Benzersiz string sayısı bu tahminden daha küçük olabilir (farklı dizilimler aynı sonucu üretebilir).
    """
    if max_len < 0:
        return 0
    dp = [0] * (max_len + 1)
    dp[0] = 1  # boş dizilim
    for L in range(1, max_len + 1):
        s = 0
        for tl in token_lengths:
            if tl <= L:
                s += dp[L - tl]
        dp[L] = s
    total = sum(dp[min_len:max_len + 1]) if max_len >= min_len else 0
    return total

def format_mb(bytes_count):
    return f"{bytes_count / 1024**2:.3f} MB"

def main():
    # Başlangıç Mesajı
    console.print(Panel("Welcome to the GenerateKey Tool", style="bold blue", title="GenerateKey"))

    kelimeler = Prompt.ask("[green]Enter words for the wordlist (separate with commas)[/green]")
    sayilar = Prompt.ask("[green]Enter the range of numbers (e.g., 1-100)[/green]")
    ozel_raw = Prompt.ask("[green]Enter any special characters to include (e.g., !@#)[/green]").strip()
    if ozel_raw == "":
        ozel = []
    else:
        parts = ozel_raw.split()
        if len(parts) == 1 and ' ' not in ozel_raw and len(ozel_raw) > 1:
            ozel = list(ozel_raw)
        else:
            ozel = parts

    try:
        min_uzunluk = int(Prompt.ask("[green]Enter minimum password length[/green]"))
        max_uzunluk = int(Prompt.ask("[green]Enter maximum password length[/green]"))
    except ValueError:
        console.print("[bold red]Length values must be numbers![/bold red]")
        sys.exit(1)

    cevap = Prompt.ask("[green]Should all case variants be generated for the tokens? (Y/N)[/green]", default="N").strip().lower()
    case_expand = cevap.startswith('y')

    dosya_yolu = Prompt.ask("[green]Enter the file path to save the wordlist (e.g., C:/path/to/wordlist.txt)[/green]").strip()
    if not dosya_yolu:
        console.print("[bold red]Please provide a valid file path.[/bold red]")
        sys.exit(1)

    original_tokens = [t for t in (kelimeler.split(',') + sayilar.split(',') + ozel) if t != ""]

    if not original_tokens:
        console.print("[bold red]Please enter at least one token (word/number/special character).[/bold red]")
        sys.exit(1)

    expanded_token_list = []
    expansion_info = []
    if case_expand:
        for t in original_tokens:
            variants = case_variants(t)
            expanded_token_list.extend(variants)
            expansion_info.append((t, len(variants)))
    else:
        expanded_token_list = list(original_tokens)
        for t in original_tokens:
            expansion_info.append((t, 1))

    # Benzersizleştir token pool'u (sıra korunur)
    seen_tokens = set()
    tokenler = []
    for t in expanded_token_list:
        if t not in seen_tokens:
            seen_tokens.add(t)
            tokenler.append(t)

    console.print(f"Total unique token pool size: {len(tokenler)}")
    if case_expand:
        console.print(f"Note: MAX_VARIANTS_PER_TOKEN = {MAX_VARIANTS_PER_TOKEN} (fallback applied if exceeded).")
    console.print("[bold cyan]Generating password combinations... Please wait![/bold cyan]")

    min_token_len = min(len(t) for t in tokenler)
    if min_token_len == 0:
        console.print("[bold red]Error: One of the tokens has zero length.[/bold red]")
        sys.exit(1)

    # Tahmini toplam "dizilim" sayısını hesapla (sıralı kombinasyon sayısı)
    token_lengths = [len(t) for t in tokenler]
    total_sequences = count_sequence_combinations(token_lengths, min_uzunluk, max_uzunluk)
    if total_sequences == 0:
        console.print("[bold red]No combinations can be generated with the given min/max length range.[/bold red]")
        sys.exit(1)

    console.print(f"Estimated total sequence count (ordered combinations): {total_sequences:,}")

    seen = set()
    written = 0
    attempted = 0
    last_print_time = time.time()
    writes_since_last = 0

    # DFS ile üretim
    def dfs(curr_str):
        nonlocal attempted, written, last_print_time, writes_since_last
        curr_len = len(curr_str)
        if min_uzunluk <= curr_len <= max_uzunluk:
            attempted += 1
            if curr_str not in seen and curr_str != "":
                f.write(curr_str + '\n')
                f.flush()
                seen.add(curr_str)
                written += 1
                writes_since_last += 1
        if curr_len >= max_uzunluk:
            return
        for t in tokenler:
            new_len = curr_len + len(t)
            if new_len > max_uzunluk:
                continue
            dfs(curr_str + t)
            now = time.time()
            if writes_since_last >= PROGRESS_PRINT_LINES or (now - last_print_time) >= PROGRESS_PRINT_INTERVAL:
                try:
                    bytes_written = f.tell()
                except Exception:
                    try:
                        bytes_written = os.path.getsize(dosya_yolu)
                    except Exception:
                        bytes_written = 0
                percent = (attempted / total_sequences) * 100 if total_sequences > 0 else 100.0
                console.print(f"\rWritten: {written:,} lines | File: {format_mb(bytes_written)} | Completed: {percent:.2f}% ", end='', flush=True)
                last_print_time = now
                writes_since_last = 0

    # Dosyaya yazma akışı
    try:
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            dfs("")
            console.print(f"\nWordlist successfully saved to {dosya_yolu}")
            final_size = os.path.getsize(dosya_yolu)
            console.print(f"Total lines (unique): {written:,}")
            console.print(f"File size: {format_mb(final_size)}")
    except KeyboardInterrupt:
        console.print("\nProcess interrupted by the user (KeyboardInterrupt). Temporary results may be in the file.")
        sys.exit(1)

if __name__ == '__main__':
    main()
