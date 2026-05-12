import subprocess
import tempfile
import os


async def execute_code(python_code: str) -> str:
    """
    Execute Python code safely with a timeout.
    
    Args:
        python_code: The Python code to execute
    
    Returns:
        The output (stdout and stderr) from executing the code
    """
    try:
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(python_code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the code with a timeout
            result = subprocess.run(
                ['python3', temp_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Combine stdout and stderr
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"\nReturn code: {result.returncode}"
            
            return output if output else "Code executed successfully with no output."
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 10 seconds."
    except Exception as e:
        return f"Error executing code: {str(e)}"
