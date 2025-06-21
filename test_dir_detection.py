#!/usr/bin/env python3
"""Test script to verify directory change detection."""

import os
import subprocess
import tempfile
from pathlib import Path

def test_directory_change_detection():
    """Test the complete directory change detection flow."""
    
    # Create test directories
    test_dir_a = Path(tempfile.mkdtemp(prefix="test_dir_a_"))
    test_dir_b = Path(tempfile.mkdtemp(prefix="test_dir_b_"))
    
    try:
        print(f"Test dir A: {test_dir_a}")
        print(f"Test dir B: {test_dir_b}")
        
        # Step 1: Create session in directory A
        os.chdir(test_dir_a)
        print(f"\n1. In directory A: {os.getcwd()}")
        
        # Save a simple session with metadata
        from staffer.session import save_session_with_metadata
        from google.genai import types
        
        test_messages = [
            types.Content(role="user", parts=[types.Part(text="hello from dir A")])
        ]
        save_session_with_metadata(test_messages)
        print("Saved session with metadata")
        
        # Step 2: Load session and check directory
        from staffer.cli.interactive import load_session_with_metadata, check_directory_change
        
        messages, metadata = load_session_with_metadata()
        print(f"Loaded session metadata: {metadata}")
        print(f"Directory change detected: {check_directory_change(metadata)}")
        
        # Step 3: Change to directory B and check again
        os.chdir(test_dir_b)
        print(f"\n2. In directory B: {os.getcwd()}")
        
        messages, metadata = load_session_with_metadata()
        print(f"Directory change detected: {check_directory_change(metadata)}")
        
        if check_directory_change(metadata):
            print("✅ Directory change detection is working!")
            return True
        else:
            print("❌ Directory change detection failed")
            return False
            
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir_a, ignore_errors=True)
        shutil.rmtree(test_dir_b, ignore_errors=True)
        
        # Return to original directory
        os.chdir("/Users/spaceship/project/staffer-slice4")

if __name__ == "__main__":
    success = test_directory_change_detection()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")