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
                # Verify that the saldo is correctly calculated from pemasukan and pengeluaran
                calculated_saldo = summary["total_pemasukan"] - summary["total_pengeluaran"]
                saldo_correct = abs(summary["saldo"] - calculated_saldo) < 0.01
                
                if saldo_correct:
                    self.log_test("Get Summary", True, f"Successfully retrieved summary with correct saldo calculation: {summary}")
                    return True
                else:
                    self.log_test("Get Summary", False, f"Saldo calculation incorrect. Expected saldo: {calculated_saldo}, Got: {summary['saldo']}")
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
        
    def test_delete_transaction_success(self):
        """Test deleting a transaction with valid admin token"""
        if not self.admin_token:
            self.log_test("Delete Transaction Success", False, "Admin token not available, login first")
            return False
            
        # First, get all transactions to find one to delete
        url = f"{API_URL}/transactions"
        response = requests.get(url)
        
        if response.status_code != 200 or not response.json():
            self.log_test("Delete Transaction Success", False, "No transactions available to delete")
            return False
            
        # Get the first transaction ID
        transaction_id = response.json()[0]["id"]
        
        # Now delete the transaction
        delete_url = f"{API_URL}/transactions/{transaction_id}"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.delete(delete_url, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            if "message" in response_data and "berhasil dihapus" in response_data["message"]:
                self.log_test("Delete Transaction Success", True, f"Successfully deleted transaction: {transaction_id}")
                return True
            else:
                self.log_test("Delete Transaction Success", False, f"Unexpected response message: {response_data}")
        else:
            self.log_test("Delete Transaction Success", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False
        
    def test_delete_transaction_unauthorized(self):
        """Test deleting a transaction without authentication"""
        # First, get all transactions to find one to delete
        url = f"{API_URL}/transactions"
        response = requests.get(url)
        
        if response.status_code != 200 or not response.json():
            self.log_test("Delete Transaction Unauthorized", False, "No transactions available to test with")
            return False
            
        # Get the first transaction ID
        transaction_id = response.json()[0]["id"]
        
        # Try to delete without authentication
        delete_url = f"{API_URL}/transactions/{transaction_id}"
        response = requests.delete(delete_url)
        
        if response.status_code == 401 or response.status_code == 403:
            self.log_test("Delete Transaction Unauthorized", True, "Correctly rejected unauthorized transaction deletion")
            return True
        else:
            self.log_test("Delete Transaction Unauthorized", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False
        
    def test_delete_transaction_invalid_id(self):
        """Test deleting a transaction with an invalid ID"""
        if not self.admin_token:
            self.log_test("Delete Transaction Invalid ID", False, "Admin token not available, login first")
            return False
            
        # Use a random UUID that doesn't exist
        invalid_id = "00000000-0000-0000-0000-000000000000"
        
        delete_url = f"{API_URL}/transactions/{invalid_id}"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.delete(delete_url, headers=headers)
        
        if response.status_code == 404:
            self.log_test("Delete Transaction Invalid ID", True, "Correctly returned 404 for non-existent transaction")
            return True
        else:
            self.log_test("Delete Transaction Invalid ID", False, f"Status code: {response.status_code}, Response: {response.text}")
        
        return False
        
    def test_data_consistency_after_deletion(self):
        """Test data consistency after deleting a transaction"""
        if not self.admin_token:
            self.log_test("Data Consistency After Deletion", False, "Admin token not available, login first")
            return False
            
        # First, get all transactions and the current summary
        transactions_url = f"{API_URL}/transactions"
        summary_url = f"{API_URL}/summary"
        
        transactions_response = requests.get(transactions_url)
        summary_response = requests.get(summary_url)
        
        if transactions_response.status_code != 200 or summary_response.status_code != 200:
            self.log_test("Data Consistency After Deletion", False, "Failed to get initial transactions or summary")
            return False
            
        initial_transactions = transactions_response.json()
        initial_summary = summary_response.json()
        
        if not initial_transactions:
            self.log_test("Data Consistency After Deletion", False, "No transactions available to delete")
            return False
            
        # Get the first transaction to delete
        transaction_to_delete = initial_transactions[0]
        transaction_id = transaction_to_delete["id"]
        
        # Calculate expected summary after deletion
        expected_pemasukan = initial_summary["total_pemasukan"]
        expected_pengeluaran = initial_summary["total_pengeluaran"]
        
        if transaction_to_delete["jenis"] == "pemasukan":
            expected_pemasukan -= transaction_to_delete["jumlah"]
        else:  # pengeluaran
            expected_pengeluaran -= transaction_to_delete["jumlah"]
            
        expected_saldo = expected_pemasukan - expected_pengeluaran
        
        # Delete the transaction
        delete_url = f"{API_URL}/transactions/{transaction_id}"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        delete_response = requests.delete(delete_url, headers=headers)
        
        if delete_response.status_code != 200:
            self.log_test("Data Consistency After Deletion", False, f"Failed to delete transaction: {delete_response.text}")
            return False
            
        # Get updated transactions and summary
        updated_transactions_response = requests.get(transactions_url)
        updated_summary_response = requests.get(summary_url)
        
        if updated_transactions_response.status_code != 200 or updated_summary_response.status_code != 200:
            self.log_test("Data Consistency After Deletion", False, "Failed to get updated transactions or summary")
            return False
            
        updated_transactions = updated_transactions_response.json()
        updated_summary = updated_summary_response.json()
        
        # Verify transaction count decreased by 1
        if len(updated_transactions) != len(initial_transactions) - 1:
            self.log_test("Data Consistency After Deletion", False, 
                          f"Expected {len(initial_transactions) - 1} transactions after deletion, got {len(updated_transactions)}")
            return False
            
        # Verify deleted transaction is not in the list
        for transaction in updated_transactions:
            if transaction["id"] == transaction_id:
                self.log_test("Data Consistency After Deletion", False, "Deleted transaction still appears in transaction list")
                return False
                
        # Verify summary is updated correctly (with small tolerance for floating point)
        pemasukan_correct = abs(updated_summary["total_pemasukan"] - expected_pemasukan) < 0.01
        pengeluaran_correct = abs(updated_summary["total_pengeluaran"] - expected_pengeluaran) < 0.01
        saldo_correct = abs(updated_summary["saldo"] - expected_saldo) < 0.01
        
        if pemasukan_correct and pengeluaran_correct and saldo_correct:
            self.log_test("Data Consistency After Deletion", True, 
                          f"Data is consistent after deletion. New summary: {updated_summary}")
            return True
        else:
            self.log_test("Data Consistency After Deletion", False, 
                          f"Summary inconsistent after deletion. Expected: {expected_pemasukan}/{expected_pengeluaran}/{expected_saldo}, " +
                          f"Got: {updated_summary['total_pemasukan']}/{updated_summary['total_pengeluaran']}/{updated_summary['saldo']}")
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
        
        # Test DELETE transaction endpoint
        self.test_delete_transaction_unauthorized()
        self.test_delete_transaction_invalid_id()
        self.test_delete_transaction_success()
        self.test_data_consistency_after_deletion()
        
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