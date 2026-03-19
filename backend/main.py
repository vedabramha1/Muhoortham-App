Let's simplify the backend code:
Go to GitHub: github.com/vedabramha1/Muhoortham-App
Go to branch conflict_190326_0145
Go to backend/main.py
Click pencil icon to edit
DELETE ALL and paste this simplified code:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import math
from datetime import datetime
from typing import Optional, List
import os

app = FastAPI(title="Muhoortham API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 27 Nakshatras
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

TARABALAM_NAMES = {1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 5: "Pratyak", 6: "Sadhana", 7: "Naidhana", 8: "Mitra", 9: "Ati Mitra"}
TARABALAM_FAVORABLE = [2, 4, 6, 8, 9]
CHANDRABALAM_FAVORABLE = [1, 3, 6, 7, 10, 11]

RAHUKALAM = {"Sunday": (8,9), "Monday": (2,3), "Tuesday": (7,8), "Wednesday": (5,6), "Thursday": (6,7), "Friday": (4,5), "Saturday": (3,4)}

def get_nakshatra_index(name):
    try:
        return NAKSHATRAS.index(name) + 1
    except:
        return 1

def calculate_tarabalam(birth_idx, day_idx):
    distance = (day_idx - birth_idx + 27) % 27 + 1
    tara_num = distance % 9 or 9
    return tara_num, TARABALAM_NAMES.get(tara_num, "Unknown"), tara_num in TARABALAM_FAVORABLE

def calculate_chandrabalam(birth_idx, rashi_idx):
    birth_rashi = ((birth_idx - 1) * 4 // 9) + 1
    count = (rashi_idx - birth_rashi + 12) % 12 + 1
    return count, count in CHANDRABALAM_FAVORABLE

def get_tithi_name(day):
    tithis = ["Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"]
    return tithis[(day - 1) % 15]

def is_bad_tithi(day):
    bad = [1, 4, 8, 9, 12, 14, 15]
    tithi_in_paksha = ((day - 1) % 15) + 1
    return tithi_in_paksha in bad

@app.get("/")
def root():
    return {"message": "Sri Lalitha Krishna Shastry Muhoortham API", "status": "running"}

@app.get("/api/nakshatras")
def get_nakshatras():
    return {"nakshatras": NAKSHATRAS}

@app.post("/api/check-muhurat")
def check_muhurat(date: str, birth_nakshatra: str, birth_nakshatra_2: Optional[str] = None, timezone: str = "IST"):
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        weekday = WEEKDAYS[dt.weekday()]
        day_of_month = dt.day
        
        birth_idx = get_nakshatra_index(birth_nakshatra)
        day_nakshatra_idx = (day_of_month % 27) + 1
        day_rashi_idx = ((day_of_month - 1) % 12) + 1
        
        # Calculate factors
        tara_num, tara_name, tara_good = calculate_tarabalam(birth_idx, day_nakshatra_idx)
        chandra_pos, chandra_good = calculate_chandrabalam(birth_idx, day_rashi_idx)
        
        tithi_idx = (day_of_month % 30) + 1
        tithi_name = get_tithi_name(tithi_idx)
        tithi_bad = is_bad_tithi(tithi_idx)
        paksha = "Shukla Paksha" if tithi_idx <= 15 else "Krishna Paksha"
        
        is_tuesday = weekday == "Tuesday"
        
        # Panchaka calculation
        vara = dt.weekday() + 1
        panchaka_sum = tithi_idx + vara + day_nakshatra_idx + day_rashi_idx
        panchaka_rem = panchaka_sum % 9
        panchaka_good = panchaka_rem in [0, 3, 5, 7]
        panchaka_names = {0: "Panchaka Rahitam", 1: "Mrityu", 2: "Agni", 3: "Panchaka Rahitam", 4: "Raja", 5: "Panchaka Rahitam", 6: "Chora", 7: "Panchaka Rahitam", 8: "Roga"}
        panchaka_name = panchaka_names.get(panchaka_rem, "Unknown")
        
        # Rahukalam
        rahu_seg = RAHUKALAM.get(weekday, (8,9))
        rahu_start = f"{6 + rahu_seg[0]}:00 AM" if rahu_seg[0] < 6 else f"{rahu_seg[0]}:00 AM"
        rahu_end = f"{6 + rahu_seg[1]}:00 AM" if rahu_seg[1] < 6 else f"{rahu_seg[1]}:00 AM"
        
        factors = [
            {"name": "Tarabalam", "value": f"{tara_name} ({tara_num})", "is_favorable": tara_good, "description": f"Birth star: {birth_nakshatra}"},
            {"name": "Chandrabalam", "value": f"Position {chandra_pos}", "is_favorable": chandra_good, "description": "Moon strength"},
            {"name": "Panchakarahitam", "value": f"{panchaka_name} (rem {panchaka_rem})", "is_favorable": panchaka_good, "description": f"Tithi({tithi_idx})+Vara({vara})+Nakshatra({day_nakshatra_idx})+Lagna({day_rashi_idx})={panchaka_sum}"},
            {"name": "Tithi", "value": f"{tithi_name} ({paksha})", "is_favorable": not tithi_bad, "description": "Avoid Prathama, Chaturthi, Ashtami, Navami, Dwadashi, Chaturdashi, Amavasya"},
            {"name": "Weekday", "value": weekday, "is_favorable": not is_tuesday, "description": "Avoid Tuesday"},
        ]
        
        # Second person
        factors_2 = None
        if birth_nakshatra_2:
            birth_idx_2 = get_nakshatra_index(birth_nakshatra_2)
            tara_num_2, tara_name_2, tara_good_2 = calculate_tarabalam(birth_idx_2, day_nakshatra_idx)
            chandra_pos_2, chandra_good_2 = calculate_chandrabalam(birth_idx_2, day_rashi_idx)
            factors_2 = [
                {"name": "Tarabalam", "value": f"{tara_name_2} ({tara_num_2})", "is_favorable": tara_good_2, "description": f"Birth star: {birth_nakshatra_2}"},
                {"name": "Chandrabalam", "value": f"Position {chandra_pos_2}", "is_favorable": chandra_good_2, "description": "Moon strength"},
            ]
        
        favorable_count = sum(1 for f in factors if f["is_favorable"])
        is_auspicious = favorable_count >= 4 and not is_tuesday and not tithi_bad
        
        if birth_nakshatra_2 and factors_2:
            is_auspicious = is_auspicious and factors_2[0]["is_favorable"] and factors_2[1]["is_favorable"]
        
        verdict = "AUSPICIOUS - Good day" if is_auspicious else "NOT AUSPICIOUS"
        
        return {
            "date": date,
            "weekday": weekday,
            "birth_nakshatra": birth_nakshatra,
            "birth_nakshatra_2": birth_nakshatra_2,
            "timezone": timezone,
            "overall_verdict": verdict,
            "is_auspicious": is_auspicious,
            "factors": factors,
            "factors_person_2": factors_2,
            "inauspicious_timings": {
                "rahukalam": {"start": rahu_start, "end": rahu_end},
                "yamagandam": {"start": "10:30 AM", "end": "12:00 PM"},
                "varjyam": {"start": "2:00 PM", "end": "3:30 PM"},
                "durmuhoortham": [{"start": "12:30 PM", "end": "1:30 PM"}]
            },
            "panchang_details": {
                "tithi": f"{tithi_name} ({paksha})",
                "nakshatra": NAKSHATRAS[day_nakshatra_idx - 1],
                "rashi": ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"][day_rashi_idx - 1],
                "sunrise": "6:15 AM",
                "sunset": "6:30 PM"
            }
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
