#!/usr/bin/env python3
"""
Test script for Anthropic client initialization
"""

import os
import importlib
import sys
import inspect

# Try importing anthropic
try:
    import anthropic
    print(f"Anthropic module is installed at: {anthropic.__file__}")
    print(f"Anthropic version: {getattr(anthropic, '__version__', 'Unknown')}")
except ImportError as e:
    print(f"Error importing anthropic: {e}")
    sys.exit(1)

# Inspect available classes in anthropic
print("\nClasses in anthropic module:")
for name, obj in inspect.getmembers(anthropic, inspect.isclass):
    print(f"- {name}")

# Inspect Client class if it exists
if hasattr(anthropic, 'Client'):
    client_class = anthropic.Client
    print("\nClient.__init__ signature:")
    print(inspect.signature(client_class.__init__))
    
    print("\nClient.__init__ parameters:")
    for param_name, param in inspect.signature(client_class.__init__).parameters.items():
        if param_name != 'self':
            print(f"- {param_name}: {param.default if param.default is not inspect.Parameter.empty else 'Required'}")

# Inspect Anthropic class if it exists
if hasattr(anthropic, 'Anthropic'):
    anthropic_class = anthropic.Anthropic
    print("\nAnthropic.__init__ signature:")
    print(inspect.signature(anthropic_class.__init__))
    
    print("\nAnthropic.__init__ parameters:")
    for param_name, param in inspect.signature(anthropic_class.__init__).parameters.items():
        if param_name != 'self':
            print(f"- {param_name}: {param.default if param.default is not inspect.Parameter.empty else 'Required'}")

# Try creating a client
print("\nAttempting to create client:")
api_key = os.environ.get('ANTHROPIC_API_KEY', 'dummy-api-key-for-testing')

try:
    print("Method 1: Using 'Anthropic' class with api_key only")
    if hasattr(anthropic, 'Anthropic'):
        client = anthropic.Anthropic(api_key=api_key)
        print("Success!")
    else:
        print("'Anthropic' class not available")
except Exception as e:
    print(f"Error: {e}")

try:
    print("\nMethod 2: Using 'Client' class with api_key only")
    if hasattr(anthropic, 'Client'):
        client = anthropic.Client(api_key=api_key)
        print("Success!")
    else:
        print("'Client' class not available")
except Exception as e:
    print(f"Error: {e}")

try:
    # Try creating client with more specific parameter format
    print("\nMethod 3: Using raw class instantiation without __init__")
    if hasattr(anthropic, 'Client'):
        client_class = anthropic.Client
        client = object.__new__(client_class)
        print("Object created, attempting to set attributes directly")
        client._api_key = api_key
        print("Success creating raw object and setting _api_key!")
    else:
        print("'Client' class not available")
except Exception as e:
    print(f"Error: {e}")

print("\nTest completed")