from setuptools import setup

APP = ['SpookyLoopMenulet.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleShortVersionString': '0.2.1',
        'LSUIElement': True,
        'CFBundleDevelopmentRegion' : 'en',
        'CFBundleIdentifier': 'org.bc.spookyloop',
        'CFBundleURLTypes': [{
            'CFBundleURLName': 'eMail Message',
            # these are the things you can call from a browser and it will open the app
            'CFBundleURLSchemes': [
                'spookyloop',
                'loopit',
            ]
        }]
    },
    'packages': ['rumps'],
}

setup(
    app=APP,
    name='SpookyLoop',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'], install_requires=['rumps']
)
