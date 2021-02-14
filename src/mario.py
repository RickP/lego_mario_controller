import asyncio
import time
import wx
from wxasync import WxAsyncApp, StartCoroutine
from pynput.keyboard import Key, Controller
from bleak import BleakScanner, BleakClient

# Key assignments
KEY_JUMP = 'a'
KEY_LEAN_FORWARD = Key.right
KEY_LEAN_BACKWARD = Key.left
KEY_RED_TILE = 'b'
KEY_GREEN_TILE = Key.down

# Timing
BUTTON_TIME_DEFAULT = 0.1
BUTTON_TIME_JUMP = 1.5

# BLE stuff
LEGO_CHARACTERISTIC_UUID = "00001624-1212-efde-1623-785feabcd123"
LEGO_SERVICE_UUID = "00001623-1212-efde-1623-785feabcd123"
SUBSCRIBE_IMU_COMMAND = bytearray([0x0A, 0x00, 0x41, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x01])
SUBSCRIBE_RGB_COMMAND = bytearray([0x0A, 0x00, 0x41, 0x01, 0x00, 0x05, 0x00, 0x00, 0x00, 0x01])

# GUI class
class MarioFrame(wx.Frame):

    def __init__(self, parent=None, id=-1, title="Lego Mario Keys"):
        wx.Frame.__init__(self, parent, id, title, size=(450, 100))
        self.initGUI()
        self.controller = MarioController(self)
        StartCoroutine(self.controller.run(), self)

    def initGUI(self):

        panel = wx.Panel(self)

        font = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.DEFAULT)

        self.status_field = wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
        self.status_field.SetFont(font)

        self.cam_field = wx.StaticText(self, label="", style=wx.ALIGN_LEFT, size=wx.Size(50, wx.DefaultCoord))
        self.cam_field.SetFont(font)

        self.accel_field = wx.StaticText(self, label="", style=wx.ALIGN_LEFT, size=wx.Size(200, wx.DefaultCoord))
        self.accel_field.SetFont(font)

        self.key_switch_label = wx.StaticText(self, label="Send keys: ", style=wx.ALIGN_RIGHT, size=wx.Size(100, wx.DefaultCoord))
        self.key_switch_label.SetFont(font)

        self.key_switch = wx.CheckBox(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.status_field, flag=wx.ALL, border=5, )

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.cam_field, flag=wx.ALL|wx.FIXED_MINSIZE, border=5)
        hbox.Add(self.accel_field, flag=wx.ALL|wx.FIXED_MINSIZE, border=5)
        hbox.Add(self.key_switch_label, flag=wx.ALL|wx.FIXED_MINSIZE, border=5)
        hbox.Add(self.key_switch, flag=wx.ALL, border=5)

        vbox.Add(hbox, flag=wx.ALL, border=5)

        self.SetSizer(vbox)

# Class for the controller
class MarioController:

    def __init__(self, gui):
        self.gui = gui
        self.keyboard = Controller()
        self.current_tile = 0
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.is_connected = False

    def signed(char):
        return char - 256 if char > 127 else char

    async def process_keys(self):
        if self.is_connected and self.gui.key_switch.GetValue():
            if self.current_tile == 1:
                self.keyboard.press(KEY_RED_TILE)
                await asyncio.sleep(BUTTON_TIME_DEFAULT)
                self.keyboard.release(KEY_RED_TILE)
                self.current_tile = 0
            elif self.current_tile == 2:
                self.keyboard.press(KEY_GREEN_TILE)
                await asyncio.sleep(BUTTON_TIME_DEFAULT)
                self.keyboard.release(KEY_GREEN_TILE)
                self.current_tile = 0
            if self.current_z > 10:
                self.keyboard.press(KEY_LEAN_BACKWARD)
            elif self.current_z < -10:
                self.keyboard.press(KEY_LEAN_FORWARD)
            else:
                self.keyboard.release(KEY_LEAN_BACKWARD)
                self.keyboard.release(KEY_LEAN_FORWARD)
            if self.current_x > 5:
                self.keyboard.press(KEY_JUMP)
                await asyncio.sleep(BUTTON_TIME_JUMP)
                self.keyboard.release(KEY_JUMP)
        await asyncio.sleep(0.05)


    def notification_handler(self, sender, data):
        # Camera sensor data
        if data[0] == 8:

            # RGB code
            if data[5] == 0x0:
                if data[4] == 0xb8:
                    self.gui.cam_field.SetLabel("Start tile")
                    self.current_tile = 3
                if data[4] == 0xb7:
                    self.gui.cam_field.SetLabel("Goal tile")
                    self.current_tile = 4
                print("Barcode: " + " ".join(hex(n) for n in data))

            # Red tile
            elif data[6] == 0x15:
                self.gui.cam_field.SetLabel("Red tile")
                self.current_tile = 1
            # Green tile
            elif data[6] == 0x25:
                self.gui.cam_field.SetLabel("Green tile")
                self.current_tile = 2
            # No tile
            elif data[6] == 0x1a:
                self.gui.cam_field.SetLabel("No tile")
                self.current_tile = 0


        # Accelerometer data
        elif data[0] == 7:
            self.current_x = int((self.current_x*0.5) + (MarioController.signed(data[4])*0.5))
            self.current_y = int((self.current_y*0.5) + (MarioController.signed(data[5])*0.5))
            self.current_z = int((self.current_z*0.5) + (MarioController.signed(data[6])*0.5))
            self.gui.accel_field.SetLabel("X: %i | Y: %i | Z: %i" % (self.current_x, self.current_y, self.current_z))


    async def run(self):
        while True:
            self.is_connected = False
            self.gui.status_field.SetLabel("Looking for Mario. Switch on and press Bluetooth key.")
            self.gui.cam_field.SetLabel("")
            self.gui.accel_field.SetLabel("")
            devices = await BleakScanner.discover()
            for d in devices:
                if d.name.lower().startswith("lego mario") or LEGO_SERVICE_UUID in d.metadata['uuids']:
                    self.gui.status_field.SetLabel("Found Mario!")
                    try:
                        async with BleakClient(d.address) as client:
                            await client.is_connected()
                            self.gui.status_field.SetLabel("Mario is connected")
                            self.is_connected = True
                            await client.start_notify(LEGO_CHARACTERISTIC_UUID, self.notification_handler)
                            await asyncio.sleep(0.1)
                            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, SUBSCRIBE_IMU_COMMAND)
                            await asyncio.sleep(0.1)
                            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, SUBSCRIBE_RGB_COMMAND)
                            while await client.is_connected():
                                await self.process_keys()
                    except:
                        pass


# Run it
if __name__ == "__main__":
    # The application object.
    app = WxAsyncApp()
    # The app frame
    frm = MarioFrame()
    # Drawing it
    frm.Show()

    # Start the main loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.MainLoop())
