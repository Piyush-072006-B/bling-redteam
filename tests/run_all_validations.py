import os
import sys
import subprocess

def create_evidence_dirs():
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs = [
        os.path.join(workspace_root, 'evidence'),
        os.path.join(workspace_root, 'evidence', 'graph_snapshots'),
        os.path.join(workspace_root, 'evidence', 'topology_diffs'),
        os.path.join(workspace_root, 'evidence', 'evasion_exports'),
        os.path.join(workspace_root, 'evidence', 'kafka_logs'),
        os.path.join(workspace_root, 'evidence', 'replay_runs'),
        os.path.join(workspace_root, 'evidence', 'demo_runs')
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
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if result.returncode == 0:
            print("SUCCESS: All validation tests passed.")
            print(f"Evidence has been captured in {os.path.join(workspace_root, 'evidence')}")
        else:
            print("FAILED: Some validation tests failed. Check the logs above.")
            
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
