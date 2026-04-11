import pandas as pd
import time
from scrapling.fetchers import Fetcher

# ╔════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION — Change these values to control the range        ║
# ╚════════════════════════════════════════════════════════════════════╝
FROM_ROW = 15001      # <-- Start from this row (1-based, inclusive)
TO_ROW   = 17121     # <-- End at this row   (1-based, inclusive)


def scrape_doctor_profile(fetcher, url):
    page = fetcher.get(url)

    about_doctor = "N/A"
    symptoms_services = []
    specialized_in = []

    title_spans = page.css('span[class*="CardWithIconInTitlestyle__Text"]')

    for title_span in title_spans:
        title_text = title_span.text.strip()

        title_div = title_span.parent
        card = title_div.parent

        content_divs = card.css(
            'div[class*="CardWithIconInTitlestyle__Content"]'
        )
        if not content_divs:
            continue

        content = content_divs[0]

        if "About The Doctor" in title_text:
            truncate = content.css('span[class*="TruncateTextstyle"]')
            if truncate:
                about_doctor = truncate[0].text.strip()

            if not about_doctor or about_doctor == "N/A":
                all_spans = content.css("span")
                for sp in all_spans:
                    txt = sp.text.strip()
                    if txt:
                        about_doctor = txt
                        break

            if not about_doctor or about_doctor == "N/A":
                about_doctor = content.text.strip() or "N/A"

        elif "Symptoms and Services" in title_text:
            service_links = content.css("a")
            symptoms_services = [
                a.text.strip() for a in service_links if a.text.strip()
            ]

    spec_spans = page.css('span[class*="SpecialtyText"]')
    for span in spec_spans:
        links = span.css("a")
        for link in links:
            txt = link.text.strip()
            if txt:
                specialized_in.append(txt)

    return {
        "about_doctor": about_doctor,
        "symptoms_text": ", ".join(symptoms_services) if symptoms_services else "N/A",
        "subspecialties_text": ", ".join(specialized_in) if specialized_in else "N/A",
    }


def main():
    input_file = "vezeeta_doctors3.csv"
    df = pd.read_csv(input_file)

    if "profile_url" not in df.columns:
        raise ValueError(
            f"'profile_url' column not found. "
            f"Available columns: {list(df.columns)}"
        )

    # ── Ensure the 3 columns exist (keep old values if already present) ──
    for col in ["about_doctor", "symptoms_text", "subspecialties_text"]:
        if col not in df.columns:
            df[col] = ""  # empty string, NOT "N/A"

    # ── Convert FROM/TO from 1-based to 0-based index ───────────────
    start_idx = FROM_ROW - 1  # inclusive
    end_idx   = TO_ROW        # exclusive for slicing, so TO_ROW is included

    # Clamp to valid range
    start_idx = max(0, start_idx)
    end_idx   = min(len(df), end_idx)

    total = end_idx - start_idx
    print(f"📋  Total rows in file: {len(df)}")
    print(f"🔧  Scraping rows {FROM_ROW} to {TO_ROW} ({total} doctor(s))\n")

    fetcher = Fetcher(auto_match=False)

    count = 0
    for idx in range(start_idx, end_idx):
        row = df.iloc[idx]
        url = str(row["profile_url"]).strip()
        count += 1

        if not url.startswith("http"):
            url = "https://www.vezeeta.com" + url

        print(f"[{count}/{total}]  Row #{idx + 1}  Scraping: {url}")

        try:
            info = scrape_doctor_profile(fetcher, url)

            df.at[idx, "about_doctor"]       = info["about_doctor"]
            df.at[idx, "symptoms_text"]      = info["symptoms_text"]
            df.at[idx, "subspecialties_text"] = info["subspecialties_text"]

        except Exception as exc:
            print(f"  ❌ Error: {exc}")

        time.sleep(0.3)

    # ── Save the FULL dataframe back (all rows preserved) ───────────
    df.to_csv(input_file, index=False, encoding="utf-8-sig")
    print(f"\n{'=' * 80}")
    print(f"✅  Done!  Updated rows {FROM_ROW}–{TO_ROW} → {input_file}")
    print(f"   Rows outside this range are UNTOUCHED.")
    print(f"   Columns: about_doctor, symptoms_text, subspecialties_text")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()