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
        self.root = tk.Tk()
        # self.rootname=tk.Tk()
        self.label = tk.Label(self.root)
        self.frames={}
        # self.current_action='Clear'
        self.screenshot_stop_event = threading.Event()
        self.heartbeat_stop_event = threading.Event()
        self.client_socket.settimeout(2)

    def handle(self):
        # name=input("Enter name: ")
        # self.client_socket.sendto(f"STUDENT,{name}".encode(),self.addr)
        self.root.title("Student Screen")
        self.root.geometry("1000x1000")
        self.root.attributes("-fullscreen", False)
        # self.root.attributes("-topmost", True)
        self.label.pack(fill="both", expand=True)
        
        self.client_socket.sendto(f"STUDENT".encode(),self.SERVER_ADDR)


        t1 = threading.Thread(target=self.handle_screenshots)
        t1.start()
        t2 = threading.Thread(target=self.send_heartbeat)
        t2.start()
        self.root.mainloop()

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
        while True:
            try:
                data, server_addr = self.client_socket.recvfrom(65535)
            except socket.timeout:
                continue
            # print(1)
            if data==b'Watch':
                self.heartbeat_stop_event.set()
                time.sleep(0.1)
                self.root.after(0,self.Clear_label)
                # self.label.config(image='')  
                # self.label.image = None 
                t = threading.Thread(target=self.send_screenshots)
                t.start()

            elif data==b'Share':
                print(50)
                time.sleep(0.1)
                self.root.after(0,self.Clear_label)
                self.screenshot_stop_event.set()
                if self.heartbeat_stop_event.is_set():
                    t = threading.Thread(target=self.send_heartbeat)
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
                    self.root.after(0, self.update_label, image)

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


student=StudentClient("192.168.68.63", 5000)
student.handle()