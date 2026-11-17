from setuptools import setup

APP = ['main.py']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Easy Typer',
        'CFBundleDisplayName': 'Easy Typer',
        'CFBundleIdentifier': 'com.deweyai.easytyper',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Runs cleanly in the menu bar without a Dock icon
        'NSAppleEventsUsageDescription': 'Easy Typer needs permission to type into your active document.',
    },
    'packages': ['rumps', 'pyautogui'],
}

setup(
    app=APP,
    name='Easy Typer',
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
