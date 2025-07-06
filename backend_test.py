import requests
import json
from datetime import datetime
import locale
import sys
import time

# Set locale to Indonesian for date formatting verification
try:
    locale.setlocale(locale.LC_TIME, 'id_ID.utf8')
except locale.Error:
    print("Indonesian locale not available, using default locale")

# Get the backend URL from frontend/.env
BACKEND_URL = "https://a639fdcf-b672-498a-aebb-44ec6a64c1f6.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

    def log_test(self, test_name, passed, message=""):
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {test_name}: {message}")
        self.test_results["tests"].append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1

    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        url = f"{API_URL}/login"
        data = {"username": "admin", "password": "admin"}
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            response_data = response.json()
            if "token" in response_data and response_data["token"] == "admin_session_token":
                self.admin_token = response_data["token"]
                self.log_test("Admin Login Success", True, "Successfully logged in as admin")
                return True
            else:
                self.log_test("Admin Login Success", False, f"Token not found or incorrect: {response_data}")
        else:
            self.log_test("Admin Login Success", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def test_admin_login_failure(self):
        """Test admin login with incorrect credentials"""
        url = f"{API_URL}/login"
        data = {"username": "wrong", "password": "wrong"}
        response = requests.post(url, json=data)
        
        if response.status_code == 401:
            self.log_test("Admin Login Failure", True, "Correctly rejected invalid credentials")
            return True
        else:
            self.log_test("Admin Login Failure", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def test_get_transactions_empty(self):
        """Test getting transactions when database is empty"""
        url = f"{API_URL}/transactions"
        response = requests.get(url)
        
        if response.status_code == 200:
            transactions = response.json()
            if isinstance(transactions, list):
                self.log_test("Get Transactions (Empty)", True, f"Successfully retrieved transactions: {len(transactions)} found")
                return True
            else:
                self.log_test("Get Transactions (Empty)", False, f"Response is not a list: {transactions}")
        else:
            self.log_test("Get Transactions (Empty)", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def test_create_transaction(self):
        """Test creating a new transaction"""
        if not self.admin_token:
            self.log_test("Create Transaction", False, "Admin token not available, login first")
            return False
        
        url = f"{API_URL}/transactions"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test with Indonesian transaction data
        data = {
            "tanggal": datetime.now().isoformat(),
            "keterangan": "Iuran kas Budi",
            "jenis": "pemasukan",
            "jumlah": 50000
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            transaction = response.json()
            if "id" in transaction and transaction["keterangan"] == "Iuran kas Budi":
                self.log_test("Create Transaction (Pemasukan)", True, f"Successfully created transaction: {transaction['id']}")
                
                # Create a pengeluaran transaction
                data = {
                    "tanggal": datetime.now().isoformat(),
                    "keterangan": "Pembelian shuttlecock",
                    "jenis": "pengeluaran",
                    "jumlah": 75000
                }
                
                response = requests.post(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    transaction = response.json()
                    if "id" in transaction and transaction["keterangan"] == "Pembelian shuttlecock":
                        self.log_test("Create Transaction (Pengeluaran)", True, f"Successfully created transaction: {transaction['id']}")
                        
                        # Create one more pengeluaran transaction
                        data = {
                            "tanggal": datetime.now().isoformat(),
                            "keterangan": "Sewa lapangan GOR",
                            "jenis": "pengeluaran",
                            "jumlah": 200000
                        }
                        
                        response = requests.post(url, json=data, headers=headers)
                        
                        if response.status_code == 200:
                            transaction = response.json()
                            if "id" in transaction and transaction["keterangan"] == "Sewa lapangan GOR":
                                self.log_test("Create Transaction (Pengeluaran 2)", True, f"Successfully created transaction: {transaction['id']}")
                                return True
                
                self.log_test("Create Multiple Transactions", False, "Failed to create all test transactions")
                return False
            else:
                self.log_test("Create Transaction", False, f"Transaction data incorrect: {transaction}")
        else:
            self.log_test("Create Transaction", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def test_get_transactions_with_data(self):
        """Test getting transactions after adding data"""
        url = f"{API_URL}/transactions"
        response = requests.get(url)
        
        if response.status_code == 200:
            transactions = response.json()
            if isinstance(transactions, list) and len(transactions) >= 3:
                # Check date formatting - accept either English or Indonesian month names
                date_format_correct = True
                for transaction in transactions:
                    # Check if date has a valid format (day month year)
                    date_parts = transaction["tanggal"].split()
                    if len(date_parts) != 3:
                        date_format_correct = False
                        break
                    
                    # Check if first part is a day (1-31)
                    try:
                        day = int(date_parts[0])
                        if day < 1 or day > 31:
                            date_format_correct = False
                            break
                    except ValueError:
                        date_format_correct = False
                        break
                    
                    # Check if last part is a year (4 digits)
                    try:
                        year = int(date_parts[2])
                        if year < 2000 or year > 2100:  # Reasonable year range
                            date_format_correct = False
                            break
                    except ValueError:
                        date_format_correct = False
                        break
                
                if date_format_correct:
                    self.log_test("Get Transactions (With Data)", True, f"Successfully retrieved {len(transactions)} transactions with proper date format: {transactions[0]['tanggal']}")
                    return True
                else:
                    self.log_test("Get Transactions (With Data)", False, f"Date format is not valid: {transactions[0]['tanggal']}")
            else:
                self.log_test("Get Transactions (With Data)", False, f"Expected at least 3 transactions, got: {len(transactions)}")
        else:
            self.log_test("Get Transactions (With Data)", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def test_get_summary(self):
        """Test getting financial summary"""
        url = f"{API_URL}/summary"
        response = requests.get(url)
        
        if response.status_code == 200:
            summary = response.json()
            if "total_pemasukan" in summary and "total_pengeluaran" in summary and "saldo" in summary:
                # Verify calculations
                expected_pemasukan = 50000  # From our test data
                expected_pengeluaran = 75000 + 200000  # From our test data
                expected_saldo = expected_pemasukan - expected_pengeluaran
                
                calculations_correct = (
                    abs(summary["total_pemasukan"] - expected_pemasukan) < 0.01 and
                    abs(summary["total_pengeluaran"] - expected_pengeluaran) < 0.01 and
                    abs(summary["saldo"] - expected_saldo) < 0.01
                )
                
                if calculations_correct:
                    self.log_test("Get Summary", True, f"Successfully retrieved summary with correct calculations: {summary}")
                    return True
                else:
                    self.log_test("Get Summary", False, f"Calculations incorrect. Expected: pemasukan={expected_pemasukan}, pengeluaran={expected_pengeluaran}, saldo={expected_saldo}. Got: {summary}")
            else:
                self.log_test("Get Summary", False, f"Summary data incomplete: {summary}")
        else:
            self.log_test("Get Summary", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def test_unauthorized_transaction_creation(self):
        """Test creating a transaction without authentication"""
        url = f"{API_URL}/transactions"
        data = {
            "tanggal": datetime.now().isoformat(),
            "keterangan": "Unauthorized transaction",
            "jenis": "pemasukan",
            "jumlah": 10000
        }
        
        # No authorization header
        response = requests.post(url, json=data)
        
        if response.status_code == 401 or response.status_code == 403:
            self.log_test("Unauthorized Transaction Creation", True, "Correctly rejected unauthorized transaction creation")
            return True
        else:
            self.log_test("Unauthorized Transaction Creation", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n===== Starting Backend API Tests =====\n")
        
        # Test admin authentication
        self.test_admin_login_success()
        self.test_admin_login_failure()
        
        # Test transactions API
        self.test_get_transactions_empty()
        self.test_create_transaction()
        self.test_get_transactions_with_data()
        self.test_get_summary()
        
        # Test authentication protection
        self.test_unauthorized_transaction_creation()
        
        # Print summary
        print("\n===== Test Summary =====")
        print(f"Total tests: {self.test_results['passed'] + self.test_results['failed']}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print("========================\n")
        
        return self.test_results["failed"] == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)