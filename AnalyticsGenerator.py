import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import openai
import os
import re

# Set your OpenAI API key
openai.api_key = "your_api_key_here"

class GPTPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPT-Enhanced Data Plotter")
        self.root.geometry("800x600")
        
        self.csv_file = None
        self.df = None
        self.is_dark_mode = False  # Track current theme state
        
        # Create GUI components
        self.create_widgets()
    
    def create_widgets(self):
        # File selection button
        self.load_file_btn = tk.Button(
            self.root, text="Load CSV File", command=self.load_csv_file, bg="#cce7ff", fg="black"
        )
        self.load_file_btn.pack(pady=10)
        
        # Display column names
        self.columns_label = tk.Label(
            self.root, text="Columns will be displayed here", bg="#f0f0f0", width=100
        )
        self.columns_label.pack(pady=10)
        
        # User prompt entry
        self.prompt_label = tk.Label(self.root, text="Enter your prompt for the plot:")
        self.prompt_label.pack(pady=5)
        
        self.prompt_entry = tk.Entry(self.root, width=80)
        self.prompt_entry.pack(pady=5)
        
        # Generate plot button
        self.generate_plot_btn = tk.Button(
            self.root, text="Generate Plot", command=self.generate_plot, bg="#d1f5d3", fg="black"
        )
        self.generate_plot_btn.pack(pady=10)
        
        # Toggle Light/Dark Mode button
        self.toggle_theme_btn = tk.Button(
            self.root, text="Toggle Dark Mode", command=self.toggle_theme, bg="#ffd580", fg="black"
        )
        self.toggle_theme_btn.place(relx=0.05, rely=0.95, anchor="sw")  # Bottom left corner
        
        # Exit button
        self.exit_btn = tk.Button(self.root, text="Exit", command=self.root.quit, bg="#ff6961", fg="white")
        self.exit_btn.place(relx=0.9, rely=0.95, anchor="se")  # Bottom right corner
    
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.root.config(bg="#2b2b2b")
            self.load_file_btn.config(bg="#4f4f4f", fg="white")
            self.columns_label.config(bg="#4f4f4f", fg="white")
            self.prompt_label.config(bg="#2b2b2b", fg="white")
            self.prompt_entry.config(bg="#4f4f4f", fg="white", insertbackground="white")
            self.generate_plot_btn.config(bg="#3b6b3b", fg="white")
            self.toggle_theme_btn.config(bg="#ffcc66", fg="black", text="Toggle Light Mode")
            self.exit_btn.config(bg="#992b2b", fg="white")
        else:
            self.root.config(bg="white")
            self.load_file_btn.config(bg="#cce7ff", fg="black")
            self.columns_label.config(bg="#f0f0f0", fg="black")
            self.prompt_label.config(bg="white", fg="black")
            self.prompt_entry.config(bg="white", fg="black", insertbackground="black")
            self.generate_plot_btn.config(bg="#d1f5d3", fg="black")
            self.toggle_theme_btn.config(bg="#ffd580", fg="black", text="Toggle Dark Mode")
            self.exit_btn.config(bg="#ff6961", fg="white")
    
    def load_csv_file(self):
        # Open file dialog to load CSV
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self.csv_file = file_path
                self.columns_label.config(
                    text=f"Loaded Columns: {', '.join(self.df.columns)}"
                )
                messagebox.showinfo("File Loaded", "CSV file loaded successfully!")
            except Exception as e:
                self.log_error(f"Error loading CSV file: {str(e)}")
                messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
    
    def generate_plot(self):
        if self.df is None:
            messagebox.showerror("Error", "No CSV file loaded.")
            return

        user_prompt = self.prompt_entry.get()
        if not user_prompt:
            messagebox.showerror("Error", "Please enter a prompt.")
            return

        try:
            # Use GPT-4 to generate plotting code
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant proficient in Python and data visualization. "
                            "You will generate plotting code based on user input and provided dataset column names. "
                            "The dataset is already loaded into a variable called `df` (a pandas DataFrame). "
                            "Use this variable directly for plotting without loading any files."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Given the following dataset columns:\n"
                            f"{', '.join(self.df.columns)}\n"
                            f"and the prompt: \"{user_prompt}\", write Python code using "
                            "seaborn to generate the requested plot. Only include executable Python code. "
                            "Do not include any file loading commands or hardcoded file names."
                        ),
                    },
                ],
                max_tokens=500,
                temperature=0.7,
            )
            raw_response = response['choices'][0]['message']['content'].strip()

            # Extract the Python code block using regex
            code_match = re.search(r"```python(.*?)```", raw_response, re.DOTALL)
            if code_match:
                generated_code = code_match.group(1).strip()
            else:
                generated_code = raw_response.strip()

            # Log the generated code for debugging
            self.log_error(f"Generated code:\n{generated_code}")

            # Dynamically execute the generated code
            self.execute_and_plot(generated_code)
        except Exception as e:
            self.log_error(f"Error generating plot with GPT: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate plot: {str(e)}")

    
    def execute_and_plot(self, code):
        try:
            if not code.strip():
                raise ValueError("The generated code is empty and cannot be executed.")

            def dynamic_plot(df):
                if "plt.show()" not in code:
                    code_to_execute = code + "\nplt.show()"
                else:
                    code_to_execute = code

                exec(code_to_execute, {"df": df, "sns": sns, "plt": plt})

            self.log_error(f"Executing code:\n{code}")
            dynamic_plot(self.df)

        except SyntaxError as e:
            error_msg = f"SyntaxError in generated code: {e.text.strip() if e.text else 'Unknown'}"
            self.log_error(f"{error_msg}\nCode:\n{code}")
            messagebox.showerror("Error", error_msg)
        except Exception as e:
            self.log_error(f"Error executing plot code: {str(e)}\nCode:\n{code}")
            messagebox.showerror("Error", f"Failed to execute the plot: {str(e)}")

    def log_error(self, error_message):
        """Log errors to a text file."""
        log_file = "error_log.txt"
        with open(log_file, "a") as file:
            file.write(f"{error_message}\n")
        print(f"Error logged: {error_message}")

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = GPTPlotApp(root)
    root.mainloop()
