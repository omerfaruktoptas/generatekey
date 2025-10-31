#!/usr/bin/env python3
# wordlist_blocks_case_prompt_with_progress.py
# Blok bazlı wordlist üretici. Kullanıcıya büyük/küçük harf varyantı isteyip istemediğini sorar.
# Üretim sırasında dosya boyutunu (MB) ve tamamlanma yüzdesini (tahmini) gösterir.
# NOT: Tahmini tamamlanma oranı token kombinasyonlarına (sıralı dizilim sayısına) dayanmaktadır.
#      Program benzersiz sonuçlar yazarken bazı kombinasyonlar aynı sonuca yol açarsa
#      yazılan satır sayısı bu tahminden farklı olabilir. Daha doğru ama bellek-aç gözlü bir
#      yöntem isterseniz tüm benzersiz sonuçları belleğe alıp sayıp sonra yazdırabiliriz.

import sys
import itertools
import os
import time

MAX_VARIANTS_PER_TOKEN = 1024  # Güvenlik limiti; gerekirse artırılabilir
PROGRESS_PRINT_INTERVAL = 0.5  # saniye, ilerleme güncellemeleri arasındaki minimum süre
PROGRESS_PRINT_LINES = 1000    # veya bu kadar satır yazıldığında zorla güncelle

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
    kelimeler = read_tokens("Kelime listesi girin (aralarına boşluk koyun): ")
    sayilar = read_tokens("Sayı listesi girin (aralarına boşluk koyun): ")
    ozel_raw = input("Özel karakterler girin (aralarına boşluk koyun, boş bırakabilirsiniz): ").strip()
    if ozel_raw == "":
        ozel = []
    else:
        parts = ozel_raw.split()
        if len(parts) == 1 and ' ' not in ozel_raw and len(ozel_raw) > 1:
            ozel = list(ozel_raw)
        else:
            ozel = parts

    try:
        min_uzunluk = int(input("Şifrenin minimum uzunluğunu girin: "))
        max_uzunluk = int(input("Şifrenin maksimum uzunluğunu girin: "))
    except ValueError:
        print("Uzunluklar sayı olmalı.")
        sys.exit(1)

    cevap = input("Bloklar için tüm büyük/küçük harf varyantları üretilsin mi? (E/h) [h]: ").strip().lower()
    case_expand = cevap.startswith('e')

    dosya_yolu = input("Dosya kaydetme yolu girin (örn. C:/dosya_yolu/wordlist.txt): ").strip()
    if not dosya_yolu:
        print("Geçerli bir dosya yolu girin.")
        sys.exit(1)

    original_tokens = [t for t in (kelimeler + sayilar + ozel) if t != ""]

    if not original_tokens:
        print("En az bir token (kelime/sayı/özel) girin.")
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

    print("Token genişletme bilgisi (orijinal -> varyant sayısı):")
    for orig, count in expansion_info:
        print(f"  '{orig}' -> {count} varyant")

    print(f"Toplam token havuzu büyüklüğü (benzersiz varyantlarla): {len(tokenler)}")
    if case_expand:
        print(f"Not: MAX_VARIANTS_PER_TOKEN = {MAX_VARIANTS_PER_TOKEN} (aşılırsa fallback uygulanır).")
    print("Üretim başlıyor... (büyük çıktı olasılığına dikkat)")

    min_token_len = min(len(t) for t in tokenler)
    if min_token_len == 0:
        print("Hata: Tokenlerden en az biri boş uzunlukta.")
        sys.exit(1)

    # Tahmini toplam "dizilim" sayısını hesapla (sıralı kombinasyon sayısı)
    token_lengths = [len(t) for t in tokenler]
    total_sequences = count_sequence_combinations(token_lengths, min_uzunluk, max_uzunluk)
    if total_sequences == 0:
        print("Oluşturulabilecek hiçbir kombinasyon yok (min/max uzunluk aralığıyla uyuşmuyor).")
        sys.exit(1)

    print(f"Tahmini dizilim sayısı (sıralı kombinasyonlar): {total_sequences:,} (bu benzersiz sonuç sayısı olmayabilir).")

    seen = set()
    written = 0
    attempted = 0
    last_print_time = time.time()
    writes_since_last = 0

    # DFS ile üretim, budama ile
    def dfs(curr_str):
        nonlocal attempted, written, last_print_time, writes_since_last
        curr_len = len(curr_str)
        # Eğer geçerli uzunluktaysa "deneme" sayısını bir artır ve yaz (benzersizse)
        if min_uzunluk <= curr_len <= max_uzunluk:
            attempted += 1
            if curr_str not in seen and curr_str != "":
                f.write(curr_str + '\n')
                # flush az çok anlık f.tell() doğru vermesi için
                f.flush()
                seen.add(curr_str)
                written += 1
                writes_since_last += 1
        # Erken dön
        if curr_len >= max_uzunluk:
            return
        for t in tokenler:
            new_len = curr_len + len(t)
            if new_len > max_uzunluk:
                continue
            dfs(curr_str + t)
            # Agar çok büyük derinlikler varsa arada yazma güncellemesi yapmak için kontrol
            now = time.time()
            if writes_since_last >= PROGRESS_PRINT_LINES or (now - last_print_time) >= PROGRESS_PRINT_INTERVAL:
                # Dosya boyutunu al (f.tell() çağrıldıktan sonra flush edildiği sürece yeterince doğru)
                try:
                    bytes_written = f.tell()
                except Exception:
                    # güvenlik için os.path.getsize kullan (dosya henüz kaydedilmemişse hata olabilir)
                    try:
                        bytes_written = os.path.getsize(dosya_yolu)
                    except Exception:
                        bytes_written = 0
                percent = (attempted / total_sequences) * 100 if total_sequences > 0 else 100.0
                print(f"\rYazılan: {written:,} satır | Dosya: {format_mb(bytes_written)} | Tamamlandı (tahmini): {percent:.2f}% ", end='', flush=True)
                last_print_time = now
                writes_since_last = 0

    # Dosyaya yazma akışı
    try:
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            dfs("")
            # Son durumu yazdır
            try:
                bytes_written = f.tell()
            except Exception:
                try:
                    bytes_written = os.path.getsize(dosya_yolu)
                except Exception:
                    bytes_written = 0
    except KeyboardInterrupt:
        print("\nİşlem kullanıcı tarafından durduruldu (KeyboardInterrupt). Geçici sonuçlar dosyada olabilir.")
        # Son dosya boyutunu dene
        try:
            bytes_written = os.path.getsize(dosya_yolu)
        except Exception:
            bytes_written = 0
        percent = (attempted / total_sequences) * 100 if total_sequences > 0 else 100.0
        print(f"Yazılan: {written:,} satır | Dosya: {format_mb(bytes_written)} | Tamamlandı (tahmini): {percent:.2f}%")
        sys.exit(1)

    # final print newline to end the \r line
    percent = (attempted / total_sequences) * 100 if total_sequences > 0 else 100.0
    print()  # newline after carriage return line
    print(f"Wordlist başarıyla {dosya_yolu} yoluna kaydedildi.")
    try:
        final_size = os.path.getsize(dosya_yolu)
    except Exception:
        final_size = 0
    print(f"Toplam satır (benzersiz): {written:,}")
    print(f"Dosya boyutu: {format_mb(final_size)}")
    print(f"Tahmini tamamlanma (% dizilim): {percent:.2f}% (tahmin sıralı kombinasyonlara dayanır; benzersiz satırlar daha az olabilir.)")

    if written == 0:
        print("Hiç sonuç üretilmedi. Muhtemel sebep: tokenlerin toplam uzunlukları min_uzunluk'un altına düşüyor ve özel karakterler boş olduğundan padding yapılamıyor.")

if __name__ == '__main__':
    main()