import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Modal,
  SafeAreaView,
  StatusBar,
  Switch,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// 27 Nakshatras
const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
  "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
  "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
  "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
  "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
];

// Timezones
const TIMEZONES = [
  { label: "IST (India)", value: "IST" },
  { label: "EST (Eastern US)", value: "EST" },
  { label: "PST (Pacific US)", value: "PST" },
  { label: "CST (Central US)", value: "CST" },
  { label: "MDT (Mountain US)", value: "MDT" },
];

// Generate years
const YEARS = Array.from({ length: 11 }, (_, i) => 2020 + i);

// Months
const MONTHS = [
  { label: "January", value: 1 },
  { label: "February", value: 2 },
  { label: "March", value: 3 },
  { label: "April", value: 4 },
  { label: "May", value: 5 },
  { label: "June", value: 6 },
  { label: "July", value: 7 },
  { label: "August", value: 8 },
  { label: "September", value: 9 },
  { label: "October", value: 10 },
  { label: "November", value: 11 },
  { label: "December", value: 12 },
];

// Get days in month
const getDaysInMonth = (year: number, month: number) => {
  return new Date(year, month, 0).getDate();
};

interface MuhooratFactor {
  name: string;
  value: string;
  is_favorable: boolean;
  description: string;
}

interface MuhooratResult {
  date: string;
  weekday: string;
  birth_nakshatra: string;
  birth_nakshatra_2: string | null;
  timezone: string;
  overall_verdict: string;
  is_auspicious: boolean;
  factors: MuhooratFactor[];
  factors_person_2: MuhooratFactor[] | null;
  inauspicious_timings: {
    rahukalam: { start: string; end: string };
    yamagandam: { start: string; end: string };
    durmuhoortham: { start: string; end: string }[];
    varjyam: { start: string; end: string };
  };
  panchang_details: {
    tithi: string;
    nakshatra: string;
    rashi: string;
    lagna: string;
    sunrise: string;
    sunset: string;
  };
}

// Custom Picker Component
const CustomPicker = ({
  visible,
  onClose,
  options,
  selectedValue,
  onSelect,
  title,
}: {
  visible: boolean;
  onClose: () => void;
  options: { label: string; value: any }[];
  selectedValue: any;
  onSelect: (value: any) => void;
  title: string;
}) => {
  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>{title}</Text>
            <TouchableOpacity onPress={onClose} style={styles.modalCloseBtn}>
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.optionsList}>
            {options.map((option, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.optionItem,
                  selectedValue === option.value && styles.optionItemSelected,
                ]}
                onPress={() => {
                  onSelect(option.value);
                  onClose();
                }}
              >
                <Text
                  style={[
                    styles.optionText,
                    selectedValue === option.value && styles.optionTextSelected,
                  ]}
                >
                  {option.label}
                </Text>
                {selectedValue === option.value && (
                  <Ionicons name="checkmark" size={20} color="#FF6B00" />
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

export default function Index() {
  const today = new Date();
  const [selectedYear, setSelectedYear] = useState(today.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState(today.getDate());
  const [selectedNakshatra, setSelectedNakshatra] = useState(NAKSHATRAS[0]);
  const [selectedNakshatra2, setSelectedNakshatra2] = useState(NAKSHATRAS[1]);
  const [enableSecondPerson, setEnableSecondPerson] = useState(false);
  const [selectedTimezone, setSelectedTimezone] = useState("IST");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MuhooratResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Picker visibility states
  const [showYearPicker, setShowYearPicker] = useState(false);
  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [showDayPicker, setShowDayPicker] = useState(false);
  const [showNakshatraPicker, setShowNakshatraPicker] = useState(false);
  const [showNakshatraPicker2, setShowNakshatraPicker2] = useState(false);
  const [showTimezonePicker, setShowTimezonePicker] = useState(false);

  const daysInMonth = getDaysInMonth(selectedYear, selectedMonth);
  const DAYS = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  // Adjust day if exceeds month's days
  useEffect(() => {
    if (selectedDay > daysInMonth) {
      setSelectedDay(daysInMonth);
    }
  }, [selectedMonth, selectedYear]);

  const formatDate = () => {
    const month = selectedMonth.toString().padStart(2, '0');
    const day = selectedDay.toString().padStart(2, '0');
    return `${selectedYear}-${month}-${day}`;
  };

  const checkMuhurat = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const requestBody: any = {
        date: formatDate(),
        birth_nakshatra: selectedNakshatra,
        timezone: selectedTimezone,
      };
      
      if (enableSecondPerson) {
        requestBody.birth_nakshatra_2 = selectedNakshatra2;
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/check-muhurat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to check muhurat');
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getMonthLabel = () => {
    return MONTHS.find(m => m.value === selectedMonth)?.label || '';
  };

  const getTimezoneLabel = () => {
    return TIMEZONES.find(t => t.value === selectedTimezone)?.label || '';
  };

  const renderFactors = (factors: MuhooratFactor[], title: string) => (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>
        <Ionicons name="analytics" size={18} color="#FF6B00" /> {title}
      </Text>
      {factors.map((factor, index) => (
        <View key={index} style={styles.factorItem}>
          <View style={styles.factorHeader}>
            <Ionicons
              name={factor.is_favorable ? "checkmark-circle" : "close-circle"}
              size={24}
              color={factor.is_favorable ? "#00C851" : "#ff4444"}
            />
            <Text style={styles.factorName}>{factor.name}</Text>
            <View style={[
              styles.factorBadge,
              factor.is_favorable ? styles.factorBadgeGood : styles.factorBadgeBad
            ]}>
              <Text style={[
                styles.factorBadgeText,
                factor.is_favorable ? styles.factorBadgeTextGood : styles.factorBadgeTextBad
              ]}>
                {factor.is_favorable ? "GOOD" : "BAD"}
              </Text>
            </View>
          </View>
          <Text style={styles.factorValue}>{factor.value}</Text>
          <Text style={styles.factorDescription}>{factor.description}</Text>
        </View>
      ))}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Image 
            source={require('../assets/images/app-logo.jpg')} 
            style={styles.logoImage}
          />
          <Text style={styles.headerTitle}>Sri Lalitha Krishna Shastry</Text>
          <Text style={styles.headerSubtitle}>Muhoortham App</Text>
        </View>

        {/* Input Section */}
        <View style={styles.inputSection}>
          <Text style={styles.sectionTitle}>Select Date</Text>
          
          <View style={styles.dateRow}>
            {/* Year */}
            <TouchableOpacity
              style={styles.datePickerBtn}
              onPress={() => setShowYearPicker(true)}
            >
              <Text style={styles.datePickerLabel}>Year</Text>
              <Text style={styles.datePickerValue}>{selectedYear}</Text>
              <Ionicons name="chevron-down" size={16} color="#888" />
            </TouchableOpacity>

            {/* Month */}
            <TouchableOpacity
              style={[styles.datePickerBtn, styles.datePickerBtnMiddle]}
              onPress={() => setShowMonthPicker(true)}
            >
              <Text style={styles.datePickerLabel}>Month</Text>
              <Text style={styles.datePickerValue}>{getMonthLabel().slice(0, 3)}</Text>
              <Ionicons name="chevron-down" size={16} color="#888" />
            </TouchableOpacity>

            {/* Day */}
            <TouchableOpacity
              style={styles.datePickerBtn}
              onPress={() => setShowDayPicker(true)}
            >
              <Text style={styles.datePickerLabel}>Day</Text>
              <Text style={styles.datePickerValue}>{selectedDay}</Text>
              <Ionicons name="chevron-down" size={16} color="#888" />
            </TouchableOpacity>
          </View>

          {/* Birth Nakshatra 1 */}
          <Text style={styles.sectionTitle}>Birth Star (Nakshatra)</Text>
          <TouchableOpacity
            style={styles.fullWidthPicker}
            onPress={() => setShowNakshatraPicker(true)}
          >
            <Ionicons name="star" size={20} color="#FF6B00" />
            <Text style={styles.fullWidthPickerText}>{selectedNakshatra}</Text>
            <Ionicons name="chevron-down" size={20} color="#888" />
          </TouchableOpacity>

          {/* Toggle for Second Person */}
          <View style={styles.toggleRow}>
            <View style={styles.toggleLabel}>
              <Ionicons name="people" size={20} color="#FF6B00" />
              <Text style={styles.toggleText}>Check for Spouse also</Text>
            </View>
            <Switch
              value={enableSecondPerson}
              onValueChange={setEnableSecondPerson}
              trackColor={{ false: '#333', true: '#FF6B00' }}
              thumbColor={enableSecondPerson ? '#fff' : '#888'}
            />
          </View>

          {/* Birth Nakshatra 2 (Conditional) */}
          {enableSecondPerson && (
            <>
              <Text style={styles.sectionTitle}>Birth Star (Person 2)</Text>
              <TouchableOpacity
                style={styles.fullWidthPicker}
                onPress={() => setShowNakshatraPicker2(true)}
              >
                <Ionicons name="star-outline" size={20} color="#FF6B00" />
                <Text style={styles.fullWidthPickerText}>{selectedNakshatra2}</Text>
                <Ionicons name="chevron-down" size={20} color="#888" />
              </TouchableOpacity>
            </>
          )}

          {/* Timezone */}
          <Text style={styles.sectionTitle}>Timezone</Text>
          <TouchableOpacity
            style={styles.fullWidthPicker}
            onPress={() => setShowTimezonePicker(true)}
          >
            <Ionicons name="globe" size={20} color="#FF6B00" />
            <Text style={styles.fullWidthPickerText}>{getTimezoneLabel()}</Text>
            <Ionicons name="chevron-down" size={20} color="#888" />
          </TouchableOpacity>

          {/* Check Button */}
          <TouchableOpacity
            style={styles.checkButton}
            onPress={checkMuhurat}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="search" size={20} color="#fff" />
                <Text style={styles.checkButtonText}>Check Muhurat</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Error */}
        {error && (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={24} color="#ff4444" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Results */}
        {result && (
          <View style={styles.resultsContainer}>
            {/* Overall Verdict */}
            <View style={[
              styles.verdictCard,
              result.is_auspicious ? styles.verdictGood : styles.verdictBad
            ]}>
              <Ionicons
                name={result.is_auspicious ? "checkmark-circle" : "close-circle"}
                size={48}
                color={result.is_auspicious ? "#00C851" : "#ff4444"}
              />
              <Text style={[
                styles.verdictText,
                result.is_auspicious ? styles.verdictTextGood : styles.verdictTextBad
              ]}>
                {result.is_auspicious ? "AUSPICIOUS" : "NOT AUSPICIOUS"}
              </Text>
              <Text style={styles.verdictSubtext}>{result.overall_verdict}</Text>
              <Text style={styles.verdictDate}>
                {result.weekday}, {result.date}
              </Text>
              {result.birth_nakshatra_2 && (
                <Text style={styles.verdictPersons}>
                  For: {result.birth_nakshatra} & {result.birth_nakshatra_2}
                </Text>
              )}
            </View>

            {/* Panchang Details */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>
                <Ionicons name="calendar" size={18} color="#FF6B00" /> Panchang Details
              </Text>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Tithi</Text>
                <Text style={styles.detailValue}>{result.panchang_details.tithi}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Nakshatra</Text>
                <Text style={styles.detailValue}>{result.panchang_details.nakshatra}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Rashi</Text>
                <Text style={styles.detailValue}>{result.panchang_details.rashi}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Lagna</Text>
                <Text style={styles.detailValue}>{result.panchang_details.lagna}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Sunrise</Text>
                <Text style={styles.detailValue}>{result.panchang_details.sunrise}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Sunset</Text>
                <Text style={styles.detailValue}>{result.panchang_details.sunset}</Text>
              </View>
            </View>

            {/* Muhurat Factors for Person 1 */}
            {renderFactors(
              result.factors.filter(f => !['Rahukalam', 'Varjyam'].includes(f.name)), 
              result.birth_nakshatra_2 ? `Analysis - ${result.birth_nakshatra}` : 'Muhurat Analysis'
            )}

            {/* Muhurat Factors for Person 2 */}
            {result.factors_person_2 && (
              renderFactors(result.factors_person_2, `Analysis - ${result.birth_nakshatra_2}`)
            )}

            {/* Inauspicious Timings */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>
                <Ionicons name="time" size={18} color="#FF6B00" /> Timings to Avoid
              </Text>
              <View style={styles.timingItem}>
                <Ionicons name="warning" size={20} color="#ff9800" />
                <View style={styles.timingContent}>
                  <Text style={styles.timingLabel}>Rahukalam</Text>
                  <Text style={styles.timingValue}>
                    {result.inauspicious_timings.rahukalam.start} - {result.inauspicious_timings.rahukalam.end}
                  </Text>
                </View>
              </View>
              <View style={styles.timingItem}>
                <Ionicons name="warning" size={20} color="#ff9800" />
                <View style={styles.timingContent}>
                  <Text style={styles.timingLabel}>Yamagandam</Text>
                  <Text style={styles.timingValue}>
                    {result.inauspicious_timings.yamagandam.start} - {result.inauspicious_timings.yamagandam.end}
                  </Text>
                </View>
              </View>
              <View style={styles.timingItem}>
                <Ionicons name="warning" size={20} color="#ff9800" />
                <View style={styles.timingContent}>
                  <Text style={styles.timingLabel}>Varjyam</Text>
                  <Text style={styles.timingValue}>
                    {result.inauspicious_timings.varjyam.start} - {result.inauspicious_timings.varjyam.end}
                  </Text>
                </View>
              </View>
              {result.inauspicious_timings.durmuhoortham.map((dur, index) => (
                <View key={index} style={styles.timingItem}>
                  <Ionicons name="warning" size={20} color="#ff9800" />
                  <View style={styles.timingContent}>
                    <Text style={styles.timingLabel}>Durmuhoortham {index + 1}</Text>
                    <Text style={styles.timingValue}>
                      {dur.start} - {dur.end}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      {/* Pickers */}
      <CustomPicker
        visible={showYearPicker}
        onClose={() => setShowYearPicker(false)}
        options={YEARS.map(y => ({ label: y.toString(), value: y }))}
        selectedValue={selectedYear}
        onSelect={setSelectedYear}
        title="Select Year"
      />

      <CustomPicker
        visible={showMonthPicker}
        onClose={() => setShowMonthPicker(false)}
        options={MONTHS.map(m => ({ label: m.label, value: m.value }))}
        selectedValue={selectedMonth}
        onSelect={setSelectedMonth}
        title="Select Month"
      />

      <CustomPicker
        visible={showDayPicker}
        onClose={() => setShowDayPicker(false)}
        options={DAYS.map(d => ({ label: d.toString(), value: d }))}
        selectedValue={selectedDay}
        onSelect={setSelectedDay}
        title="Select Day"
      />

      <CustomPicker
        visible={showNakshatraPicker}
        onClose={() => setShowNakshatraPicker(false)}
        options={NAKSHATRAS.map(n => ({ label: n, value: n }))}
        selectedValue={selectedNakshatra}
        onSelect={setSelectedNakshatra}
        title="Select Birth Star (Person 1)"
      />

      <CustomPicker
        visible={showNakshatraPicker2}
        onClose={() => setShowNakshatraPicker2(false)}
        options={NAKSHATRAS.map(n => ({ label: n, value: n }))}
        selectedValue={selectedNakshatra2}
        onSelect={setSelectedNakshatra2}
        title="Select Birth Star (Person 2)"
      />

      <CustomPicker
        visible={showTimezonePicker}
        onClose={() => setShowTimezonePicker(false)}
        options={TIMEZONES}
        selectedValue={selectedTimezone}
        onSelect={setSelectedTimezone}
        title="Select Timezone"
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 30,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 30,
    paddingTop: Platform.OS === 'android' ? 40 : 20,
  },
  logoImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 12,
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 18,
    color: '#FF6B00',
    marginTop: 4,
    fontWeight: '600',
  },
  inputSection: {
    backgroundColor: '#16213e',
    marginHorizontal: 16,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#888',
    marginBottom: 10,
    marginTop: 16,
  },
  dateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  datePickerBtn: {
    flex: 1,
    backgroundColor: '#0f0f23',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  datePickerBtnMiddle: {
    marginHorizontal: 10,
  },
  datePickerLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  datePickerValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  fullWidthPicker: {
    backgroundColor: '#0f0f23',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  fullWidthPickerText: {
    flex: 1,
    fontSize: 16,
    color: '#fff',
    marginLeft: 12,
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0f0f23',
    borderRadius: 12,
    padding: 14,
    marginTop: 16,
  },
  toggleLabel: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  toggleText: {
    fontSize: 14,
    color: '#fff',
    marginLeft: 10,
  },
  checkButton: {
    backgroundColor: '#FF6B00',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 24,
  },
  checkButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginLeft: 10,
  },
  errorContainer: {
    backgroundColor: '#2a1515',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  errorText: {
    color: '#ff4444',
    marginLeft: 12,
    flex: 1,
  },
  resultsContainer: {
    marginHorizontal: 16,
  },
  verdictCard: {
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 16,
  },
  verdictGood: {
    backgroundColor: '#0d2818',
    borderWidth: 2,
    borderColor: '#00C851',
  },
  verdictBad: {
    backgroundColor: '#2a1515',
    borderWidth: 2,
    borderColor: '#ff4444',
  },
  verdictText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 12,
  },
  verdictTextGood: {
    color: '#00C851',
  },
  verdictTextBad: {
    color: '#ff4444',
  },
  verdictSubtext: {
    fontSize: 14,
    color: '#888',
    marginTop: 8,
    textAlign: 'center',
  },
  verdictDate: {
    fontSize: 16,
    color: '#fff',
    marginTop: 8,
    fontWeight: '600',
  },
  verdictPersons: {
    fontSize: 14,
    color: '#FF6B00',
    marginTop: 8,
    fontWeight: '500',
  },
  card: {
    backgroundColor: '#16213e',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#0f0f23',
  },
  detailLabel: {
    fontSize: 14,
    color: '#888',
  },
  detailValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  factorItem: {
    backgroundColor: '#0f0f23',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  factorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  factorName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 10,
    flex: 1,
  },
  factorBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  factorBadgeGood: {
    backgroundColor: '#0d2818',
  },
  factorBadgeBad: {
    backgroundColor: '#2a1515',
  },
  factorBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  factorBadgeTextGood: {
    color: '#00C851',
  },
  factorBadgeTextBad: {
    color: '#ff4444',
  },
  factorValue: {
    fontSize: 14,
    color: '#FF6B00',
    marginBottom: 4,
    marginLeft: 34,
  },
  factorDescription: {
    fontSize: 12,
    color: '#666',
    marginLeft: 34,
    lineHeight: 18,
  },
  timingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f0f23',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
  },
  timingContent: {
    marginLeft: 12,
    flex: 1,
  },
  timingLabel: {
    fontSize: 14,
    color: '#ff9800',
    fontWeight: '600',
  },
  timingValue: {
    fontSize: 14,
    color: '#fff',
    marginTop: 2,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '60%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  modalCloseBtn: {
    padding: 4,
  },
  optionsList: {
    paddingBottom: 30,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  optionItemSelected: {
    backgroundColor: '#fff5ee',
  },
  optionText: {
    fontSize: 16,
    color: '#333',
  },
  optionTextSelected: {
    color: '#FF6B00',
    fontWeight: '600',
  },
});
