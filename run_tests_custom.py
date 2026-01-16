
import pytest
import sys
import os

# เพิ่ม path ให้ import backend modules ได้
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class CustomReport:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.failed_tests = []

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.total += 1
            # ดึงชื่อฟังก์ชันเทส
            test_name = report.nodeid.split("::")[-1]
            
            if report.outcome == "passed":
                self.passed += 1
                print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {test_name:<40}")
            elif report.outcome == "failed":
                self.failed += 1
                self.failed_tests.append(test_name)
                print(f"{Colors.RED}[FAIL]   {Colors.RESET} {test_name:<40}")
            elif report.outcome == "skipped":
                print(f"{Colors.YELLOW}[SKIP]   {Colors.RESET} {test_name:<40}")

def run_tests():
    print("=" * 60)
    print(f"  {Colors.BOLD}{Colors.BLUE}Starting CryptoAI Automated Tests{Colors.RESET}")
    print("=" * 60)
    
    plugin = CustomReport()
    
    # รัน pytest พร้อมระบุ plugin ที่เราสร้าง
    # -p no:terminal ใช้ปิด output เดิมของ pytest
    pytest.main(["-q", "--disable-warnings", "backend/tests"], plugins=[plugin])
    
    print("\n" + "=" * 60)
    print(f"  {Colors.BOLD}Test Summary{Colors.RESET}")
    print("=" * 60)
    print(f"  Total verified: {plugin.total}")
    print(f"  {Colors.GREEN}Passed:         {plugin.passed}{Colors.RESET}")
    
    if plugin.failed > 0:
        print(f"  {Colors.RED}Failed:         {plugin.failed}{Colors.RESET}")
        print("\n  Failed Tests:")
        for t in plugin.failed_tests:
            print(f"   - {t}")
        sys.exit(1)
    else:
        print(f"  {Colors.RED}Failed:         0{Colors.RESET}")
        print(f"\n  {Colors.GREEN}All systems operational!{Colors.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
