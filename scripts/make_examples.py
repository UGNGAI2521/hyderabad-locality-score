"""Example listings for the preview. Every record is marked example=True and shown as 'Example' on the site.
Prices are illustrative placeholders, not market data."""
import json, math, random
random.seed(7)
loc = {d["name"]: d for d in json.load(open("data/localities.json"))}
#  mode, type, locality, title, bhk, baths, area, unit, price(INR; rent = per month), furnishing, status, extras
ROWS = [
 ("buy", "flat", "Gachibowli", "3 BHK flat in a gated community", 3, 3, 1850, "sqft", 21500000, "Semi-furnished", "Ready to move", ["Clubhouse", "Covered parking", "East facing"]),
 ("rent", "flat", "Gachibowli", "2 BHK flat near the stadium", 2, 2, 1250, "sqft", 42000, "Fully furnished", "Ready to move", ["Gym", "Power backup", "Pets allowed"]),
 ("buy", "flat", "Madhapur", "2 BHK flat close to Mindspace", 2, 2, 1180, "sqft", 13200000, "Unfurnished", "Ready to move", ["Lift", "Security", "Near metro"]),
 ("rent", "office", "Madhapur", "Plug-and-play office, 40 seats", 0, 2, 3200, "sqft", 320000, "Fully furnished", "Ready to move", ["Meeting rooms", "Cafeteria", "24x7 access"]),
 ("buy", "flat", "Kondapur", "3 BHK flat with lake view", 3, 3, 1720, "sqft", 17800000, "Semi-furnished", "Ready to move", ["Swimming pool", "Kids' play area", "Corner unit"]),
 ("rent", "house", "Kondapur", "Independent house, 2 floors", 4, 4, 2600, "sqft", 85000, "Semi-furnished", "Ready to move", ["Terrace", "Car parking for 2", "Borewell"]),
 ("rent", "office", "HITEC City", "Grade A office floor", 0, 4, 12000, "sqft", 1080000, "Bare shell", "Ready to move", ["Power backup", "Visitor parking", "Near metro"]),
 ("buy", "shop", "HITEC City", "Ground-floor retail shop", 0, 1, 650, "sqft", 18500000, "Unfurnished", "Ready to move", ["Main road frontage", "High footfall"]),
 ("rent", "flat", "HITEC City", "1 BHK studio for working professionals", 1, 1, 680, "sqft", 26000, "Fully furnished", "Ready to move", ["Walk to offices", "Housekeeping"]),
 ("buy", "flat", "Financial District", "4 BHK sky apartment", 4, 5, 3400, "sqft", 46000000, "Semi-furnished", "Under construction", ["High floor", "Private lift lobby", "Clubhouse"]),
 ("rent", "office", "Financial District", "Co-working cabin, 8 seats", 0, 1, 450, "sqft", 72000, "Fully furnished", "Ready to move", ["Shared lounge", "Meeting room credits"]),
 ("buy", "flat", "Nanakramguda", "3 BHK flat in a new tower", 3, 3, 2050, "sqft", 25500000, "Unfurnished", "Under construction", ["Gym", "Pool", "EV charging"]),
 ("buy", "flat", "Manikonda", "2 BHK flat near the lake", 2, 2, 1150, "sqft", 9400000, "Semi-furnished", "Ready to move", ["Lift", "Power backup"]),
 ("rent", "flat", "Manikonda", "3 BHK flat for families", 3, 3, 1600, "sqft", 38000, "Semi-furnished", "Ready to move", ["Near schools", "Covered parking"]),
 ("buy", "plot", "Narsingi", "East-facing residential plot", 0, 0, 300, "sqyd", 31500000, "", "Ready to register", ["Gated layout", "Clear title documents to verify"]),
 ("buy", "villa", "Narsingi", "4 BHK villa in a gated layout", 4, 5, 4200, "sqft", 52000000, "Semi-furnished", "Ready to move", ["Private garden", "Home theatre room", "Clubhouse"]),
 ("buy", "plot", "Kokapet", "Corner plot near the ORR", 0, 0, 400, "sqyd", 64000000, "", "Ready to register", ["Corner plot", "40 ft road"]),
 ("buy", "villa", "Kokapet", "5 BHK luxury villa", 5, 6, 6200, "sqft", 98000000, "Fully furnished", "Ready to move", ["Private pool", "Smart home", "Staff quarters"]),
 ("rent", "flat", "Kokapet", "3 BHK flat in a high-rise", 3, 3, 2100, "sqft", 62000, "Semi-furnished", "Ready to move", ["Skyline view", "Clubhouse"]),
 ("buy", "flat", "Raidurg", "2 BHK flat near Durgam Cheruvu", 2, 2, 1300, "sqft", 15600000, "Semi-furnished", "Ready to move", ["Walk to the lake", "Near metro"]),
 ("rent", "shop", "Raidurg", "Café space near the cable bridge", 0, 1, 900, "sqft", 140000, "Unfurnished", "Ready to move", ["Corner unit", "Outdoor seating"]),
 ("buy", "flat", "Miyapur", "2 BHK flat beside the metro", 2, 2, 1100, "sqft", 7600000, "Unfurnished", "Ready to move", ["Near metro", "Lift"]),
 ("rent", "flat", "Miyapur", "2 BHK flat in a gated community", 2, 2, 1200, "sqft", 24000, "Semi-furnished", "Ready to move", ["Park", "Security"]),
 ("buy", "house", "Miyapur", "Independent house, G+1", 3, 3, 2200, "sqft", 16500000, "Unfurnished", "Ready to move", ["Terrace", "Car parking"]),
 ("buy", "plot", "Nallagandla", "Residential plot in an approved layout", 0, 0, 220, "sqyd", 15400000, "", "Ready to register", ["Gated layout", "Underground drainage"]),
 ("rent", "flat", "Nallagandla", "3 BHK flat near the lake", 3, 3, 1680, "sqft", 40000, "Semi-furnished", "Ready to move", ["Swimming pool", "Near schools"]),
]
out = []
for i, (mode, typ, l, title, bhk, baths, area, unit, price, furn, status, extras) in enumerate(ROWS, 1):
    c = loc[l]; r = random.uniform(0.002, 0.007); a = random.uniform(0, 2 * math.pi)
    out.append(dict(id=f"ex{i:02d}", example=True, mode=mode, type=typ, locality=l, title=title, bhk=bhk, baths=baths,
        area=area, unit=unit, price=price, furnishing=furn, status=status, features=extras,
        lat=round(c["lat"] + r * math.sin(a), 5), lon=round(c["lon"] + r * math.cos(a), 5)))
assert all(o["locality"] in loc for o in out) and len({o["id"] for o in out}) == len(out)
json.dump(out, open("data/listings.json", "w"), indent=0)
print(len(out), "example listings;", sorted({o["type"] for o in out}))
