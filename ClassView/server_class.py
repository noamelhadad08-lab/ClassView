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
        self.IP=IP
        self.PORT=PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lock = threading.Lock()
        self.TeacherIn=False
        self.Teacheraddr=None
        self.students_frames={}
        self.teacher_frames={'timeout':time.time(),'frames':{}}
        self.chunk_size = 1300
        self.timecheck=time.time()
        self.command=b'Share'
        # self.server_socket.settimeout(1)

    def handle_screenshots(self):
        # logging.basicConfig(
        # filename='log.txt',
        # level=logging.INFO,
        # format='%(asctime)s - %(levelname)s - %(message)s'
        # )
        self.server_socket.bind((self.IP, self.PORT))
        while True:
            try:
                data, addr = self.server_socket.recvfrom(65535)
            except ConnectionResetError:
                continue

            if data==b"TEACHER" and not self.TeacherIn:
                self.Teacheraddr=addr
                self.TeacherIn=True
                if len(self.students_frames)>0:
                    self.server_socket.sendto("Studentsin".encode(),addr)
                    print(15)

                    for i in self.students_frames:
                        self.server_socket.sendto('Teacherin'.encode(),i)
                        self.students_frames[i]['timeout']=time.time()
                    
                    
                    self.timecheck=time.time()
            
            if data==b"TEACHER" and self.TeacherIn:
                continue


            elif data==b"STUDENT":
                # name=data.decode().split(',')[1]
                self.students_frames[addr] = {'timeout':time.time(),'frames':{}}
                if(self.TeacherIn):
                    self.server_socket.sendto('Teacherin'.encode(),addr)

                    if(len(self.students_frames)==1):
                        self.timecheck=time.time()
                        self.server_socket.sendto("Studentsin".encode(),self.Teacheraddr)
                    else:
                        self.server_socket.sendto(self.command,addr)


            elif data==b"alive":
                if(addr==self.Teacheraddr):
                    self.teacher_frames['timeout']=time.time()
                else:
                    self.students_frames[addr]['timeout']=time.time()
            
            elif addr==self.Teacheraddr and len(self.students_frames)>0 and (data==b'Share' or data==b'Watch') :
                self.command=data
                for i in self.students_frames:
                    self.server_socket.sendto(data,i)
                # if len(self.students_frames)==0:



            elif addr==self.Teacheraddr and len(self.students_frames)>0:
                frame_number,packet_number,length,packet=data.split(b',',3)

                packet_number=int(packet_number.decode())
                frame_number=int(frame_number.decode())
                length=int(length.decode())


                if frame_number not in self.teacher_frames['frames']:
                    self.teacher_frames['frames'][frame_number]={'packets': {},'frame_timeout':time.time()}
                    self.teacher_frames['timeout']=time.time()


                self.teacher_frames['frames'][frame_number]["packets"][packet_number] = packet
                if(len(self.teacher_frames['frames'][frame_number]["packets"])==length):
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
                                chunk=self.teacher_frames['frames'][frame_number]["packets"][i]
                                packet=(f'{frame_number},{i},{length},').encode()
                                self.server_socket.sendto(packet+chunk,key)

                            
                        del self.teacher_frames['frames'][frame_number]
            
            elif addr in self.students_frames and self.TeacherIn:
                frame_number,packet_number,length,packet=data.split(b',',3)
                
                packet_number=int(packet_number.decode())
                frame_number=int(frame_number.decode())
                length=int(length.decode())


                if frame_number not in self.students_frames[addr]['frames']:
                    self.students_frames[addr]['frames'][frame_number]={'packets': {},'frame_timeout':time.time()}
                    self.students_frames[addr]['timeout']=time.time()


                self.students_frames[addr]['frames'][frame_number]["packets"][packet_number] = packet
                # self.students_frames[addr]['frames'][frame_number]["last_update"]= time.time()
                # logging.info("add: "+str(addr)+": "+frame_number.__str__())
                if(len(self.students_frames[addr]['frames'][frame_number]["packets"])==length):
                    image_data=b''
                    for i in self.students_frames[addr]['frames'][frame_number]["packets"]:
                        image_data+=self.students_frames[addr]['frames'][frame_number]["packets"][i]


                    
                    for i in range(length):
                        start=i*self.chunk_size
                        end=start+self.chunk_size

                        chunk=image_data[start:end]
                        _, student_port = addr
                        packet=(f'{frame_number},{i},{length},{student_port},').encode()+chunk
                        self.server_socket.sendto(packet,self.Teacheraddr)

                    # logging.info("delete: "+addr.__str__()+": "+frame_number.__str__())
                    del self.students_frames[addr]['frames'][frame_number]
                
            
            
            if (time.time()-self.timecheck>3):
                if len(self.students_frames)>0:

                    del_list=[]
                    for i in self.students_frames:
                        if(time.time()-self.students_frames[i]['timeout']>2):
                            print(1)
                            _, student_port = i
                            packet=(f'del,{student_port}')
                            if self.TeacherIn:
                                self.server_socket.sendto(packet.encode(),self.Teacheraddr)
                            del_list.append(i)

                    for i in del_list:
                        del self.students_frames[i]
                    
                    if self.TeacherIn and len(self.students_frames)==0:
                        self.server_socket.sendto('zerostudents'.encode(),self.Teacheraddr)

                    for i in self.students_frames:
                        list_students_frame_number=list(self.students_frames[i]['frames'].keys())
                        for j in list_students_frame_number:

                            if(time.time()-self.students_frames[i]['frames'][j]['frame_timeout']>2):
                                del self.students_frames[i]['frames'][j]


                if self.TeacherIn:
                    
                    if time.time()-self.teacher_frames['timeout']>2:
                        print(7)
                        self.TeacherIn=False
                        self.teacher_frames={'timeout':time.time(),'frames':{}}
                        for i in self.students_frames:
                            self.server_socket.sendto(b'Share',i)
                        self.command=b'Share'


                    list_teacher_frame_number=list(self.teacher_frames['frames'].keys())
                    for i in list_teacher_frame_number:
                        if(time.time()-self.teacher_frames['frames'][i]['frame_timeout']>2):
                            del self.teacher_frames['frames'][i]

                    self.timecheck=time.time()
                


server= Server(IP,PORT)
server.handle_screenshots()
    # def recv_picture(self):
        