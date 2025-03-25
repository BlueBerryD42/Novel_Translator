import tkinter as tk
from llama_cpp import Llama

# Initialize the model
model = Llama(model_path="D:\\AI\\models\\dolphin-2.9-llama3-8b.Q4_K_M.gguf")


# Function to handle input and display output
def generate_response():
    user_input = input_text.get("1.0", tk.END).strip()  # Get user input from text box
    if user_input:  # Only process if input is not empty
        try:
            output = model(user_input)  # Generate response using Llama model
            output_text.config(state=tk.NORMAL)  # Enable the output text widget
            output_text.delete("1.0", tk.END)  # Clear previous output
            output_text.insert(tk.END, output)  # Insert new output
            output_text.config(state=tk.DISABLED)  # Make it read-only again
        except Exception as e:
            output_text.config(state=tk.NORMAL)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, f"Error: {str(e)}")
            output_text.config(state=tk.DISABLED)


# Create the main application window
root = tk.Tk()
root.title("Llama Text Generator")

# Create widgets
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(pady=10)

input_label = tk.Label(frame, text="Enter Prompt:")
input_label.grid(row=0, column=0, sticky="w")

input_text = tk.Text(frame, height=5, width=50)
input_text.grid(row=1, column=0, padx=5, pady=5, columnspan=2)

generate_button = tk.Button(frame, text="Generate Response", command=generate_response)
generate_button.grid(row=2, column=0, pady=5)

output_label = tk.Label(frame, text="Generated Output:")
output_label.grid(row=3, column=0, sticky="w")

output_text = tk.Text(frame, height=10, width=50, state=tk.DISABLED, bg="#f4f4f4")
output_text.grid(row=4, column=0, padx=5, pady=5, columnspan=2)

# Run the application
root.mainloop()
