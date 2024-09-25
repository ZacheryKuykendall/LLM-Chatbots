#!/usr/bin/env python3
import os
import sys
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoConfig,
    AutoModel,
    logging,
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress warnings
logging.set_verbosity_error()

def get_huggingface_token():
    """
    Retrieve the Hugging Face API token from environment variables.
    """
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        print("Hugging Face API token not found in environment variables.")
        print("Please set 'HUGGINGFACE_API_TOKEN' in your .env file.")
        sys.exit(1)
    return token

def select_model():
    """
    Prompt the user to input a Hugging Face model name or path.
    """
    print("Enter the Hugging Face model name or local path.")
    print("Examples: 'gpt2', 'EleutherAI/gpt-neo-125M', './models/local_model'")
    model_name_or_path = input("Model name or path: ").strip()
    if not model_name_or_path:
        print("No model name or path provided. Exiting.")
        sys.exit(1)
    return model_name_or_path

def chat_with_model(model_name_or_path, use_auth_token):
    """
    Start a chat session with the selected model.
    """
    # Load tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_auth_token=use_auth_token)
    except Exception as e:
        print(f"Error loading tokenizer from '{model_name_or_path}': {e}")
        sys.exit(1)

    # Load model
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name_or_path, use_auth_token=use_auth_token)
    except Exception as e:
        print(f"Error loading model as AutoModelForCausalLM: {e}")
        print("Attempting to load as AutoModel...")
        try:
            model = AutoModel.from_pretrained(model_name_or_path, use_auth_token=use_auth_token)
        except Exception as e:
            print(f"Error loading model as AutoModel: {e}")
            sys.exit(1)

    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Chat loop
    print("\nYou can start chatting with the model. Type 'exit' to quit.\n")
    conversation_history = ""

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break

        conversation_history += f"User: {user_input}\nModel:"
        input_ids = tokenizer.encode(conversation_history, return_tensors="pt").to(device)

        # Generate response
        try:
            output_ids = model.generate(
                input_ids,
                max_length=input_ids.size(1) + 100,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                temperature=0.7,
                num_return_sequences=1,
            )
        except Exception as e:
            print(f"Error during generation: {e}")
            continue

        # Decode and process the output
        output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        response = output_text[len(conversation_history) :].split("User:")[0].strip()

        print(f"Model: {response}\n")
        conversation_history += f" {response}\n"

if __name__ == "__main__":
    # Get Hugging Face API token
    huggingface_token = get_huggingface_token()

    # Prompt user for model name or path
    model_name_or_path = select_model()

    # Start chat session
    chat_with_model(model_name_or_path, use_auth_token=huggingface_token)
