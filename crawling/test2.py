from scrapling.fetchers import Fetcher
import json

BASE_URL = "https://www.vezeeta.com"
URL = "https://www.vezeeta.com/en/doctor/all-specialities/egypt"

print("Fetching page...")
page = Fetcher.get(URL)
cards = page.css('div[id^="doctor-card__"]')
print(f"Found {len(cards)} doctor cards\n")

for card in cards:

    # -------- JSON-LD extraction --------
    json_block = card.css('script[type="application/ld+json"]::text').get()
    if not json_block:
        continue

    data = json.loads(json_block)

    doctor_name  = data.get("name")
    description  = data.get("description")
    specialty    = data.get("medicalSpecialty")
    fee          = data.get("priceRange")
    image_url    = data.get("image")
    profile_url  = BASE_URL + data["url"] if data.get("url") else None
    address      = data.get("address", {}).get("streetAddress")

    # -------- HTML extraction --------

    rating_el = card.css('[data-testid*="star-rating__rating-value"]')
    rating = None
    if rating_el:
        # Access the first element directly by index
        testid = rating_el[0].attrib.get("data-testid", "")
        rating = testid.split("--")[-1]  # extracts "5"

    reviews_count = card.css('[data-testid="ratings-count"]::text').get()

    waiting_time  = card.css('[data-testid*="_waiting-time"]::text').get()

    # -------- Print results --------
    print(f"Doctor       : {doctor_name}")
    print(f"Title        : {description}")
    print(f"Specialty    : {specialty}")
    print(f"Address      : {address}")
    print(f"Fee          : {fee} EGP")
    print(f"Rating       : {rating}/5" if rating else "Rating       : N/A")
    print(f"Reviews      : {reviews_count}")
    print(f"Waiting Time : {waiting_time}")
    print(f"Profile URL  : {profile_url}")
    print(f"Image        : {image_url}")
    print("-" * 50)