from ollama import chat
import os
import json
from datetime import datetime

def image_to_description(image_path: str, language: str = "german") -> str:
    """
    Sends an image to Ollama for description.
    
    Args:
        image_path (str): Path to the image file
        language (str): Language for the description (default: german)
        
    Returns:
        str: Description of the image
    """
    try:
        # Convert Windows path to raw string and normalize
        image_path = os.path.abspath(image_path).replace('\\', '/')
        # print(f"Using image path: {image_path}")

        # Verify that the image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Verify file size and readability
        file_size = os.path.getsize(image_path)
        
        if file_size == 0:
            raise ValueError("Image file is empty")
            
        # Create the prompt based on the requested language
        prompt = f"Please describe this image in {language}. Describe what you see in detail. Be verbose and provide specific details. Do not use any abbreviations or slang. This is for a rag search. Your output is only the description of the image"

        print("Sending request to Ollama...")
        response = chat(
            model='gemma3:4b',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }]
        )
        
        # Get the filename without extension
        file_name = os.path.splitext(image_path)[0]
        print(f"Saving description to: {file_name}.txt")
        # print(response['message']['content'])
        
        with open(f"{file_name}.image_description", "w+", encoding='utf-8') as file:
            json.dump({
                'description': response['message']['content'],
                'timestamp': datetime.now().isoformat()
            }, file, ensure_ascii=False, indent=4)
            print("saved to json file")
        file_name = os.path.abspath(f"{file_name}.image_description")
        print(f"Response received from Ollama and saved to file: {file_name}")
        
        return file_name
        
    except Exception as e:
        error_message = f"Error processing image: {str(e)}"
        print(error_message)
        return error_message

if __name__ == "__main__":
    # Test mit absolutem Pfad
    test_image_path = "Z:\\Google Drive\\Korn\\IMG_IMG_0069.jpg"
    print(f"Starting image description for: {test_image_path}")
    description = image_to_description(test_image_path)
    print("Final result:")
    print(description)