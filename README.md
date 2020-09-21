# Lego Mario Controller

This is a small python script that connects to a Lego Mario toy and emits keystrokes for certaim movements of the figurine. I used it as a controller for Super Mario Brothers ([Video](https://twitter.com/r1ckp/status/1301074026975162368])).

I only tested it on MacOS 10.15 - it may or may not work on other opererating systems. I had to run the NES emulator in a Linux VM (Parallels or VirtualBox) because the native emulators on MacOS did ignore the virtual keypresses from python.

Unfortuately I have no time to support this but I'll accept pull requests.

## Dependencies

You need python3 and some packages that can be installed from the project root with `pip3 install -r requirements.txt`

## Running it

    python3 src/mario.py
    
## Customization

The keys can be configured in the top of the file `src/mario.py`. For special keys use the ones defined [here](https://pythonhosted.org/pynput/_modules/pynput/keyboard/_base.html#Key) (e.g. `key.enter`)
