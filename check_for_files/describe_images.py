import os
import json
from datetime import datetime
import requests
import base64

class ImageDescriber:
    def __init__(self, verbose=False):
        self.verbose = verbose
        
        self.ollama_url = os.environ.get("OLLAMA_URL")
        if not self.ollama_url:
            self.ollama_url = "http://localhost:11434/api/generate"
            
        self.image_description_model = os.environ.get("IMAGE_DESCRIPTION_MODEL")
        if not self.image_description_model:
            self.image_description_model = "gemma3:4b"
            
        self.image_description_language = os.environ.get("IMAGE_DESCRIPTION_LANGUAGE")
        if not self.image_description_language:
            self.image_description_language = "english"
    
    def image_to_description(self, image_path: str) -> str:
        """
        Sends an image to Ollama for description.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            tuple: (file_name, success_boolean) - file_name is path to description file or error message
        """
        try:
            # Convert Windows path to raw string and normalize
            image_path = os.path.abspath(image_path).replace('\\', '/')
            if self.verbose: print(f"Using image path: {image_path}")

            # Verify that the image exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Verify file size and readability
            file_size = os.path.getsize(image_path)
            
            if file_size == 0:
                raise ValueError("Image file is empty")
                
            # Create the prompt based on the requested language
            prompt = f"Please describe this image in {self.image_description_language}. Describe what you see in detail. Be verbose and provide specific details. Do not use any abbreviations or slang. This is for a rag search. Your output is only the description of the image"

            if self.verbose: print("Sending request to Ollama for file: " + image_path)

            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

            payload = {
                "model": self.image_description_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            response = requests.post(self.ollama_url, json=payload, verify=False).json()["response"]

            # Get the filename without extension
            file_name = os.path.splitext(image_path)[0]
            
            with open(f"{file_name}.image_description", "w+", encoding='utf-8') as file:
                json.dump({
                    'description': response,
                    'timestamp': datetime.now().isoformat()
                }, file, ensure_ascii=False, indent=4)
                if self.verbose: print("saved to json file")
            file_name = os.path.abspath(f"{file_name}.image_description")
            if self.verbose: print(f"Response received from Ollama and saved to file: {file_name}")
            
            return file_name, True
            
        except Exception as e:
            error_message = f"Error processing image: {str(e)}"
            print(error_message)
            return error_message, False

def image_to_description(image_path: str) -> str:
    """
    Backward compatibility function for the old API.
    """
    describer = ImageDescriber()
    return describer.image_to_description(image_path)

if __name__ == "__main__":
    # Test with absolute path
    test_image_path = "asdf.png"
    print(f"Starting image description for: {test_image_path}")
    describer = ImageDescriber(verbose=True)
    description = describer.image_to_description(test_image_path)
    print("Final result:")
    print(description)