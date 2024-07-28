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
        keep_running: bool = True
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
        self.stuck = 0
        self.hole_count = 0
    

    def run_action(self, action: int, duration: int = None, sprint: bool = True) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        #print(self.game_area()) 

        # Simply toggles the buttons being on or off for a duration of act_freq
        if duration == None:
            duration = self.act_freq

        if sprint == True:
            self.pyboy.send_input(self.valid_actions[5])
            #self.pyboy.tick()
        else: 
            self.pyboy.send_input(self.release_button[5])
            #self.pyboy.tick()
        self.pyboy.send_input(self.valid_actions[action])
        #self.pyboy.send_input(self.valid_actions[2])
        for _ in range(duration):
            self.pyboy.tick()
        self.pyboy.send_input(self.release_button[action])
        #self.pyboy.send_input(self.release_button[2])
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

        has_stuck = False
        
        hole_found = self.find_holes()

        #print(game_area)
        self.environment.curr_mario_x = self.environment.get_x_position() #true position 
        if has_stuck == True:
            print("reached here")
            prev_mario_x = 0
            has_stuck = False
        else:
            prev_mario_x = self.environment.prev_mario_x

        stuck = self.environment.stuck
        # Implement your code here to choose the best action
        #time.sleep(0.1)
        #return random.randint(0, len(self.environment.valid_actions) - 1)

        mario_x = self.environment._read_m(0xC202) #relative
        mario_y = self.environment._read_m(0xC201)
        #print("mario prev pos: ", prev_mario_x)    
        #self.environment.curr_mario_x = self.environment.get_x_position() #true position   
        for i in range(10): # loops through 9 indexes of the object table 
            address = int(f"0xD1{i}0", 16) #convert the string to hex

            if self.environment._read_m(address) == 00: #goomba

                goomba_addr = int(f"0xD1{i}3", 16)  #x position  
                goomba_x = self.environment._read_m(goomba_addr)
                goomba_addr = int(f"0xD1{i}2", 16) #y position
                goomba_y = self.environment._read_m(goomba_addr)

                #print("mario", mario_y)
                #print("goomba", goomba_y)

                if (goomba_x-mario_x) < 10 and (goomba_x - mario_x) > 0 and (goomba_y-mario_y) < 3:
                    #print('goomba jump')
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (4, 1, False)
                elif mario_y - goomba_y > 5 and goomba_x - mario_x < 20:
                    #print("goomba above")
                    self.environment.prev_mario_x = self.environment.curr_mario_x
                    return (1, 10, True) 

        print("prev: ", self.environment.prev_mario_x)
        print("Curr: ", self.environment.curr_mario_x)
        if stuck == 5:
            print("stuck intervention")
            self.environment.prev_mario_x = 0
            self.environment.stuck = 0 
            has_stuck = True
            return (2, None, False) 
        #no idea why this is needed when this isn't really needed. particularly after the hole jump, looks like when jumping forward button is not pressed. 
        #but for the very first wall jump, it jumps perfectly fine?????
        elif (self.environment.curr_mario_x == prev_mario_x): 
            print("stuck")
            # print("prev: ", self.environment.prev_mario_x)
            # print("Curr: ", self.environment.curr_mario_x)
            self.environment.stuck += 1
            #print('wall jump') 
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (4, 15, False)
        elif hole_found:
            self.environment.prev_mario_x = self.environment.curr_mario_x
            return (4, 15, False) 
        else: 
            #print("just sprinting")
            self.environment.prev_mario_x = self.environment.curr_mario_x
            self.environment.stuck = 0
            return (2, None, False)
            

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
        # self.environment.prev_mario_x = self.environment.get_x_position()
        

        # if stuck == 5:
        #     print("stuck intervention")
        #     self.environment.prev_mario_x = 0
        #     self.environment.stuck = 0
        #     self.environment.run_action(1, 3, False)
        #     return
        # elif curr_mario_x == self.environment.prev_mario_x:
        #     self.environment.stuck += 1
        #     print("getting stuck")
    
        if isinstance(action_duration, tuple):
            action = action_duration[0]
            duration = action_duration[1]
            sprint = action_duration[2]
            # Run the action on the environment
            self.environment.run_action(action, duration, sprint)
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

    #returns the location of where mario is in real time 
    #in the form of a tuple where the entire 
    def find_mario(self) -> int:
        game_area = self.environment.game_area() #a numpy array of size 16 x 20
        for i in range(15, -1, -1):
            for j in range(19, -1, -1):
                if game_area[i,j] == 1:
                   # print("mario found")
                    return (i, j) #returns the bottom 2 values of mario's position
                
    def find_holes(self) -> bool:
        game_area = self.environment.game_area()
        
        find_mario = self.find_mario()
        
        if isinstance(find_mario, tuple):
            mario_x = find_mario[0]
            mario_y = find_mario[1]
           # print(mario_x)
            #print(mario_y)
        else:
            return False
        
        #print(game_area)
        #may need to make this hole detection better. Just detecting whether a few indices away from mario on the last row, it contains 0 
        if game_area[15][mario_y + 1] == 0:
            return True
        else:
            return False


        # if mario_x > 11:
        #     checks a specified amount in a column from mario contains all 0 (meaning a hole is there)
        #     if np.all(game_area[mario_x:, mario_y + 2] == 0):
        #         print("ready to jump 1")
        #         return True
        #     else:
        #         return False
        # else:
        #     if np.all(game_area[mario_x:mario_x+4, mario_y + 2] == 0):
        #         print("ready to jump 2")
        #         return True
        #     else:
        #         return False


