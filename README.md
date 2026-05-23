# BAHD Win StartUp Control

<div align="center">
  <p>A modern, lightweight, and powerful Windows startup and service manager.</p>
</div>

*Read this in other languages: [Turkish](README_TR.md)*

## Features

BAHD Win StartUp Control is a system utility (v1.0.0) built with Python and PyWebView, offering a sleek, modern, and responsive user interface powered by Tailwind CSS.

- **🚀 Dashboard**: Manage applications that launch automatically during the Windows boot process. Disable or enable them with a single click and check their system impact.
- **⚙️ System Services**: View and manage Windows background services. Start or stop services easily (may require Administrator privileges).
- **🗄️ Registry Keys**: Safely view advanced startup registry locations in a read-only environment to ensure system stability.
- **📝 System Logs**: Monitor real-time application logs and system events directly from the UI.
- **🌍 Internationalization (i18n)**: Full support for both **English** and **Turkish** languages, switchable on the fly.
- **🎨 Theming**: Native support for **Dark Mode** (default) and **Light Mode**.
- **📦 Import/Export**: Export your startup lists for backup or import them to restore configurations.

## Architecture

The application has transitioned from a legacy Tkinter GUI to a modern web-based UI utilizing `pywebview`. 
- **Backend**: Python 3, using `winreg` for registry manipulation and `psutil` for service tracking.
- **Frontend**: Vanilla JavaScript (SPA architecture), HTML5, and Tailwind CSS (via CDN) for styling.

## Installation & Running

### Requirements
- Windows 10/11
- Python 3.8+ (If running from source)

### Running from source
1. Clone the repository or extract the files.
2. Create and activate a virtual environment (optional but recommended).
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python advanced_startup_manager.py
   ```

### Building the Executable
To build a standalone `.exe` using PyInstaller:
```bash
pyinstaller advanced_startup_manager.spec
```
The compiled executable will be located in the `dist/` folder.

## Troubleshooting

- **PermissionError**: Modifying `HKEY_LOCAL_MACHINE` or stopping specific system services requires Administrator privileges. Right-click the executable and select **"Run as administrator"**.
- **Blank Screen / Loading Issues**: Make sure that you have an active internet connection on the first launch so the Tailwind CSS CDN can be cached, or ensure WebView2 is installed on your Windows system.

## License

This project is licensed under the MIT License.
