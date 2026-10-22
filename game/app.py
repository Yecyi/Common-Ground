"""The playable Pygame application and all keyboard/mouse/gamepad screens."""
from __future__ import annotations

import math
from pathlib import Path
import sys
import time

import pygame

from .art import Art
from .audio import Audio
from .state import GameState
from .story import OUTCOME_WORDS
from .storage import load_game,save_game,load_settings,write_json
from .ui import UI,INK,MUTED,PAPER,CREAM,GREEN,GOLD,WHITE
from .world import World,VIEW,WIDTH,HEIGHT

BASE=(1280,840)
ROOT=Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parents[1]

# One entry per community value: key, label, colour, and the goal the ending needs.
VITALS=(("environment","ENVIRONMENT",(63,118,81),70),
        ("equity","EQUITY",(171,124,59),65),
        ("resilience","RESILIENCE",(72,126,139),65))
QUIET_TEXT={
    "quiet":("THE WILLOW REFUGE","There is room to pause.","Notice a sound, a colour, or the ground beneath your feet. You can breathe at your own pace, or simply sit. There is no correct way to take this moment."),
    "quiet_river":("THE RIVER BANK","Let the water do the moving.","Watch the river for a while: its colour, its speed, what it carries. Nothing here needs fixing right now, and you do not have to feel any particular way."),
    "quiet_garden":("ABOVE THE GARDEN","Things grow without being hurried.","Look across the beds. Notice what is planted, what is still bare, and how little needs to happen in this moment."),
}
GAMEPAD_KEYS={0:pygame.K_RETURN,1:pygame.K_ESCAPE,2:pygame.K_j,3:pygame.K_TAB,7:pygame.K_ESCAPE}


def stage_word(value):
    return "Fragile" if value<25 else "Mending" if value<50 else "Growing" if value<70 else "Thriving"


class App:
    def __init__(self,save_dir=None,window=True,audio=True):
        pygame.mixer.pre_init(44100,-16,2,1024)
        pygame.init()
        flags=pygame.RESIZABLE if window else pygame.HIDDEN
        self.window=pygame.display.set_mode(BASE,flags)
        pygame.display.set_caption("Common Ground | A CAS community RPG")
        self.surface=pygame.Surface(BASE)
        self.ui=UI(self.surface)
        self.art=Art(custom_dir=ROOT/"assets"/"custom"/"sprites")
        icon=pygame.transform.scale(self.art.sprite("player"),(48,72))
        pygame.display.set_icon(icon)
        self.world=World(self.art)
        self.audio=Audio() if audio else None
        self.save_dir=Path(save_dir) if save_dir else ROOT/"saves"
        self.slot=self.save_dir/"save.json"
        self.settings=load_settings(self.save_dir/"settings.json")
        self.state=GameState()
        self.mode="title"
        self.running=True
        self.clock=pygame.time.Clock()
        self.elapsed=0.
        self.result=None
        self.conversation=None
        self.talking_to=None
        self.scroll=0
        self.max_scroll=0
        self.pending_interaction=None
        self.return_mode="title"
        self.toast=""
        self.toast_time=0.
        self.quiet_time=0.
        self.quiet_place=None
        self.save_clock=0.
        self.fullscreen=False
        self.focused=True
        self.save_valid=False
        self.active_session=False
        self.save_issue=""
        self.step=self.state.next_step()
        self.pads={}
        self.init_gamepads()
        self.check_save()
        self.apply_settings()

    # ------------------------------------------------------------------ gamepad
    def init_gamepads(self):
        try:
            pygame.joystick.init()
            for index in range(pygame.joystick.get_count()):
                self.connect_pad(index)
        except pygame.error:
            pass

    def connect_pad(self,index):
        try:
            pad=pygame.joystick.Joystick(index)
            self.pads[pad.get_instance_id()]=pad
        except pygame.error:
            pass

    def read_pad(self):
        """Left stick or d-pad movement, with a dead zone so a resting stick never drifts."""
        vector=pygame.Vector2()
        for pad in list(self.pads.values()):
            try:
                vector+=pygame.Vector2(pad.get_axis(0),pad.get_axis(1))
                if pad.get_numhats():
                    hx,hy=pad.get_hat(0)
                    vector+=pygame.Vector2(hx,-hy)
            except pygame.error:
                self.pads={key:p for key,p in self.pads.items() if p is not pad}
        if vector.length()<.35:
            return pygame.Vector2()
        return vector.normalize() if vector.length()>1 else vector

    # ------------------------------------------------------------- save and mode
    def check_save(self):
        try:
            load_game(self.slot)
            self.save_valid=True
            self.save_issue=""
        except FileNotFoundError:
            self.save_valid=False
        except (OSError,ValueError,KeyError,TypeError,AttributeError,OverflowError):
            self.save_valid=False
            self.save_issue="The saved journey could not be read. It has been kept in the saves folder."

    def apply_settings(self):
        self.ui.large=self.settings["large_text"]
        self.ui.contrast=self.settings["high_contrast"]
        if self.audio:self.audio.set_muted(self.settings["muted"])

    def change_mode(self,mode):
        self.mode=mode
        self.ui.focus=0
        self.scroll=0
        self.max_scroll=0
        self.world.path=[]
        self.world.walking=False

    def notify(self,message):
        self.toast=message
        self.toast_time=4

    def tip(self,name,message):
        """A first-time prompt, shown once and remembered between sessions."""
        if self.settings.get(name):return
        self.settings[name]=True
        self.notify(message)
        try:write_json(self.save_dir/"settings.json",self.settings)
        except OSError:pass

    def save(self,feedback=False):
        if not self.active_session:return
        try:
            save_game(self.slot,self.state,self.world.player)
            self.save_valid=True
            if feedback:self.notify("Journey saved")
        except OSError:
            self.notify("Could not save. Check that the saves folder is writable.")

    def new_game(self):
        self.active_session=False
        self.state=GameState()
        self.world.player.update(480,500)
        self.world.plume=None
        self.pending_interaction=None
        self.change_mode("intro")

    def continue_game(self):
        try:
            self.state,position=load_game(self.slot)
            self.active_session=True
            self.world.player.update(position)
            self.world.plume=None
            if not self.world.walkable(self.world.player):self.world.player.update(480,500)
            self.change_mode("play")
            self.notify("Welcome back to Willowmere")
        except (OSError,ValueError,KeyError,TypeError,AttributeError,OverflowError):
            self.check_save()
            self.notify("The save could not be loaded. Your file has been kept.")

    def action(self,action):
        if not action:return
        if action=="new":
            self.change_mode("confirm" if self.slot.exists() else "intro")
            if not self.slot.exists():self.new_game()
        elif action=="confirm_new":
            # Preserve an existing journey before starting another one.
            try:
                if self.slot.exists():
                    backup=self.slot.with_name(f"previous-journey-{time.time_ns()}.json")
                    backup.write_bytes(self.slot.read_bytes())
            except OSError:
                self.notify("Could not back up the previous journey. New game cancelled.")
                self.change_mode("title")
                return
            self.new_game()
        elif action=="continue":self.continue_game()
        elif action=="begin":
            self.active_session=True
            self.change_mode("play");self.save()
            if self.settings.get("tip_move"):
                self.notify("Start with Mira beside the crossroads. Press E to talk.")
            else:
                self.tip("tip_move","Move with WASD or the arrow keys, or click the ground. Mira is just ahead; press E to talk.")
        elif action=="resume":self.change_mode("play")
        elif action=="open_pause":self.change_mode("pause");self.save()
        elif action=="title":
            self.save();self.active_session=False;self.change_mode("title");self.check_save()
        elif action=="cancel_new":self.change_mode("title")
        elif action=="quit":
            if self.active_session:self.save()
            self.running=False
        elif action=="save":self.save(True)
        elif action=="settings":
            self.return_mode=self.mode
            self.change_mode("settings")
        elif action=="help":
            self.return_mode=self.mode
            self.change_mode("help")
        elif action=="back":self.change_mode(self.return_mode)
        elif action.startswith("setting:"):
            key=action.split(":",1)[1]
            self.settings[key]=not self.settings[key]
            self.apply_settings()
            try:write_json(self.save_dir/"settings.json",self.settings)
            except OSError:self.notify("Settings apply for this session; they could not be saved.")
        elif action=="dismiss":
            came_from_result=self.mode=="result" and self.result is not None and self.result.ok
            self.change_mode("play")
            if came_from_result:self.tip("tip_journal","Your journal (J) keeps a record of your choices and goals.")
        elif action=="leave_dialogue":self.change_mode("play")
        elif action.startswith("choice:"):
            choice=action.split(":",1)[1]
            self.result=self.state.choose(self.talking_to,choice)
            self.save()
            if self.audio and self.result.ok:
                self.audio.chime()
                if self.result.resolved:self.audio.resolve()
            if choice=="finish" and self.result.ok:
                self.change_mode("ending")
            else:self.change_mode("result")
        elif action=="quiet_reflect":
            self.result=self.state.perform(self.quiet_place.id if self.quiet_place else "quiet")
            self.save()
            if self.audio:self.audio.chime()
            self.change_mode("result")
        elif action=="finish":
            self.result=self.state.perform("finish")
            self.save()
            self.change_mode("ending" if self.result.ok else "result")
        elif action=="journal":self.change_mode("journal")
        elif action=="map":self.change_mode("map")
        elif action.startswith("travel:"):
            ident=action.split(":",1)[1]
            place=next(p for p in self.world.places if p.id==ident)
            self.change_mode("play")
            self.walk_to_place(place)

    def interact(self,place=None):
        place=place or self.world.nearest
        if place is None:
            self.notify("Walk close to a person or marked object, then press E.")
            return
        self.pending_interaction=None
        self.world.path=[]
        if place.kind in ("npc","council"):
            self.talking_to=place.id
            self.conversation=self.state.dialogue(place.id)
            self.change_mode("dialogue")
        elif place.kind=="quiet":
            self.quiet_time=0
            self.quiet_place=place
            self.change_mode("quiet")
        else:
            self.result=self.state.perform(place.id)
            self.save()
            if self.audio and self.result.ok:self.audio.chime()
            self.change_mode("result")

    def walk_to_place(self,place):
        if self.world.player.distance_to((place.x,place.y))<58:
            self.interact(place);return
        # Approach from the nearest reachable side; people never block paths.
        targets=[(place.x,place.y+29),(place.x-30,place.y+8),(place.x+30,place.y+8),(place.x,place.y-25)]
        targets.sort(key=lambda p:self.world.player.distance_to(p))
        for target in targets:
            if self.world.walk_to(target):
                self.pending_interaction=place
                self.notify("Walking to "+place.name+". Move with WASD to cancel.")
                return
        self.notify("That place cannot be reached from here.")

    def logical_mouse(self,position):
        w,h=self.window.get_size()
        factor=min(w/BASE[0],h/BASE[1])
        ox=(w-BASE[0]*factor)/2;oy=(h-BASE[1]*factor)/2
        return (int((position[0]-ox)/factor),int((position[1]-oy)/factor))

    def press(self,key):
        self.handle(pygame.event.Event(pygame.KEYDOWN,key=key))

    def handle(self,event):
        if event.type==pygame.QUIT:
            self.action("quit");return
        if event.type==pygame.WINDOWFOCUSLOST:
            self.focused=False
            if self.mode=="play":self.change_mode("pause");self.save()
        elif event.type==pygame.WINDOWFOCUSGAINED:self.focused=True
        if event.type==pygame.JOYDEVICEADDED:
            self.connect_pad(event.device_index)
        elif event.type==pygame.JOYDEVICEREMOVED:
            self.pads.pop(getattr(event,"instance_id",None),None)
        elif event.type==pygame.JOYBUTTONDOWN:
            key=GAMEPAD_KEYS.get(event.button)
            if key:self.press(key)
        elif event.type==pygame.JOYHATMOTION:
            if self.mode!="play" and event.value[1]:
                self.press(pygame.K_UP if event.value[1]>0 else pygame.K_DOWN)
        if event.type==pygame.MOUSEMOTION:
            self.ui.mouse=self.logical_mouse(event.pos)
        elif event.type==pygame.MOUSEWHEEL:
            self.scroll=max(0,min(self.max_scroll,self.scroll-event.y*44))
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            pos=self.logical_mouse(event.pos)
            action=self.ui.clicked(pos)
            if action:self.action(action)
            elif self.mode=="play" and VIEW.collidepoint(pos):
                point=self.world.screen_to_world(pos)
                place=self.world.object_at(point,self.state)
                if place:self.walk_to_place(place)
                else:
                    self.pending_interaction=None
                    self.world.walk_to(point)
        elif event.type==pygame.KEYDOWN:
            key=event.key
            if key==pygame.K_F11:
                self.fullscreen=not self.fullscreen
                flags=pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
                self.window=pygame.display.set_mode((0,0) if self.fullscreen else BASE,flags)
                return
            if key==pygame.K_m:
                self.action("setting:muted");return
            if key==pygame.K_ESCAPE:
                if self.mode=="play":self.change_mode("pause");self.save()
                elif self.mode=="pause":self.change_mode("play")
                elif self.mode in ("settings","help"):self.action("back")
                elif self.mode in ("confirm","intro"):self.change_mode("title")
                elif self.mode in ("dialogue","result","journal","map","quiet"):self.change_mode("play")
                elif self.mode=="ending":self.change_mode("play")
                return
            if self.mode=="play":
                if key in (pygame.K_e,pygame.K_SPACE,pygame.K_RETURN):self.interact()
                elif key==pygame.K_j:self.change_mode("journal")
                elif key==pygame.K_TAB:self.change_mode("map")
                elif key in (pygame.K_w,pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_UP,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT):
                    self.pending_interaction=None
                return
            if self.mode=="journal" and key==pygame.K_j or self.mode=="map" and key==pygame.K_TAB:
                self.change_mode("play");return
            if key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN):
                self.scroll=max(0,min(self.max_scroll,self.scroll+(400 if key==pygame.K_PAGEDOWN else -400)));return
            if self.mode=="dialogue" and pygame.K_1<=key<=pygame.K_9:
                index=key-pygame.K_1
                if index<len(self.conversation.choices):self.action("choice:"+self.conversation.choices[index].id)
                return
            if self.ui.buttons:
                if key in (pygame.K_UP,pygame.K_w):self.ui.focus=(self.ui.focus-1)%len(self.ui.buttons)
                elif key in (pygame.K_DOWN,pygame.K_s,pygame.K_TAB):self.ui.focus=(self.ui.focus+1)%len(self.ui.buttons)
                elif key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_e):self.action(self.ui.selected())
                if self.mode=="dialogue" and hasattr(self,"choice_rects") and self.ui.focus<len(self.choice_rects):
                    rect=self.choice_rects[self.ui.focus]
                    if rect.bottom>652:self.scroll=min(self.max_scroll,self.scroll+rect.bottom-652)
                    if rect.top<237:self.scroll=max(0,self.scroll-(237-rect.top))

    def update(self,dt):
        self.elapsed+=dt
        self.toast_time=max(0,self.toast_time-dt)
        if self.mode=="play":
            keys=pygame.key.get_pressed()
            self.world.update(dt,keys,self.state,.7 if self.settings["slow_walk"] else 1.,self.settings["reduced_motion"],self.read_pad() if self.pads else None)
            self.state.play_seconds+=dt
            self.save_clock+=dt
            if self.save_clock>20:self.save();self.save_clock=0
            if self.pending_interaction and not self.world.path:
                place=self.pending_interaction;self.pending_interaction=None
                if self.world.player.distance_to((place.x,place.y))<58:self.interact(place)
            if self.world.nearest and self.toast_time<=0 and self.settings.get("tip_move"):
                self.tip("tip_talk","Press E or Space to talk to someone, or to look at what is near you.")
        elif self.mode=="quiet":self.quiet_time+=dt
        if self.audio:
            tension=self.conversation.tension if self.mode=="dialogue" and self.conversation else 0.
            self.audio.update(dt,self.state.balance,self.mode=="quiet",tension,self.world.audio_zones(),
                              "source_repaired" in self.state.flags,"factory_shared" in self.state.flags)

    # ---------------------------------------------------------------- the HUD
    def draw_hud(self):
        s,u,state=self.surface,self.ui,self.state
        pygame.draw.rect(s,PAPER,(0,0,1280,108))
        pygame.draw.line(s,(205,213,189),(0,106),(1280,106),2)
        u.text("COMMON GROUND",(28,17),25,INK,True)
        u.text("A little care changes a place.",(29,55),18,MUTED)
        values=state.metrics
        lowest=min(values,key=values.get)
        uneven=max(values.values())-min(values.values())>=10
        hover=None
        for i,(key,label,color,goal) in enumerate(VITALS):
            x=425+i*218
            u.vital(key,(x+34,52),values[key],color)
            u.text(label,(x+76,18),15,MUTED,True)
            u.text(stage_word(values[key]),(x+76,38),24,INK,True)
            if uneven and key==lowest and values[key]<goal:
                u.text("needs care",(x+76,72),14,(142,96,38) if not u.contrast else INK,True)
            area=pygame.Rect(x-8,8,206,92)
            if self.mode=="play" and area.collidepoint(u.mouse):hover=(label,values[key],goal,area)
        u.text(f"SUPPLIES  {state.resources['supplies']}   /   SEEDS  {state.resources['seeds']}",(1253,85),15,MUTED,True,"topright")
        pygame.draw.rect(s,PAPER,(0,744,1280,96))
        pygame.draw.line(s,(205,213,189),(0,744),(1280,744),2)
        near=self.world.nearest
        caption=self.world.cue_caption(state) if not near else None
        if near:
            u.keycap("E",(26,761))
            u.text(near.name,(70,758),23,INK,True)
            verb="Talk" if near.kind in ("npc","council") else "Pause & reflect" if near.kind=="quiet" else "Interact"
            if near.id=="plots":verb="Read the sign-up list"
            u.text(verb,(70,792),17,MUTED)
        elif caption:
            u.text("NOTICE",(28,757),13,GREEN,True)
            u.paragraph(caption,(28,777),640,19,INK,gap=2)
        else:
            u.text("WASD / arrows to move",(28,758),21,INK,True)
            u.text("Or click a place to walk there.",(28,792),17,MUTED)
        # Small mouse buttons are equally accessible by keyboard shortcuts.
        u.button("J  Journal",(703,766,168,48),"journal")
        u.button("Tab  Map",(883,766,161,48),"map")
        u.button("Esc  Pause",(1056,766,197,48),"open_pause")
        if self.mode=="play":
            zone=self.world.zone()
            pygame.draw.rect(s,(32,54,47),(26,128,285,37),border_radius=6)
            u.text(zone,(41,134),17,WHITE,True)
            text,target=self.step
            if "balanced" not in state.flags:
                lines=u.lines(text,360,17)
                height=34+len(lines)*(u.font(17).get_linesize()+1)
                pygame.draw.rect(s,PAPER,(26,176,390,height),border_radius=8)
                u.text("A THREAD TO FOLLOW",(41,184),13,MUTED,True)
                u.paragraph(text,(41,205),360,17,INK,gap=1)
            if near:
                x=(near.x-self.world.camera.x)*2
                y=(near.y-self.world.camera.y)*2+108-86
                label=near.name
                w=u.font(18,True).size(label)[0]+44
                rect=pygame.Rect(0,0,w,34);rect.midbottom=(max(w/2+10,min(1280-w/2-10,x)),max(285,y))
                pygame.draw.rect(s,PAPER,rect,border_radius=6)
                u.text(label,rect.center,18,INK,True,"center")
        if hover:
            label,value,goal,area=hover
            u.tooltip([f"{label}  {value} of 100","Goal reached" if value>=goal else f"Goal: {goal}"],(area.x,102))

    def fade_hud(self):
        """In a quiet place the interface steps back so the village can be seen."""
        progress=1 if self.settings["reduced_motion"] else min(1,self.quiet_time/2.5)
        veil=pygame.Surface((1280,108),pygame.SRCALPHA);veil.fill((*PAPER,round(195*progress)))
        self.surface.blit(veil,(0,0))
        veil=pygame.Surface((1280,96),pygame.SRCALPHA);veil.fill((*PAPER,round(195*progress)))
        self.surface.blit(veil,(0,744))

    def draw_title(self):
        u=self.ui;s=self.surface
        self.world.camera.update(120,260)
        self.world.draw(s,self.state,self.elapsed,self.settings["reduced_motion"])
        # Extend the scene into the title's top and bottom, retaining crisp pixels.
        scene=pygame.transform.scale(self.world.low,BASE)
        s.blit(scene,(0,0))
        overlay=pygame.Surface(BASE,pygame.SRCALPHA)
        overlay.fill((20,39,33,95));s.blit(overlay,(0,0))
        u.panel((62,62,560,716),PAPER,20)
        u.text("A CAS PROJECT",(100,99),17,GREEN,True)
        u.text("COMMON",(94,151),64,INK,True)
        u.text("GROUND",(94,223),64,INK,True)
        pygame.draw.line(s,GOLD,(100,314),(164,314),4)
        u.paragraph("A village. A shared future.\nA little care to begin again.",(100,340),470,24,INK,gap=8)
        y=448
        if self.save_valid:
            u.button("Continue your journey",(100,y,482,58),"continue",primary=True);y+=70
        u.button("Start a new journey",(100,y,482,58),"new",primary=not self.save_valid);y+=70
        u.button("How to play",(100,y,234,49),"help")
        u.button("Settings",(348,y,234,49),"settings");y+=61
        u.button("Quit",(100,y,482,45),"quit")
        u.text("An unhurried story of people and place.",(100,736),17,MUTED)
        u.text("WILLOWMERE",(1230,696),19,WHITE,True,"topright")
        u.text("Restore the river. Hear each other.",(1230,728),22,WHITE,False,"topright")
        if self.save_issue:
            u.panel((658,72,560,100),PAPER)
            u.paragraph(self.save_issue,(680,90),516,18)

    def draw_intro(self,help_only=False):
        u=self.ui
        u.shade(140);u.panel((100,57,1080,726))
        u.text("WELCOME TO WILLOWMERE",(141,91),17,GREEN,True)
        u.text("What does a town need to heal?",(139,131),40,INK,True)
        u.paragraph("The old mill has closed. The river carries its waste, the gardens are quiet, and some neighbours have stopped being heard. You have arrived to help people decide what comes next.",(142,203),985,23,gap=6)
        columns=[("01","Listen first","Speak with Mira, Rowan, Amani and Theo. Ask what would help; a conversation cannot solve everything."),
                 ("02","Share the work","Recover supplies, clear litter and plant the three garden beds. Repair the pump to stop the source of pollution."),
                 ("03","Make room for everyone","Visit the neighbourhood circle and the quiet places. Balance grows through shared decisions, practical support and care.")]
        for i,(num,title,body) in enumerate(columns):
            x=142+i*340
            u.text(num,(x,346),25,GOLD,True)
            u.text(title,(x,390),22,INK,True)
            u.paragraph(body,(x,433),296,20,gap=5)
        u.text("No combat. No countdown. You can reconsider your decisions.",(142,584),20,GREEN,True)
        u.text("WASD / arrows  Move     E / Space  Interact     J  Journal     Tab  Map",(142,624),19,MUTED)
        u.text("Gamepad: left stick or d-pad moves, A interacts, B goes back, X journal, Y map.",(142,654),17,MUTED)
        u.button("Back" if help_only else "Begin the journey",(142,704,994,50),"back" if help_only else "begin",primary=True)

    def modal_header(self,eyebrow,title,rect=(140,120,1000,600)):
        u=self.ui
        u.shade(105);u.panel(rect)
        u.text(eyebrow,(rect[0]+34,rect[1]+22),16,GREEN,True)
        u.text(title,(rect[0]+32,rect[1]+56),35,INK,True)

    def draw_dialogue(self):
        u=self.ui;c=self.conversation
        self.modal_header(c.role.upper(),c.speaker,(120,123,1040,615))
        u.text("YOUR SUPPLIES  "+str(self.state.resources['supplies']),(1120,152),16,MUTED,True,"topright")
        clip=pygame.Rect(151,237,978,415)
        previous=self.surface.get_clip();self.surface.set_clip(clip)
        y=u.paragraph(c.text,(155,238-self.scroll),960,23,gap=6)+22
        self.choice_rects=[]
        for i,choice in enumerate(c.choices):
            title_lines=len(u.lines(choice.label,880,21,True))
            hint_lines=len(u.lines(choice.hint,880,17)) if choice.hint else 0
            h=max(66,26+title_lines*(u.font(21,True).get_linesize()+1)+hint_lines*(u.font(17).get_linesize()+1))
            u.button(choice.label,(155,y,970,h),"choice:"+choice.id,hint=choice.hint,number=i+1)
            self.choice_rects.append(pygame.Rect(155,y,970,h))
            y+=h+11
        self.max_scroll=max(0,y+self.scroll-clip.bottom+10)
        self.surface.set_clip(previous)
        # Clipped choices must never accept clicks outside the scrolling viewport.
        self.ui.buttons=[(r.clip(clip),a,e and r.colliderect(clip)) for r,a,e in self.ui.buttons]
        if self.max_scroll:
            u.text("Scroll / Page Down for more choices",(155,663),16,MUTED)
        u.button("Leave the conversation",(155,691,970,35),"leave_dialogue")

    def draw_outcome(self,result,top):
        """Who a decision reached, as words and pips so it never depends on colour alone."""
        u=self.ui
        u.text(result.outcome_title.upper(),(176,top),15,GREEN,True)
        count=len(result.outcome)
        gap=12
        width=(928-gap*(count-1))//count
        for i,(label,level) in enumerate(result.outcome):
            rect=pygame.Rect(176+i*(width+gap),top+26,width,92)
            pygame.draw.rect(self.surface,WHITE,rect,border_radius=10)
            pygame.draw.rect(self.surface,INK if u.contrast else (197,205,184),rect,2 if u.contrast else 1,border_radius=10)
            line=rect.y+10
            for text in u.lines(label,width-24,17,True)[:2]:
                u.text(text,(rect.x+12,line),17,INK,True)
                line+=u.font(17,True).get_linesize()
            for pip in range(3):
                center=(rect.x+22+pip*22,rect.bottom-20)
                pygame.draw.circle(self.surface,GREEN,center,8,0 if pip<level else 2)
            u.text(OUTCOME_WORDS[level],(rect.x+22+3*22+4,rect.bottom-20),17,INK,True,"midleft")

    def draw_result(self):
        u=self.ui;r=self.result
        self.modal_header("A SMALL STEP" if r.ok else "SOMETHING TO CONSIDER",r.title,(140,123,1000,615))
        clip=pygame.Rect(174,253,930,333-(130 if r.outcome else 0))
        previous=self.surface.get_clip();self.surface.set_clip(clip)
        y=u.paragraph(r.text,(176,257-self.scroll),923,24,gap=10)
        self.max_scroll=max(0,y+self.scroll-clip.bottom)
        self.surface.set_clip(previous)
        if r.outcome:self.draw_outcome(r,clip.bottom+10)
        if self.max_scroll:u.text("Scroll / Page Down to read more",(176,603),17,MUTED)
        u.text("Your journal keeps a record of the town's choices.",(176,640),18,MUTED)
        u.button("Continue",(176,686,928,40),"dismiss",primary=True)

    def draw_pause(self):
        u=self.ui
        self.modal_header("TAKE YOUR TIME","A moment to pause",(382,123,516,604))
        u.text("Your journey saves as you go.",(418,234),20,MUTED)
        for i,(label,action) in enumerate([("Return to the village","resume"),("Save journey","save"),("Settings","settings"),("How to play","help"),("Return to title","title"),("Save & quit","quit")]):
            u.button(label,(418,284+i*64,444,51),action,primary=i==0)

    def draw_settings(self):
        u=self.ui
        self.modal_header("MAKE YOURSELF AT HOME","Settings",(260,80,760,680))
        items=[("muted","Mute sound","All story information is also shown as text."),
               ("large_text","Larger text","Enlarge dialogue, choices and interface text."),
               ("reduced_motion","Reduced motion","Still water, particles and characters, and a still reflection circle."),
               ("high_contrast","Higher contrast","Darker text, stronger borders and clear object markers."),
               ("slow_walk","Gentler movement","Walk at a slower pace. There is no time limit."),
               ("show_way","Show the way","A gentle marker over the place the next suggestion points to.")]
        for i,(key,label,hint) in enumerate(items):
            mark="ON" if self.settings[key] else "OFF"
            u.button(f"{label}  [{mark}]",(296,196+i*76,688,70),"setting:"+key,hint)
        u.button("Back",(296,681,688,49),"back",primary=True)

    def draw_confirm(self):
        u=self.ui
        self.modal_header("A NEW BEGINNING","Start another journey?",(220,205,840,430))
        u.paragraph("Your current journey will be kept as a backup in the saves folder. The new journey will become the one shown by Continue.",(256,337),766,23,gap=8)
        u.button("Keep my current journey",(256,478,766,52),"cancel_new",primary=True)
        u.button("Start a new journey",(256,545,766,52),"confirm_new")

    def draw_quiet(self):
        u=self.ui
        eyebrow,title,prompt=QUIET_TEXT.get(self.quiet_place.id if self.quiet_place else "quiet",QUIET_TEXT["quiet"])
        u.shade(45);u.panel((330,120,620,622))
        u.text(eyebrow,(640,150),17,GREEN,True,"midtop")
        u.text(title,(640,190),32,INK,True,"midtop")
        phase=(math.sin(self.quiet_time*.7)+1)/2
        radius=78 if self.settings["reduced_motion"] else int(66+phase*24)
        pygame.draw.circle(self.surface,(215,229,204),(640,360),100)
        pygame.draw.circle(self.surface,(142,179,144),(640,360),radius)
        pygame.draw.circle(self.surface,GREEN,(640,360),radius,2)
        u.text("Just be here.",(640,358),21,INK,True,"center")
        u.paragraph(prompt,(372,468),536,22,gap=7)
        u.button("Reflect & return whenever you are ready",(372,656,536,54),"quiet_reflect",primary=True)

    def draw_journal(self):
        u=self.ui
        self.modal_header("PEOPLE, PLACE & POSSIBILITY","Your field journal",(100,58,1080,720))
        # Left column stays fixed while the reflection log scrolls independently.
        u.text("WORKING TOWARDS BALANCE",(136,181),16,GREEN,True)
        for i,(key,label) in enumerate((("environment","Environment"),("equity","Equity"),("resilience","Resilience"))):
            x=136+i*126
            u.text(f"{self.state.metrics[key]:.0f}",(x,214),23,GREEN,True)
            u.text(label,(x,249),13,MUTED)
        y=290
        concise=["Repair the river pump","Plant all 3 garden beds","Work with all 4 neighbours","Share supplies at the circle","Pause in the willow refuge","Environment reaches 70","Equity reaches 65","Resilience reaches 65"]
        for text,(_,done) in zip(concise,self.state.objectives()):
            pygame.draw.circle(self.surface,GREEN if done else (185,193,174),(146,y+11),8,0 if done else 2)
            y=u.paragraph(text,(167,y),330,18,INK if done else MUTED,gap=2)+18
        pygame.draw.line(self.surface,(211,216,196),(526,184),(526,705))
        u.text("CHOICES & REFLECTIONS",(562,181),16,GREEN,True)
        clip=pygame.Rect(556,219,580,469)
        previous=self.surface.get_clip();self.surface.set_clip(clip)
        y=223-self.scroll
        entries=list(reversed(self.state.journal))
        if not entries:
            y=u.paragraph("A journey begins with a conversation. Find Mira near the crossroads; your discoveries will appear here.",(563,y),557,22,MUTED)
        for entry in entries:
            y=u.paragraph(entry["title"],(563,y),550,21,INK,True,gap=3)+7
            y=u.paragraph(entry["body"],(563,y),550,19,MUTED,gap=4)+26
        self.max_scroll=max(0,y+self.scroll-clip.bottom)
        self.surface.set_clip(previous)
        u.text("Wheel / Page Up & Down to read the journal",(562,699),15,MUTED)
        u.button("Return to the village",(136,724,1008,39),"dismiss",primary=True)

    def draw_map(self):
        u=self.ui
        self.modal_header("CLICK A PLACE TO WALK THERE","Willowmere",(100,55,1080,728))
        rect=pygame.Rect(140,185,664,493)
        mini=self.world.backgrounds[1 if self.state.balance>=.55 else 0].copy()
        for name,x,y in self.world.decor:
            sprite=self.art.sprite(name,self.state.balance>=.55)
            mini.blit(sprite,(x-sprite.get_width()//2,y-sprite.get_height()))
        self.surface.blit(pygame.transform.scale(mini,rect.size),rect)
        pygame.draw.rect(self.surface,(174,188,159),rect,2,border_radius=3)
        items=[("Mira / community","mira"),("Rowan / garden","rowan"),("Amani / Riverside","amani"),("Theo / old mill","theo"),("Neighbourhood circle","council"),("Neighbours arguing","dispute"),("Garden sign-up board","plots"),("River pump","pump"),("Willow refuge","quiet"),("River bank bench","quiet_river"),("Garden overlook","quiet_garden")]
        places={p.id:p for p in self.world.places}
        items=[(label,ident) for label,ident in items if not self.world.hidden(places[ident],self.state)]
        step=min(68,470//len(items))
        for i,(label,ident) in enumerate(items):
            p=places[ident]
            x=rect.x+p.x/WIDTH*rect.w;y=rect.y+p.y/HEIGHT*rect.h
            pygame.draw.circle(self.surface,GREEN,(round(x),round(y)),12)
            u.text(i+1,(x,y),15,WHITE,True,"center")
            u.button(f"{i+1}  {label}",(831,185+i*step,307,step-8),"travel:"+ident)
        px=rect.x+self.world.player.x/WIDTH*rect.w;py=rect.y+self.world.player.y/HEIGHT*rect.h
        pygame.draw.circle(self.surface,GOLD,(round(px),round(py)),9)
        pygame.draw.circle(self.surface,WHITE,(round(px),round(py)),10,2)
        u.text("YOU",(px,py+15),14,INK,True,"midtop")
        u.text("Cross the bridge to reach Riverside. Every neighbour has something to offer.",(142,692),18,MUTED)
        u.button("Return to the village",(140,727,998,40),"dismiss",primary=True)

    def draw_recap_row(self,row,y):
        """One decision in the ethical review: what was chosen, who gained, who was left out."""
        u=self.ui
        parts=[(row["label"],21,True,INK),
               ("You chose: "+row["chosen"],18,False,INK),
               ("Who it helped: "+row["benefited"],18,False,MUTED),
               ("Who it left out or put at risk: "+row["missed"],18,False,MUTED),
               (row["revisited"],17,False,GREEN),
               ("Ask yourself: "+row["question"],17,False,INK)]
        width=900
        heights=[len(u.lines(text,width,size,bold))*(u.font(size,bold).get_linesize()+3) for text,size,bold,_ in parts]
        total=sum(heights)+30
        rect=pygame.Rect(160,y,952,total)
        pygame.draw.rect(self.surface,WHITE,rect,border_radius=10)
        pygame.draw.rect(self.surface,INK if u.contrast else (197,205,184),rect,2 if u.contrast else 1,border_radius=10)
        line=y+14
        for (text,size,bold,color),height in zip(parts,heights):
            u.paragraph(text,(rect.x+22,line),width,size,color,bold,gap=3)
            line+=height
        return y+total+12

    def draw_ending(self):
        u=self.ui
        self.modal_header("A BEGINNING YOU MADE TOGETHER","Common ground, found.",(120,70,1040,700))
        clip=pygame.Rect(151,184,978,462)
        previous=self.surface.get_clip();self.surface.set_clip(clip)
        y=190-self.scroll
        for i,paragraph in enumerate(self.state.epilogue()):
            y=u.paragraph(paragraph,(160,y),952,25 if i==0 else 21,INK if i==0 else MUTED,gap=7)+10
        y+=8
        for i,(key,label) in enumerate((("environment","A place to grow"),("equity","A place at the table"),("resilience","A place to breathe"))):
            x=185+i*325
            u.symbol(key,(x+25,y+22),GREEN,1.3)
            u.text(label,(x,y+54),22,INK,True)
            u.text(str(round(self.state.metrics[key])),(x,y+88),30,GREEN,True)
        y+=146
        rows=self.state.recap()
        if rows:
            u.text("YOUR CHOICES, AND WHO THEY REACHED",(160,y),16,GREEN,True);y+=30
            for row in rows:
                y=self.draw_recap_row(row,y)
        u.text("What would you do differently in your own community?",(160,y+8),21,INK)
        y+=52
        self.max_scroll=max(0,y+self.scroll-clip.bottom)
        self.surface.set_clip(previous)
        if self.max_scroll:u.text("Scroll / Page Down to read how your choices shaped the ending",(160,654),16,MUTED)
        u.button("Keep exploring",(160,704,458,46),"dismiss",primary=True)
        u.button("Save & return to title",(635,704,484,46),"title")

    def draw(self):
        self.ui.begin()
        self.surface.fill(INK)
        if self.mode in ("title","confirm","intro") or self.mode in ("settings","help") and self.return_mode=="title":
            self.draw_title()
            if self.mode!="title":self.ui.begin()
        else:
            self.step=self.state.next_step()
            marker=None
            if self.mode=="play" and self.settings["show_way"] and "balanced" not in self.state.flags:
                marker=self.world.hint_place(self.step[1],self.state)
            drift=(0,0)
            if self.mode=="quiet" and not self.settings["reduced_motion"]:
                drift=(math.sin(self.quiet_time*.17)*14,math.cos(self.quiet_time*.13)*8)
            self.world.draw(self.surface,self.state,self.elapsed,self.settings["reduced_motion"],self.settings["high_contrast"],drift,marker)
            self.draw_hud()
            if self.mode=="quiet":self.fade_hud()
            if self.mode!="play":self.ui.begin()
        if self.mode=="intro":self.draw_intro()
        elif self.mode=="help":self.draw_intro(True)
        elif self.mode=="confirm":self.draw_confirm()
        elif self.mode=="dialogue":self.draw_dialogue()
        elif self.mode=="result":self.draw_result()
        elif self.mode=="pause":self.draw_pause()
        elif self.mode=="settings":self.draw_settings()
        elif self.mode=="quiet":self.draw_quiet()
        elif self.mode=="journal":self.draw_journal()
        elif self.mode=="map":self.draw_map()
        elif self.mode=="ending":self.draw_ending()
        if self.toast_time>0 and self.mode=="play":
            width=min(1180,self.ui.font(18).size(self.toast)[0]+44)
            pygame.draw.rect(self.surface,INK,(640-width/2,110,width,37),border_radius=8)
            self.ui.text(self.toast,(640,128),18,WHITE,False,"center")
        return self.surface

    def present(self):
        w,h=self.window.get_size();factor=min(w/1280,h/840)
        size=(max(1,round(1280*factor)),max(1,round(840*factor)))
        self.window.fill(INK)
        self.window.blit(pygame.transform.smoothscale(self.surface,size),((w-size[0])//2,(h-size[1])//2))
        pygame.display.flip()

    def run(self):
        self.draw();self.present()
        while self.running:
            dt=min(self.clock.tick(60)/1000,.05)
            for event in pygame.event.get():
                previous_mode=self.mode
                self.handle(event)
                if self.mode!=previous_mode:self.draw()
            self.update(dt);self.draw();self.present()
        self.close()

    def close(self):
        if self.audio:self.audio.close()
        pygame.quit()
