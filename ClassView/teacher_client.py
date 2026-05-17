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
    
    def handle(self):
        self.root.title("Teacher Screen")
        # self.root.state("zoomed")
        self.root.geometry("1000x1000")
        self.root.attributes("-fullscreen", False)

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

        t1 = threading.Thread(target=self.recv_screenshots)
        t2 = threading.Thread(target=self.send_screen_shot)
        t1.start()
        t2.start()
        self.root.mainloop()
        

    
    def send_screen_shot(self):
        frame_number=0
        with mss.mss() as sct:
            while True:
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

                time.sleep(0.1)
                frame_number+=1

    def recv_screenshots(self):
        while True:
            data, server_addr = self.client_socket.recvfrom(65535)

            if(data.split(b',')[0]==b'del'):
                port=int(data.decode().split(',')[1])
                self.root.after(0, self.handle_delete, port)
            
                continue

            # if data[0:7]==b"STUDENT":
            #     name=data.decode().split(',')[1]
            
            frame_number,packet_number,length,port,packet=data.split(b',',4)
            port=int(port.decode())

            if port not in self.students_frames:
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


    def handle_delete(self, port):
        # last_label.config(image="")
        # last_label.image = None
        del self.students_frames[port]
        

        for i,j in enumerate(self.students_frames):
            self.students_frames[j]["label"] = self.labels[i]
            # self.students_frames[j]['label'].grid(row=int(self.labels[i].grid_info()["row"]),column=self.labels[i].grid_info()['column'])
            


        self.labels[len(self.students_frames)].config(image="")
        self.labels[len(self.students_frames)].image = None
        # start =False

        # cur_row=self.students_frames[port]['label'].grid_info()["row"]
        # cur_column=self.students_frames[port]['label'].grid_info()["column"]

        # for i,j in enumerate(self.students_frames):
        #     #and i+1<len(list(self.students_frames.items()
        #     if start==True:
        #         next_row=self.students_frames[j]['label'].grid_info()["row"]
        #         next_column=self.students_frames[j]['label'].grid_info()["column"]
        #         label=self.students_frames[j]['label']

        #         self.students_frames[j]['label'].grid(row=int(cur_row),column=int(cur_column),sticky='nsew')

        #         cur_row=next_row
        #         cur_column=next_column
        #         last_label = label

        #     if j==port:
        #         start=True


        
        # del self.students_frames[port]

    def update_label(self, image,port):
        label = self.students_frames[port]["label"]

        w = max(label.winfo_width(), 50)
        h = max(label.winfo_height(), 50)

        image = image.resize((w, h))
        photo = ImageTk.PhotoImage(image)
        self.students_frames[port]["label"].config(image=photo)  
        self.students_frames[port]["label"].image = photo 


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


