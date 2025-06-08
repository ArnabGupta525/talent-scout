import os
import toml
from pathlib import Path

def convert_env_to_toml(env_file_path='.env', output_file='config.toml'):
    """
    Convert .env file to TOML format
    """
    if not os.path.exists(env_file_path):
        print(f"Error: {env_file_path} not found")
        return
    
    config = {}
    
    with open(env_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Split on first '=' only
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Convert boolean strings
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                
                # Try to convert to integer
                elif value.isdigit():
                    value = int(value)
                
                # Convert key to lowercase for TOML convention
                config[key.lower()] = value
    
    # Write to TOML file
    with open(output_file, 'w') as file:
        toml.dump(config, file)
    
    print(f"Successfully converted {env_file_path} to {output_file}")

def convert_env_to_streamlit_secrets(env_file_path='.env'):
    """
    Convert .env file to Streamlit secrets.toml format
    """
    if not os.path.exists(env_file_path):
        print(f"Error: {env_file_path} not found")
        return
    
    # Create .streamlit directory if it doesn't exist
    Path('.streamlit').mkdir(exist_ok=True)
    
    config = {}
    
    with open(env_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Convert boolean strings
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                
                # Try to convert to integer
                elif value.isdigit():
                    value = int(value)
                
                config[key] = value
    
    # Write to Streamlit secrets file
    output_file = '.streamlit/secrets.toml'
    with open(output_file, 'w') as file:
        toml.dump(config, file)
    
    print(f"Successfully created {output_file}")
    print("Remember to add .streamlit/secrets.toml to your .gitignore file!")

if __name__ == "__main__":
    # Install required package first: pip install toml
    
    print("Choose conversion type:")
    print("1. Convert .env to config.toml")
    print("2. Convert .env to Streamlit secrets.toml")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        convert_env_to_toml()
    elif choice == '2':
        convert_env_to_streamlit_secrets()
    else:
        print("Invalid choice")