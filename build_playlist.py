import re
import urllib.request

INDEX_URL = "https://iptv-org.github.io/iptv/index.m3u"
MARATHI_URL = "https://iptv-org.github.io/iptv/languages/mar.m3u"
HINDI_URL = "https://iptv-org.github.io/iptv/languages/hin.m3u"
EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_IN1.xml.gz"

# Marathi channels start at 1, 2, 3... (case-insensitive substring match)
PINNED_MARATHI = [
    "Zee Marathi",
    "Colors Marathi",
    "ABP Majha",
    "TV9 Marathi",
    "Zee 24 Taas",
    "Saam TV",
]

# Hindi channels start at 101, 102, 103... (case-insensitive substring match)
PINNED_HINDI = [
    "Star Plus",
    "Zee TV",
    "Colors",
    "Sony Entertainment Television",
    "Aaj Tak",
    "ABP News",
    "NDTV India",
    "India TV",
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

def format_extinf(extinf, chno, group=None):
    # Remove old channel numbers and strip @SD/@HD suffixes from tvg-id so they match XMLTV IDs
    cleaned = re.sub(r'\s*tvg-chno="[^"]*"', "", extinf)
    cleaned = re.sub(r'(tvg-id="[^"@]+)@[^"]*"', r'\1"', cleaned)
    if group:
        if 'group-title="' in cleaned:
            cleaned = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', cleaned)
        else:
            cleaned = cleaned.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{group}"', 1)
    return cleaned.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-chno="{chno}"', 1)

def add_language_block(entries, pinned_list, start_chno, group_name, output, used_urls):
    chno = start_chno
    # 1. Add pinned channels in exact priority order
    for target in pinned_list:
        for extinf, url, name in entries:
            if target.lower() in name.lower() and url not in used_urls:
                output.append(format_extinf(extinf, chno, group_name))
                output.append(url)
                used_urls.add(url)
                chno += 1
                break
    # 2. Add remaining channels in that language
    for extinf, url, name in entries:
        if url not in used_urls:
            output.append(format_extinf(extinf, chno, group_name))
            output.append(url)
            used_urls.add(url)
            chno += 1
    return chno

def main():
    marathi_entries = fetch_entries(MARATHI_URL)
    hindi_entries = fetch_entries(HINDI_URL)
    global_entries = fetch_entries(INDEX_URL)

    output = [f'#EXTM3U x-tvg-url="{EPG_URL}"']
    used_urls = set()

    # Block 1: Marathi channels starting at 1
    next_chno = add_language_block(
        marathi_entries, PINNED_MARATHI, 1, "Marathi", output, used_urls
    )

    # Block 2: Hindi channels starting at 101
    hindi_start = max(101, ((next_chno // 100) + 1) * 100 + 1)
    next_chno = add_language_block(
        hindi_entries, PINNED_HINDI, hindi_start, "Hindi", output, used_urls
    )

    # Block 3: Global index.m3u channels starting at 501
    global_start = max(501, ((next_chno // 100) + 1) * 100 + 1)
    for extinf, url, name in global_entries:
        if url not in used_urls:
            output.append(format_extinf(extinf, global_start))
            output.append(url)
            used_urls.add(url)
            global_start += 1

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output) + "\n")

if __name__ == "__main__":
    main()
