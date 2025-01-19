# Unit Converter Pro

A modern, feature-rich unit conversion application built with Python and ttkbootstrap, offering real-time currency conversion, UTC time conversion, and multiple unit categories in a sleek interface.

## 🌟 Key Features

- **Multi-Category Conversion**
  - Length, Mass, Temperature
  - Currency (Real-time rates)
  - Time, Speed, Area
  - Volume, Pressure, Energy
  - Digital Storage
  - And many more...

- **Real-Time Currency Conversion**
  - Live exchange rates via ExchangeRate-API
  - Support for major world currencies
  - Automatic rate updates
  - Configurable API key

- **UTC Time Conversion**
  - Current UTC time display
  - Local time conversion
  - Custom time input support
  - Animated results

- **Modern UI Features**
  - Clean, intuitive interface
  - Responsive design
  - Dark/Light theme support
  - Input validation
  - Error handling
  - Status notifications

## 🛠️ Technical Features

- Built with Python 3.7+
- Tkinter with ttkbootstrap for modern UI
- Threaded currency rate updates
- Caching system for improved performance
- State persistence
- Error recovery system
- Input debouncing
- Modular design

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/unit-converter-pro.git

# Install dependencies
pip install -r requirements.txt

# Run the application
python unit_convert.py
```

## 📋 Requirements

- Python 3.7+
- ttkbootstrap==1.10.1
- pytz==2023.3

## 🚀 Usage

1. Select unit category from dropdown
2. Choose source and target units
3. Enter value to convert
4. Get instant conversion results

For currency conversion, obtain an API key from [ExchangeRate-API](https://exchangerate-api.com).

## 📝 License

MIT License

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
