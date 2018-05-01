# -*- coding:utf-8 -*-
import socket
import numpy as np
import cv2
import time
import shutil
import math
import os
import threading

raspberrypi_addr = "192.168.1.5"


def send_time(t_ms):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((raspberrypi_addr, 9999))
    s.send(str(t_ms).encode("utf-8"))
    s.close()


def get_template(cap):
    point_start = (0, 0)
    point_end = (0, 0)
    template_capture = ""
    template_capture_ori = ""
    template_windowname = "template"


    def on_mouse(event, x, y, flags, param):
        nonlocal point_start
        nonlocal point_end
        nonlocal template_capture
        nonlocal template_capture_ori
        if event == cv2.EVENT_LBUTTONDOWN:
            point_start = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            template_capture = template_capture_ori.copy()
            cv2.rectangle(template_capture, point_start, (x, y), (255, 0, 0), 2)
            cv2.imshow(template_windowname, template_capture)
        elif event == cv2.EVENT_LBUTTONUP:
            point_end = (x, y)
            template_capture = template_capture_ori.copy()
            cv2.rectangle(template_capture, point_start, point_end, (0, 0, 255), 2)
            cv2.imshow(template_windowname, template_capture)
            min_x = min(point_start[0], point_end[0])
            min_y = min(point_start[1], point_end[1])
            width = abs(point_end[0]-point_start[0])
            height = abs(point_end[1]-point_start[1])
            template_img = template_capture[min_y:min_y+height, min_x:min_x+width]
            cv2.imwrite("template.jpg", template_img)
            cv2.imshow(template_windowname, template_img)


    while True:
        ret, frame = cap.read()
        frame = np.rot90(frame)
        frame = np.rot90(frame)
        frame = np.rot90(frame)
        cv2.imshow(template_windowname, frame)
        if cv2.waitKey(1) == 32: #空格键

            template_capture_ori = frame
            break
    template_capture = template_capture_ori.copy()
    cv2.imshow(template_windowname, template_capture)
    cv2.setMouseCallback(template_windowname, on_mouse)

global man_pos
global board_pos
global distance
man_pos = (0, 0)
board_pos = (0, 0)
distance = 0

class CameraReader(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.threshold_canny_low = 29
        self.threshold_canny_high = 57
        self.threshold_guss = 3
        self.cap_focus = 87
        self.cap_exposuer =10
        self.cap = cv2.VideoCapture(0)


    def get_man_pos(self, frame_src, frame_dst, template_img):
        template_h = template_img.shape[0]
        template_w = template_img.shape[1]
        threshold_man = 0.5
        res = cv2.matchTemplate(frame_src, template_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > threshold_man:
            cv2.rectangle(frame_dst, max_loc, (max_loc[0] + template_w, max_loc[1] + template_h), (255, 0, 0), 1)
            return (int(max_loc[0] + template_w/2), int(max_loc[1] + template_h/2))
        else:
            print(min_val)
            return (0, 0)

    def get_board_pos(self, frame_src, frame_dst, man_pos):
        img_gauss = cv2.GaussianBlur(frame_src, (5, 5), 5)
        img_canny = cv2.Canny(img_gauss, self.threshold_canny_low, self.threshold_canny_high)
        #cv2.imshow("canny", img_canny)
        img_canny_dst = img_canny.copy()
        for j in range(max(man_pos[1]-50, 0), 639):
            for i in range(max(man_pos[0]-80, 0), min(man_pos[0]+80, 479)):
                img_canny_dst[j][i] = 0
        y_top = np.nonzero([max(row) for row in img_canny_dst])[0][0]
        x_top = int(np.mean(np.nonzero(img_canny_dst[y_top])))
        y_bottom = y_top + 50
        H, W = img_canny.shape
        for row in range(y_bottom, H):
            if img_canny[row, x_top]!=0:
                y_bottom = row
                break
        board_pos = (x_top, int((y_top+y_bottom)/2))
        cv2.circle(frame_dst, (x_top, int((y_top+y_bottom)/2)), 5, (0,255,255), 5)
        cv2.line(frame_dst , board_pos, man_pos, (0, 0,255))
        cv2.imshow("canny_dst", img_canny_dst)
        return board_pos



    def change_canny_low(self, x):
        self.threshold_canny_low = x

    def change_guss(self, x):
        self.threshold_guss = x

    def change_canny_high(self, x):
        self.threshold_canny_high = x

    def change_cap_focus(self, x):
        self.cap_focus = x
        self.cap.set(cv2.CAP_PROP_FOCUS, float(x)/255)


    def change_cap_exposuer(self, x):
        self.cap_exposuer = x
        self.cap.set(cv2.CAP_PROP_EXPOSURE, float(x)/255)

    def run(self):
        global man_pos
        global board_pos
        global distance
        window_name_src = "window_name_src"
        window_name_dst = "window_name_dst"

        #get_template(self.cap)
        template_img = cv2.imread("template.jpg")
        cv2.namedWindow(window_name_dst)
        cv2.createTrackbar("canny_low", window_name_dst, 1, 255, self.change_canny_low)
        cv2.createTrackbar("canny_high", window_name_dst, 1, 255, self.change_canny_high)
        cv2.createTrackbar("cap_focus", window_name_dst, 1, 255, self.change_cap_focus)
        cv2.createTrackbar("cap_exposuer", window_name_dst, 1, 255, self.change_cap_exposuer)
        cv2.createTrackbar("cap_guss", window_name_dst, 5, 255, self.change_guss)
        while True:
            ret, frame_src = self.cap.read()
            frame_src = np.rot90(frame_src)
            frame_src = np.rot90(frame_src)
            frame_src = np.rot90(frame_src)
            frame_dst = frame_src.copy()

            #找到人的位置
            man_pos = self.get_man_pos(frame_src, frame_dst, template_img)
            if man_pos != (0, 0):
            #找到板子的位置
                board_pos = self.get_board_pos(frame_src, frame_dst, man_pos)
                distance = (man_pos[0]-board_pos[0]) ** 2 + (man_pos[1]-board_pos[1]) ** 2
                distance = distance ** 0.5

            cv2.imshow(window_name_dst, frame_dst)
            if cv2.waitKey(33) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()


class Player(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global man_pos
        global board_pos
        global distance
        input("开始吗？")
        while True:
            #print(man_pos, board_pos)
            time.sleep(3)
            print(distance)
            jump_time = int(distance * 2.92)
            send_time(jump_time)


def main():
    camera_reader = CameraReader()
    camera_reader.start()
    player = Player()
    player.start()


    #send_time(1000)


if __name__ == '__main__':
    main()