import socket
import threading
import time
import mss
from PIL import Image, ImageTk
import io
import logging

IP = "0.0.0.0"
PORT = 5000

class Server:

    def __init__(self,IP,PORT):
        self.Ip=IP
        self.PORT=PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lock = threading.Lock()
        self.TeacherIn=False
        self.Teacheraddr=None
        self.students_frames={}
        self.teacher_frames={}
        self.chunk_size = 1300

    def recv_screenshot(self):
        logging.basicConfig(
        filename='log.txt',   # שם הקובץ
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.server_socket.bind(("0.0.0.0", 5000))
        while True:
            data, addr = self.server_socket.recvfrom(65535)
            if not self.TeacherIn and data==b"TEACHER":
                self.TeacherIn=True
                self.Teacheraddr=addr

            elif data==b"STUDENT" and self.TeacherIn:
                # name=data.decode().split(',')[1]
                if addr not in self.students_frames:
                    self.students_frames[addr] = {}

            elif addr==self.Teacheraddr and len(self.students_frames)>0:
                frame_number,packet_number,length,packet=data.split(b',',3)

                packet_number=int(packet_number.decode())
                frame_number=int(frame_number.decode())
                length=int(length.decode())


                if frame_number not in self.teacher_frames:
                    self.teacher_frames[frame_number]={'packets': {}}


                self.teacher_frames[frame_number]["packets"][packet_number] = packet
                if(len(self.teacher_frames[frame_number]["packets"])==length):
                        # image_data=b''
                        # for i in sorted(self.teacher_frames[frame_number]["packets"]):
                        #     image_data+=self.teacher_frames[frame_number]["packets"][i]


                        
                        for i in range(length):
                            # image_data+=self.teacher_frames[frame_number]["packets"][i]
                            # start=i*self.chunk_size
                            # end=start+self.chunk_size

                            # chunk=image_data[start:end]
                            # packet=(f'{frame_number},{i},{length},').encode()+chunk
                            
                            for key in self.students_frames:
                                chunk=self.teacher_frames[frame_number]["packets"][i]
                                packet=(f'{frame_number},{i},{length},').encode()
                                self.server_socket.sendto(packet+chunk,key)

                            
                        del self.teacher_frames[frame_number]
            
            elif addr in self.students_frames:
                frame_number,packet_number,length,packet=data.split(b',',3)

                packet_number=int(packet_number.decode())
                frame_number=int(frame_number.decode())
                length=int(length.decode())


                if frame_number not in self.students_frames[addr]:
                    self.students_frames[addr][frame_number]={'packets': {}}


                self.students_frames[addr][frame_number]["packets"][packet_number] = packet
                # self.students_frames[addr][frame_number]["last_update"]= time.time()
                # logging.info("add: "+str(addr)+": "+frame_number.__str__())
                if(len(self.students_frames[addr][frame_number]["packets"])==length):
                    image_data=b''
                    for i in self.students_frames[addr][frame_number]["packets"]:
                        image_data+=self.students_frames[addr][frame_number]["packets"][i]


                    
                    for i in range(length):
                        start=i*self.chunk_size
                        end=start+self.chunk_size

                        chunk=image_data[start:end]
                        _, student_port = addr
                        packet=(f'{frame_number},{i},{length},{student_port},').encode()+chunk
                        self.server_socket.sendto(packet,self.Teacheraddr)

                    # logging.info("delete: "+addr.__str__()+": "+frame_number.__str__())
                    del self.students_frames[addr][frame_number]
                
                    # for i,j in self.students_frames:
                    #     if(time.time()-self.students_frames[i][j]["last_update"]>1.0):
                    #         del self.students_frames[i][j]

server= Server(IP,PORT)
server.recv_screenshot()
    # def recv_picture(self):
        