Commit changes
Step 2: Update main.py
Go to backend/main.py → Edit:
DELETE ALL and paste this (fixed version):
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
import os

app = FastAPI(title="Muhoortham API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TARABALAM_NAMES = {1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 5: "Pratyak", 6: "Sadhana", 7: "Naidhana", 8: "Mitra", 9: "Ati Mitra"}
TARABALAM_FAVORABLE = [2, 4, 6, 8, 9]
CHANDRABALAM_FAVORABLE = [1, 3, 6, 7, 10, 11]

@app.get("/")
def root():
    return {"message": "Sri Lalitha Krishna Shastry Muhoortham API", "status": "running"}

@app.get("/api/nakshatras")
def get_nakshatras():
    return {"nakshatras": NAKSHATRAS}

@app.get("/api/check-muhurat")
def check_muhurat(date: str, birth_nakshatra: str, birth_nakshatra_2: Optional[str] = None, timezone: str = "IST"):
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        weekday = WEEKDAYS[dt.weekday()]
        day_of_month = dt.day
        
        birth_idx = NAKSHATRAS.index(birth_nakshatra) + 1 if birth_nakshatra in NAKSHATRAS else 1
        day_nakshatra_idx = (day_of_month % 27) + 1
        day_rashi_idx = ((day_of_month - 1) % 12) + 1
        
        distance = (day_nakshatra_idx - birth_idx + 27) % 27 + 1
        tara_num = distance % 9 if distance % 9 != 0 else 9
        tara_name = TARABALAM_NAMES.get(tara_num, "Unknown")
        tara_good = tara_num in TARABALAM_FAVORABLE
        
        birth_rashi = ((birth_idx - 1) * 4 // 9) + 1
        chandra_pos = (day_rashi_idx - birth_rashi + 12) % 12 + 1
        chandra_good = chandra_pos in CHANDRABALAM_FAVORABLE
        
        tithi_idx = (day_of_month % 30) + 1
        tithis = ["Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"]
        tithi_name = tithis[(tithi_idx - 1) % 15]
        paksha = "Shukla Paksha" if tithi_idx <= 15 else "Krishna Paksha"
        tithi_bad = ((tithi_idx - 1) % 15 + 1) in [1, 4, 8, 9, 12, 14, 15]
        
        is_tuesday = weekday == "Tuesday"
        
        vara = dt.weekday() + 1
        panchaka_sum = tithi_idx + vara + day_nakshatra_idx + day_rashi_idx
        panchaka_rem = panchaka_sum % 9
        panchaka_good = panchaka_rem in [0, 3, 5, 7]
        panchaka_names = {0: "Panchaka Rahitam", 1: "Mrityu", 2: "Agni", 3: "Panchaka Rahitam", 4: "Raja", 5: "Panchaka Rahitam", 6: "Chora", 7: "Panchaka Rahitam", 8: "Roga"}
        panchaka_name = panchaka_names.get(panchaka_rem, "Unknown")
        
        factors = [
            {"name": "Tarabalam", "value": tara_name + " (" + str(tara_num) + ")", "is_favorable": tara_good, "description": "Birth star: " + birth_nakshatra},
            {"name": "Chandrabalam", "value": "Position " + str(chandra_pos), "is_favorable": chandra_good, "description": "Moon strength"},
            {"name": "Panchakarahitam", "value": panchaka_name, "is_favorable": panchaka_good, "description": "Sum=" + str(panchaka_sum) + ", Rem=" + str(panchaka_rem)},
            {"name": "Tithi", "value": tithi_name + " (" + paksha + ")", "is_favorable": not tithi_bad, "description": "Lunar day"},
            {"name": "Weekday", "value": weekday, "is_favorable": not is_tuesday, "description": "Avoid Tuesday"},
        ]
        
        factors_2 = None
        if birth_nakshatra_2 and birth_nakshatra_2 in NAKSHATRAS:
            birth_idx_2 = NAKSHATRAS.index(birth_nakshatra_2) + 1
            distance_2 = (day_nakshatra_idx - birth_idx_2 + 27) % 27 + 1
            tara_num_2 = distance_2 % 9 if distance_2 % 9 != 0 else 9
            tara_name_2 = TARABALAM_NAMES.get(tara_num_2, "Unknown")
            tara_good_2 = tara_num_2 in TARABALAM_FAVORABLE
            birth_rashi_2 = ((birth_idx_2 - 1) * 4 // 9) + 1
            chandra_pos_2 = (day_rashi_idx - birth_rashi_2 + 12) % 12 + 1
            chandra_good_2 = chandra_pos_2 in CHANDRABALAM_FAVORABLE
            factors_2 = [
                {"name": "Tarabalam", "value": tara_name_2 + " (" + str(tara_num_2) + ")", "is_favorable": tara_good_2, "description": "Birth star: " + birth_nakshatra_2},
                {"name": "Chandrabalam", "value": "Position " + str(chandra_pos_2), "is_favorable": chandra_good_2, "description": "Moon strength"},
            ]
        
        favorable_count = sum(1 for f in factors if f["is_favorable"])
        is_auspicious = favorable_count >= 4 and not is_tuesday and not tithi_bad
        
        if factors_2:
            is_auspicious = is_auspicious and factors_2[0]["is_favorable"] and factors_2[1]["is_favorable"]
        
        verdict = "AUSPICIOUS - Good day" if is_auspicious else "NOT AUSPICIOUS"
        
        rashi_names = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
        
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
                "rahukalam": {"start": "7:30 AM", "end": "9:00 AM"},
                "yamagandam": {"start": "10:30 AM", "end": "12:00 PM"},
                "varjyam": {"start": "2:00 PM", "end": "3:30 PM"},
                "durmuhoortham": [{"start": "12:30 PM", "end": "1:30 PM"}]
            },
            "panchang_details": {
                "tithi": tithi_name + " (" + paksha + ")",
                "nakshatra": NAKSHATRAS[day_nakshatra_idx - 1],
                "rashi": rashi_names[day_rashi_idx - 1],
                "sunrise": "6:15 AM",
                "sunset": "6:30 PM"
            }
        }
    except Exception as e:
        return {"error": str(e), "date": date}
