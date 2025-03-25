import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from llama_cpp import Llama
import os
import time
import threading
import queue
import torch

# Set the custom cache directory for models
os.environ['TRANSFORMERS_CACHE'] = "D:/AI/hugging_faces"
os.environ['HF_HOME'] = "D:/AI/hugging_faces"


class ChatApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chatbot")
        self.root.geometry("700x800")
        self.root.configure(bg='#2d2d2d')

        # Initialize model and control variables
        self.llm = None
        self.model_ready = False
        self.generating = False
        self.stop_event = threading.Event()
        self.response_queue = queue.Queue()

        # Set the device to GPU if available, otherwise CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Define model names
        self.model_name = "mradermacher/DeepSeek-R1-Distill-Qwen-14B-abliterated-v2-GGUF"
        self.model_filename = "DeepSeek-R1-Distill-Qwen-14B-abliterated-v2.Q6_K.gguf"

        # Create UI elements
        self.create_widgets()

        # Start model loading in background
        self.start_model_loading()

        # Start response display updater
        self.root.after(100, self.process_response_queue)

    def create_widgets(self):
        # Custom dark theme style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#2d2d2d', foreground='#ffffff')
        style.configure('TButton', font=('Arial', 10), padding=5, background='#3d3d3d')
        style.configure('TFrame', background='#2d2d2d')
        style.map('TButton', background=[('active', '#4d4d4d')])

        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat history
        self.chat_history = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=('Arial', 10),
            state='disabled',
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white'
        )
        self.chat_history.tag_config('user', foreground='#64b5f6')
        self.chat_history.tag_config('assistant', foreground='#81c784')
        self.chat_history.tag_config('system', foreground='#ff8a65')
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)

        # User input
        self.user_input = tk.Text(
            input_frame,
            height=3,
            width=50,
            font=('Arial', 10),
            wrap=tk.WORD,
            bg='#3d3d3d',
            fg='#ffffff',
            insertbackground='white'
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind('<Return>', self.handle_input)

        # Button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.LEFT)

        # Send button
        self.send_button = ttk.Button(
            button_frame,
            text="Send",
            command=self.generate_response,
            state='disabled'
        )
        self.send_button.pack(pady=(0, 5))

        # Stop button
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_generation,
            state='disabled'
        )
        self.stop_button.pack()

        # Status bar
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X)

    def handle_input(self, event):
        """Handle Enter key press with Shift for new lines"""
        if event.state == 1:  # Shift key pressed
            self.user_input.insert(tk.INSERT, '\n')
            return "break"  # Prevent default behavior
        else:
            self.generate_response()
            return "break"  # Prevent default behavior

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def start_model_loading(self):
        self.update_status("Downloading model...")
        threading.Thread(target=self.load_model, daemon=True).start()

    def load_model(self):
        try:
            start_time = time.time()

            # Check if CUDA is available and log it
            if torch.cuda.is_available():
                print(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                print("CUDA not available. Using CPU.")

            # Load the model (do not call .to())
            self.llm = Llama.from_pretrained(
                repo_id=self.model_name,
                filename=self.model_filename,
                n_gpu_layers=35,  # Adjust based on your GPU capacity (6GB VRAM)
                n_batch=256,  # Reduce if you encounter memory issues
                n_threads=8,  # Optimized for CPU threading
                verbose=True
            )

            # If CUDA is available, you may want to check if `llama_cpp` supports automatic usage
            if torch.cuda.is_available():
                print("Using GPU for processing.")
            else:
                print("Using CPU for processing.")

            self.model_ready = True
            download_time = round(time.time() - start_time, 2)
            self.append_to_chat(f"Model loaded in {download_time} seconds", 'system')
            self.send_button.config(state='normal')
            self.update_status("Ready")
        except Exception as e:
            # Log error details for debugging
            self.append_to_chat(f"Error loading model: {str(e)}", 'system')
            self.update_status("Error loading model")

    def append_to_chat(self, message, sender):
        self.chat_history.config(state='normal')

        if sender == 'assistant' and not message.strip():
            self.chat_history.insert(tk.END, "Assistant: ", sender)
        else:
            self.chat_history.insert(tk.END, f"{sender.capitalize()}: {message}\n\n", sender)

        self.chat_history.yview(tk.END)
        self.chat_history.config(state='disabled')

    def generate_response(self):
        if not self.model_ready:
            messagebox.showerror("Error", "Model not loaded yet!")
            return

        user_text = self.user_input.get('1.0', tk.END).strip()
        if not user_text:
            return

        # Disable input during processing
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.update_status("Processing...")
        self.generating = True
        self.stop_event.clear()

        # Show user message
        self.append_to_chat(user_text, 'user')

        # Clear input
        self.root.focus_set()  # Move focus away from input box
        self.user_input.delete('1.0', tk.END)  # Now clear it

        # Start response generation in background
        threading.Thread(target=self.stream_response, args=(user_text,), daemon=True).start()

    def stream_response(self, user_text):
        try:
            response_generator = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": user_text}],
                stream=True
            )

            # Create assistant message placeholder
            self.append_to_chat("", 'assistant')
            self.chat_history.mark_set("response_end", tk.END)

            # Stream response chunks
            for chunk in response_generator:
                if self.stop_event.is_set():
                    break

                chunk_content = chunk['choices'][0]['delta'].get('content', '')
                if chunk_content:
                    self.response_queue.put(chunk_content)

            self.response_queue.put(None)  # End of stream
        except Exception as e:
            self.response_queue.put(f"\n\nError: {str(e)}")
            self.response_queue.put(None)

    def process_response_queue(self):
        try:
            while True:
                chunk = self.response_queue.get_nowait()
                if chunk is None:
                    self.finish_generation()
                    break

                self.chat_history.config(state='normal')
                self.chat_history.insert("response_end", chunk, 'assistant')
                self.chat_history.yview(tk.END)
                self.chat_history.config(state='disabled')
                self.root.update()
        except queue.Empty:
            pass

        self.root.after(100, self.process_response_queue)

    def finish_generation(self):
        self.generating = False
        self.user_input.config(state='normal')
        self.send_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.update_status("Ready")
        self.append_to_chat("", 'assistant')  # Add spacing

    def stop_generation(self):
        if self.generating:
            self.stop_event.set()
            self.append_to_chat("\n\n[Generation stopped by user]", 'assistant')
            self.finish_generation()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApplication(root)
    root.mainloop()
