import subprocess
import sys
import os

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read().splitlines()
        
        print("[INFO] Checking dependencies...")
        missing_packages = []
        
        for req in requirements:
            if "==" in req:
                package = req.split("==")[0]
            else:
                package = req
                
            try:
                __import__(package.replace("[standard]", ""))
            except ImportError:
                missing_packages.append(req)
        
        if missing_packages:
            print(f"[WARNING] Missing dependencies: {', '.join(missing_packages)}")
            install = input("Do you want to install them now? (y/n): ")
            if install.lower() == "y":
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print("[SUCCESS] Dependencies installed successfully!")
            else:
                print("[ERROR] Cannot run the application without required dependencies.")
                return False
        else:
            print("[SUCCESS] All dependencies are installed!")

        
        return True
    except Exception as e:
        print(f"[ERROR] Error checking dependencies: {str(e)}")
        return False

def run_app():
    """Run the AIS Marine Traffic Analyzer application."""
    if check_dependencies():
        print("\n[INFO] Starting AIS Marine Traffic Analyzer...")
        try:
            subprocess.run([sys.executable, "run.py"], check=True)
        except KeyboardInterrupt:
            print("\n[INFO] Application stopped by user.")
        except Exception as e:
            print(f"\n[ERROR] Error running application: {str(e)}")

if __name__ == "__main__":
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    run_app()