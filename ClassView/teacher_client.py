import socket
import threading
import time
import mss
from PIL import Image, ImageTk
import io
import tkinter as tk



class TeacherClient:
    def __init__(self,server_ip,listen_port,server_port):
        self.listen_port=listen_port
        self.root = tk.Tk()
        self.labels = []
        self.server_addr = (server_ip, server_port)
        self.client_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.students_frames={}
        self.chunk_size = 1300
        self.current_action='None'
        self.heartbeat_stop_event = threading.Event()
        self.listen_stop_event = threading.Event()
        self.client_socket.settimeout(2)
        self.Share_button=tk.Button(self.root)
        self.Watch_button=tk.Button(self.root)
    
    def handle(self):
        self.root.title("Teacher Screen")
        # self.root.state("zoomed")
        self.root.geometry("1000x1000")
        self.root.attributes("-fullscreen", False)
        
        frame = tk.Frame(self.root)
        frame.grid(row=5, column=0, columnspan=6, pady=20)

        self.Share_button = tk.Button(frame, text="Share Window", command=self.Share)
        self.Watch_button = tk.Button(frame, text="Watch Students", command=self.Watch)

        self.Share_button.pack(side="left", padx=10)
        self.Watch_button.pack(side="left", padx=10)
        
        # self.Share_button.config(state="disabled")
        # self.Watch_button.config(state="disabled")

        for i in range(5):
            for j in range(6):

                label = tk.Label(self.root)
                label.grid(row=i,column=j,sticky="nsew")
                self.labels.append(label)
        
        for i in range(5):
            self.root.grid_rowconfigure(i, weight=1,uniform="rows")
        
        for i in range(6):
            self.root.grid_columnconfigure(i, weight=1,uniform="cols")
        

        
        self.client_socket.bind(('0.0.0.0',self.listen_port))
        self.client_socket.sendto("TEACHER".encode(),self.server_addr)
        

        t = threading.Thread(target=self.send_heartbeat)
        t.start()

        t = threading.Thread(target=self.handle_packets)
        t.start()


        # self.Watch_loop()

        # t1 = threading.Thread(target=self.update_data)
        # t2 = threading.Thread(target=self.send_screen_shot)
        # t1.start()
        # t2.start()
        self.root.mainloop()
        
    
    def Share(self):
        self.current_action='Share'
        time.sleep(0.1)
        # time.sleep(0.2)
        # self.root.after(0,self.Clear_labels)

        self.Share_button.config(state="disabled")
        self.Watch_button.config(state="normal")

        self.heartbeat_stop_event.set()
        self.client_socket.sendto('Share'.encode(),self.server_addr)
        threading.Thread(target=self.Share_loop, daemon=True).start()

    def Share_loop(self):
        # btn.config(state="disabled")
        frame_number=0
        with mss.mss() as sct:
            while self.current_action=='Share':
                self.send_screen_shot(sct,frame_number)
                frame_number+=1
                time.sleep(0.1)
                


    def send_screen_shot(self,sct,frame_number):
    # frame_number=0
    # with mss.mss() as sct:
    #     while self.current_action=='Share':
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
                self.client_socket.sendto(packet,self.server_addr)

            # time.sleep(0.1)
            # frame_number+=1



    def Watch(self):
        self.Watch_button.config(state="disabled")
        self.Share_button.config(state="normal")
        self.current_action='Watch'
        time.sleep(0.1)
        self.client_socket.sendto('Watch'.encode(),self.server_addr)
        if self.heartbeat_stop_event.is_set():
            threading.Thread(target=self.send_heartbeat, daemon=True).start()
        # threading.Thread(target=self.Watch_loop, daemon=True).start()

        
    
    def handle_packets(self):
        while True:
            try:
                data, server_addr = self.client_socket.recvfrom(65535)
            except socket.timeout:
                continue

            if data==b'Studentsin':
                self.Share_button.config(state="normal")
                self.Watch_button.config(state="normal")


            elif data==b'zerostudents':
                self.current_action=b'None'
                print(3)
                # self.root.after(0,self.Clear_labels)
                self.Share_button.config(state="disabled")
                self.Watch_button.config(state="disabled")
                if self.heartbeat_stop_event.is_set():
                    threading.Thread(target=self.send_heartbeat, daemon=True).start()


            elif(data.split(b',')[0]==b'del'):
                port=int(data.decode().split(',')[1])

                try:
                    del self.students_frames[port]
                    self.root.after(0, self.handle_delete)
                except:
                    continue
            
            
            else:

                frame_number,packet_number,length,port,packet=data.split(b',',4)
                port=int(port.decode())

                if port not in self.students_frames:
                    print(1)
                    self.students_frames[port] = {"label":self.labels[len(self.students_frames)]}


                packet_number=int(packet_number.decode())
                frame_number=int(frame_number.decode())
                length=int(length.decode()) 


                if frame_number not in self.students_frames[port]:
                    self.students_frames[port][frame_number]={'packets': {}}

                self.students_frames[port][frame_number]["packets"][packet_number] = packet

                if(len(self.students_frames[port][frame_number]["packets"])==length):
                    image_data=b''
                    for i in self.students_frames[port][frame_number]["packets"]:
                        image_data+=self.students_frames[port][frame_number]["packets"][i]

                    image = Image.open(io.BytesIO(image_data))
                    self.root.after(0, self.update_label, image,port)

                    del self.students_frames[port][frame_number]
                


    def send_heartbeat(self):
        self.heartbeat_stop_event.clear()
        while not self.heartbeat_stop_event.is_set():
            self.client_socket.sendto('alive'.encode(),self.server_addr)
            time.sleep(0.3)
    



    def Clear_labels(self):
        for i in range(len(self.labels)):
            self.labels[i].config(image="")
            self.labels[i].image = None


    # def update_data(self,data):

        


    def handle_delete(self):
        print(8)

        for i,j in enumerate(self.students_frames):
            self.students_frames[j]["label"] = self.labels[i]

        self.labels[len(self.students_frames)].config(image="")
        self.labels[len(self.students_frames)].image = None


    def update_label(self, image,port):
        if self.current_action=='Watch':
            label = self.students_frames[port]["label"]

            w = max(label.winfo_width(), 50)
            h = max(label.winfo_height(), 50)

            image = image.resize((w, h))
            photo = ImageTk.PhotoImage(image)
            self.students_frames[port]["label"].config(image=photo)  
            self.students_frames[port]["label"].image = photo 
        else:
            self.students_frames[port]["label"].config(image='')  
            self.students_frames[port]["label"].image = None 


PORT = 5001
SERVERIP="192.168.68.63"
SERVERPORT=5000
teacher=TeacherClient(SERVERIP, PORT,SERVERPORT)
teacher.handle()
    #     self.root.title("Teacher Screen")
    #     self.root.geometry("800x600")
    #     self.root.attributes("-fullscreen", False)
    #     self.label.pack()

    #     server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     server_socket.bind((self.IP, self.PORT))
    #     server_socket.listen()
        
    #     accept_thread = threading.Thread(target=self.accept_clients,args=(server_socket,))
    #     accept_thread.start()
        
    #     self.root.mainloop()

        
            
    
    # def accept_clients(self,server_socket):
    #     # t1 = threading.Thread(target=self.send_screen_shot)
    #     while True:
    #         client_socket, _ = server_socket.accept()
    #         client_thread = threading.Thread(target=self.handle_client,args=(client_socket,))
    #         client_thread.start()
       

    # def handle_client(self,client_socket):
    #     handle_thread = threading.Thread(target=self.show_screen_shot,args=(client_socket,))
    #     handle_thread.start()


    # def show_screen_shot(self,client_socket):
    #     while True:
    #         size=""
    #         size_chunck=client_socket.recv(1).decode()

    #         while size_chunck!='\n':
    #             size+=size_chunck
    #             size_chunck=client_socket.recv(1).decode()

    #         size=int(size.strip())
    #         image_data = b""    

    #         while len(image_data) < size:
    #             remaining = size - len(image_data)
    #             chunk = client_socket.recv(min(4096,remaining))
    #             if not chunk:
    #                 break
    #             image_data += chunk

    #         image = Image.open(io.BytesIO(image_data))
    #         image = image.resize((800, 600))

    #         self.root.after(0, self.update_label, image)

    # def update_label(self, image):
    #     photo = ImageTk.PhotoImage(image)
    #     self.label.config(image=photo)
    #     self.label.image = photo


