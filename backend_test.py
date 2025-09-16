#!/usr/bin/env python3
"""
RIASEC Career Test Backend API Testing
Tests all backend endpoints for the Arabic RIASEC system
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List

import requests


class MockResponse:
    """Simple response object for offline testing."""

    def __init__(self, json_data: Any, status_code: int = 200):
        self._json = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data, ensure_ascii=False)

    def json(self) -> Any:
        return self._json

class RIASECAPITester:
    def __init__(
        self,
        base_url: str = "https://future-major-test.preview.emergentagent.com",
        offline: bool = False,
    ):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = "admin123"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.offline = offline

        if self.offline:
            self._init_offline_data()

    def _init_offline_data(self) -> None:
        """Initialize data used when running without network access."""
        axes = ["R", "I", "A", "S", "E", "C"]
        self._questions = [
            {
                "id": f"q{i}",
                "text_ar": f"سؤال {i}",
                "axis": axes[(i - 1) % 6],
                "is_active": True,
            }
            for i in range(1, 31)
        ]
        self._institutions = [
            {
                "id": "inst1",
                "name_ar": "جامعة بغداد",
                "city": "بغداد",
                "governorate": "بغداد",
                "type": "university",
            },
            {
                "id": "inst2",
                "name_ar": "جامعة البصرة",
                "city": "البصرة",
                "governorate": "البصرة",
                "type": "university",
            },
        ]
        self._majors = [
            {
                "id": "m1",
                "institution_id": "inst1",
                "college_name_ar": "كلية الهندسة",
                "major_name_ar": "هندسة ميكانيكية",
                "branch_eligibility": ["scientific"],
                "study_mode": "morning",
                "riasec_match": ["R", "I"],
            },
            {
                "id": "m2",
                "institution_id": "inst2",
                "college_name_ar": "كلية الفنون الجميلة",
                "major_name_ar": "التصميم",
                "branch_eligibility": ["arts", "literary"],
                "study_mode": "morning",
                "riasec_match": ["A"],
            },
        ]
        self._last_attempt: Dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # HTTP helpers
    def _get(self, path: str, **kwargs) -> MockResponse | requests.Response:
        if self.offline:
            return self._offline_get(path, **kwargs)
        return requests.get(f"{self.api_url}{path}", **kwargs)

    def _post(
        self, path: str, json: Any = None, **kwargs
    ) -> MockResponse | requests.Response:
        if self.offline:
            return self._offline_post(path, json=json, **kwargs)
        return requests.post(f"{self.api_url}{path}", json=json, **kwargs)

    # ------------------------------------------------------------------
    # Offline implementations
    def _offline_get(self, path: str, headers: Dict[str, str] | None = None, **_: Any) -> MockResponse:
        if path == "/":
            return MockResponse({"message": "RIASEC API running"})
        if path == "/questions":
            return MockResponse(self._questions)
        if path.startswith("/attempt/"):
            attempt_id = path.split("/")[-1]
            if self._last_attempt and self._last_attempt["id"] == attempt_id:
                return MockResponse(self._last_attempt)
            return MockResponse({"detail": "Not found"}, status_code=404)
        if path == "/admin/stats":
            auth = headers.get("Authorization") if headers else None
            if auth == f"Bearer {self.admin_token}":
                return MockResponse(
                    {
                        "total_attempts": 1,
                        "total_students": 1,
                        "branch_distribution": {"scientific": 1},
                        "popular_axes": {"R": 1},
                    }
                )
            return MockResponse({"detail": "Invalid admin token"}, status_code=401)
        if path == "/institutions":
            return MockResponse(self._institutions)
        if path.startswith("/majors"):
            if "branch=scientific" in path:
                filtered = [
                    m for m in self._majors if "scientific" in m["branch_eligibility"]
                ]
                return MockResponse(filtered)
            return MockResponse(self._majors)
        return MockResponse({}, status_code=404)

    def _offline_post(
        self, path: str, json: Any | None = None, **_: Any
    ) -> MockResponse:
        if path != "/attempt" or not json:
            return MockResponse({}, status_code=404)

        student = json.get("student", {})
        answers = json.get("answers", [])
        question_map = {q["id"]: q for q in self._questions}
        axis_scores: Dict[str, List[int]] = {a: [] for a in ["R", "I", "A", "S", "E", "C"]}
        for ans in answers:
            q = question_map.get(ans["question_id"])
            if q:
                axis_scores[q["axis"]].append(ans["value"])

        scores: Dict[str, float] = {}
        for axis, vals in axis_scores.items():
            if vals:
                avg = sum(vals) / len(vals)
                scores[axis] = round((avg - 1) / 4 * 100, 1)
            else:
                scores[axis] = 0.0

        top_axes = sorted(scores, key=scores.get, reverse=True)[:3]
        recommendations: List[Dict[str, str]] = []
        if "R" in top_axes[:2] and "I" in top_axes[:2]:
            recommendations.append(
                {"major": "هندسة ميكانيكية", "college": "كلية الهندسة"}
            )
        elif "A" in top_axes[:2]:
            recommendations.append(
                {"major": "التصميم", "college": "كلية الفنون الجميلة"}
            )
        else:
            recommendations.append(
                {"major": "إدارة الأعمال", "college": "كلية الإدارة والاقتصاد"}
            )

        attempt_result = {
            "id": "offline-attempt-1",
            "student": student,
            "scores": scores,
            "top_axes": top_axes,
            "recommendations": recommendations,
            "completed_at": datetime.utcnow().isoformat(),
        }
        self._last_attempt = attempt_result
        return MockResponse(attempt_result)

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = self._get("/", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "RIASEC" in data.get("message", ""):
                self.log_test("API Root", True)
                return True
            else:
                self.log_test("API Root", False, f"Status: {response.status_code}, Response: {data}")
                return False
        except Exception as e:
            self.log_test("API Root", False, str(e))
            return False

    def test_get_questions(self):
        """Test questions endpoint"""
        try:
            response = self._get("/questions", timeout=10)
            success = response.status_code == 200
            
            if success:
                questions = response.json()
                if isinstance(questions, list) and len(questions) >= 30:
                    # Check question structure
                    sample_question = questions[0]
                    required_fields = ['id', 'text_ar', 'axis', 'is_active']
                    
                    if all(field in sample_question for field in required_fields):
                        # Check RIASEC axes distribution
                        axes = [q['axis'] for q in questions]
                        riasec_axes = set(['R', 'I', 'A', 'S', 'E', 'C'])
                        found_axes = set(axes)
                        
                        if riasec_axes.issubset(found_axes):
                            self.log_test("Get Questions", True, f"Found {len(questions)} questions with all RIASEC axes")
                            return questions
                        else:
                            missing = riasec_axes - found_axes
                            self.log_test("Get Questions", False, f"Missing RIASEC axes: {missing}")
                    else:
                        missing_fields = [f for f in required_fields if f not in sample_question]
                        self.log_test("Get Questions", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Get Questions", False, f"Expected list of 30+ questions, got {len(questions) if isinstance(questions, list) else type(questions)}")
            else:
                self.log_test("Get Questions", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Questions", False, str(e))
        
        return None

    def test_submit_attempt(self, questions: List[Dict]):
        """Test submitting a complete test attempt"""
        if not questions:
            self.log_test("Submit Attempt", False, "No questions available")
            return None
            
        try:
            # Create test student data
            student_data = {
                "name": "طالب تجريبي",
                "branch": "scientific",
                "governorate": "بغداد",
                "phone": "07901234567",
                "email": "test@example.com"
            }
            
            # Create answers favoring R (Realistic) and I (Investigative) axes
            answers = []
            for question in questions:
                if question['axis'] in ['R', 'I']:
                    value = 5  # Strongly agree
                elif question['axis'] in ['A', 'S']:
                    value = 2  # Disagree
                else:  # E, C
                    value = 3  # Neutral
                    
                answers.append({
                    "question_id": question['id'],
                    "value": value
                })
            
            # Submit attempt
            attempt_data = {
                "student": student_data,
                "answers": answers
            }
            
            response = self._post("/attempt", json=attempt_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate result structure
                required_fields = ['id', 'student', 'scores', 'top_axes', 'recommendations', 'completed_at']
                if all(field in result for field in required_fields):
                    
                    # Check RIASEC scores
                    scores = result['scores']
                    if isinstance(scores, dict) and len(scores) == 6:
                        
                        # Check if R and I are indeed top scores (since we favored them)
                        top_axes = result['top_axes']
                        if 'R' in top_axes[:2] or 'I' in top_axes[:2]:
                            
                            # Check recommendations
                            recommendations = result['recommendations']
                            if isinstance(recommendations, list) and len(recommendations) > 0:
                                self.log_test("Submit Attempt", True, f"Got {len(recommendations)} recommendations, top axes: {top_axes[:3]}")
                                return result
                            else:
                                self.log_test("Submit Attempt", False, "No recommendations returned")
                        else:
                            self.log_test("Submit Attempt", False, f"Expected R/I in top axes, got: {top_axes}")
                    else:
                        self.log_test("Submit Attempt", False, f"Invalid scores structure: {scores}")
                else:
                    missing = [f for f in required_fields if f not in result]
                    self.log_test("Submit Attempt", False, f"Missing fields: {missing}")
            else:
                self.log_test("Submit Attempt", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Submit Attempt", False, str(e))
        
        return None

    def test_get_attempt(self, attempt_result: Dict):
        """Test retrieving attempt by ID"""
        if not attempt_result:
            self.log_test("Get Attempt", False, "No attempt result available")
            return
            
        try:
            attempt_id = attempt_result['id']
            response = self._get(f"/attempt/{attempt_id}", timeout=10)
            
            if response.status_code == 200:
                retrieved = response.json()
                if retrieved['id'] == attempt_id:
                    self.log_test("Get Attempt", True)
                else:
                    self.log_test("Get Attempt", False, "ID mismatch")
            else:
                self.log_test("Get Attempt", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Attempt", False, str(e))

    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self._get("/admin/stats", headers=headers, timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                required_fields = ['total_attempts', 'total_students', 'branch_distribution', 'popular_axes']
                
                if all(field in stats for field in required_fields):
                    self.log_test("Admin Stats", True, f"Attempts: {stats['total_attempts']}, Students: {stats['total_students']}")
                else:
                    missing = [f for f in required_fields if f not in stats]
                    self.log_test("Admin Stats", False, f"Missing fields: {missing}")
            else:
                self.log_test("Admin Stats", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Stats", False, str(e))

    def test_admin_auth_failure(self):
        """Test admin authentication failure"""
        try:
            headers = {"Authorization": "Bearer wrong_token"}
            response = self._get("/admin/stats", headers=headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Admin Auth Failure", True, "Correctly rejected invalid token")
            else:
                self.log_test("Admin Auth Failure", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Auth Failure", False, str(e))

    def test_institutions(self):
        """Test institutions endpoint"""
        try:
            response = self._get("/institutions", timeout=10)
            
            if response.status_code == 200:
                institutions = response.json()
                if isinstance(institutions, list) and len(institutions) > 0:
                    sample = institutions[0]
                    required_fields = ['id', 'name_ar', 'city', 'governorate', 'type']
                    
                    if all(field in sample for field in required_fields):
                        self.log_test("Get Institutions", True, f"Found {len(institutions)} institutions")
                    else:
                        missing = [f for f in required_fields if f not in sample]
                        self.log_test("Get Institutions", False, f"Missing fields: {missing}")
                else:
                    self.log_test("Get Institutions", False, "No institutions returned")
            else:
                self.log_test("Get Institutions", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Institutions", False, str(e))

    def test_majors(self):
        """Test majors endpoint with filtering"""
        try:
            # Test basic majors endpoint
            response = self._get("/majors", timeout=10)
            
            if response.status_code == 200:
                majors = response.json()
                if isinstance(majors, list) and len(majors) > 0:
                    sample = majors[0]
                    required_fields = ['id', 'institution_id', 'college_name_ar', 'major_name_ar', 'branch_eligibility', 'study_mode', 'riasec_match']
                    
                    if all(field in sample for field in required_fields):
                        self.log_test("Get Majors", True, f"Found {len(majors)} majors")
                        
                        # Test filtering by branch
                        response_filtered = self._get("/majors?branch=scientific", timeout=10)
                        if response_filtered.status_code == 200:
                            filtered_majors = response_filtered.json()
                            self.log_test("Filter Majors by Branch", True, f"Scientific majors: {len(filtered_majors)}")
                        else:
                            self.log_test("Filter Majors by Branch", False, f"Status: {response_filtered.status_code}")
                            
                    else:
                        missing = [f for f in required_fields if f not in sample]
                        self.log_test("Get Majors", False, f"Missing fields: {missing}")
                else:
                    self.log_test("Get Majors", False, "No majors returned")
            else:
                self.log_test("Get Majors", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Majors", False, str(e))

    def test_scenario_scientific_student(self):
        """Test scenario: Scientific student with R-I preferences should get engineering recommendations"""
        questions = self.test_get_questions()
        if not questions:
            return
            
        try:
            student_data = {
                "name": "طالب علمي",
                "branch": "scientific",
                "governorate": "بغداد"
            }
            
            # Create answers strongly favoring R (Realistic) and I (Investigative)
            answers = []
            for question in questions:
                if question['axis'] in ['R', 'I']:
                    value = 5  # Strongly agree
                elif question['axis'] in ['A', 'S', 'E']:
                    value = 1  # Strongly disagree
                else:  # C
                    value = 2  # Disagree
                    
                answers.append({
                    "question_id": question['id'],
                    "value": value
                })
            
            attempt_data = {
                "student": student_data,
                "answers": answers
            }
            
            response = self._post("/attempt", json=attempt_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                top_axes = result['top_axes']
                recommendations = result['recommendations']
                
                # Check if R and I are top axes
                if 'R' in top_axes[:2] and 'I' in top_axes[:2]:
                    # Check if engineering majors are recommended
                    engineering_found = any('هندسة' in rec.get('major', '') or 'هندسة' in rec.get('college', '') 
                                          for rec in recommendations)
                    
                    if engineering_found:
                        self.log_test("Scientific Student R-I Scenario", True, f"Top axes: {top_axes[:3]}, Found engineering recommendations")
                    else:
                        self.log_test("Scientific Student R-I Scenario", False, "No engineering recommendations found")
                else:
                    self.log_test("Scientific Student R-I Scenario", False, f"Expected R-I top axes, got: {top_axes[:3]}")
            else:
                self.log_test("Scientific Student R-I Scenario", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Scientific Student R-I Scenario", False, str(e))

    def test_scenario_literary_student(self):
        """Test scenario: Literary student with A preferences should get arts/media recommendations"""
        questions = self.test_get_questions()
        if not questions:
            return
            
        try:
            student_data = {
                "name": "طالب أدبي",
                "branch": "literary",
                "governorate": "البصرة"
            }
            
            # Create answers strongly favoring A (Artistic)
            answers = []
            for question in questions:
                if question['axis'] == 'A':
                    value = 5  # Strongly agree
                elif question['axis'] in ['S', 'E']:
                    value = 4  # Agree
                else:  # R, I, C
                    value = 2  # Disagree
                    
                answers.append({
                    "question_id": question['id'],
                    "value": value
                })
            
            attempt_data = {
                "student": student_data,
                "answers": answers
            }
            
            response = self._post("/attempt", json=attempt_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                top_axes = result['top_axes']
                recommendations = result['recommendations']
                
                # Check if A is top axis
                if 'A' in top_axes[:2]:
                    # Check if arts/media majors are recommended
                    arts_found = any(any(keyword in rec.get('major', '') or keyword in rec.get('college', '') 
                                        for keyword in ['فن', 'إعلام', 'تصميم', 'آداب'])
                                   for rec in recommendations)
                    
                    if arts_found:
                        self.log_test("Literary Student A Scenario", True, f"Top axes: {top_axes[:3]}, Found arts/media recommendations")
                    else:
                        self.log_test("Literary Student A Scenario", False, "No arts/media recommendations found")
                else:
                    self.log_test("Literary Student A Scenario", False, f"Expected A in top axes, got: {top_axes[:3]}")
            else:
                self.log_test("Literary Student A Scenario", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Literary Student A Scenario", False, str(e))

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting RIASEC Backend API Tests")
        print(f"🌐 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Basic API tests
        if not self.test_api_root():
            print("❌ API Root failed - stopping tests")
            return False
            
        questions = self.test_get_questions()
        if questions:
            attempt_result = self.test_submit_attempt(questions)
            if attempt_result:
                self.test_get_attempt(attempt_result)
        
        # Admin tests
        self.test_admin_stats()
        self.test_admin_auth_failure()
        
        # Data endpoints
        self.test_institutions()
        self.test_majors()
        
        # Scenario tests
        self.test_scenario_scientific_student()
        self.test_scenario_literary_student()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests PASSED!")
            return True
        else:
            failed_tests = [t for t in self.test_results if not t['success']]
            print(f"❌ {len(failed_tests)} tests FAILED:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
            return False

def main() -> int:
    parser = argparse.ArgumentParser(description="RIASEC backend tests")
    parser.add_argument(
        "--base-url",
        default="https://future-major-test.preview.emergentagent.com",
        help="Base URL of the API",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run tests without network access using mock responses",
    )
    args = parser.parse_args()

    tester = RIASECAPITester(base_url=args.base_url, offline=args.offline)
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
