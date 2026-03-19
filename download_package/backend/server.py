from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import swisseph as swe
import pytz
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ PANCHANG CONSTANTS ============

# 27 Nakshatras with their names
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# 30 Tithis
TITHIS = [
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

# Weekdays
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Tarabalam - favorable remainders when counting from birth star to day star mod 9
TARABALAM_NAMES = {
    1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 
    5: "Pratyak", 6: "Sadhana", 7: "Naidhana", 8: "Mitra", 9: "Ati Mitra"
}
TARABALAM_FAVORABLE = [2, 4, 6, 8, 9]  # Sampat, Kshema, Sadhana, Mitra, Ati Mitra

# Chandrabalam - favorable rashi counts (1-indexed)
CHANDRABALAM_FAVORABLE = [1, 3, 6, 7, 10, 11]

# Bad Tithis to avoid (1-indexed): Prathama after Amavasya (1), Chaturthi (4), Ashtami (8), Navami (9), Dwadashi (12), Chaturdashi (14), Amavasya (30)
# Also Krishna Paksha equivalents
BAD_TITHIS_INDICES = [1, 4, 8, 9, 12, 14, 15, 16, 19, 23, 24, 27, 29, 30]  # Extended for both pakshas

# Varjyam start ghatikas from nakshatra beginning (1 ghatika = 24 minutes)
VARJYAM_GHATIKAS = {
    "Ashwini": 50, "Bharani": 4, "Krittika": 30, "Rohini": 40, "Mrigashira": 14,
    "Ardra": 21, "Punarvasu": 30, "Pushya": 20, "Ashlesha": 32, "Magha": 30,
    "Purva Phalguni": 20, "Uttara Phalguni": 1, "Hasta": 21, "Chitra": 20,
    "Swati": 14, "Vishakha": 14, "Anuradha": 10, "Jyeshtha": 14, "Mula": 20,
    "Purva Ashadha": 20, "Uttara Ashadha": 20, "Shravana": 10, "Dhanishta": 10,
    "Shatabhisha": 18, "Purva Bhadrapada": 16, "Uttara Bhadrapada": 30, "Revati": 30
}

# Rahukalam segments by weekday (1-indexed segment of 8 parts of day)
RAHUKALAM_SEGMENTS = {
    "Sunday": 8, "Monday": 2, "Tuesday": 7, "Wednesday": 5,
    "Thursday": 6, "Friday": 4, "Saturday": 3
}

# Yamagandam segments by weekday
YAMAGANDAM_SEGMENTS = {
    "Sunday": 5, "Monday": 4, "Tuesday": 3, "Wednesday": 2,
    "Thursday": 1, "Friday": 7, "Saturday": 6
}

# Durmuhoortham times (simplified - 2 periods per day based on weekday)
# These are approximate muhurta numbers from sunrise
DURMUHOORTHAM_MUHURTAS = {
    "Sunday": [(14, 15)],      
    "Monday": [(7, 8), (14, 15)],
    "Tuesday": [(4, 5), (14, 15)],
    "Wednesday": [(10, 11), (14, 15)],
    "Thursday": [(9, 10), (14, 15)],
    "Friday": [(6, 7), (14, 15)],
    "Saturday": [(1, 2), (14, 15)]
}

# Timezone configurations
TIMEZONE_CONFIG = {
    "IST": {"name": "Asia/Kolkata", "offset": 5.5, "lat": 13.0827, "lon": 80.2707},  # Chennai
    "EST": {"name": "America/New_York", "offset": -5, "lat": 40.7128, "lon": -74.0060},  # New York
    "PST": {"name": "America/Los_Angeles", "offset": -8, "lat": 34.0522, "lon": -118.2437},  # Los Angeles
    "CST": {"name": "America/Chicago", "offset": -6, "lat": 41.8781, "lon": -87.6298},  # Chicago
    "MDT": {"name": "America/Denver", "offset": -7, "lat": 39.7392, "lon": -104.9903}  # Denver
}

# ============ PYDANTIC MODELS ============

class MuhooratRequest(BaseModel):
    date: str  # Format: YYYY-MM-DD
    birth_nakshatra: str
    birth_nakshatra_2: Optional[str] = None  # Second person's birth star (optional)
    timezone: str = "IST"

class MuhooratFactor(BaseModel):
    name: str
    value: str
    is_favorable: bool
    description: str

class MuhooratResponse(BaseModel):
    date: str
    weekday: str
    birth_nakshatra: str
    birth_nakshatra_2: Optional[str] = None
    timezone: str
    overall_verdict: str
    is_auspicious: bool
    factors: List[MuhooratFactor]
    factors_person_2: Optional[List[MuhooratFactor]] = None  # Factors for second person
    inauspicious_timings: dict
    panchang_details: dict

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# ============ PANCHANG CALCULATION FUNCTIONS ============

def get_julian_day(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """Calculate Julian Day Number"""
    return swe.julday(year, month, day, hour)

def get_sunrise_sunset(jd: float, lat: float, lon: float) -> tuple:
    """Calculate sunrise and sunset times"""
    try:
        # Get sunrise
        sunrise_info = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, swe.CALC_RISE)
        sunrise_jd = sunrise_info[1][0] if sunrise_info[0] == 0 else jd + 0.25
        
        # Get sunset  
        sunset_info = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, swe.CALC_SET)
        sunset_jd = sunset_info[1][0] if sunset_info[0] == 0 else jd + 0.75
        
        return sunrise_jd, sunset_jd
    except:
        # Fallback to approximate times
        return jd + 0.25, jd + 0.75

def jd_to_datetime(jd: float, tz_name: str) -> datetime:
    """Convert Julian Day to datetime in given timezone"""
    utc_tuple = swe.jdut1_to_utc(jd, 1)  # 1 = Gregorian calendar
    year, month, day, hour, minute, second = utc_tuple
    
    # Handle fractional seconds
    second = int(second)
    
    utc_dt = datetime(int(year), int(month), int(day), int(hour), int(minute), second, tzinfo=pytz.UTC)
    local_tz = pytz.timezone(tz_name)
    return utc_dt.astimezone(local_tz)

def get_moon_longitude(jd: float) -> float:
    """Get Moon's sidereal longitude (Nirayana)"""
    # Calculate moon position
    moon_pos = swe.calc_ut(jd, swe.MOON)[0]
    moon_long = moon_pos[0]
    
    # Apply Lahiri Ayanamsa for sidereal position
    ayanamsa = swe.get_ayanamsa(jd)
    sidereal_long = (moon_long - ayanamsa) % 360
    
    return sidereal_long

def get_sun_longitude(jd: float) -> float:
    """Get Sun's sidereal longitude (Nirayana)"""
    sun_pos = swe.calc_ut(jd, swe.SUN)[0]
    sun_long = sun_pos[0]
    
    ayanamsa = swe.get_ayanamsa(jd)
    sidereal_long = (sun_long - ayanamsa) % 360
    
    return sidereal_long

def calculate_tithi(jd: float) -> tuple:
    """Calculate Tithi (lunar day) - returns index (1-30) and name"""
    moon_long = get_moon_longitude(jd)
    sun_long = get_sun_longitude(jd)
    
    # Tithi = difference between Moon and Sun / 12 degrees
    diff = (moon_long - sun_long) % 360
    tithi_index = int(diff / 12) + 1
    
    if tithi_index > 30:
        tithi_index = 30
    
    tithi_name = TITHIS[tithi_index - 1]
    paksha = "Shukla Paksha" if tithi_index <= 15 else "Krishna Paksha"
    
    return tithi_index, tithi_name, paksha

def calculate_nakshatra(jd: float) -> tuple:
    """Calculate Nakshatra from Moon's position - returns index (1-27) and name"""
    moon_long = get_moon_longitude(jd)
    
    # Each nakshatra spans 13°20' (13.3333 degrees)
    nakshatra_index = int(moon_long / (360 / 27)) + 1
    
    if nakshatra_index > 27:
        nakshatra_index = 1
    
    nakshatra_name = NAKSHATRAS[nakshatra_index - 1]
    
    return nakshatra_index, nakshatra_name

def calculate_rashi(jd: float) -> tuple:
    """Calculate Moon's Rashi (zodiac sign) - returns index (1-12)"""
    moon_long = get_moon_longitude(jd)
    rashi_index = int(moon_long / 30) + 1
    
    rashi_names = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
                   "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
    
    return rashi_index, rashi_names[rashi_index - 1]

def calculate_lagna(jd: float, lat: float, lon: float) -> tuple:
    """
    Calculate Lagna (Ascendant) - the rising sign at a given time and location
    Returns index (1-12) and name
    """
    try:
        # Calculate houses using Swiss Ephemeris
        # Use Placidus house system (most common in Vedic astrology adaptations)
        houses = swe.houses(jd, lat, lon, b'P')
        ascendant_long = houses[1][0]  # Ascendant is first element of second tuple
        
        # Apply ayanamsa for sidereal position
        ayanamsa = swe.get_ayanamsa(jd)
        sidereal_asc = (ascendant_long - ayanamsa) % 360
        
        lagna_index = int(sidereal_asc / 30) + 1
        if lagna_index > 12:
            lagna_index = 1
            
    except:
        # Fallback: estimate lagna based on time of day and sun position
        sun_long = get_sun_longitude(jd)
        # Approximate lagna - roughly 1 sign every 2 hours from sunrise
        hours_from_midnight = (jd % 1) * 24
        lagna_offset = int(hours_from_midnight / 2)
        sidereal_asc = (sun_long + lagna_offset * 30) % 360
        lagna_index = int(sidereal_asc / 30) + 1
        if lagna_index > 12:
            lagna_index = 1
    
    lagna_names = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
                   "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
    
    return lagna_index, lagna_names[lagna_index - 1]

def get_birth_nakshatra_index(nakshatra_name: str) -> int:
    """Get nakshatra index (1-27) from name"""
    try:
        return NAKSHATRAS.index(nakshatra_name) + 1
    except ValueError:
        return 1

def get_nakshatra_rashi(nakshatra_index: int) -> int:
    """Get the rashi (1-12) for a nakshatra"""
    # Each rashi has 2.25 nakshatras
    # Nakshatra 1-2.25 = Mesha, 2.25-4.5 = Vrishabha, etc.
    return int((nakshatra_index - 1) * 4 / 9) + 1

def calculate_tarabalam(birth_nakshatra_index: int, day_nakshatra_index: int) -> tuple:
    """Calculate Tarabalam - returns (tara_number, tara_name, is_favorable)"""
    # Count from birth nakshatra to day nakshatra (inclusive, circular)
    distance = (day_nakshatra_index - birth_nakshatra_index + 27) % 27 + 1
    
    # Get remainder when divided by 9 (remainder 0 = 9)
    tara_num = distance % 9
    if tara_num == 0:
        tara_num = 9
    
    tara_name = TARABALAM_NAMES.get(tara_num, "Unknown")
    is_favorable = tara_num in TARABALAM_FAVORABLE
    
    return tara_num, tara_name, is_favorable

def calculate_chandrabalam(birth_nakshatra_index: int, day_rashi_index: int) -> tuple:
    """Calculate Chandrabalam based on Moon's rashi"""
    # Get birth rashi from birth nakshatra
    birth_rashi = get_nakshatra_rashi(birth_nakshatra_index)
    
    # Count from birth rashi to day's moon rashi
    count = (day_rashi_index - birth_rashi + 12) % 12 + 1
    
    is_favorable = count in CHANDRABALAM_FAVORABLE
    
    return count, is_favorable

def calculate_panchaka(tithi_index: int, weekday_index: int, nakshatra_index: int, lagna_index: int) -> tuple:
    """
    Calculate Panchaka dosha (Panchakarahitam)
    Formula: (Tithi + Vaara + Nakshatra + Lagnam) / 9
    
    Parameters:
    - tithi_index: 1-30 (lunar day)
    - weekday_index: 0-6 (Sunday=0 to Saturday=6)
    - nakshatra_index: 1-27 (Ashwini=1 to Revati=27)
    - lagna_index: 1-12 (Mesha=1 to Meena=12)
    
    Good remainders: 0, 3, 5, 7 (Panchaka Rahitam)
    Bad remainders: 1 (Mrityu), 2 (Agni), 4 (Raja), 6 (Chora), 8 (Roga)
    """
    # Weekday: Sunday=1, Monday=2, ... Saturday=7
    vara = weekday_index + 1
    
    # Calculate total and remainder
    total = tithi_index + vara + nakshatra_index + lagna_index
    remainder = total % 9
    
    panchaka_names = {
        0: "Panchaka Rahitam", 1: "Mrityu Panchaka", 2: "Agni Panchaka",
        3: "Panchaka Rahitam", 4: "Raja Panchaka", 5: "Panchaka Rahitam",
        6: "Chora Panchaka", 7: "Panchaka Rahitam", 8: "Roga Panchaka"
    }
    
    is_favorable = remainder in [0, 3, 5, 7]
    
    # Include calculation details in description
    calculation_details = f"Tithi({tithi_index}) + Vara({vara}) + Nakshatra({nakshatra_index}) + Lagna({lagna_index}) = {total}, {total} ÷ 9 = remainder {remainder}"
    
    return remainder, panchaka_names.get(remainder, "Unknown"), is_favorable, calculation_details

def calculate_rahukalam(sunrise_jd: float, sunset_jd: float, weekday: str, tz_name: str) -> tuple:
    """Calculate Rahukalam timing"""
    segment = RAHUKALAM_SEGMENTS.get(weekday, 8)
    
    day_duration = sunset_jd - sunrise_jd
    segment_duration = day_duration / 8
    
    start_jd = sunrise_jd + (segment - 1) * segment_duration
    end_jd = start_jd + segment_duration
    
    start_time = jd_to_datetime(start_jd, tz_name)
    end_time = jd_to_datetime(end_jd, tz_name)
    
    return start_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p")

def calculate_yamagandam(sunrise_jd: float, sunset_jd: float, weekday: str, tz_name: str) -> tuple:
    """Calculate Yamagandam timing"""
    segment = YAMAGANDAM_SEGMENTS.get(weekday, 1)
    
    day_duration = sunset_jd - sunrise_jd
    segment_duration = day_duration / 8
    
    start_jd = sunrise_jd + (segment - 1) * segment_duration
    end_jd = start_jd + segment_duration
    
    start_time = jd_to_datetime(start_jd, tz_name)
    end_time = jd_to_datetime(end_jd, tz_name)
    
    return start_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p")

def calculate_durmuhoortham(sunrise_jd: float, weekday: str, tz_name: str) -> list:
    """Calculate Durmuhoortham periods"""
    # Each muhurta = 48 minutes = 0.0333 days
    muhurta_duration = 48 / (24 * 60)  # in days
    
    periods = []
    muhurtas = DURMUHOORTHAM_MUHURTAS.get(weekday, [(14, 15)])
    
    for start_muhurta, end_muhurta in muhurtas:
        start_jd = sunrise_jd + (start_muhurta - 1) * muhurta_duration
        end_jd = sunrise_jd + end_muhurta * muhurta_duration
        
        start_time = jd_to_datetime(start_jd, tz_name)
        end_time = jd_to_datetime(end_jd, tz_name)
        
        periods.append({
            "start": start_time.strftime("%I:%M %p"),
            "end": end_time.strftime("%I:%M %p")
        })
    
    return periods

def calculate_varjyam(nakshatra_name: str, nakshatra_start_jd: float, tz_name: str) -> tuple:
    """Calculate Varjyam period based on nakshatra"""
    ghatikas = VARJYAM_GHATIKAS.get(nakshatra_name, 20)
    
    # 1 ghatika = 24 minutes = 0.0167 days
    ghatika_duration = 24 / (24 * 60)  # in days
    varjyam_duration = 4 * ghatika_duration  # 4 ghatikas = 96 minutes
    
    start_jd = nakshatra_start_jd + ghatikas * ghatika_duration
    end_jd = start_jd + varjyam_duration
    
    start_time = jd_to_datetime(start_jd, tz_name)
    end_time = jd_to_datetime(end_jd, tz_name)
    
    return start_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p")

def is_tithi_bad(tithi_index: int, paksha: str) -> tuple:
    """Check if tithi should be avoided"""
    # Bad tithis: Prathama (after Amavasya), Chaturthi, Ashtami, Navami, Dwadashi, Chaturdashi, Amavasya
    bad_tithis_in_paksha = {
        "Shukla Paksha": [1, 4, 8, 9, 12, 14],  # Prathama (after Amavasya), Chaturthi, Ashtami, Navami, Dwadashi, Chaturdashi
        "Krishna Paksha": [4, 8, 9, 12, 14, 15]  # Same pattern + Amavasya (15 in Krishna = 30 overall)
    }
    
    # Adjust index for Krishna Paksha
    check_index = tithi_index if tithi_index <= 15 else tithi_index - 15
    bad_list = bad_tithis_in_paksha.get(paksha, [])
    
    is_bad = check_index in bad_list
    
    if is_bad:
        if check_index == 1 and paksha == "Shukla Paksha":
            return True, "Prathama after Amavasya - Avoid"
        elif check_index == 4:
            return True, "Chaturthi - Avoid"
        elif check_index == 8:
            return True, "Ashtami - Avoid"
        elif check_index == 9:
            return True, "Navami - Avoid"
        elif check_index == 12:
            return True, "Dwadashi - Avoid"
        elif check_index == 14:
            return True, "Chaturdashi - Avoid"
        elif check_index == 15 and paksha == "Krishna Paksha":
            return True, "Amavasya - Avoid"
    
    return False, "Tithi is favorable"

# ============ API ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "Hindu Muhurat Panchang API", "version": "1.0"}

@api_router.get("/nakshatras")
async def get_nakshatras():
    """Get list of all 27 Nakshatras"""
    return {"nakshatras": NAKSHATRAS}

@api_router.get("/timezones")
async def get_timezones():
    """Get list of supported timezones"""
    return {"timezones": list(TIMEZONE_CONFIG.keys())}

@api_router.post("/check-muhurat", response_model=MuhooratResponse)
async def check_muhurat(request: MuhooratRequest):
    """Check if a date is auspicious based on birth nakshatra and various factors"""
    try:
        # Validate and parse date
        try:
            date_parts = request.date.split("-")
            if len(date_parts) != 3:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            year = int(date_parts[0])
            month = int(date_parts[1])
            day = int(date_parts[2])
            
            # Validate date ranges
            if month < 1 or month > 12:
                raise HTTPException(status_code=400, detail="Invalid month. Must be between 1 and 12")
            if day < 1 or day > 31:
                raise HTTPException(status_code=400, detail="Invalid day. Must be between 1 and 31")
            if year < 1900 or year > 2100:
                raise HTTPException(status_code=400, detail="Invalid year. Must be between 1900 and 2100")
                
            # Validate the actual date (e.g., Feb 30 is invalid)
            from datetime import date as date_class
            date_class(year, month, day)  # This will raise ValueError for invalid dates
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date: {str(e)}")
        
        # Validate nakshatra
        if request.birth_nakshatra not in NAKSHATRAS:
            raise HTTPException(status_code=400, detail=f"Invalid nakshatra. Must be one of: {', '.join(NAKSHATRAS)}")
        
        # Validate second nakshatra if provided
        if request.birth_nakshatra_2 and request.birth_nakshatra_2 not in NAKSHATRAS:
            raise HTTPException(status_code=400, detail=f"Invalid second nakshatra. Must be one of: {', '.join(NAKSHATRAS)}")
        
        # Validate timezone
        if request.timezone not in TIMEZONE_CONFIG:
            raise HTTPException(status_code=400, detail=f"Invalid timezone. Must be one of: {', '.join(TIMEZONE_CONFIG.keys())}")
        
        # Get timezone config
        tz_config = TIMEZONE_CONFIG.get(request.timezone, TIMEZONE_CONFIG["IST"])
        tz_name = tz_config["name"]
        lat = tz_config["lat"]
        lon = tz_config["lon"]
        tz_offset = tz_config["offset"]
        
        # Calculate Julian Day at local noon
        local_noon_utc = 12 - tz_offset  # Convert local noon to UTC
        jd = get_julian_day(year, month, day, local_noon_utc)
        
        # Get sunrise and sunset
        sunrise_jd, sunset_jd = get_sunrise_sunset(jd - 0.5, lat, lon)
        
        # Calculate weekday
        weekday_index = int(jd + 1.5) % 7  # 0 = Sunday
        weekday = WEEKDAYS[weekday_index]
        
        # Calculate Panchang elements
        tithi_index, tithi_name, paksha = calculate_tithi(jd)
        nakshatra_index, nakshatra_name = calculate_nakshatra(jd)
        rashi_index, rashi_name = calculate_rashi(jd)
        lagna_index, lagna_name = calculate_lagna(jd, lat, lon)
        
        # Get birth nakshatra index
        birth_nakshatra_index = get_birth_nakshatra_index(request.birth_nakshatra)
        
        # Calculate all factors for Person 1
        factors = []
        favorable_count = 0
        
        # 1. Tarabalam
        tara_num, tara_name, tara_favorable = calculate_tarabalam(birth_nakshatra_index, nakshatra_index)
        factors.append(MuhooratFactor(
            name="Tarabalam",
            value=f"{tara_name} ({tara_num})",
            is_favorable=tara_favorable,
            description=f"Star compatibility based on birth star ({request.birth_nakshatra}) and day's star ({nakshatra_name})"
        ))
        if tara_favorable:
            favorable_count += 1
        
        # 2. Chandrabalam
        chandra_count, chandra_favorable = calculate_chandrabalam(birth_nakshatra_index, rashi_index)
        factors.append(MuhooratFactor(
            name="Chandrabalam",
            value=f"Position {chandra_count}",
            is_favorable=chandra_favorable,
            description=f"Moon's strength based on its position in {rashi_name}"
        ))
        if chandra_favorable:
            favorable_count += 1
        
        # 3. Panchaka Rahitam (Tithi + Vara + Nakshatra + Lagna) / 9
        panchaka_rem, panchaka_name, panchaka_favorable, panchaka_calc = calculate_panchaka(tithi_index, weekday_index, nakshatra_index, lagna_index)
        factors.append(MuhooratFactor(
            name="Panchakarahitam",
            value=f"{panchaka_name} (remainder {panchaka_rem})",
            is_favorable=panchaka_favorable,
            description=f"Formula: {panchaka_calc}"
        ))
        if panchaka_favorable:
            favorable_count += 1
        
        # 4. Tithi Check
        tithi_bad, tithi_reason = is_tithi_bad(tithi_index, paksha)
        factors.append(MuhooratFactor(
            name="Tithi",
            value=f"{tithi_name} ({paksha})",
            is_favorable=not tithi_bad,
            description=tithi_reason if tithi_bad else "Tithi is favorable for auspicious activities"
        ))
        if not tithi_bad:
            favorable_count += 1
        
        # 5. Tuesday Check
        is_tuesday = weekday == "Tuesday"
        factors.append(MuhooratFactor(
            name="Weekday",
            value=weekday,
            is_favorable=not is_tuesday,
            description="Tuesday should be avoided for auspicious activities" if is_tuesday else "Weekday is favorable"
        ))
        if not is_tuesday:
            favorable_count += 1
        
        # Calculate factors for Person 2 if provided
        factors_person_2 = None
        is_auspicious_person_2 = True
        
        if request.birth_nakshatra_2:
            birth_nakshatra_2_index = get_birth_nakshatra_index(request.birth_nakshatra_2)
            factors_person_2 = []
            favorable_count_2 = 0
            
            # Tarabalam for Person 2
            tara_num_2, tara_name_2, tara_favorable_2 = calculate_tarabalam(birth_nakshatra_2_index, nakshatra_index)
            factors_person_2.append(MuhooratFactor(
                name="Tarabalam",
                value=f"{tara_name_2} ({tara_num_2})",
                is_favorable=tara_favorable_2,
                description=f"Star compatibility based on birth star ({request.birth_nakshatra_2}) and day's star ({nakshatra_name})"
            ))
            if tara_favorable_2:
                favorable_count_2 += 1
            
            # Chandrabalam for Person 2
            chandra_count_2, chandra_favorable_2 = calculate_chandrabalam(birth_nakshatra_2_index, rashi_index)
            factors_person_2.append(MuhooratFactor(
                name="Chandrabalam",
                value=f"Position {chandra_count_2}",
                is_favorable=chandra_favorable_2,
                description=f"Moon's strength based on its position in {rashi_name}"
            ))
            if chandra_favorable_2:
                favorable_count_2 += 1
            
            # Panchaka is same for both (based on date, not birth star)
            factors_person_2.append(MuhooratFactor(
                name="Panchakarahitam",
                value=f"{panchaka_name} (remainder {panchaka_rem})",
                is_favorable=panchaka_favorable,
                description=f"Formula: {panchaka_calc}"
            ))
            if panchaka_favorable:
                favorable_count_2 += 1
            
            # Tithi is same for both
            factors_person_2.append(MuhooratFactor(
                name="Tithi",
                value=f"{tithi_name} ({paksha})",
                is_favorable=not tithi_bad,
                description=tithi_reason if tithi_bad else "Tithi is favorable for auspicious activities"
            ))
            if not tithi_bad:
                favorable_count_2 += 1
            
            # Weekday is same for both
            factors_person_2.append(MuhooratFactor(
                name="Weekday",
                value=weekday,
                is_favorable=not is_tuesday,
                description="Tuesday should be avoided for auspicious activities" if is_tuesday else "Weekday is favorable"
            ))
            if not is_tuesday:
                favorable_count_2 += 1
            
            is_auspicious_person_2 = favorable_count_2 >= 4 and not is_tuesday and not tithi_bad
        
        # Calculate inauspicious timings
        rahu_start, rahu_end = calculate_rahukalam(sunrise_jd, sunset_jd, weekday, tz_name)
        yama_start, yama_end = calculate_yamagandam(sunrise_jd, sunset_jd, weekday, tz_name)
        durmuhoortham_periods = calculate_durmuhoortham(sunrise_jd, weekday, tz_name)
        
        # For Varjyam, we use sunrise as approximate nakshatra start (simplified)
        varjyam_start, varjyam_end = calculate_varjyam(nakshatra_name, sunrise_jd, tz_name)
        
        # Add timing factors as informational
        factors.append(MuhooratFactor(
            name="Rahukalam",
            value=f"{rahu_start} - {rahu_end}",
            is_favorable=True,  # Informational - avoid this period
            description="Avoid starting new activities during this period"
        ))
        
        factors.append(MuhooratFactor(
            name="Varjyam",
            value=f"{varjyam_start} - {varjyam_end}",
            is_favorable=True,  # Informational
            description="Inauspicious period based on nakshatra - avoid important activities"
        ))
        
        # Determine overall verdict
        is_auspicious = favorable_count >= 4 and not is_tuesday and not tithi_bad
        
        # If second person provided, both must be auspicious
        if request.birth_nakshatra_2:
            is_auspicious = is_auspicious and is_auspicious_person_2
        
        if is_auspicious:
            if request.birth_nakshatra_2:
                verdict = "AUSPICIOUS - Good day for both persons"
            else:
                verdict = "AUSPICIOUS - Good day for important activities"
        else:
            issues = []
            if is_tuesday:
                issues.append("Tuesday")
            if tithi_bad:
                issues.append(tithi_reason)
            if not tara_favorable:
                issues.append(f"Tarabalam unfavorable for {request.birth_nakshatra}")
            if not chandra_favorable:
                issues.append(f"Chandrabalam unfavorable for {request.birth_nakshatra}")
            if not panchaka_favorable:
                issues.append(panchaka_name)
            
            # Add issues for person 2
            if request.birth_nakshatra_2:
                if not tara_favorable_2:
                    issues.append(f"Tarabalam unfavorable for {request.birth_nakshatra_2}")
                if not chandra_favorable_2:
                    issues.append(f"Chandrabalam unfavorable for {request.birth_nakshatra_2}")
            
            verdict = f"NOT AUSPICIOUS - Issues: {', '.join(issues)}"
        
        # Sunrise/Sunset times
        sunrise_time = jd_to_datetime(sunrise_jd, tz_name)
        sunset_time = jd_to_datetime(sunset_jd, tz_name)
        
        return MuhooratResponse(
            date=request.date,
            weekday=weekday,
            birth_nakshatra=request.birth_nakshatra,
            birth_nakshatra_2=request.birth_nakshatra_2,
            timezone=request.timezone,
            overall_verdict=verdict,
            is_auspicious=is_auspicious,
            factors=factors,
            factors_person_2=factors_person_2,
            inauspicious_timings={
                "rahukalam": {"start": rahu_start, "end": rahu_end},
                "yamagandam": {"start": yama_start, "end": yama_end},
                "durmuhoortham": durmuhoortham_periods,
                "varjyam": {"start": varjyam_start, "end": varjyam_end}
            },
            panchang_details={
                "tithi": f"{tithi_name} ({paksha})",
                "nakshatra": nakshatra_name,
                "rashi": rashi_name,
                "lagna": lagna_name,
                "sunrise": sunrise_time.strftime("%I:%M %p"),
                "sunset": sunset_time.strftime("%I:%M %p")
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating muhurat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating muhurat: {str(e)}")

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
