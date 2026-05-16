import os
import sys
import subprocess

def create_evidence_dirs():
    dirs = [
        r'D:\bling-redteam\evidence',
        r'D:\bling-redteam\evidence\graph_snapshots',
        r'D:\bling-redteam\evidence\topology_diffs',
        r'D:\bling-redteam\evidence\evasion_exports',
        r'D:\bling-redteam\evidence\kafka_logs',
        r'D:\bling-redteam\evidence\replay_runs',
        r'D:\bling-redteam\evidence\demo_runs'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("Evidence directories ready.")

def main():
    print("=" * 60)
    print("BLING Adversarial Sandbox - Validation Framework")
    print("=" * 60)
    
    create_evidence_dirs()
    
    print("\nRunning test suite...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Run pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_dir, "-v", "--disable-warnings"],
            capture_output=False
        )
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("SUCCESS: All validation tests passed.")
            print("Evidence has been captured in D:\\bling-redteam\\evidence")
        else:
            print("FAILED: Some validation tests failed. Check the logs above.")
            
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
