#!/usr/bin/env python3
"""
Comprehensive Greek Translations Testing Suite
Tests the comprehensive Greek translations that were just added for the entire CRM application.
"""

import requests
import json
import sys
import os

# Backend URL from environment
BACKEND_URL = "https://vat-smart-crm.preview.emergentagent.com/api"

class GreekTranslationsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log_result(self, test_name, success, error_msg=None):
        """Log test result"""
        if success:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")

    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request"""
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            
            return response.status_code < 400, response
        except Exception as e:
            return False, str(e)

    def test_complete_translation_coverage(self):
        """Test 1: Complete Translation Coverage Test"""
        print("\n🇬🇷 Testing Complete Greek Translation Coverage...")
        
        # Get Greek translations via /api/translations/el
        success, response = self.make_request("GET", "/translations/el")
        if not success or response.status_code != 200:
            self.log_result("GET /api/translations/el - Endpoint accessibility", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")
            return None
        
        try:
            greek_response = response.json()
        except:
            self.log_result("GET /api/translations/el - JSON response format", False, "Invalid JSON response")
            return None
        
        if "language" not in greek_response or "translations" not in greek_response:
            self.log_result("GET /api/translations/el - Response structure", False, 
                          "Missing 'language' or 'translations' fields")
            return None
        
        if greek_response["language"] != "el":
            self.log_result("GET /api/translations/el - Language code verification", False,
                          f"Expected 'el', got '{greek_response['language']}'")
            return None
        
        greek_translations = greek_response["translations"]
        
        # Verify comprehensive coverage for all CRM sections
        crm_sections = {
            "Dashboard": ["dashboard", "quick_actions", "recent_activity"],
            "Contacts": ["contacts", "contact_management", "company"],
            "Accounts": ["accounts", "account_management", "vat_number"],
            "Products": ["products", "product_management", "category"],
            "Invoices": ["invoices", "invoice_billing", "invoice_status"],
            "Calendar": ["calendar", "events_schedule", "meeting"],
            "Admin": ["admin", "system_management", "role_plan"]
        }
        
        section_coverage = {}
        for section, keys in crm_sections.items():
            found_keys = sum(1 for key in keys if key in greek_translations)
            coverage_percent = (found_keys / len(keys)) * 100
            section_coverage[section] = coverage_percent
            
            if coverage_percent >= 50:  # At least 50% of section keys should be present
                self.log_result(f"Translation Coverage - {section} section", True)
            else:
                self.log_result(f"Translation Coverage - {section} section", False,
                              f"Only {coverage_percent:.1f}% coverage")
        
        # Overall coverage check
        total_translations = len(greek_translations)
        if total_translations >= 200:  # Expected 200+ keys as mentioned in review
            self.log_result("Translation Coverage - Total translation count", True,
                          f"Found {total_translations} translations")
        else:
            self.log_result("Translation Coverage - Total translation count", False,
                          f"Expected 200+ translations, found {total_translations}")
        
        return greek_translations

    def test_key_internal_interface_translations(self, greek_translations):
        """Test 2: Key Internal Interface Translations Verification"""
        print("\n🔍 Testing Key Internal Interface Translations...")
        
        if not greek_translations:
            self.log_result("Key Interface Translations - Prerequisites", False, "No Greek translations available")
            return
        
        # Expected key translations from the review request
        expected_translations = {
            # Dashboard translations
            "dashboard": "Πίνακας Ελέγχου",
            "quick_actions": "Γρήγορες Ενέργειες", 
            "recent_activity": "Πρόσφατη Δραστηριότητα",
            
            # Contacts
            "contacts": "Επαφές",
            "contact_management": "Διαχείριση πελατών και υποψηφίων",
            "company": "Εταιρεία",
            
            # Accounts
            "accounts": "Λογαριασμοί",
            "account_management": "Διαχείριση εταιρειών και πελατών",
            "vat_number": "Αριθμός ΦΠΑ",
            
            # Products
            "products": "Προϊόντα",
            "product_management": "Διαχείριση υπηρεσιών και καταλόγου",
            "category": "Κατηγορία",
            
            # Invoices
            "invoices": "Τιμολόγια",
            "invoice_billing": "Τιμολόγηση & Peppol",
            "invoice_status": "Κατάσταση Τιμολογίου",
            
            # Calendar
            "calendar": "Ημερολόγιο",
            "events_schedule": "Γεγονότα & Πρόγραμμα",
            "meeting": "Συνάντηση",
            
            # Admin
            "admin": "Διαχειριστής",
            "system_management": "Διαχείριση συστήματος",
            "role_plan": "Ρόλος/Πλάνο"
        }
        
        correct_translations = 0
        total_expected = len(expected_translations)
        
        for key, expected_value in expected_translations.items():
            if key in greek_translations:
                actual_value = greek_translations[key]
                if actual_value == expected_value:
                    correct_translations += 1
                    self.log_result(f"Key Translation - {key}", True)
                else:
                    # Check if it contains Greek characters (alternative valid translation)
                    if any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in actual_value):
                        correct_translations += 1
                        self.log_result(f"Key Translation - {key} (alternative)", True,
                                      f"Expected: '{expected_value}', Got: '{actual_value}'")
                    else:
                        self.log_result(f"Key Translation - {key}", False,
                                      f"Expected: '{expected_value}', Got: '{actual_value}'")
            else:
                self.log_result(f"Key Translation - {key}", False, "Translation key not found")
        
        # Overall key translations score
        accuracy = (correct_translations / total_expected) * 100
        if accuracy >= 80:
            self.log_result("Key Interface Translations - Overall accuracy", True,
                          f"{accuracy:.1f}% accuracy ({correct_translations}/{total_expected})")
        else:
            self.log_result("Key Interface Translations - Overall accuracy", False,
                          f"Only {accuracy:.1f}% accuracy ({correct_translations}/{total_expected})")

    def test_forms_and_ui_elements(self, greek_translations):
        """Test 3: Forms and UI Elements Test"""
        print("\n📝 Testing Forms and UI Elements Translations...")
        
        if not greek_translations:
            self.log_result("Forms and UI Elements - Prerequisites", False, "No Greek translations available")
            return
        
        # Common UI terms that should be translated
        ui_elements = {
            "save": "Αποθήκευση",
            "cancel": "Ακύρωση", 
            "edit": "Επεξεργασία",
            "delete": "Διαγραφή",
            "name": "Όνομα",
            "email": "Email",
            "phone": "Τηλέφωνο",
            "address": "Διεύθυνση",
            "success": "Επιτυχία",
            "error": "Σφάλμα",
            "loading": "Φόρτωση..."
        }
        
        ui_translations_found = 0
        for key, expected_value in ui_elements.items():
            if key in greek_translations:
                actual_value = greek_translations[key]
                # Check if it's a valid Greek translation (contains Greek characters or matches expected)
                if (actual_value == expected_value or 
                    any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in actual_value)):
                    ui_translations_found += 1
                    self.log_result(f"UI Element - {key}", True)
                else:
                    self.log_result(f"UI Element - {key}", False,
                                  f"Expected Greek text, got: '{actual_value}'")
            else:
                # Check for alternative key names
                alternative_keys = [f"{key}_btn", f"btn_{key}", f"form_{key}", f"label_{key}"]
                found_alternative = False
                for alt_key in alternative_keys:
                    if alt_key in greek_translations:
                        found_alternative = True
                        ui_translations_found += 1
                        self.log_result(f"UI Element - {key} (as {alt_key})", True)
                        break
                
                if not found_alternative:
                    self.log_result(f"UI Element - {key}", False, "Translation not found")
        
        # UI elements coverage
        ui_coverage = (ui_translations_found / len(ui_elements)) * 100
        if ui_coverage >= 70:
            self.log_result("Forms and UI Elements - Coverage", True,
                          f"{ui_coverage:.1f}% of UI elements translated")
        else:
            self.log_result("Forms and UI Elements - Coverage", False,
                          f"Only {ui_coverage:.1f}% of UI elements translated")

    def test_business_terms_translation(self, greek_translations):
        """Test 4: Business Terms Translation Test"""
        print("\n💼 Testing Business Terms Translations...")
        
        if not greek_translations:
            self.log_result("Business Terms - Prerequisites", False, "No Greek translations available")
            return
        
        # CRM specific and business terms
        business_terms = {
            # CRM specific
            "customer": "Πελάτης",
            "prospect": "Υποψήφιος", 
            "deal": "Συμφωνία",
            "payment": "Πληρωμή",
            
            # Invoice related
            "invoice": "Τιμολόγιο",
            "vat": "ΦΠΑ",
            "total": "Σύνολο",
            "paid": "Πληρωμένα",
            
            # VIES and Peppol (should contain Greek or remain as technical terms)
            "vies_integration": "Ενσωμάτωση VIES",
            "peppol_invoicing": "Τιμολόγηση Peppol"
        }
        
        business_terms_found = 0
        for key, expected_value in business_terms.items():
            found_translation = False
            
            # Check exact key
            if key in greek_translations:
                actual_value = greek_translations[key]
                if (actual_value == expected_value or 
                    any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in actual_value)):
                    business_terms_found += 1
                    found_translation = True
                    self.log_result(f"Business Term - {key}", True)
            
            # Check for variations of the key
            if not found_translation:
                variations = [f"{key}s", f"{key}_term", f"crm_{key}", f"business_{key}"]
                for variation in variations:
                    if variation in greek_translations:
                        actual_value = greek_translations[variation]
                        if any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in actual_value):
                            business_terms_found += 1
                            found_translation = True
                            self.log_result(f"Business Term - {key} (as {variation})", True)
                            break
            
            if not found_translation:
                self.log_result(f"Business Term - {key}", False, "Translation not found")
        
        # Business terms coverage
        business_coverage = (business_terms_found / len(business_terms)) * 100
        if business_coverage >= 60:
            self.log_result("Business Terms - Coverage", True,
                          f"{business_coverage:.1f}% of business terms translated")
        else:
            self.log_result("Business Terms - Coverage", False,
                          f"Only {business_coverage:.1f}% of business terms translated")

    def test_translation_count_comparison(self, greek_translations):
        """Test 5: Translation Count Comparison"""
        print("\n📊 Testing Translation Count Comparison...")
        
        if not greek_translations:
            self.log_result("Translation Count - Prerequisites", False, "No Greek translations available")
            return
        
        # Get English translations for comparison
        success, response = self.make_request("GET", "/translations/en")
        if not success or response.status_code != 200:
            self.log_result("Translation Count - English translations fetch", False,
                          "Could not fetch English translations for comparison")
            return
        
        try:
            english_response = response.json()
            english_translations = english_response["translations"]
        except:
            self.log_result("Translation Count - English translations parse", False,
                          "Could not parse English translations")
            return
        
        greek_count = len(greek_translations)
        english_count = len(english_translations)
        
        # Compare counts
        coverage_ratio = greek_count / english_count if english_count > 0 else 0
        
        self.log_result("Translation Count - Greek vs English comparison", True,
                      f"Greek: {greek_count}, English: {english_count}, Coverage: {coverage_ratio:.1%}")
        
        # Check if Greek has significantly more translations than basic homepage
        if greek_count >= 200:
            self.log_result("Translation Count - Comprehensive coverage", True,
                          f"Greek has {greek_count} translations (200+ expected)")
        else:
            self.log_result("Translation Count - Comprehensive coverage", False,
                          f"Greek has only {greek_count} translations (200+ expected)")
        
        # Check completeness compared to English
        if coverage_ratio >= 0.85:  # At least 85% of English translations
            self.log_result("Translation Count - Completeness vs English", True,
                          f"{coverage_ratio:.1%} completeness")
        else:
            self.log_result("Translation Count - Completeness vs English", False,
                          f"Only {coverage_ratio:.1%} completeness compared to English")
        
        # Check for Greek authenticity (not just English text)
        greek_char_count = 0
        sample_size = min(50, len(greek_translations))  # Check up to 50 translations
        
        for i, (key, value) in enumerate(greek_translations.items()):
            if i >= sample_size:
                break
            if any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in value):
                greek_char_count += 1
        
        greek_authenticity = greek_char_count / sample_size if sample_size > 0 else 0
        
        if greek_authenticity >= 0.6:  # At least 60% should contain Greek characters
            self.log_result("Translation Count - Greek text authenticity", True,
                          f"{greek_authenticity:.1%} of sampled translations contain Greek characters")
        else:
            self.log_result("Translation Count - Greek text authenticity", False,
                          f"Only {greek_authenticity:.1%} of sampled translations contain Greek characters")

    def test_specific_crm_sections(self, greek_translations):
        """Test specific CRM sections mentioned in the review"""
        print("\n🏢 Testing Specific CRM Section Translations...")
        
        if not greek_translations:
            self.log_result("CRM Sections - Prerequisites", False, "No Greek translations available")
            return
        
        # Test specific sections mentioned in the review request
        crm_sections_detailed = {
            "Dashboard": {
                "keys": ["dashboard", "quick_actions", "recent_activity", "stats", "overview"],
                "expected_greek": ["Πίνακας", "Γρήγορες", "Πρόσφατη", "Στατιστικά", "Επισκόπηση"]
            },
            "Contacts": {
                "keys": ["contacts", "contact_management", "customer_management", "company", "contact"],
                "expected_greek": ["Επαφές", "Διαχείριση", "πελατών", "Εταιρεία", "Επαφή"]
            },
            "Accounts": {
                "keys": ["accounts", "account_management", "companies", "vat_number", "account"],
                "expected_greek": ["Λογαριασμοί", "Διαχείριση", "εταιρειών", "ΦΠΑ", "Λογαριασμός"]
            },
            "Products": {
                "keys": ["products", "product_management", "catalog", "category", "product"],
                "expected_greek": ["Προϊόντα", "Διαχείριση", "κατάλογος", "Κατηγορία", "Προϊόν"]
            },
            "Invoices": {
                "keys": ["invoices", "billing", "peppol", "invoice_status", "invoice"],
                "expected_greek": ["Τιμολόγια", "Τιμολόγηση", "Peppol", "Κατάσταση", "Τιμολόγιο"]
            },
            "Calendar": {
                "keys": ["calendar", "events", "schedule", "meeting", "event"],
                "expected_greek": ["Ημερολόγιο", "Γεγονότα", "Πρόγραμμα", "Συνάντηση", "Γεγονός"]
            },
            "Admin": {
                "keys": ["admin", "administration", "system_management", "role", "user_management"],
                "expected_greek": ["Διαχειριστής", "Διαχείριση", "συστήματος", "Ρόλος", "χρηστών"]
            }
        }
        
        for section_name, section_data in crm_sections_detailed.items():
            keys = section_data["keys"]
            expected_terms = section_data["expected_greek"]
            
            found_translations = 0
            greek_content_found = 0
            
            for key in keys:
                if key in greek_translations:
                    found_translations += 1
                    translation_value = greek_translations[key]
                    
                    # Check if translation contains Greek characters or expected terms
                    has_greek_chars = any(ord(char) >= 0x0370 and ord(char) <= 0x03FF for char in translation_value)
                    has_expected_term = any(term in translation_value for term in expected_terms)
                    
                    if has_greek_chars or has_expected_term:
                        greek_content_found += 1
            
            # Calculate section coverage
            key_coverage = found_translations / len(keys) if keys else 0
            greek_coverage = greek_content_found / found_translations if found_translations > 0 else 0
            
            if key_coverage >= 0.4 and greek_coverage >= 0.6:  # At least 40% keys found, 60% with Greek content
                self.log_result(f"CRM Section - {section_name}", True,
                              f"Key coverage: {key_coverage:.1%}, Greek content: {greek_coverage:.1%}")
            else:
                self.log_result(f"CRM Section - {section_name}", False,
                              f"Insufficient coverage - Keys: {key_coverage:.1%}, Greek: {greek_coverage:.1%}")

    def run_comprehensive_test(self):
        """Run all comprehensive Greek translation tests"""
        print("🚀 Starting Comprehensive Greek Translations Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        
        try:
            # Test 1: Complete Translation Coverage
            greek_translations = self.test_complete_translation_coverage()
            
            # Test 2: Key Internal Interface Translations
            self.test_key_internal_interface_translations(greek_translations)
            
            # Test 3: Forms and UI Elements
            self.test_forms_and_ui_elements(greek_translations)
            
            # Test 4: Business Terms Translation
            self.test_business_terms_translation(greek_translations)
            
            # Test 5: Translation Count Comparison
            self.test_translation_count_comparison(greek_translations)
            
            # Test 6: Specific CRM Sections
            self.test_specific_crm_sections(greek_translations)
            
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Test execution error: {e}")
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            print(f"\n🔍 Errors:")
            for error in self.test_results["errors"]:
                print(f"  • {error}")
        
        return self.test_results["failed"] == 0

if __name__ == "__main__":
    tester = GreekTranslationsTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)