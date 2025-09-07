#!/usr/bin/env python3
"""
Calendar Functionality Testing Suite
Tests the calendar frontend integration with backend APIs, focusing on:
- Calendar API Integration (frontend to backend)
- Event CRUD Operations
- Event Types (meeting, call, deadline, invoice_due)
- CRM Integration (linking events to contacts/accounts)
- Date/Time Handling
- Event Display
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import uuid
import sys
import os

# Backend URL from environment
BACKEND_URL = "https://vat-smart-crm.preview.emergentagent.com/api"

class CalendarFunctionalityTester:
    def __init__(self):
        self.session = requests.Session()
        self.session_token = None
        self.user_id = None
        self.test_results = {
            "calendar_api": {"passed": 0, "failed": 0, "errors": []},
            "event_crud": {"passed": 0, "failed": 0, "errors": []},
            "event_types": {"passed": 0, "failed": 0, "errors": []},
            "crm_integration": {"passed": 0, "failed": 0, "errors": []},
            "datetime_handling": {"passed": 0, "failed": 0, "errors": []},
            "event_display": {"passed": 0, "failed": 0, "errors": []}
        }
        self.created_entities = {
            "contacts": [],
            "accounts": [],
            "events": []
        }

    def log_result(self, category, test_name, success, error_msg=None):
        """Log test result"""
        if success:
            self.test_results[category]["passed"] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results[category]["failed"] += 1
            self.test_results[category]["errors"].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")

    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with proper headers"""
        url = f"{BACKEND_URL}{endpoint}"
        
        # Add session token if available
        if self.session_token and headers is None:
            headers = {"Authorization": f"Bearer {self.session_token}"}
        elif self.session_token and headers:
            headers["Authorization"] = f"Bearer {self.session_token}"
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            
            return response.status_code < 400, response
        except Exception as e:
            return False, str(e)

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("🔐 Setting up authentication...")
        # Use the test session token created in the database
        self.session_token = "5a7e5ca6-69c0-4434-ae3c-759ff027f1fd"
        print("ℹ️  Using valid test session token for calendar tests")

    def setup_test_data(self):
        """Create test contacts and accounts for CRM integration testing"""
        print("📋 Setting up test data for CRM integration...")
        
        # Create test contact
        contact_data = {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@techcorp.be",
            "phone": "+32 2 555 0123",
            "company": "TechCorp Belgium",
            "position": "Project Manager",
            "address": "Rue de la Science 14, 1040 Brussels, Belgium"
        }
        
        success, response = self.make_request("POST", "/contacts", data=contact_data)
        if success and response.status_code == 200:
            contact = response.json()
            self.created_entities["contacts"].append(contact["id"])
            self.test_contact_id = contact["id"]
            print(f"✅ Created test contact: {contact['name']}")
        else:
            print(f"❌ Failed to create test contact: {response.status_code if hasattr(response, 'status_code') else response}")
            return False

        # Create test account
        account_data = {
            "name": "TechCorp Belgium BVBA",
            "industry": "Technology Services",
            "website": "https://techcorp.be",
            "annual_revenue": 5000000.0,
            "employee_count": 120,
            "address": "Rue de la Science 14, 1040 Brussels, Belgium",
            "vat_number": "BE0987654321",
            "notes": "Major technology partner"
        }
        
        success, response = self.make_request("POST", "/accounts", data=account_data)
        if success and response.status_code == 200:
            account = response.json()
            self.created_entities["accounts"].append(account["id"])
            self.test_account_id = account["id"]
            print(f"✅ Created test account: {account['name']}")
        else:
            print(f"❌ Failed to create test account: {response.status_code if hasattr(response, 'status_code') else response}")
            return False
        
        return True

    def test_calendar_api_integration(self):
        """Test Calendar API Integration - frontend to backend connectivity"""
        print("\n📅 Testing Calendar API Integration...")
        
        # Test GET /calendar/events endpoint (used by frontend to load events)
        success, response = self.make_request("GET", "/calendar/events")
        if success and response.status_code == 200:
            events = response.json()
            self.log_result("calendar_api", "GET /calendar/events - Load calendar events", True)
        else:
            self.log_result("calendar_api", "GET /calendar/events - Load calendar events", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test GET /contacts endpoint (used by frontend for CRM integration)
        success, response = self.make_request("GET", "/contacts")
        if success and response.status_code == 200:
            self.log_result("calendar_api", "GET /contacts - Load contacts for CRM integration", True)
        else:
            self.log_result("calendar_api", "GET /contacts - Load contacts for CRM integration", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test GET /accounts endpoint (used by frontend for CRM integration)
        success, response = self.make_request("GET", "/accounts")
        if success and response.status_code == 200:
            self.log_result("calendar_api", "GET /accounts - Load accounts for CRM integration", True)
        else:
            self.log_result("calendar_api", "GET /accounts - Load accounts for CRM integration", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

    def test_event_crud_operations(self):
        """Test Event CRUD Operations through frontend workflow"""
        print("\n🔄 Testing Event CRUD Operations...")
        
        # Test CREATE event (simulating frontend form submission)
        start_date = datetime.now(timezone.utc) + timedelta(days=2)
        end_date = start_date + timedelta(hours=2)
        
        event_data = {
            "title": "Quarterly Business Review",
            "description": "Q4 business review meeting with TechCorp Belgium team",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "event_type": "meeting",
            "location": "Brussels Conference Center, Room A",
            "all_day": False,
            "reminder_minutes": 60
        }
        
        success, response = self.make_request("POST", "/calendar/events", data=event_data)
        if success and response.status_code == 200:
            event = response.json()
            self.created_entities["events"].append(event["id"])
            self.test_event_id = event["id"]
            self.log_result("event_crud", "POST /calendar/events - Create event via frontend", True)
        else:
            self.log_result("event_crud", "POST /calendar/events - Create event via frontend", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")
            return

        # Test READ specific event (simulating frontend event details view)
        success, response = self.make_request("GET", f"/calendar/events/{self.test_event_id}")
        if success and response.status_code == 200:
            event_details = response.json()
            # Verify event data integrity
            if (event_details["title"] == event_data["title"] and 
                event_details["event_type"] == event_data["event_type"]):
                self.log_result("event_crud", "GET /calendar/events/{id} - Read event details", True)
            else:
                self.log_result("event_crud", "GET /calendar/events/{id} - Read event details", False,
                              "Event data mismatch")
        else:
            self.log_result("event_crud", "GET /calendar/events/{id} - Read event details", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test UPDATE event (simulating frontend edit form)
        update_data = {
            "title": "Extended Quarterly Business Review",
            "description": "Extended Q4 business review meeting with TechCorp Belgium team - now 3 hours",
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(hours=3)).isoformat(),
            "event_type": "meeting",
            "location": "Brussels Conference Center, Room A & B",
            "all_day": False,
            "reminder_minutes": 90
        }
        
        success, response = self.make_request("PUT", f"/calendar/events/{self.test_event_id}", data=update_data)
        if success and response.status_code == 200:
            updated_event = response.json()
            if updated_event["title"] == update_data["title"]:
                self.log_result("event_crud", "PUT /calendar/events/{id} - Update event via frontend", True)
            else:
                self.log_result("event_crud", "PUT /calendar/events/{id} - Update event via frontend", False,
                              "Update data not reflected")
        else:
            self.log_result("event_crud", "PUT /calendar/events/{id} - Update event via frontend", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

    def test_event_types(self):
        """Test different event types functionality"""
        print("\n🏷️ Testing Event Types...")
        
        event_types = [
            {
                "type": "meeting",
                "title": "Client Strategy Meeting",
                "description": "Strategic planning session with key stakeholders"
            },
            {
                "type": "call",
                "title": "Follow-up Call with TechCorp",
                "description": "Phone call to discuss project progress"
            },
            {
                "type": "deadline",
                "title": "Project Milestone Deadline",
                "description": "Final deliverable due date"
            },
            {
                "type": "invoice_due",
                "title": "Invoice Payment Due - TechCorp",
                "description": "Payment due for Q4 services"
            }
        ]
        
        created_event_ids = []
        
        for event_type_data in event_types:
            start_date = datetime.now(timezone.utc) + timedelta(days=3, hours=len(created_event_ids))
            end_date = start_date + timedelta(hours=1)
            
            event_data = {
                "title": event_type_data["title"],
                "description": event_type_data["description"],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "event_type": event_type_data["type"],
                "location": "Various locations",
                "all_day": False,
                "reminder_minutes": 30
            }
            
            success, response = self.make_request("POST", "/calendar/events", data=event_data)
            if success and response.status_code == 200:
                event = response.json()
                created_event_ids.append(event["id"])
                self.created_entities["events"].append(event["id"])
                
                # Verify event type is correctly stored
                if event["event_type"] == event_type_data["type"]:
                    self.log_result("event_types", f"Create {event_type_data['type']} event", True)
                else:
                    self.log_result("event_types", f"Create {event_type_data['type']} event", False,
                                  f"Event type mismatch: expected {event_type_data['type']}, got {event['event_type']}")
            else:
                self.log_result("event_types", f"Create {event_type_data['type']} event", False,
                              f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test filtering events by type (simulating frontend calendar display logic)
        success, response = self.make_request("GET", "/calendar/events")
        if success and response.status_code == 200:
            all_events = response.json()
            event_types_found = set(event["event_type"] for event in all_events)
            expected_types = {"meeting", "call", "deadline", "invoice_due"}
            
            if expected_types.issubset(event_types_found):
                self.log_result("event_types", "All event types present in calendar", True)
            else:
                missing_types = expected_types - event_types_found
                self.log_result("event_types", "All event types present in calendar", False,
                              f"Missing event types: {missing_types}")
        else:
            self.log_result("event_types", "All event types present in calendar", False,
                          f"Failed to fetch events: {response.status_code if hasattr(response, 'status_code') else response}")

    def test_crm_integration(self):
        """Test CRM Integration - linking events to contacts and accounts"""
        print("\n🔗 Testing CRM Integration...")
        
        # Test event linked to contact
        start_date = datetime.now(timezone.utc) + timedelta(days=4)
        end_date = start_date + timedelta(hours=1)
        
        contact_event_data = {
            "title": "One-on-One with Sarah Johnson",
            "description": "Monthly check-in meeting with project manager",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "event_type": "meeting",
            "related_id": self.test_contact_id,
            "related_type": "contact",
            "location": "Office Meeting Room 3",
            "all_day": False,
            "reminder_minutes": 15
        }
        
        success, response = self.make_request("POST", "/calendar/events", data=contact_event_data)
        if success and response.status_code == 200:
            event = response.json()
            self.created_entities["events"].append(event["id"])
            
            # Verify CRM linking
            if (event["related_id"] == self.test_contact_id and 
                event["related_type"] == "contact"):
                self.log_result("crm_integration", "Link event to contact", True)
            else:
                self.log_result("crm_integration", "Link event to contact", False,
                              f"CRM link mismatch: expected contact {self.test_contact_id}, got {event.get('related_id')}")
        else:
            self.log_result("crm_integration", "Link event to contact", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test event linked to account
        start_date = datetime.now(timezone.utc) + timedelta(days=5)
        end_date = start_date + timedelta(hours=2)
        
        account_event_data = {
            "title": "TechCorp Account Review",
            "description": "Quarterly account review for TechCorp Belgium",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "event_type": "meeting",
            "related_id": self.test_account_id,
            "related_type": "account",
            "location": "TechCorp Offices, Brussels",
            "all_day": False,
            "reminder_minutes": 60
        }
        
        success, response = self.make_request("POST", "/calendar/events", data=account_event_data)
        if success and response.status_code == 200:
            event = response.json()
            self.created_entities["events"].append(event["id"])
            
            # Verify CRM linking
            if (event["related_id"] == self.test_account_id and 
                event["related_type"] == "account"):
                self.log_result("crm_integration", "Link event to account", True)
            else:
                self.log_result("crm_integration", "Link event to account", False,
                              f"CRM link mismatch: expected account {self.test_account_id}, got {event.get('related_id')}")
        else:
            self.log_result("crm_integration", "Link event to account", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test retrieving events with CRM relationships
        success, response = self.make_request("GET", "/calendar/events")
        if success and response.status_code == 200:
            events = response.json()
            crm_linked_events = [e for e in events if e.get("related_id") and e.get("related_type")]
            
            if len(crm_linked_events) >= 2:  # At least the two we just created
                self.log_result("crm_integration", "Retrieve CRM-linked events", True)
            else:
                self.log_result("crm_integration", "Retrieve CRM-linked events", False,
                              f"Expected at least 2 CRM-linked events, found {len(crm_linked_events)}")
        else:
            self.log_result("crm_integration", "Retrieve CRM-linked events", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

    def test_datetime_handling(self):
        """Test proper date/time handling and timezone support"""
        print("\n🕐 Testing Date/Time Handling...")
        
        # Test various datetime scenarios
        test_scenarios = [
            {
                "name": "All-day event",
                "start": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=6),
                "duration_hours": 24,
                "all_day": True
            },
            {
                "name": "Multi-day event",
                "start": datetime.now(timezone.utc) + timedelta(days=7),
                "duration_hours": 48,
                "all_day": False
            },
            {
                "name": "Short meeting",
                "start": datetime.now(timezone.utc) + timedelta(days=8, hours=2),
                "duration_hours": 0.5,
                "all_day": False
            },
            {
                "name": "Business hours event",
                "start": datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=9),
                "duration_hours": 8,
                "all_day": False
            }
        ]
        
        for scenario in test_scenarios:
            start_date = scenario["start"]
            end_date = start_date + timedelta(hours=scenario["duration_hours"])
            
            event_data = {
                "title": f"DateTime Test - {scenario['name']}",
                "description": f"Testing {scenario['name']} datetime handling",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "event_type": "meeting",
                "location": "Test Location",
                "all_day": scenario["all_day"],
                "reminder_minutes": 30
            }
            
            success, response = self.make_request("POST", "/calendar/events", data=event_data)
            if success and response.status_code == 200:
                event = response.json()
                self.created_entities["events"].append(event["id"])
                
                # Verify datetime preservation
                returned_start = datetime.fromisoformat(event["start_date"].replace('Z', '+00:00'))
                returned_end = datetime.fromisoformat(event["end_date"].replace('Z', '+00:00'))
                
                # Allow for small differences due to serialization
                start_diff = abs((returned_start - start_date).total_seconds())
                end_diff = abs((returned_end - end_date).total_seconds())
                
                if start_diff < 1 and end_diff < 1:  # Less than 1 second difference
                    self.log_result("datetime_handling", f"DateTime preservation - {scenario['name']}", True)
                else:
                    self.log_result("datetime_handling", f"DateTime preservation - {scenario['name']}", False,
                                  f"DateTime mismatch: start diff {start_diff}s, end diff {end_diff}s")
            else:
                self.log_result("datetime_handling", f"DateTime preservation - {scenario['name']}", False,
                              f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test timezone handling with ISO format
        utc_now = datetime.now(timezone.utc)
        iso_event_data = {
            "title": "ISO DateTime Format Test",
            "description": "Testing ISO datetime format handling",
            "start_date": utc_now.isoformat(),
            "end_date": (utc_now + timedelta(hours=1)).isoformat(),
            "event_type": "meeting",
            "location": "Timezone Test Location",
            "all_day": False,
            "reminder_minutes": 15
        }
        
        success, response = self.make_request("POST", "/calendar/events", data=iso_event_data)
        if success and response.status_code == 200:
            self.created_entities["events"].append(response.json()["id"])
            self.log_result("datetime_handling", "ISO datetime format support", True)
        else:
            self.log_result("datetime_handling", "ISO datetime format support", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

    def test_event_display(self):
        """Test event display and calendar functionality"""
        print("\n📊 Testing Event Display...")
        
        # Test retrieving all events for calendar display
        success, response = self.make_request("GET", "/calendar/events")
        if success and response.status_code == 200:
            events = response.json()
            
            # Verify event structure for frontend display
            required_fields = ["id", "title", "start_date", "end_date", "event_type"]
            display_ready = True
            
            for event in events:
                missing_fields = [field for field in required_fields if field not in event]
                if missing_fields:
                    display_ready = False
                    break
            
            if display_ready and len(events) > 0:
                self.log_result("event_display", "Events have required display fields", True)
            else:
                self.log_result("event_display", "Events have required display fields", False,
                              f"Missing fields or no events found")
        else:
            self.log_result("event_display", "Events have required display fields", False,
                          f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

        # Test event sorting by date (important for calendar display)
        if success and response.status_code == 200:
            events = response.json()
            if len(events) >= 2:
                # Check if events can be sorted by start_date
                try:
                    sorted_events = sorted(events, key=lambda x: datetime.fromisoformat(x["start_date"].replace('Z', '+00:00')))
                    self.log_result("event_display", "Events sortable by date for calendar display", True)
                except Exception as e:
                    self.log_result("event_display", "Events sortable by date for calendar display", False,
                                  f"Sorting error: {str(e)}")
            else:
                self.log_result("event_display", "Events sortable by date for calendar display", True)

        # Test event color coding by type (frontend calendar feature)
        event_type_colors = {
            "meeting": "blue",
            "call": "green", 
            "deadline": "orange",
            "invoice_due": "red"
        }
        
        if success and response.status_code == 200:
            events = response.json()
            color_mappable = True
            
            for event in events:
                if event.get("event_type") not in event_type_colors:
                    color_mappable = False
                    break
            
            if color_mappable:
                self.log_result("event_display", "Event types support color coding", True)
            else:
                self.log_result("event_display", "Event types support color coding", False,
                              "Unknown event types found")

    def test_event_deletion(self):
        """Test event deletion functionality"""
        print("\n🗑️ Testing Event Deletion...")
        
        # Delete one test event to verify deletion works
        if self.created_entities["events"]:
            event_id_to_delete = self.created_entities["events"][0]
            
            success, response = self.make_request("DELETE", f"/calendar/events/{event_id_to_delete}")
            if success and response.status_code == 200:
                self.log_result("event_crud", "DELETE /calendar/events/{id} - Delete event", True)
                self.created_entities["events"].remove(event_id_to_delete)
                
                # Verify event is actually deleted
                success, response = self.make_request("GET", f"/calendar/events/{event_id_to_delete}")
                if not success or response.status_code == 404:
                    self.log_result("event_crud", "Verify event deletion", True)
                else:
                    self.log_result("event_crud", "Verify event deletion", False,
                                  "Event still exists after deletion")
            else:
                self.log_result("event_crud", "DELETE /calendar/events/{id} - Delete event", False,
                              f"Status: {response.status_code if hasattr(response, 'status_code') else response}")

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created events
        for event_id in self.created_entities["events"]:
            success, response = self.make_request("DELETE", f"/calendar/events/{event_id}")
            if success and response.status_code == 200:
                print(f"✅ Deleted event {event_id}")
            else:
                print(f"❌ Failed to delete event {event_id}")

        # Delete created contacts
        for contact_id in self.created_entities["contacts"]:
            success, response = self.make_request("DELETE", f"/contacts/{contact_id}")
            if success and response.status_code == 200:
                print(f"✅ Deleted contact {contact_id}")
            else:
                print(f"❌ Failed to delete contact {contact_id}")

        # Delete created accounts
        for account_id in self.created_entities["accounts"]:
            success, response = self.make_request("DELETE", f"/accounts/{account_id}")
            if success and response.status_code == 200:
                print(f"✅ Deleted account {account_id}")
            else:
                print(f"❌ Failed to delete account {account_id}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("🎯 CALENDAR FUNCTIONALITY TEST SUMMARY")
        print("="*70)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            status = "✅" if failed == 0 else "❌"
            category_name = category.replace("_", " ").title()
            print(f"{status} {category_name}: {passed} passed, {failed} failed")
            
            if results["errors"]:
                for error in results["errors"]:
                    print(f"   ❌ {error}")
        
        print("-" * 70)
        print(f"TOTAL: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 All calendar functionality tests passed!")
            return True
        else:
            print(f"⚠️  {total_failed} calendar tests failed")
            return False

    def run_all_tests(self):
        """Run all calendar functionality tests"""
        print("🚀 Starting Calendar Functionality Tests...")
        print(f"Backend URL: {BACKEND_URL}")
        
        try:
            self.setup_authentication()
            
            if not self.setup_test_data():
                print("❌ Failed to setup test data, aborting tests")
                return False
            
            self.test_calendar_api_integration()
            self.test_event_crud_operations()
            self.test_event_types()
            self.test_crm_integration()
            self.test_datetime_handling()
            self.test_event_display()
            self.test_event_deletion()
            self.cleanup_test_data()
            
            return self.print_summary()
            
        except Exception as e:
            print(f"❌ Calendar test suite failed with error: {e}")
            return False

if __name__ == "__main__":
    tester = CalendarFunctionalityTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)