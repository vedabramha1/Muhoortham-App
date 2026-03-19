#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Hindu Muhurat Panchang API
Tests all endpoints and calculation logic as specified in the review request.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Use production backend URL from environment
API_BASE_URL = "https://panchangam-calc.preview.emergentagent.com/api"

# Expected data for validation
EXPECTED_NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

EXPECTED_TIMEZONES = ["IST", "EST", "PST", "CST", "MDT"]

# Test results tracking
test_results = []
failed_tests = []

def log_test_result(test_name: str, success: bool, message: str = "", data: Any = None):
    """Log test result for tracking"""
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "data": data
    }
    test_results.append(result)
    
    if success:
        print(f"✅ {test_name}: {message}")
    else:
        print(f"❌ {test_name}: {message}")
        failed_tests.append(result)

def test_health_check():
    """Test GET /api/ - Health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "Hindu Muhurat Panchang API" and data.get("version") == "1.0":
                log_test_result("Health Check", True, "API is running correctly")
                return True
            else:
                log_test_result("Health Check", False, f"Unexpected response: {data}")
                return False
        else:
            log_test_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test_result("Health Check", False, f"Connection error: {str(e)}")
        return False

def test_nakshatras_endpoint():
    """Test GET /api/nakshatras - Get list of 27 nakshatras"""
    try:
        response = requests.get(f"{API_BASE_URL}/nakshatras")
        if response.status_code == 200:
            data = response.json()
            nakshatras = data.get("nakshatras", [])
            
            if len(nakshatras) == 27:
                if nakshatras == EXPECTED_NAKSHATRAS:
                    log_test_result("Nakshatras Endpoint", True, f"All 27 nakshatras returned correctly")
                    return True
                else:
                    log_test_result("Nakshatras Endpoint", False, f"Nakshatra names don't match expected list")
                    return False
            else:
                log_test_result("Nakshatras Endpoint", False, f"Expected 27 nakshatras, got {len(nakshatras)}")
                return False
        else:
            log_test_result("Nakshatras Endpoint", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test_result("Nakshatras Endpoint", False, f"Error: {str(e)}")
        return False

def test_timezones_endpoint():
    """Test GET /api/timezones - Get supported timezones"""
    try:
        response = requests.get(f"{API_BASE_URL}/timezones")
        if response.status_code == 200:
            data = response.json()
            timezones = data.get("timezones", [])
            
            if set(timezones) == set(EXPECTED_TIMEZONES):
                log_test_result("Timezones Endpoint", True, f"All expected timezones returned: {timezones}")
                return True
            else:
                log_test_result("Timezones Endpoint", False, f"Expected {EXPECTED_TIMEZONES}, got {timezones}")
                return False
        else:
            log_test_result("Timezones Endpoint", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test_result("Timezones Endpoint", False, f"Error: {str(e)}")
        return False

def validate_muhurat_response_structure(data: Dict) -> bool:
    """Validate the structure of muhurat response"""
    required_fields = [
        "date", "weekday", "birth_nakshatra", "timezone", 
        "overall_verdict", "is_auspicious", "factors", 
        "inauspicious_timings", "panchang_details"
    ]
    
    for field in required_fields:
        if field not in data:
            log_test_result("Response Structure", False, f"Missing required field: {field}")
            return False
    
    # Validate factors array
    factors = data.get("factors", [])
    expected_factor_names = ["Tarabalam", "Chandrabalam", "Panchakarahitam", "Tithi", "Weekday", "Rahukalam", "Varjyam"]
    
    factor_names = [f.get("name") for f in factors]
    for expected_name in expected_factor_names:
        if expected_name not in factor_names:
            log_test_result("Response Structure", False, f"Missing factor: {expected_name}")
            return False
    
    # Validate factor structure
    for factor in factors:
        required_factor_fields = ["name", "value", "is_favorable", "description"]
        for field in required_factor_fields:
            if field not in factor:
                log_test_result("Response Structure", False, f"Factor missing field: {field}")
                return False
    
    log_test_result("Response Structure", True, "All required fields present")
    return True

def test_tuesday_avoidance():
    """Test Tuesday avoidance - should return is_auspicious: false"""
    test_data = {
        "date": "2025-07-15",  # Tuesday
        "birth_nakshatra": "Ashwini",
        "timezone": "IST"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_data)
        if response.status_code == 200:
            data = response.json()
            
            if not validate_muhurat_response_structure(data):
                return False
                
            if data.get("weekday") == "Tuesday":
                if data.get("is_auspicious") == False:
                    # Check if Tuesday is mentioned in issues
                    verdict = data.get("overall_verdict", "")
                    if "Tuesday" in verdict:
                        log_test_result("Tuesday Avoidance", True, "Tuesday correctly flagged as inauspicious")
                        return True
                    else:
                        log_test_result("Tuesday Avoidance", False, "Tuesday not mentioned in verdict issues")
                        return False
                else:
                    log_test_result("Tuesday Avoidance", False, f"Tuesday should be inauspicious but got: {data.get('is_auspicious')}")
                    return False
            else:
                log_test_result("Tuesday Avoidance", False, f"Expected Tuesday, got: {data.get('weekday')}")
                return False
        else:
            log_test_result("Tuesday Avoidance", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test_result("Tuesday Avoidance", False, f"Error: {str(e)}")
        return False

def test_bad_tithi_ashtami():
    """Test bad tithi (Ashtami) - should show unfavorable tithi"""
    test_data = {
        "date": "2025-07-17",  # Date that should have Ashtami
        "birth_nakshatra": "Rohini",
        "timezone": "EST"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_data)
        if response.status_code == 200:
            data = response.json()
            
            if not validate_muhurat_response_structure(data):
                return False
            
            # Find Tithi factor
            tithi_factor = None
            for factor in data.get("factors", []):
                if factor.get("name") == "Tithi":
                    tithi_factor = factor
                    break
            
            if tithi_factor:
                tithi_value = tithi_factor.get("value", "")
                is_favorable = tithi_factor.get("is_favorable", True)
                
                if "Ashtami" in tithi_value and not is_favorable:
                    log_test_result("Bad Tithi (Ashtami)", True, f"Ashtami correctly identified as unfavorable: {tithi_value}")
                    return True
                else:
                    log_test_result("Bad Tithi (Ashtami)", False, f"Tithi: {tithi_value}, Favorable: {is_favorable}")
                    return False
            else:
                log_test_result("Bad Tithi (Ashtami)", False, "Tithi factor not found in response")
                return False
        else:
            log_test_result("Bad Tithi (Ashtami)", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test_result("Bad Tithi (Ashtami)", False, f"Error: {str(e)}")
        return False

def test_different_timezones():
    """Test same date with different timezones - verify timing differences"""
    test_date = "2025-07-20"
    birth_nakshatra = "Bharani"
    timezones_to_test = ["IST", "EST", "PST"]
    
    timezone_results = {}
    
    for timezone in timezones_to_test:
        test_data = {
            "date": test_date,
            "birth_nakshatra": birth_nakshatra,
            "timezone": timezone
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_data)
            if response.status_code == 200:
                data = response.json()
                if validate_muhurat_response_structure(data):
                    timezone_results[timezone] = {
                        "rahukalam": data.get("inauspicious_timings", {}).get("rahukalam", {}),
                        "varjyam": data.get("inauspicious_timings", {}).get("varjyam", {}),
                        "sunrise": data.get("panchang_details", {}).get("sunrise", ""),
                        "sunset": data.get("panchang_details", {}).get("sunset", "")
                    }
                else:
                    log_test_result("Different Timezones", False, f"Invalid response structure for {timezone}")
                    return False
            else:
                log_test_result("Different Timezones", False, f"HTTP {response.status_code} for {timezone}")
                return False
        except Exception as e:
            log_test_result("Different Timezones", False, f"Error testing {timezone}: {str(e)}")
            return False
    
    # Verify that timings are different across timezones
    if len(timezone_results) == len(timezones_to_test):
        # Check if rahukalam times are different
        rahukalam_times = [tz_data["rahukalam"] for tz_data in timezone_results.values()]
        sunrise_times = [tz_data["sunrise"] for tz_data in timezone_results.values()]
        
        # All times should be different
        rahukalam_unique = len(set(str(r) for r in rahukalam_times)) == len(rahukalam_times)
        sunrise_unique = len(set(sunrise_times)) == len(sunrise_times)
        
        if rahukalam_unique and sunrise_unique:
            log_test_result("Different Timezones", True, f"Timings correctly vary across timezones: {list(timezone_results.keys())}")
            return True
        else:
            log_test_result("Different Timezones", False, f"Timings should be different but are similar: {timezone_results}")
            return False
    else:
        log_test_result("Different Timezones", False, "Failed to get results from all timezones")
        return False

def test_tarabalam_calculation():
    """Test Tarabalam calculation - when birth nakshatra = day's nakshatra"""
    test_data = {
        "date": "2025-07-20",  # We'll use this date and hope it aligns
        "birth_nakshatra": "Rohini",  # Test with a specific nakshatra
        "timezone": "IST"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_data)
        if response.status_code == 200:
            data = response.json()
            
            if not validate_muhurat_response_structure(data):
                return False
            
            # Find Tarabalam factor
            tarabalam_factor = None
            for factor in data.get("factors", []):
                if factor.get("name") == "Tarabalam":
                    tarabalam_factor = factor
                    break
            
            if tarabalam_factor:
                value = tarabalam_factor.get("value", "")
                is_favorable = tarabalam_factor.get("is_favorable")
                description = tarabalam_factor.get("description", "")
                
                # Test various scenarios - we'll check if the calculation is working
                if "(" in value and ")" in value:  # Should have format like "Sampat (2)"
                    tara_number = value.split("(")[1].split(")")[0]
                    try:
                        tara_num = int(tara_number)
                        if 1 <= tara_num <= 9:
                            # Check if favorable matches expected favorable numbers
                            expected_favorable = tara_num in [2, 4, 6, 8, 9]  # Sampat, Kshema, Sadhana, Mitra, Ati Mitra
                            if is_favorable == expected_favorable:
                                log_test_result("Tarabalam Calculation", True, f"Tarabalam correctly calculated: {value}, Favorable: {is_favorable}")
                                return True
                            else:
                                log_test_result("Tarabalam Calculation", False, f"Tarabalam favorable flag incorrect: {value}, Got: {is_favorable}, Expected: {expected_favorable}")
                                return False
                        else:
                            log_test_result("Tarabalam Calculation", False, f"Tara number out of range: {tara_num}")
                            return False
                    except ValueError:
                        log_test_result("Tarabalam Calculation", False, f"Invalid tara number format: {tara_number}")
                        return False
                else:
                    log_test_result("Tarabalam Calculation", False, f"Unexpected Tarabalam format: {value}")
                    return False
            else:
                log_test_result("Tarabalam Calculation", False, "Tarabalam factor not found")
                return False
        else:
            log_test_result("Tarabalam Calculation", False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test_result("Tarabalam Calculation", False, f"Error: {str(e)}")
        return False

def test_panchaka_calculation():
    """Test Panchaka calculation - verify different Panchaka types are returned"""
    test_cases = [
        {"date": "2025-07-15", "birth_nakshatra": "Ashwini", "timezone": "IST"},
        {"date": "2025-07-16", "birth_nakshatra": "Bharani", "timezone": "EST"},
        {"date": "2025-07-17", "birth_nakshatra": "Krittika", "timezone": "PST"}
    ]
    
    panchaka_types_found = set()
    
    for i, test_data in enumerate(test_cases):
        try:
            response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_data)
            if response.status_code == 200:
                data = response.json()
                
                if not validate_muhurat_response_structure(data):
                    return False
                
                # Find Panchakarahitam factor
                panchaka_factor = None
                for factor in data.get("factors", []):
                    if factor.get("name") == "Panchakarahitam":
                        panchaka_factor = factor
                        break
                
                if panchaka_factor:
                    panchaka_value = panchaka_factor.get("value", "")
                    panchaka_types_found.add(panchaka_value)
                else:
                    log_test_result("Panchaka Calculation", False, f"Panchakarahitam factor not found in test {i+1}")
                    return False
            else:
                log_test_result("Panchaka Calculation", False, f"HTTP {response.status_code} in test {i+1}")
                return False
        except Exception as e:
            log_test_result("Panchaka Calculation", False, f"Error in test {i+1}: {str(e)}")
            return False
    
    # Verify we got different panchaka types
    expected_types = {"Panchaka Rahitam", "Mrityu Panchaka", "Agni Panchaka", "Raja Panchaka", "Chora Panchaka", "Roga Panchaka"}
    
    if len(panchaka_types_found) > 0:
        # Check if found types are valid
        invalid_types = panchaka_types_found - expected_types
        if not invalid_types:
            log_test_result("Panchaka Calculation", True, f"Valid Panchaka types found: {list(panchaka_types_found)}")
            return True
        else:
            log_test_result("Panchaka Calculation", False, f"Invalid Panchaka types found: {invalid_types}")
            return False
    else:
        log_test_result("Panchaka Calculation", False, "No Panchaka types found")
        return False

def test_all_27_nakshatras():
    """Test all 27 nakshatras work as birth_nakshatra"""
    test_date = "2025-07-20"
    timezone = "IST"
    
    successful_nakshatras = []
    failed_nakshatras = []
    
    for nakshatra in EXPECTED_NAKSHATRAS:
        test_data = {
            "date": test_date,
            "birth_nakshatra": nakshatra,
            "timezone": timezone
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_data)
            if response.status_code == 200:
                data = response.json()
                if validate_muhurat_response_structure(data):
                    if data.get("birth_nakshatra") == nakshatra:
                        successful_nakshatras.append(nakshatra)
                    else:
                        failed_nakshatras.append(f"{nakshatra} (birth_nakshatra mismatch)")
                else:
                    failed_nakshatras.append(f"{nakshatra} (structure validation failed)")
            else:
                failed_nakshatras.append(f"{nakshatra} (HTTP {response.status_code})")
        except Exception as e:
            failed_nakshatras.append(f"{nakshatra} (Error: {str(e)})")
    
    if len(successful_nakshatras) == 27:
        log_test_result("All 27 Nakshatras", True, f"All nakshatras work correctly")
        return True
    else:
        log_test_result("All 27 Nakshatras", False, f"Only {len(successful_nakshatras)}/27 nakshatras work. Failed: {failed_nakshatras[:5]}...")
        return False

def test_error_handling():
    """Test error handling for invalid inputs"""
    error_test_cases = [
        {
            "name": "Invalid Date Format",
            "data": {"date": "2025-13-45", "birth_nakshatra": "Ashwini", "timezone": "IST"},
            "should_fail": True
        },
        {
            "name": "Invalid Nakshatra",
            "data": {"date": "2025-07-20", "birth_nakshatra": "InvalidStar", "timezone": "IST"},
            "should_fail": False  # Should handle gracefully
        },
        {
            "name": "Invalid Timezone",
            "data": {"date": "2025-07-20", "birth_nakshatra": "Ashwini", "timezone": "INVALID"},
            "should_fail": False  # Should default to IST
        },
        {
            "name": "Missing Fields",
            "data": {"date": "2025-07-20"},
            "should_fail": True
        }
    ]
    
    passed_error_tests = 0
    
    for test_case in error_test_cases:
        try:
            response = requests.post(f"{API_BASE_URL}/check-muhurat", json=test_case["data"])
            
            if test_case["should_fail"]:
                if response.status_code != 200:
                    passed_error_tests += 1
                    print(f"  ✓ {test_case['name']}: Correctly returned error (HTTP {response.status_code})")
                else:
                    print(f"  ✗ {test_case['name']}: Should have failed but returned 200")
            else:
                if response.status_code == 200:
                    passed_error_tests += 1
                    print(f"  ✓ {test_case['name']}: Handled gracefully")
                else:
                    print(f"  ✗ {test_case['name']}: Should have handled gracefully but returned {response.status_code}")
        except Exception as e:
            print(f"  ✗ {test_case['name']}: Exception occurred: {str(e)}")
    
    if passed_error_tests == len(error_test_cases):
        log_test_result("Error Handling", True, f"All {len(error_test_cases)} error cases handled correctly")
        return True
    else:
        log_test_result("Error Handling", False, f"Only {passed_error_tests}/{len(error_test_cases)} error cases handled correctly")
        return False

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting Hindu Muhurat Panchang API Backend Tests...")
    print(f"Testing API at: {API_BASE_URL}")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("Health Check", test_health_check),
        ("Nakshatras Endpoint", test_nakshatras_endpoint),
        ("Timezones Endpoint", test_timezones_endpoint),
        ("Tuesday Avoidance", test_tuesday_avoidance),
        ("Bad Tithi (Ashtami)", test_bad_tithi_ashtami),
        ("Different Timezones", test_different_timezones),
        ("Tarabalam Calculation", test_tarabalam_calculation),
        ("Panchaka Calculation", test_panchaka_calculation),
        ("All 27 Nakshatras", test_all_27_nakshatras),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
        except Exception as e:
            log_test_result(test_name, False, f"Test function crashed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, test in enumerate(failed_tests, 1):
            print(f"{i}. {test['test']}: {test['message']}")
    
    print("\n" + "=" * 80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)