import tkinter as tk
from tkinter import messagebox, ttk
import telnetlib
import json

CONFIG_FILE = "config.json"
RELAYS_PER_BOARD = 27  # Updated to include the 2 AC relays

class RelayControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Relay Controller")
        self.load_config()
        
        # IP and Port Entry
        tk.Label(root, text="IP Address:").grid(row=0, column=0)
        self.ip_entry = tk.Entry(root)
        self.ip_entry.grid(row=0, column=1)
        self.ip_entry.insert(0, self.config.get("ip", "192.168.1.100"))
        
        tk.Label(root, text="Port:").grid(row=1, column=0)
        self.port_entry = tk.Entry(root)
        self.port_entry.grid(row=1, column=1)
        self.port_entry.insert(0, self.config.get("port", "23"))
        
        self.save_button = tk.Button(root, text="Save Config", command=self.save_config)
        self.save_button.grid(row=2, column=0, columnspan=2)
        
        # Board Selection Dropdown
        tk.Label(root, text="Number of Boards:").grid(row=3, column=0)
        self.num_boards = tk.IntVar(value=self.config.get("boards", 1))
        self.board_selector = ttk.Combobox(root, textvariable=self.num_boards, values=[1, 2, 3, 4], state="readonly")
        self.board_selector.grid(row=3, column=1)
        self.board_selector.bind("<<ComboboxSelected>>", lambda e: self.create_relay_controls())
        
        # Control Buttons
        self.clear_all_button = tk.Button(root, text="Clear All", command=self.clear_all_relays)
        self.clear_all_button.grid(row=4, column=0, columnspan=1)
        
        self.fire_all_button = tk.Button(root, text="Fire All", command=self.fire_all_relays)
        self.fire_all_button.grid(row=4, column=1, columnspan=1)
        
        self.relay_frame = tk.Frame(root)
        self.relay_frame.grid(row=5, column=0, columnspan=2)
        self.create_relay_controls()
        
    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {"ip": "192.168.1.100", "port": "23", "boards": 1}
    
    def save_config(self):
        self.config["ip"] = self.ip_entry.get()
        self.config["port"] = self.port_entry.get()
        self.config["boards"] = self.num_boards.get()
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)
        messagebox.showinfo("Success", "Configuration saved!")
    
    def create_relay_controls(self):
        for widget in self.relay_frame.winfo_children():
            widget.destroy()
        
        self.relay_states = {}
        num_relays = self.num_boards.get() * RELAYS_PER_BOARD
        
        for i in range(1, num_relays + 1):
            var = tk.BooleanVar()
            relay_number = i % RELAYS_PER_BOARD
            label = f"Relay {i}" if relay_number not in (0, 26, 27) else f"Relay {i} (AC)"
            chk = tk.Checkbutton(self.relay_frame, text=label, variable=var, command=lambda i=i: self.toggle_relay(i))
            chk.grid(row=(i-1) // 5, column=(i-1) % 5, sticky="w")
            self.relay_states[i] = var
    
    def send_command(self, command):
        try:
            ip = self.config["ip"]
            port = int(self.config["port"])
            
            print(f"Connecting to {ip}:{port}")  # Debugging output
            with telnetlib.Telnet(ip, port, timeout=5) as tn:
                print(f"Sending command: {command}")  # Debugging output
                tn.write(command.encode("ascii") + b"\r\n")
                response = tn.read_until(b"%", timeout=2)  # Wait for response
                print(f"Response: {response}")  # Debugging output
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to send command: {e}")
    
    def toggle_relay(self, relay):
        try:
            state = "S" if self.relay_states[relay].get() else "C"
            command = f"{state}{relay:02d}%"
            self.send_command(command)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle relay {relay}: {e}")
    
    def clear_all_relays(self):
        self.send_command("A%")
        for relay in self.relay_states:
            self.relay_states[relay].set(False)
    
    def fire_all_relays(self):
        command = "".join([f"S{relay:02d}%" for relay in self.relay_states])
        self.send_command(command)
        for relay in self.relay_states:
            self.relay_states[relay].set(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = RelayControllerApp(root)
    root.mainloop()
