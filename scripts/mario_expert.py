"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import random
import numpy as np

import cv2
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent


class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        act_freq: int = 1,
        emulation_speed: int = 1,
        headless: bool = False,
        
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button
        self.prev_mario_x = 0
        self.curr_mario_x = 0
        self.stuck = 0 #general stuck
        self.stuck_on_pipe = 0 #specific scenario
        self.hole_count = 0
        self.prev_x = 0
        self.prev_y = 0
    

    def run_action(self, action: int, duration: int = None, action2: int = None, duration2: int = None, sprint: bool = True) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        #print(self.game_area()) 

        # Simply toggles the buttons being on or off for a duration of act_freq
        if duration == None:
            duration = self.act_freq

        if self.stuck == 4:
            print("Print reached here")
            self.pyboy.send_input(self.valid_actions[1])
            for _ in range(5):
                self.pyboy.tick()
            self.pyboy.send_input(self.release_button[1])
            #self.pyboy.tick()
            self.stuck = 0

        if sprint == True:
            self.pyboy.send_input(self.valid_actions[5])
            #self.pyboy.tick()
        else: 
            self.pyboy.send_input(self.release_button[5])
            #self.pyboy.tick()
            
        self.pyboy.send_input(self.valid_actions[action])
        #self.pyboy.send_input(self.valid_actions[2])
        for _ in range(duration):
            if action2 != None or duration2 != None:
                self.pyboy.send_input(self.valid_actions[action2])
                if 1305 <= self.curr_mario_x <= 1400:
                    print("go down 2nd uniquue pipe")
                    self.pyboy.send_input(self.valid_actions[0])
                    for _ in range(8):
                        self.pyboy.tick()
                    break
                for _ in range(duration2):
                    self.pyboy.tick()
                self.pyboy.send_input(self.release_button[action2])   
            self.pyboy.tick()
        #used mainly for consecutive 
            
        self.pyboy.send_input(self.release_button[action])
        
        if action2 != None:
            self.pyboy.send_input(self.release_button[action2])   
        for _ in range(duration): 
            self.pyboy.tick()


        




class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path

        self.environment = MarioController(headless=headless)

        self.video = None

    def choose_action(self):

        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()
        #print(game_area.shape)

        hole_found = self.find_holes()
        found_qBlocks = self.find_qBlocks()
        on_pipe = self.on_pipe()
        find_mario = self.find_mario()

        #Maybe add a condition where if it detects the star music playing, curr_mario_x be set to prev_mario_x instead?
        self.environment.curr_mario_x = self.environment.get_x_position() #true position 
        prev_mario_x = self.environment.prev_mario_x

        if find_mario is not None:
            x, y = find_mario
            self.environment.prev_x = x
            self.environment.prev_y = y
        else:
            x = self.environment.prev_x
            y = self.environment.prev_y

        #stuck = self.environment.stuck
        # Implement your code here to choose the best action
        #time.sleep(0.1)
        #return random.randint(0, len(self.environment.valid_actions) - 1)

        mario_x = self.environment._read_m(0xC202) #relative
        mario_y = self.environment._read_m(0xC201)
 
        for i in range(10): # loops through 9 indexes of the object table 
            address = int(f"0xD1{i}0", 16) #convert the string to hex

            #goomba detection
            if self.environment._read_m(address) == 00: #goomba

                goomba_addr = int(f"0xD1{i}3", 16)  #x position  
                goomba_x = self.environment._read_m(goomba_addr)
                goomba_addr = int(f"0xD1{i}2", 16) #y position
                goomba_y = self.environment._read_m(goomba_addr)

                #print("mario", mario_y)
                #print("goomba", goomba_y)

                if (goomba_x-mario_x) < 15 and (goomba_x - mario_x) > 0 and  0 < (goomba_y-mario_y) < 3 :
                    print('goomba jump')
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 1, None, None, False)
                #for the nasty goombas who are underneath mario
                elif (goomba_x - mario_x) < 15 and (goomba_x - mario_x) > 0 and -5 <= (goomba_y - mario_y) < 0:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 1, None, None, False)
                #for gooombas that are located to left of mario
                elif -5 < (goomba_x - mario_x) < 0 and 0 < (goomba_y - mario_y) < 3:
                    print('goomba jump when located left')
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (2, 2, 4, 4, False)
                elif mario_y - goomba_y > 5 and  13 < goomba_x - mario_x < 20: #original: 13 < goomba_x - mario_x < 20
                    print("goomba above")
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (1, 5, None, None, True) 
                elif  3 <= mario_y - goomba_y <= 8 and 1 < goomba_x - mario_x < 5 and self.environment._read_m(0xC20A) == 0x01: 
                    print("Goomba unique for 1-2")
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 5, None, None, False)
            #Turtle detection
            elif self.environment._read_m(address) == 0x04: 
                turtle_addr = int(f"0xD1{i}3", 16) #x position
                turtle_x = self.environment._read_m(turtle_addr)
                turtle_addr = int(f"0xD1{i}2", 16)
                turtle_y = self.environment._read_m(turtle_addr)

                if (turtle_x-mario_x) < 12 and (turtle_x - mario_x) > 0 and (turtle_y-mario_y) < 3:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 1, None, None, False)
                elif mario_y - turtle_y > 5 and turtle_x - mario_x < 20:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (1, 5, None, None, True) 
            #Bat detection
            elif self.environment._read_m(address) == 0x0E:
                bat_addr = int(f"0xD1{i}3", 16)
                bat_x = self.environment._read_m(bat_addr)
                bat_addr = int(f"0xD1{i}2", 16)
                bat_y = self.environment._read_m(bat_addr)
                if (bat_x-mario_x) < 12 and (bat_x - mario_x) > 0 and (bat_y-mario_y) < 3:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 14, 2, 1, True)
                # elif 0<= (bat_x) <= 2 and (bat_y - mario_y) < 3:
                #     self.environment.prev_mario_x = self.environment.curr_mario_x
                #     return (1, 5, None, None, True)
                elif mario_y - bat_y > 5 and bat_x - mario_x < 20:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (1, 8, None, None, True)
            #picks powerups. Currently mushrooms
            elif self.environment._read_m(address) == 0x28 or self.environment._read_m(address) == 0x29 or self.environment._read_m(address) == 0x2C or self.environment._read_m(address) == 0x34:#
                powerup_addr = int(f"0xD1{i}3", 16)
                powerup_x = self.environment._read_m(powerup_addr)
                powerup_addr = int(f"0xD1{i}2", 16)
                powerup_y = self.environment._read_m(powerup_addr)
                if (powerup_x-mario_x) < 10 and (powerup_x - mario_x) > 0 and (powerup_y-mario_y) < 3:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (2, 5, None, None, True)
                elif (mario_x - powerup_x) < 10 and mario_x - powerup_x > 0 and (powerup_y - mario_y) < 3:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    print("Move left powerup")
                    return (1, 5, 4, 1, True)
                elif mario_y - powerup_y > 5 and powerup_x - mario_x < 20:
                    return (4, 8, 2, 1, False) 

            #Bee detection
            elif self.environment._read_m(address) == 0x42:
                bee_addr = int(f"0xD1{i}3", 16)
                bee_x = self.environment._read_m(bee_addr)
                bee_addr = int(f"0xD1{i}2", 16)
                bee_y = self.environment._read_m(bee_addr)
                if (bee_x-mario_x) < 12 and (bee_x - mario_x) > 0 and (bee_y-mario_y) < 3:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 9, None, None, True)
                elif mario_y - bee_y > 5 and bee_x - mario_x < 20:
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 15, None, None, True)

        # found_qBlocks = self.find_qBlocks()
        # on_pipe = self.on_pipe()
        # print("stuck val", self.environment.stuck)
        print(game_area)
        
        
        if hole_found:
            print("Here 1")
            self.environment.prev_mario_x = self.environment.curr_mario_x
            #add a condition where it returns (4, 14, 2, 1, False or True) for a certain x coordinate (for the 2nd pipe)
            return (2, 2, 4, 19, False) #19 had best result rather than 20? 
        
        elif found_qBlocks:
            print("here 2")
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (4, 8, None, None, False)
        
        elif on_pipe:
            print("on pipe")
            print("stuck val", self.environment.stuck)
            self.environment.stuck += 1
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (0, 8, 2, 2, False)
        
        elif on_pipe == False:
            print("GET OFF PIPE")
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (4, 8, 2, 1, True)
        # elif self.environment._read_m(0xC207) == 0x02 and np.all(game_area[:,0] == 10):
        #     return (2)
        
        #used to do the left jump 1st and 2nd time in special room #2 in 1-1
        elif (self.environment.curr_mario_x == prev_mario_x) and ((game_area[x][19] == 10 and x == 13)   or game_area[9][y - 2] == 10) and np.all(game_area[:, 0] == 10):
            print("unique left jump")
            #self.environment.stuck += 1
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (1, 8, 4, 15, True)
        
        elif self.environment.stuck == 3:
            self.environment.stuck +=1
            print('wall jump') 
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (4, 12, 2, 2, False)  #original 4, 12, 2, 1, True
        
        elif (self.environment.curr_mario_x == prev_mario_x):
            print("stuck")
            # print("prev: ", self.environment.prev_mario_x)
            # print("Curr: ", self.environment.curr_mario_x)
            self.environment.stuck += 1
            self.environment.prev_mario_x = self.environment.curr_mario_x
            
            #For a very specific scenario in special room #2 on level 1-1
            if np.all(game_area[x-2, 5:7] == 0) and np.all(game_area[:, 0] == 10):
                print("Unique right jump")
                self.environment.stuck = 0
                return (4, 14, 2, 2, False) 
            else:
                return (2, 2, None, None, False)
        # elif found_qBlocks:
        #     print("here 2")
        #     self.environment.stuck += 1
        #     self.environment.prev_mario_x = self.environment.curr_mario_x
        #     return (4, 8, None, None, False)
        else: 
            print("just sprinting")
            #when the bottom of mario and right next to bottom of mario has ground while in air, hold down button
            if np.all(game_area[15, y:y+2]==10) and self.environment._read_m(0xC20A) == 0x00:
                print("Stay down")
                return (0, 5, None, None, False)
            self.environment.prev_mario_x = self.environment.curr_mario_x
            self.environment.stuck = 0
            return (2, 1, None, None, True)
            

        # if self.environment._read_m(0xC20A): #Mario on ground flag. 
        #     return 4 #constant jumping
        # else:
        #     return 0
        

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """
        # Choose an action - button press or other...
        action_duration = self.choose_action()

        if isinstance(action_duration, tuple):
            action = action_duration[0]
            duration = action_duration[1]
            action2 = action_duration[2]
            duration2 = action_duration[3]
            sprint = action_duration[4]
            # Run the action on the environment
            self.environment.run_action(action, duration, action2, duration2, sprint)
        else:
            self.environment.run_action(action_duration)

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()


    #finding coins or qblocks
    def find_qBlocks(self) -> bool:
        game_area = self.environment.game_area()
        find_mario = self.find_mario()
        qblock_x = 0
        qblock_y = 0
           # print(mario_x)
            #print("hello", mario_y)
        #print(game_area)
        for i in range(15, -1, -1):
            for j in range(19, -1, -1):
                #detects both coins (5) or mystery blocks (5)
                if game_area[i,j] == 13 or game_area[i,j] == 5:
                    qblock_x = i
                    qblock_y = j
                    #print(f"block_x {i} and block_y {j}")
        #print(f"Qblock_x {qblock_x}, qblock_y {qblock_y}")     
        if find_mario is not None:
            mario_x, mario_y = find_mario
            #print(f"mario_x {mario_x}, mario_y {mario_y}") 
            if  0<=(mario_y - qblock_y) < 2  and  0 <= (mario_x-qblock_x) < 5: #y is vertical. x is horizontal. ORIGINAL: (qblock_y==mario_y). 
                print("found block")
                return True
            else:
                return False 
        

    def on_pipe(self) -> bool:
        game_area = self.environment.game_area()
        find_mario = self.find_mario()
        if isinstance(find_mario, tuple):
            mario_x = find_mario[0]
            mario_y = find_mario[1]
            if mario_x > 14:
                return False
            if self.environment.stuck_on_pipe == 2:
                print("Here 5")
                self.environment.stuck_on_pipe = 0
                return False
            if self.environment.stuck_on_pipe == 1 and (game_area[mario_x+1][mario_y] == 14 or game_area[mario_x+1][mario_y - 1] == 14):
                print("here 6")
                self.environment.stuck_on_pipe += 1
                #self.environment.stuck_on_pipe = 0
                return True
            if game_area[mario_x+1][mario_y] == 14 or game_area[mario_x+1][mario_y - 1] == 14:
                self.environment.stuck_on_pipe += 1
                return True
        else:
            return False
        
    #returns the location of where mario is in real time 
    #in the form of a tuple where the entire 
    def find_mario(self) -> int:
        game_area = self.environment.game_area() #a numpy array of size 16 x 20
        for i in range(15, -1, -1):
            for j in range(19, -1, -1):
                if game_area[i,j] == 1:
                   # print("mario found")
                    return (i, j) #returns the bottom 2 values of mario's position
        
        return None

    
    #may need to change from bool to integer where each represent a different style of holes. 
    def find_holes(self) -> bool:
        game_area = self.environment.game_area()
        
        find_mario = self.find_mario()
        
        if find_mario is not None:
            mario_x, mario_y = find_mario
        else:
            return False
        
        #print(game_area)
        #may need to make this hole detection better. Just detecting whether a few indices away from mario on the last row, it contains 0 
        if mario_y >= 18 and mario_x > 11:
            return False
        elif self.find_qBlocks():
             return False
        
        elif np.all(game_area[mario_x+1: mario_x + 5, mario_y+1:mario_y+3] == 0) and self.environment._read_m(0xC20A):
            print("block jumping")
            return True
        
        else:
            return False


