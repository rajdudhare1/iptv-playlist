import re
import urllib.request

INDEX_URL = "https://iptv-org.github.io/iptv/index.m3u"
MARATHI_URL = "https://iptv-org.github.io/iptv/languages/mar.m3u"

# Exact channel order for buttons 1, 2, 3, 4... (case-insensitive substring match)
PINNED_MARATHI = [
    "Zee Marathi",
    "Colors Marathi",
    "ABP Majha",
    "TV9 Marathi",
    "Zee 24 Taas",
    "Saam TV",
]

def fetch_entries(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="ignore")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    entries = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF:"):
            extinf = lines[i]
            stream_url = ""
            j = i + 1
            while j < len(lines) and not lines[j].startswith("#EXTINF:"):
                if not lines[j].startswith("#"):
                    stream_url = lines[j]
                    break
                j += 1
            if stream_url:
                name = extinf.split(",")[-1].strip()
                entries.append((extinf, stream_url, name))
            i = j
        else:
            i += 1
    return entries

def set_chno_and_group(extinf, chno, group=None):
    cleaned = re.sub(r'\s*tvg-chno="[^"]*"', "", extinf)
    if group:
        if 'group-title="' in cleaned:
            cleaned = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', cleaned)
        else:
            cleaned = cleaned.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{group}"', 1)
    return cleaned.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-chno="{chno}"', 1)

def main():
    marathi_entries = fetch_entries(MARATHI_URL)
    global_entries = fetch_entries(INDEX_URL)

    output = ["#EXTM3U"]
    used_urls = set()
    chno = 1

    # 1. Pin favorite Marathi channels at 1, 2, 3, 4...
    for target in PINNED_MARATHI:
        for extinf, url, name in marathi_entries:
            if target.lower() in name.lower() and url not in used_urls:
                output.append(set_chno_and_group(extinf, chno, "Marathi"))
                output.append(url)
                used_urls.add(url)
                chno += 1
                break

    # 2. Add remaining Marathi channels right after pinned ones
    for extinf, url, name in marathi_entries:
        if url not in used_urls:
            output.append(set_chno_and_group(extinf, chno, "Marathi"))
            output.append(url)
            used_urls.add(url)
            chno += 1

    # 3. Start global index.m3u channels at 101 (or next clean hundred) so numbers never collide
    global_chno = max(101, ((chno // 100) + 1) * 100 + 1)
    for extinf, url, name in global_entries:
        if url not in used_urls:
            output.append(set_chno_and_group(extinf, global_chno))
            output.append(url)
            used_urls.add(url)
            global_chno += 1

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output) + "\n")

if __name__ == "__main__":
    main()
