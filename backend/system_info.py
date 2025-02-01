import platform
import os
import sys
import traceback

def print_system_info():
    try:
        # Python and Platform Details
        print("Python Version:", sys.version)
        print("Platform Details:", platform.platform())
        print("Operating System:", platform.system())
        print("OS Release:", platform.release())
        print("Machine Architecture:", platform.machine())
        
        # Linux-specific information
        if platform.system() == 'Linux':
            try:
                with open('/etc/os-release', 'r') as f:
                    print("\nOS Release Information:")
                    print(f.read())
            except FileNotFoundError:
                print("Could not read /etc/os-release")
        
        # Environment variables
        print("\nKey Environment Variables:")
        print("HOME:", os.environ.get('HOME'))
        print("PATH:", os.environ.get('PATH'))
        
        # Python path and installed packages
        print("\nPython Path:")
        print(sys.path)
        
        # Installed packages
        try:
            import pkg_resources
            print("\nInstalled Packages:")
            for package in sorted(pkg_resources.working_set, key=lambda x: x.key):
                print(f"{package.key}=={package.version}")
        except Exception as e:
            print(f"Could not list packages: {e}")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print_system_info()
