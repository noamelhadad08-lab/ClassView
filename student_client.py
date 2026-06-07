import socket
import threading
import mss
import io
from PIL import Image,ImageTk
import time
import tkinter as tk

class StudentClient:
    def __init__(self,SERVER_IP,SERVER_PORT):
        self.SERVER_ADDR = (SERVER_IP, SERVER_PORT)
        self.client_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.chunk_size = 1300
        self.root=tk.Tk()
        self.entry = tk.Entry(self.root)
        self.screenshot_window = None
        self.label = None
        self.popup=None
        self.frames={}
        self.name=''
        self.screenshot_stop_event = threading.Event()
        self.heartbeat_stop_event = threading.Event()
        self.client_socket.settimeout(2)
        self.running=True


    def enter_name_window(self):

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.title("Login")
        self.root.geometry("1000x1000")

        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)


        self.popup = tk.Toplevel(self.root)
        self.popup.geometry("200x100")
        self.popup_label = tk.Label(self.popup, text="")
        self.popup_label.pack(expand=True)
        self.popup.withdraw()


        label = tk.Label(self.root, text="Enter your name:")
        label.pack(pady=10)

        
        self.entry.pack(pady=10)

        button = tk.Button(self.root, text="Enter", command=self.handle)
        button.pack(pady=10)
        
        self.root.mainloop()



    def handle(self):
        
        self.name=self.entry.get()
        if self.name=='':
            return  
        

        self.client_socket.sendto(f"STUDENT,{self.name}".encode(),self.SERVER_ADDR)
        self.root.withdraw()
        
        self.screenshot_window = tk.Toplevel(self.root)
        self.screenshot_window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.label = tk.Label(self.screenshot_window)

        
        self.screenshot_window.title("Student Screen")
        self.screenshot_window.geometry("1000x1000")

        self.screenshot_window.attributes("-fullscreen", True)
        self.screenshot_window.attributes("-topmost", True)

        self.label.pack(fill="both", expand=True)
        


        t1 = threading.Thread(target=self.handle_screenshots, daemon=True)
        t1.start()
        t2 = threading.Thread(target=self.send_heartbeat, daemon=True)
        t2.start()



    def send_screenshots(self):
        self.screenshot_stop_event.clear()
        frame_number=0
        with mss.mss() as sct:
            while not self.screenshot_stop_event.is_set():
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img=img.resize((960, 540))

                buffer = io.BytesIO()

                img.save(buffer, format="JPEG", quality=50)

                data= buffer.getvalue()
                chunks_number=(len(data)+self.chunk_size-1)//self.chunk_size
                for i in range(chunks_number):
                    start=i*self.chunk_size
                    end=start+self.chunk_size

                    chunk=data[start:end]

                    packet=(f'{frame_number},{i},{chunks_number},').encode()+chunk
                    self.client_socket.sendto(packet,self.SERVER_ADDR)

                time.sleep(0.1)
                frame_number+=1


    def send_heartbeat(self):
        self.heartbeat_stop_event.clear()
        print(5)
        while not self.heartbeat_stop_event.is_set():
            self.client_socket.sendto('alive'.encode(),self.SERVER_ADDR)
            time.sleep(0.3)

    def handle_screenshots(self):
        while self.running:
            try:
                data, server_addr = self.client_socket.recvfrom(65535)
            except socket.timeout:
                continue
            # print(1)
            if data==b'Watch':
                self.screenshot_window.attributes("-fullscreen", False)
                self.screenshot_window.attributes("-topmost", False)

                self.heartbeat_stop_event.set()
                time.sleep(0.1)
                self.screenshot_window.after(0,self.Clear_label)
                t = threading.Thread(target=self.send_screenshots, daemon=True)
                t.start()

            elif data==b'Share':
                self.screenshot_window.attributes("-fullscreen", True)
                self.screenshot_window.attributes("-topmost", True)
                
                print(50)
                time.sleep(0.1)
                self.screenshot_window.after(0,self.Clear_label)
                self.screenshot_stop_event.set()
                if self.heartbeat_stop_event.is_set():
                    t = threading.Thread(target=self.send_heartbeat, daemon=True)
                    t.start()
            
            elif(data==b'Teacherin'):
                continue


            # if(data==b'Teacherout'):
            #     continue
            
            else:
                frame_number,packet_number,length,packet=data.split(b',',3)


                frame_number=int(frame_number.decode())
                packet_number=int(packet_number.decode())
                length=int(length.decode())

                if frame_number not in self.frames:
                        self.frames[frame_number]={'packets': {}}

                self.frames[frame_number]["packets"][packet_number] = packet

                if(len(self.frames[frame_number]["packets"])==length):
                    image_data=b''
                    for i in self.frames[frame_number]["packets"]:
                        image_data+=self.frames[frame_number]["packets"][i]

                    image = Image.open(io.BytesIO(image_data))
                    self.screenshot_window.after(0, self.update_label, image)

                    del self.frames[frame_number]

    def update_label(self, image):
        
        w = self.label.winfo_width()
        h = self.label.winfo_height()

        image = image.resize((w, h))

        photo = ImageTk.PhotoImage(image)
        self.label.config(image=photo)  
        self.label.image = photo 


    def Clear_label(self):
        self.label.config(image='')  
        self.label.image = None 


    def on_close(self):
        self.running = False
        self.client_socket.close()
        self.root.destroy()
    
    # def notification(self,text):ד
    #     self.popup_label.config(text=text)

    #     self.popup.deiconify()

    #     self.root.after(2000, self.popup.withdraw)


student=StudentClient("192.168.68.63", 5000)
student.enter_name_window()