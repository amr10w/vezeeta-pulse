from scrapling.fetchers import Fetcher
import json
import time
import csv

BASE_URL = "https://www.vezeeta.com"
BASE_URL_PAGE = "https://www.vezeeta.com/en/doctor/all-specialities/egypt"

all_doctors = []

CSV_FILE = "vezeeta_doctors3.csv"
CSV_HEADERS = [
    "ID", "page", "name", "description", "specialty", "address",
    "fee", "rating", "reviews_count", "waiting_time",
    "profile_url", "image_url"
]

# ╔════════════════════════════════════════════════════════════════════╗
# ║  CONFIGURATION                                                    ║
# ╚════════════════════════════════════════════════════════════════════╝
MAX_EMPTY_PAGES = 15  # <-- Stop only after 5 consecutive empty pages

# Create the CSV file and write headers upfront
with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
    writer.writeheader()

iter = 1
empty_streak = 0  # Track consecutive empty pages

for page_num in range(1, 1733):
    if page_num == 1:
        url = BASE_URL_PAGE
    else:
        url = f"{BASE_URL_PAGE}?page={page_num}"

    try:
        page = Fetcher.get(url)
        cards = page.css('div[id^="doctor-card__"]')
        print(f"Found {len(cards)} doctor cards on page {page_num}")

        if not cards:
            empty_streak += 1
            print(f"⚠️  No cards on page {page_num} "
                  f"(empty streak: {empty_streak}/{MAX_EMPTY_PAGES})")

            if empty_streak >= MAX_EMPTY_PAGES:
                print(f"\n🛑  {MAX_EMPTY_PAGES} consecutive empty pages — stopping.")
                break

            time.sleep(1.5)
            continue  # <-- Skip this page, try the next one

        # Reset streak when we find doctors
        empty_streak = 0

        page_doctors = []

        for card in cards:
            json_block = card.css('script[type="application/ld+json"]::text').get()
            if not json_block:
                continue

            data = json.loads(json_block)

            doctor_name = data.get("name")
            description = data.get("description")
            specialty = data.get("medicalSpecialty")
            fee = data.get("priceRange")
            image_url = data.get("image")
            profile_url = BASE_URL + data["url"] if data.get("url") else None
            address = data.get("address", {}).get("streetAddress")

            rating_el = card.css('[data-testid*="star-rating__rating-value"]')
            rating = None
            if rating_el:
                testid = rating_el[0].attrib.get("data-testid", "")
                rating = testid.split("--")[-1]

            reviews_count = card.css('[data-testid="ratings-count"]::text').get()
            waiting_time = card.css('[data-testid*="_waiting-time"]::text').get()

            doctor = {
                "ID": iter,
                "page": page_num,
                "name": doctor_name,
                "description": description,
                "specialty": specialty,
                "address": address,
                "fee": fee,
                "rating": rating,
                "reviews_count": reviews_count,
                "waiting_time": waiting_time,
                "profile_url": profile_url,
                "image_url": image_url,
            }
            iter += 1
            all_doctors.append(doctor)
            page_doctors.append(doctor)

        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            for doc in page_doctors:
                writer.writerow(doc)

        print(f"✅ Saved {len(page_doctors)} doctors from page {page_num} to {CSV_FILE}")

    except Exception as e:
        empty_streak += 1
        print(f"❌ Error on page {page_num}: {e} "
              f"(empty streak: {empty_streak}/{MAX_EMPTY_PAGES})")

        if empty_streak >= MAX_EMPTY_PAGES:
            print(f"\n🛑  {MAX_EMPTY_PAGES} consecutive failures — stopping.")
            break

        continue

    time.sleep(1.5)

print(f"\n{'=' * 50}")
print(f"✅ Done! Scraped {len(all_doctors)} doctors across {page_num} pages.")
print(f"📄 All data saved to: {CSV_FILE}")
print(f"{'=' * 50}")