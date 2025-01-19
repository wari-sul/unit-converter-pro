import ttkbootstrap as ttk
from ttkbootstrap import Style
import tkinter as tk
from tkinter import messagebox
import urllib.request
import urllib.error
import json
import threading
import os
from datetime import datetime
import pytz

# Remove the hardcoded API key
API_KEY = None
API_KEY_FILE = "api_key.json"
CURRENCY_API_BASE_URL = "https://v6.exchangerate-api.com/v6/"

def load_api_key():
    try:
        if not os.path.exists(API_KEY_FILE):
            return None
        with open(API_KEY_FILE, 'r') as f:
            data = json.load(f)
            return data.get('api_key')
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None

def save_api_key(api_key):
    with open(API_KEY_FILE, 'w') as f:
        json.dump({'api_key': api_key}, f)

def prompt_api_key():
    global API_KEY
    # Create a popup dialog
    dialog = tk.Toplevel()
    dialog.title("API Key Configuration")
    dialog.geometry("400x200")
    dialog.transient(root)  # Make dialog modal
    
    message = ttk.Label(dialog, text="Please enter your ExchangeRate-API key\n(Get one from exchangerate-api.com)",
                       wraplength=350)
    message.pack(pady=10)
    
    # API key entry
    api_entry = ttk.Entry(dialog, width=40)
    api_entry.pack(pady=10)
    
    def save_and_close():
        global API_KEY
        key = api_entry.get().strip()
        if key:
            API_KEY = key
            save_api_key(key)
            dialog.destroy()
            # Update currency rates with new API key
            app.update_currency_rates()
    
    def skip():
        dialog.destroy()
    
    # Buttons frame
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=20)
    
    ttk.Button(button_frame, text="Save", command=save_and_close).pack(side=tk.LEFT, padx=10)
    ttk.Button(button_frame, text="Skip for now", command=skip).pack(side=tk.LEFT)

# Function to fetch exchange rates
def get_exchange_rates():
    global API_KEY
    if not API_KEY:
        API_KEY = load_api_key()  # Try loading again
    try:
        if not API_KEY:
            result = messagebox.askyesno(
                "API Key Required",
                "Currency conversion requires an API key from exchangerate-api.com. Would you like to configure it now?"
            )
            if result:
                prompt_api_key()
            return None
            
        url = f"{CURRENCY_API_BASE_URL}{API_KEY}/latest/USD"
        with urllib.request.urlopen(url) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                return data['conversion_rates']
            else:
                raise urllib.error.HTTPError(url, response.getcode(), "Failed to fetch exchange rates", None, None)
    except urllib.error.URLError as e:
        messagebox.showerror("Network Error", f"Unable to connect to exchange rate service:\n{str(e)}")
        return None
    except json.JSONDecodeError as e:
        messagebox.showerror("Data Error", f"Invalid response from exchange rate service:\n{str(e)}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Error fetching exchange rates:\n{str(e)}")
        return None

# Conversion data
conversion_data = {
    'currency': {},  # Will be populated with real-time exchange rates
    'length': {
        'meters': 1,
        'centimeters': 100,
        'millimeters': 1000,
        'feet': 3.28084,
        'inches': 39.3701
    },
    'mass': {
        'kilograms': 1,
        'grams': 1000,
        'milligrams': 1e6,
        'pounds': 2.20462,
        'ounces': 35.274
    },
    'time': {
        'seconds': 1,
        'minutes': 1 / 60,
        'hours': 1 / 3600,
        'days': 1 / 86400
    },
    'temperature': {
        'celsius': 1,
        'fahrenheit': 1,
        'kelvin': 1
    },
    'electric current': {
        'amperes': 1,
        'milliamperes': 1000,
        'microamperes': 1e6
    },
    'amount of substance': {
        'moles': 1,
        'kilomoles': 1e-3
    },
    'luminous intensity': {
        'candelas': 1
    },
    'speed': {
        'meters per second': 1,
        'kilometers per hour': 3.6,
        'miles per hour': 2.23694
    },
    'area': {
        'square meters': 1,
        'square kilometers': 1e-6,
        'square feet': 10.7639,
        'acres': 0.000247105,
        'hectares': 1e-4
    },
    'volume': {
        'cubic meters': 1,
        'liters': 1000,
        'milliliters': 1e6,
        'cubic feet': 35.3147,
        'gallons': 264.172
    },
    'pressure': {
        'pascals': 1,
        'atmospheres': 9.86923e-6,
        'bars': 0.00001,
        'torr': 0.00750062
    },
    'energy': {
        'joules': 1,
        'kilowatt-hours': 2.77778e-7,
        'calories': 0.239006,
        'BTUs': 0.000947817
    },
    'power': {
        'watts': 1,
        'kilowatts': 0.001,
        'horsepower': 0.00134102
    },
    'frequency': {
        'hertz': 1,
        'kilohertz': 0.001,
        'megahertz': 1e-6
    },
    'digital storage': {
        'bytes': 1,
        'kilobytes': 0.001,
        'megabytes': 1e-6,
        'gigabytes': 1e-9,
        'terabytes': 1e-12
    }
}

def validate_conversion(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ValueError as ve:
            self.result_label.config(text=f"Invalid input: {str(ve)}", fg='red')
        except Exception as e:
            self.result_label.config(text=f"Error: {str(e)}", fg='red')
    return wrapper

class UnitConverterApp:
    def __init__(self, root):
        # Add at the beginning of __init__
        global API_KEY
        API_KEY = load_api_key()
        if API_KEY:
            print(f"API key loaded successfully")  # Debug line
            
        # Add caching with size limit
        self.conversion_cache = {}
        self.MAX_CACHE_SIZE = 100
        self.root = root
        try:
            self._initialize_ui()
        except Exception as e:
            self._handle_initialization_error(e)

    def _handle_initialization_error(self, error):
        messagebox.showerror(
            "Initialization Error",
            f"Error initializing application: {str(error)}\nTrying to recover..."
        )
        self._initialize_minimal_ui()

    def _initialize_ui(self):
        self.conversion_cache = {}
        self.last_currency_update = None
        self.update_interval = 3600  # 1 hour in seconds
        style = Style(theme='flatly')
        self.root.title("Unit Converter")
        self.root.geometry('600x500')
        self.root.resizable(False, False)

        # Initialize unit type variable first
        self.unit_type_var = tk.StringVar()
        self.unit_type_var.set('length')
        self.from_unit_var = ttk.StringVar()
        self.to_unit_var = ttk.StringVar()

        # Configure style for modern look
        style.configure('TButton', font=('Arial', 10))
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, expand=True, fill='both')

        # Main converter tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='Unit Converter')

        # UTC converter tab
        self.utc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.utc_frame, text='UTC Converter')

        # Setup UTC converter
        self.setup_utc_converter()

        # Add padding around all widgets
        self.padding = {'padx': 15, 'pady': 10}

        # Initialize conversion_data['currency'] with empty dict
        conversion_data['currency'] = {}

        # Initialize currency rates
        self.update_currency_rates()

        # Configure grid weights for main frame
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.rowconfigure(4, weight=1)

        # Create refresh button for currency rates with modern styling
        self.refresh_button = ttk.Button(self.main_frame, text="Refresh Rates",
                                      command=self.update_currency_rates,
                                      style='success.TButton',
                                      width=12)
        self.refresh_button.grid(row=0, column=2, **self.padding, sticky='nsew')

        self.from_unit_var = ttk.StringVar()
        self.to_unit_var = ttk.StringVar()

        self.unit_label = ttk.Label(self.main_frame, text="Select Unit Category:")
        self.unit_label.grid(row=0, column=0, **self.padding)

        unit_types = list(conversion_data.keys())
        self.unit_menu = ttk.OptionMenu(self.main_frame, self.unit_type_var, unit_types[0], *unit_types)
        self.unit_menu.configure(width=15)
        self.unit_menu.grid(row=0, column=1, **self.padding, sticky='nsew')

        self.from_unit_label = ttk.Label(self.main_frame, text="From:")
        self.from_unit_label.grid(row=1, column=0, **self.padding, sticky='nsew')

        self.from_unit_menu = ttk.OptionMenu(self.main_frame, self.from_unit_var, "")
        self.from_unit_menu.configure(width=15)
        self.from_unit_menu.grid(row=1, column=1, **self.padding, sticky='nsew')

        self.to_unit_label = ttk.Label(self.main_frame, text="To:")
        self.to_unit_label.grid(row=2, column=0, **self.padding, sticky='nsew')

        self.to_unit_menu = ttk.OptionMenu(self.main_frame, self.to_unit_var, "")
        self.to_unit_menu.configure(width=15)
        self.to_unit_menu.grid(row=2, column=1, **self.padding, sticky='nsew')

        self.input_label = ttk.Label(self.main_frame, text="Input:")
        self.input_label.grid(row=3, column=0, **self.padding)

        self.input_entry = ttk.Entry(self.main_frame)
        self.input_entry.grid(row=3, column=1, **self.padding, sticky='nsew')

        # Create convert button with modern styling
        self.convert_button = ttk.Button(self.main_frame, text="Convert",
                                      command=self.convert,
                                      style='primary.TButton',
                                      width=10)
        self.convert_button.grid(row=3, column=2, **self.padding, sticky='nsew')

        # Result label with better visibility
        self.result_label = tk.Label(self.main_frame, text="",
                                   bg='#f0f0f0',
                                   font=('Arial', 12, 'bold'),
                                   wraplength=300)  # Allow text wrapping
        self.result_label.grid(row=4, columnspan=3, **self.padding)

        # Add keyboard binding for Enter key
        self.input_entry.bind('<Return>', lambda event: self.convert())

        # Status bar
        self.status_bar = tk.Label(self.main_frame, text="Ready",
                                 bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                 bg='#e0e0e0', font=('Arial', 8))
        self.status_bar.grid(row=5, columnspan=3, sticky='ew', **self.padding)

        # Initialize unit menus
        self.unit_type_var.trace('w', self.update_unit_menus)
        self.update_unit_menus()  # Call explicitly to initialize menus

        # Check for API key
        global API_KEY
        API_KEY = load_api_key()
        if not API_KEY:
            self.root.after(1000, prompt_api_key)  # Show prompt after window loads

        # Add debounce timer
        self._convert_after_id = None
        
        # Modify input binding
        self.input_entry.bind('<KeyRelease>', self._debounced_convert)

        # Clear caches periodically
        self._clear_caches()

        # Restore state
        self._restore_state()

        # Initialize lazy load cache
        self._loaded_categories = {}

    def _debounced_convert(self, event=None):
        if hasattr(self, '_convert_timer'):
            self.root.after_cancel(self._convert_timer)
        self._convert_timer = self.root.after(300, self.convert)

    def update_unit_menus(self, *args):
        selected_category = self.unit_type_var.get()
        
        if not hasattr(self, '_menu_cache'):
            self._menu_cache = {}
        
        # Use cached menu items if available
        if selected_category in self._menu_cache:
            self._update_menus_from_cache(selected_category)
            return
            
        # Generate new menu items
        units = list(conversion_data.get(selected_category, {}).keys())
        self._menu_cache[selected_category] = units
        self._update_menus_from_cache(selected_category)

    def _update_menus_from_cache(self, selected_category):
        units = self._menu_cache[selected_category]

        # If currency is selected but rates haven't been fetched yet, show loading message
        if (selected_category == 'currency' and not conversion_data['currency']):
            self.status_bar.config(text="Loading currency rates...")
            return

        from_units = units

        if not from_units:  # Check if the list is empty
            if selected_category != 'currency':  # Only show error for non-currency units
                messagebox.showerror("Error", f"No units available for {selected_category}")
            return

        to_units = from_units[:]

        # Clear existing menu items
        self.from_unit_menu['menu'].delete(0, 'end')
        self.to_unit_menu['menu'].delete(0, 'end')

        # Add new menu items
        for unit in from_units:
            self.from_unit_menu['menu'].add_command(label=unit, command=lambda value=unit: self.from_unit_var.set(value))

        for unit in to_units:
            self.to_unit_menu['menu'].add_command(label=unit, command=lambda value=unit: self.to_unit_var.set(value))

        # Set default values only if we have units available
        if from_units:
            self.from_unit_var.set(from_units[0])
            self.to_unit_var.set(to_units[0])

    def update_currency_rates(self):
        # Check if update is needed
        if (self.last_currency_update and 
            (datetime.now() - self.last_currency_update).seconds < self.update_interval):
            return

        def fetch_rates():
            rates = get_exchange_rates()
            if rates:
                self.root.after(0, self._update_ui_with_rates, rates)
                self.last_currency_update = datetime.now()

        thread = threading.Thread(target=fetch_rates, daemon=True)
        thread.start()

    def _update_ui_with_rates(self, rates):
        if rates is None:
            messagebox.showerror("Error", "Failed to fetch currency rates. Please check your internet connection.")
            return
        conversion_data['currency'] = rates if rates else {}
        self.status_bar.config(text="Currency rates updated successfully")
        if self.unit_type_var.get() == 'currency':
            self.update_unit_menus()
        # Schedule next update after one hour
        self.root.after(3600000, self.update_currency_rates)

    def convert_temperature(self, value, from_unit, to_unit):
        # First convert to Celsius
        if from_unit == 'fahrenheit':
            celsius = (value - 32) * 5/9
        elif from_unit == 'kelvin':
            celsius = value - 273.15
        else:  # celsius
            celsius = value

        # Then convert to target unit
        if to_unit == 'fahrenheit':
            return (celsius * 9/5) + 32
        elif to_unit == 'kelvin':
            return celsius + 273.15
        return celsius  # celsius to celsius

    def setup_utc_converter(self):
        # UTC Converter UI
        utc_style = {'padx': 10, 'pady': 10}

        # Current UTC time display
        self.utc_time_label = ttk.Label(self.utc_frame, text="Current UTC Time:")
        self.utc_time_label.pack(**utc_style)

        self.utc_display = ttk.Label(self.utc_frame, text="", font=('Arial', 14, 'bold'))
        self.utc_display.pack(padx=10, pady=10)

        # Local time display
        self.local_time_label = ttk.Label(self.utc_frame, text="Local Time:")
        self.local_time_label.pack(padx=10, pady=10)

        self.local_display = ttk.Label(self.utc_frame, text="", font=('Arial', 14, 'bold'))
        self.local_display.pack(padx=10, pady=10)

    # Time input fields with modern styling
        input_frame = ttk.Frame(self.utc_frame)
        input_frame.pack(padx=10, pady=10)

        ttk.Label(input_frame, text="Enter UTC Time:", style='primary.TLabel').pack(side='left', padx=5)
        self.time_entry = ttk.Entry(input_frame, style='primary.TEntry', width=25)
        self.time_entry.pack(side='left', padx=5)
        self.time_entry.insert(0, "YYYY-MM-DD HH:MM:SS")

        # Add placeholder behavior
        def on_focus_in(event):
            if self.time_entry.get() == "YYYY-MM-DD HH:MM:SS":
                self.time_entry.delete(0, 'end')
                self.time_entry.config(style='primary.TEntry')

        def on_focus_out(event):
            if not self.time_entry.get():
                self.time_entry.insert(0, "YYYY-MM-DD HH:MM:SS")
                self.time_entry.config(style='secondary.TEntry')

        self.time_entry.bind('<FocusIn>', on_focus_in)
        self.time_entry.bind('<FocusOut>', on_focus_out)

    # Convert button
        self.utc_convert_btn = ttk.Button(self.utc_frame, text="Convert to Local Time",
                                         command=self.convert_utc_time,
                                         style='Accent.TButton')
        self.utc_convert_btn.pack(padx=10, pady=10)

        # Result display
        self.utc_result = ttk.Label(self.utc_frame, text="", font=('Arial', 12))
        self.utc_result.pack(padx=10, pady=10)

        # Start updating current time
        self.update_current_time()

    def update_current_time(self):
        # Update UTC time
        utc_now = datetime.now(pytz.UTC)
        self.utc_display.config(text=utc_now.strftime("%Y-%m-%d %H:%M:%S"))

        # Update local time
        local_now = datetime.now()
        self.local_display.config(text=local_now.strftime("%Y-%m-%d %H:%M:%S"))

        # Schedule next update
        self.root.after(1000, self.update_current_time)

    def convert_utc_time(self):
        try:
            # Get input UTC time
            utc_str = self.time_entry.get()
            utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
            utc_dt = pytz.UTC.localize(utc_dt)

            # Convert to local time
            local_dt = utc_dt.astimezone()

            # Display result with animation
            self.utc_result.config(text="")
            self.animate_result(f"Local time: {local_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        except ValueError:
            self.utc_result.config(text="Invalid time format. Use YYYY-MM-DD HH:MM:SS")

    def animate_result(self, text, index=0):
        if not hasattr(self, 'utc_result') or not self.utc_result.winfo_exists():
            return
        
        # Process chunks instead of single characters
        chunk_size = 3
        if index <= len(text):
            chunk_end = min(index + chunk_size, len(text))
            self.utc_result.config(text=text[:chunk_end])
            if chunk_end < len(text):
                self.root.after(30, lambda: self.animate_result(text, chunk_end))

    def validate_input(self, value, unit_type):
        MAX_VALUES = {
            'currency': 999999999,
            'temperature': 1000000,
            'length': 1000000000
        }
        if value > MAX_VALUES.get(unit_type, float('inf')):
            raise ValueError(f"Value too large for {unit_type}")

    @validate_conversion
    def convert(self):
        try:
            # Generate cache key
            cache_key = (
                self.unit_type_var.get(),
                self.from_unit_var.get(),
                self.to_unit_var.get(),
                self.input_entry.get().strip()
            )
            
            # Check cache
            if cache_key in self.conversion_cache:
                self.result_label.config(
                    text=self.conversion_cache[cache_key],
                    fg='black'
                )
                return

            # Input validation
            input_text = self.input_entry.get().strip()
            if not input_text:
                self.result_label.config(text="Please enter a value", fg='red')
                return

            unit_type = self.unit_type_var.get()
            from_unit = self.from_unit_var.get()
            to_unit = self.to_unit_var.get()

            # Validate numeric input
            try:
                input_value = float(input_text)
                if input_value < 0 and unit_type not in ['temperature']:
                    self.result_label.config(text="Please enter a positive value", fg='red')
                    return
                self.validate_input(input_value, unit_type)
            except ValueError:
                self.result_label.config(text="Please enter a valid number", fg='red')
                return
            conversions = conversion_data.get(unit_type, {})

            if unit_type == 'currency':
                if not conversion_data['currency']:
                    self.result_label.config(text="Currency rates not available. Please refresh.", fg='red')
                    return
                try:
                    if conversion_data['currency'][from_unit] == 0:
                        raise ValueError("Invalid exchange rate")
                    usd_value = input_value / conversion_data['currency'][from_unit]
                    result = usd_value * conversion_data['currency'][to_unit]
                    result_text = f"{input_value:.2f} {from_unit} = {result:.2f} {to_unit}"
                    self.result_label.config(text=result_text, fg='black')
                except KeyError:
                    self.result_label.config(text="Currency not available", fg='red')
            elif unit_type == 'temperature':
                result = self.convert_temperature(input_value, from_unit, to_unit)
                result_text = f"{input_value} {from_unit} = {result:.4f} {to_unit}"
                self.result_label.config(text=result_text, fg='black')
            elif from_unit in conversions and to_unit in conversions:
                result = (input_value * conversions[to_unit]) / conversions[from_unit]
                result_text = f"{input_value} {from_unit} = {result:.4f} {to_unit}"
                self.result_label.config(text=result_text, fg='black')
            else:
                self.result_label.config(text="Invalid units")

            # Cache result
            self.conversion_cache[cache_key] = result_text

            # Save state
            self._save_state()

            # Manage cache size
            self._manage_cache()

        except ValueError as ve:
            self.result_label.config(text=f"Invalid input: {str(ve)}", fg='red')
        except KeyError as ke:
            self.result_label.config(text=f"Unit not found: {str(ke)}", fg='red')
        except Exception as e:
            self.result_label.config(text=f"Error: {str(e)}", fg='red')

    def _clear_caches(self):
        self.conversion_cache.clear()
        self._menu_cache.clear()
        self.root.after(3600000, self._clear_caches)  # Clear every hour

    def _save_state(self):
        try:
            state = {
                'unit_type': self.unit_type_var.get(),
                'from_unit': self.from_unit_var.get(),
                'to_unit': self.to_unit_var.get(),
                'input_value': self.input_entry.get()
            }
            with open('converter_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def _restore_state(self):
        try:
            with open('converter_state.json', 'r') as f:
                state = json.load(f)
                self.unit_type_var.set(state['unit_type'])
                self.from_unit_var.set(state['from_unit'])
                self.to_unit_var.set(state['to_unit'])
                self.input_entry.insert(0, state['input_value'])
        except:
            pass

    def _lazy_load_conversion_data(self, category):
        if category not in self._loaded_categories:
            self._loaded_categories[category] = conversion_data[category]
        return self._loaded_categories[category]

    def _manage_cache(self):
        if len(self.conversion_cache) > self.MAX_CACHE_SIZE:
            # Remove oldest 20% of entries
            items_to_remove = int(self.MAX_CACHE_SIZE * 0.2)
            for _ in range(items_to_remove):
                self.conversion_cache.pop(next(iter(self.conversion_cache)))

    def _on_closing(self):
        self._save_state()
        self.root.destroy()

if __name__ == "__main__":
    try:
        root = ttk.Window(themename="flatly")
        app = UnitConverterApp(root)
        root.protocol("WM_DELETE_WINDOW", app._on_closing)
        root.mainloop()
    except Exception as e:
        error_message = f"Error starting application:\n{str(e)}"
        try:
            # Try to show error in GUI
            messagebox.showerror("Application Error", error_message)
        except:
            # Fallback to console if GUI fails
            print(error_message)
