"""A walkable, persistent village with original pixel-art scenery."""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
import random

import pygame

from .layout import HEIGHT, RIVERSIDE_EDGE, TILE, WIDTH

VIEW = pygame.Rect(0, 108, 1280, 636)
# Windows of the Hall and the health post, lit from inside during the night of the storm.
LIT_WINDOWS = tuple((1362 + x, 212 + 70, 14, 20) for x in (28, 54, 108, 134)) + ((1176 + 29, 228 + 60, 14, 18), (1176 + 91, 228 + 60, 14, 18))
SANDBAGS = (1010, 396)
COTS = (1450, 368)
ORCHARD = (1400, 640)
WEATHER_TINT = {"overcast": ((92, 104, 120), 46), "storm": ((14, 22, 46), 132), "aftermath": ((86, 100, 112), 38)}
MILL = (665, 181)
RIVER_X = 848


@dataclass
class Place:
    id: str
    name: str
    x: float
    y: float
    sprite: str
    kind: str = "task"
    # Where a supported resident helps out; they walk there once you have listened.
    post: tuple | None = None


def _cue_river(state):
    return "The water below the outflow runs clearer now." if "source_repaired" in state.flags else "A grey-green film drifts downstream from the mill outflow."


def _cue_tree(state):
    return "New buds have opened on the old tree beside the outflow." if "source_repaired" in state.flags else "A bare tree stands where the outflow soaks the ground."


def _cue_flood(state):
    if "beat_amani_3" in state.completed:
        return "Water lines from old floods. Riverside residents now help plan the drainage."
    return "Water lines on the wall, from floods nobody planned for. Riverside says it was never asked about drainage."


def _cue_sign(state):
    if state.choices.get("allocation") == "needs" or "council_review" in state.completed:
        return "A delivery cart waits where a hand-lettered sign once asked: what about Riverside?"
    return "A faded sign reads: What about Riverside?"


def _cue_rope(state):
    return "A queue rope shows where the line forms at the square." if rope_visible(state) else None


def _cue_chimney(state):
    if "factory_shared" in state.flags:
        return "The mill chimney is clean. The workshop's work happens in the open."
    if state.choices.get("theo") == "restart":
        return "Smoke rises from the mill chimney again, and neighbours are watching the river."
    return "Soot darkens the old mill chimney."


def _cue_orchard(state):
    if "memory_tree" not in state.completed:
        return None
    return "Young trees on the slope below the Hall, each one named after a child on the street."


def _cue_hall(state):
    phase = state.storm_phase()
    if phase == "forecast" and "prep_hall" in state.completed:
        return "Cots are stacked ready along the Hall's wall, and the water tanks are full."
    if phase == "forecast":
        return "The Common Hall is quiet. Soon it may be the only dry place for a lot of people."
    if phase == "aftermath":
        return "Mud on the Hall's steps, and cots still out where people slept."
    return None


def _cue_health_post(state):
    if "beat_noor_1" in state.completed:
        return "The health post door is propped open. A hand-lettered sign gives the hours, and a number to ring when someone needs more than a neighbour."
    return "The health post is open two days a week. A box of leaflets holds the door."


def rope_visible(state):
    """The queue rope stays until the circle moves away from a first-come queue."""
    if "council" not in state.completed:
        return True
    return state.choices.get("allocation") == "queue" and "council_review" not in state.completed


def cart_ready(state):
    return state.choices.get("allocation") == "needs" or "council_review" in state.completed


# Things worth noticing. Each has a spot, a radius, and a caption that follows the story.
CUES = (
    (830, 330, 110, _cue_river),
    (770, 262, 70, _cue_tree),
    (1010, 371, 95, _cue_flood),
    (1025, 657, 95, _cue_flood),
    (925, 384, 70, _cue_sign),
    (420, 508, 70, _cue_rope),
    (693, 120, 90, _cue_chimney),
    (1400, 600, 90, _cue_orchard),
    (1450, 372, 90, _cue_hall),
    (1240, 372, 70, _cue_health_post),
)

# Residents' homes are the Place coordinates; these are where they help once supported.
POSTS = {"rowan": (748, 648), "theo": (702, 286), "amani": (955, 410)}
# Scenery that follows the story.
DEAD_TREE = (770, 262)
SIGN = (925, 384)
ROPE = (420, 508)
FLOODED_HOUSES = ((1010, 371), (1025, 657))


class World:
    def __init__(self, art):
        self.art = art
        self.player = pygame.Vector2(480, 500)
        self.camera = pygame.Vector2(160, 240)
        self.walking = False
        self.facing = "down"
        self.stride = 0.0
        self.path = []
        self.places = [
            Place("mira", "Mira", 480, 450, "mira", "npc"),
            Place("rowan", "Rowan", 655, 665, "rowan", "npc", POSTS["rowan"]),
            Place("amani", "Amani", 980, 470, "amani", "npc", POSTS["amani"]),
            Place("theo", "Theo", 685, 258, "theo", "npc", POSTS["theo"]),
            Place("council", "Neighbourhood circle", 480, 310, "bench", "council"),
            Place("dispute", "Neighbours arguing", 548, 340, "dispute", "npc"),
            Place("plots", "Garden sign-up board", 540, 640, "noticeboard", "council"),
            Place("pump", "River pump", 750, 327, "pump"),
            Place("quiet", "Willow refuge", 185, 620, "bench", "quiet"),
            Place("quiet_river", "River bank bench", 918, 520, "bench", "quiet"),
            Place("quiet_garden", "Garden overlook", 772, 588, "bench", "quiet"),
            Place("noticeboard", "The story of Willowmere", 370, 448, "noticeboard", "lore"),
            Place("garden_1", "Community garden", 607, 600, "plot"),
            Place("garden_2", "Community garden", 657, 600, "plot"),
            Place("garden_3", "Community garden", 707, 600, "plot"),
            Place("litter_1", "Discarded bottles", 360, 350, "litter"),
            Place("litter_2", "Plastic by the river", 745, 472, "litter"),
            Place("litter_3", "Debris in the grove", 265, 585, "litter"),
            Place("litter_4", "Factory waste", 633, 288, "litter"),
            Place("litter_5", "Riverside litter", 960, 540, "litter"),
            Place("litter_6", "Roadside waste", 549, 719, "litter"),
            Place("crate_1", "Shared repair supplies", 340, 490, "crate"),
            Place("crate_2", "Salvaged supplies", 734, 235, "crate"),
            Place("crate_3", "Riverside supplies", 1013, 514, "crate"),
            # Hillside and the people who live beyond Riverside.
            Place("kit", "Kit", 1110, 470, "kit", "npc"),
            Place("noor", "Noor", 1240, 372, "noor", "npc"),
            Place("odile", "Odile", 1650, 372, "odile", "npc"),
            Place("sample_up", "River sample: upstream", 915, 140, "sample"),
            Place("sample_out", "River sample: outflow", 915, 310, "sample"),
            Place("sample_down", "River sample: downstream", 915, 610, "sample"),
            Place("quiet_lookout", "The Lookout", 1568, 160, "bench", "quiet"),
            # Part Two: Storm Season.
            Place("storm", "Storm board at the Hall", 1400, 376, "noticeboard", "council"),
            Place("recover_streets", "Storm debris in the square", 620, 372, "debris"),
            Place("recover_homes", "Flooded Riverside homes", 1090, 395, "debris"),
            Place("recover_hall", "The Hall after the night", 1500, 376, "debris"),
        ]
        self.homes = {p.id: (p.x, p.y) for p in self.places}
        self.decor = [
            ("house", 479, 241), ("house", 297, 320),
            ("house", 1010, 371), ("house", 1025, 657),
            ("workshop", 665, 181), ("house", 425, 722),
            ("clinic", 1240, 340), ("hall", 1450, 340), ("cottage", 1650, 340),
        ]
        self.solids = [pygame.Rect(427,168,104,69),pygame.Rect(245,248,104,68),
                       pygame.Rect(958,298,104,69),pygame.Rect(973,584,104,69),
                       pygame.Rect(605,107,120,70),pygame.Rect(373,649,104,69),
                       pygame.Rect(1188,267,104,69),pygame.Rect(1370,244,160,90),pygame.Rect(1612,280,76,54)]
        self.trees = [(135,232),(166,286),(185,199),(85,330),(290,190),
                      (577,223),(565,321),(778,169),(1010,199),(971,248),
                      (89,574),(124,645),(220,709),(298,702),(103,718),
                      (366,589),(559,548),(760,685),(926,740),(1080,740),
                      (1060,440),(104,476),(544,787),(320,786),(97,115),
                      # Hillside
                      (1140,150),(1200,170),(1300,160),(1380,150),(1470,140),(1620,170),(1700,150),(1731,260),
                      (1331,300),(1180,560),(1230,700),(1300,760),(1560,540),(1640,700),(1720,600),(1500,740),(1660,500)]
        for x,y in self.trees:
            self.solids.append(pygame.Rect(x-9,y-14,18,16))
        self.solids.append(pygame.Rect(DEAD_TREE[0]-9,DEAD_TREE[1]-14,18,16))
        self.backgrounds = [self.make_background(False),self.make_background(True)]
        self.low = pygame.Surface((640,318))
        self.green_layer = pygame.Surface((640,318))
        self.grade = pygame.Surface((640,318))
        self.plume_image = self.make_plume()
        self.plume = None
        self.nearest = None
        self.synced_state = None
        self.motes = self.make_motes()
        self.weather_layer = pygame.Surface((640, 318))
        rng = random.Random(23)
        self.rain = [(rng.uniform(0, 640), rng.uniform(0, 318), rng.uniform(.8, 1.3)) for _ in range(150)]
        self.puddles = [(rng.uniform(40, WIDTH - 40), rng.uniform(80, HEIGHT - 40), rng.uniform(10, 26)) for _ in range(34)]

    def tile_kind(self,x,y):
        wx,wy=x*TILE,y*TILE
        if 800 <= wx < 896:
            return "bridge" if 384 <= wy < 448 else "water"
        main = 64 <= wx < 1696 and 384 <= wy < 448
        lookout_lane = 1536 <= wx < 1600 and 128 <= wy < 384
        spine = 448 <= wx < 512 and 128 <= wy < 736
        garden = 224 <= wx < 768 and 608 <= wy < 640
        west = 224 <= wx < 288 and 416 <= wy < 640
        factory = 480 <= wx < 736 and 192 <= wy < 224
        factory_lane = 704 <= wx < 736 and 192 <= wy < 416
        pump_lane = 704 <= wx < 800 and 320 <= wy < 352
        east = 960 <= wx < 1024 and 320 <= wy < 640
        grove = 160 <= wx < 256 and 608 <= wy < 640
        return "path" if any((main,spine,garden,west,factory,factory_lane,pump_lane,east,grove,lookout_lane)) else "grass"

    def make_background(self, restored):
        s = pygame.Surface((WIDTH,HEIGHT))
        rng=random.Random(41)
        for y in range(HEIGHT//TILE):
            for x in range(WIDTH//TILE):
                kind=self.tile_kind(x,y)
                s.blit(self.art.tile(kind,restored),(x*TILE,y*TILE))
                if kind == "grass" and rng.random()<.11:
                    c=(176,181,112) if restored else (140,144,115)
                    px,py=x*TILE+rng.randrange(24),y*TILE+rng.randrange(24)
                    pygame.draw.line(s,c,(px,py),(px+2,py-3))
        # Flat, low stone garden borders and the old mill's drainage outfall.
        for r in [pygame.Rect(576,550,162,70),pygame.Rect(140,572,94,93),pygame.Rect(1330,572,150,72),pygame.Rect(1528,118,80,66)]:
            pygame.draw.rect(s,(119,139,113) if restored else (125,129,112),r,3,border_radius=9)
        pygame.draw.rect(s,(96,110,103),(762,291,38,13))
        pygame.draw.rect(s,(65,89,82),(785,293,15,10))
        return s

    def make_plume(self):
        """A grey-green film and foam on the water below the outflow, drawn once."""
        image = pygame.Surface((120, 300), pygame.SRCALPHA)
        rng = random.Random(9)
        for i in range(34):
            y = 8 + i * 8 + rng.randrange(5)
            width = 70 - abs(i - 6) * 1.2 + rng.randrange(-8, 9)
            x = 14 + rng.randrange(0, 12)
            alpha = max(30, int(120 - i * 2.4))
            pygame.draw.ellipse(image, (118, 130, 92, alpha), (x, y, max(24, int(width)), 7))
        for i in range(16):
            x, y = 14 + rng.randrange(80), 4 + i * 17 + rng.randrange(8)
            pygame.draw.line(image, (214, 220, 196, 150), (x, y), (x + rng.randrange(6, 16), y), 1)
        return image

    def make_motes(self):
        rng = random.Random(7)
        return [(rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT), rng.uniform(0, math.tau), rng.uniform(.6, 1.4)) for _ in range(110)]

    def walkable(self,position):
        x,y=position
        feet=pygame.Rect(round(x)-7,round(y)-9,14,12)
        if not (32 <= x <= WIDTH-32 and 56 <= y <= HEIGHT-32):
            return False
        if feet.colliderect(pygame.Rect(800,0,96,384)) or feet.colliderect(pygame.Rect(800,448,96,HEIGHT-448)):
            return False
        return not any(feet.colliderect(rect) for rect in self.solids)

    def move(self,vector,dt,speed=140):
        vector=pygame.Vector2(vector)
        self.walking=vector.length_squared()>.01
        if self.walking:
            if abs(vector.x)>abs(vector.y):self.facing="right" if vector.x>0 else "left"
            else:self.facing="down" if vector.y>0 else "up"
            vector=vector.normalize()*speed*min(dt,.05)
            self.stride+=vector.length()
            # Short substeps keep corners and narrow bridges solid.
            steps=max(1,math.ceil(vector.length()/4))
            for _ in range(steps):
                for axis in (0,1):
                    p=self.player.copy()
                    p[axis]+=vector[axis]/steps
                    if self.walkable(p): self.player=p

    def walk_to(self,destination):
        start=(int(self.player.x//16),int(self.player.y//16))
        goal=(int(destination[0]//16),int(destination[1]//16))
        if not self.walkable((goal[0]*16+8,goal[1]*16+8)):
            return False
        frontier=[(0,start)]; came={start:None}; costs={start:0}
        while frontier:
            _,cell=heapq.heappop(frontier)
            if cell==goal: break
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nxt=(cell[0]+dx,cell[1]+dy)
                if not self.walkable((nxt[0]*16+8,nxt[1]*16+8)): continue
                cost=costs[cell]+1
                if cost<costs.get(nxt,999999):
                    costs[nxt]=cost; came[nxt]=cell
                    priority=cost+abs(goal[0]-nxt[0])+abs(goal[1]-nxt[1])
                    heapq.heappush(frontier,(priority,nxt))
        if goal not in came: return False
        route=[];cell=goal
        while cell!=start:
            route.append(pygame.Vector2(cell[0]*16+8,cell[1]*16+8));cell=came[cell]
        self.path=list(reversed(route))
        return True

    def update(self,dt,keys,state,speed=1,reduce_motion=False,pad=None):
        vector=pygame.Vector2(int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                             int(keys[pygame.K_s] or keys[pygame.K_DOWN])-int(keys[pygame.K_w] or keys[pygame.K_UP]))
        if not vector.length_squared() and pad is not None and pad.length_squared()>.04:
            vector=pygame.Vector2(pad)
        if vector.length_squared(): self.path=[]
        elif self.path:
            vector=self.path[0]-self.player
            if vector.length()<5:
                self.path.pop(0)
                vector=pygame.Vector2()
        self.move(vector,dt,140*speed)
        target=pygame.Vector2(max(0,min(WIDTH-640,self.player.x-320)),max(0,min(HEIGHT-318,self.player.y-159)))
        self.camera=target
        self.sync_helpers(state,dt,reduce_motion)
        self.ease_plume(state,dt,reduce_motion)
        available=[p for p in self.places if not self.hidden(p,state)]
        near=min(available,key=lambda p:self.player.distance_to((p.x,p.y)))
        self.nearest=near if self.player.distance_to((near.x,near.y))<58 else None

    def sync_helpers(self,state,dt,snap=False):
        """Residents you have listened to walk to the place they care about."""
        first=self.synced_state is not state
        self.synced_state=state
        for p in self.places:
            if p.post is None: continue
            goal=p.post if f"support_{p.id}" in state.completed else self.homes[p.id]
            here=pygame.Vector2(p.x,p.y)
            gap=pygame.Vector2(goal)-here
            if snap or first or gap.length()<=1:
                p.x,p.y=goal
            else:
                step=gap.normalize()*min(gap.length(),38*min(dt,.05))
                p.x,p.y=here+step

    def ease_plume(self,state,dt,snap=False):
        target=0.0 if "source_repaired" in state.flags else 1.0
        if self.plume is None or snap:
            self.plume=target
        else:
            self.plume+=(target-self.plume)*min(1,dt*.7)

    def hidden(self,p,state):
        if p.id.startswith("litter_") or p.id.startswith("crate_"):
            return p.id in state.completed
        if p.id=="dispute":
            return "council" not in state.completed
        if p.id=="plots":
            return "garden_open" not in state.flags
        if p.id.startswith("sample_"):
            return "support_kit" not in state.completed
        if p.id=="storm":
            return "storm_forecast" not in state.completed
        if p.id.startswith("recover_"):
            return "storm_s5" not in state.completed or p.id in state.completed
        return False

    def zone(self):
        x,y=self.player
        if x>RIVERSIDE_EDGE:return "HILLSIDE"
        if x>896:return "RIVERSIDE"
        if y<320:return "OLD MILL & COMMONS"
        if y>540 and x<360:return "WILLOW REFUGE"
        if y>540 and x>550:return "COMMUNITY GARDEN"
        return "WILLOWMERE"

    def audio_zones(self):
        """How near the player is to the mill, the river and the trees, from 0 to 1."""
        px,py=self.player
        tree=min(math.hypot(px-x,py-y) for x,y in self.trees)
        return {"mill":max(0,1-math.hypot(px-MILL[0],py-MILL[1])/320),
                "river":max(0,1-abs(px-RIVER_X)/260),
                "trees":max(0,1-tree/260)}

    def cue_caption(self,state):
        """A one-line observation for whatever the player is standing near, if anything."""
        px,py=self.player
        best=None
        for x,y,radius,caption in CUES:
            distance=math.hypot(px-x,py-y)
            if distance<radius and (best is None or distance<best[0]):
                text=caption(state)
                if text: best=(distance,text)
        return best[1] if best else None

    def hint_place(self,target,state):
        """The place a suggestion points to: 'collect' means the nearest remaining litter or crate."""
        if target is None: return None
        candidates=[p for p in self.places if not self.hidden(p,state)]
        if target=="collect":
            candidates=[p for p in candidates if p.id.startswith(("litter_","crate_"))]
        elif target=="garden":
            candidates=[p for p in candidates if p.id.startswith("garden_") and p.id not in state.completed][:1]
        else:
            candidates=[p for p in candidates if p.id==target]
        return min(candidates,key=lambda p:self.player.distance_to((p.x,p.y))) if candidates else None

    def sprite_for(self,p,state):
        if p.kind=="npc" and p.id!="dispute":
            return self.art.person(p.sprite,"down",0,f"support_{p.id}" in state.completed)
        if p.id.startswith("garden_"):
            stage=state.garden_stage(p.id)
            return self.art.sprite(("plot","plot_seed","plot_sprout","plot")[stage],stage==3)
        if p.id=="dispute":
            return self.art.sprite("dispute","dispute" in state.completed)
        if p.id=="plots":
            return self.art.sprite("noticeboard","plots" in state.completed)
        if p.id.startswith("sample_"):
            return self.art.sprite("sample",state.river_reading(p.id.split("_",1)[1])[0]>=2)
        restored=p.id in state.completed or (p.id=="pump" and "source_repaired" in state.flags)
        return self.art.sprite(p.sprite,restored)

    def draw_particles(self,t,balance,reduce_motion,camera):
        """Smog specks when the village is struggling, pollen and the odd butterfly when it thrives."""
        if balance<.42:
            count=int((.42-balance)/.42*len(self.motes)*.8)+8
            color=(112,116,106)
        elif balance>.6:
            count=int((balance-.6)/.4*len(self.motes))+4
            color=(255,236,160)
        else:
            return
        for i,(bx,by,phase,rate) in enumerate(self.motes[:count]):
            if reduce_motion:
                x,y=bx,by
            elif balance<.42:
                x=(bx+t*5*rate)%WIDTH;y=by+math.sin(t*.5*rate+phase)*5
            else:
                x=bx+math.sin(t*.4*rate+phase)*9;y=(by-t*4*rate)%HEIGHT
            sx,sy=x-camera.x,y-camera.y
            if 0<=sx<640 and 0<=sy<318:
                pygame.draw.rect(self.low,color,(round(sx),round(sy),2,2) if balance<.42 else (round(sx),round(sy),1,1))
        if balance>.82:
            for i in range(3):
                bx,by,phase,rate=self.motes[i]
                x=bx+(0 if reduce_motion else math.sin(t*.6+phase)*40);y=by+(0 if reduce_motion else math.cos(t*.5+phase)*24)
                sx,sy=x-camera.x,y-camera.y
                if 0<=sx<640 and 0<=sy<318:
                    flap=1 if reduce_motion else int(math.sin(t*14+phase)>0)
                    c=(236,170,96) if i%2 else (150,190,230)
                    pygame.draw.rect(self.low,c,(round(sx)-2,round(sy)-flap,2,2));pygame.draw.rect(self.low,c,(round(sx)+1,round(sy)-flap,2,2))

    def draw_marker(self,place,t,reduce_motion,camera):
        """A gentle diamond over the suggested place, or an edge arrow pointing towards it."""
        sx,sy=place.x-camera.x,place.y-camera.y-52
        bob=0 if reduce_motion else math.sin(t*3)*2
        if 6<=sx<=634 and 10<=sy<=312:
            points=[(sx,sy+bob-6),(sx+5,sy+bob),(sx,sy+bob+6),(sx-5,sy+bob)]
            pygame.draw.polygon(self.low,(32,54,47),points,3)
            pygame.draw.polygon(self.low,(248,225,158),points)
            return
        dx,dy=sx-320,sy-159
        k=min(300/abs(dx) if dx else 1e9,140/abs(dy) if dy else 1e9)
        ex,ey=320+dx*k,159+dy*k
        length=math.hypot(dx,dy) or 1
        ux,uy=dx/length,dy/length
        tip=(ex,ey);left=(ex-ux*10-uy*6,ey-uy*10+ux*6);right=(ex-ux*10+uy*6,ey-uy*10-ux*6)
        pygame.draw.polygon(self.low,(32,54,47),[tip,left,right],3)
        pygame.draw.polygon(self.low,(248,225,158),[tip,left,right])

    def draw(self,screen,state,t,reduce_motion=False,high_contrast=False,drift=(0,0),marker=None):
        cam=pygame.Vector2(max(0,min(WIDTH-640,self.camera.x+drift[0])),max(0,min(HEIGHT-318,self.camera.y+drift[1])))
        balance=state.balance
        self.low.blit(self.backgrounds[0],(-round(cam.x),-round(cam.y)))
        self.green_layer.blit(self.backgrounds[1],(-round(cam.x),-round(cam.y)))
        self.green_layer.set_alpha(round(balance*255))
        self.low.blit(self.green_layer,(0,0))
        if self.plume is None: self.plume=0.0 if "source_repaired" in state.flags else 1.0
        if self.plume>.01:
            self.plume_image.set_alpha(round(self.plume*255))
            self.low.blit(self.plume_image,(790-cam.x,282-cam.y))
        # Ripples move gently; there is no blinking or screen shake.
        if not reduce_motion:
            water_color=(132,172,157) if balance>.6 else (128,151,135)
            for i in range(20):
                x=811+(i*17)%70; y=(i*71+int(t*5))%HEIGHT
                if 382<y<449: continue
                pygame.draw.line(self.low,water_color,(x-cam.x,y-cam.y),(x+9-cam.x,y-cam.y),1)
        layers=[]
        for name,x,y in self.decor:
            layers.append((y,"sprite",x,y,name,balance>.6,None))
            if name=="house" and (x,y) in FLOODED_HOUSES:
                layers.append((y+.1,"sprite",x,y,"flood","beat_amani_3" in state.completed,None))
            if name=="workshop" and "factory_shared" not in state.flags:
                layers.append((y+.1,"sprite",x,y,"soot",False,None))
        for x,y in self.trees:
            layers.append((y,"sprite",x,y,"tree",balance>.5,None))
        phase=state.storm_phase()
        if "memory_tree" in state.completed:
            stage=max(1,state.garden_stage("memory_tree"))
            layers.append((ORCHARD[1],"sprite",ORCHARD[0],ORCHARD[1],("orchard_seed","orchard_young","orchard")[stage-1],True,None))
        if phase in ("forecast","night","aftermath"):
            if "prep_drains" in state.completed:
                layers.append((SANDBAGS[1],"sprite",SANDBAGS[0],SANDBAGS[1],"sandbags",False,None))
            if "prep_hall" in state.completed:
                layers.append((COTS[1],"sprite",COTS[0],COTS[1],"cots",False,None))
        layers.append((DEAD_TREE[1],"sprite",DEAD_TREE[0],DEAD_TREE[1],"deadtree","source_repaired" in state.flags,None))
        layers.append((SIGN[1],"sprite",SIGN[0],SIGN[1],"sign",cart_ready(state),None))
        if rope_visible(state):
            layers.append((ROPE[1],"sprite",ROPE[0],ROPE[1],"rope",False,None))
        for p in self.places:
            if self.hidden(p,state):continue
            layers.append((p.y,"place",p.x,p.y,p.sprite,False,p))
        layers.append((self.player.y,"player",self.player.x,self.player.y,"player",False,None))
        for _,kind,x,y,name,restored,p in sorted(layers,key=lambda a:a[0]):
            if x<cam.x-150 or x>cam.x+790 or y<cam.y-30 or y>cam.y+440: continue
            wobble=0
            if kind=="player":
                step=0 if reduce_motion or not self.walking else 1+int(self.stride/9)%2
                sprite=self.art.person("player",self.facing,step)
                if self.walking and not reduce_motion:wobble=int(math.sin(t*15)*1.5)
            elif kind=="place":
                sprite=self.sprite_for(p,state)
                if p.kind=="npc" and not reduce_motion and p.id!="dispute":
                    wobble=1 if math.sin(t*1.6+len(p.id)*1.7)>.93 else 0
            else:
                sprite=self.art.sprite(name,restored)
            if high_contrast and (p or kind=="player"):
                pygame.draw.ellipse(self.low,(243,244,217),(x-cam.x-17,y-cam.y-7,34,13),3)
                pygame.draw.ellipse(self.low,(20,40,29),(x-cam.x-19,y-cam.y-8,38,15),1)
            self.low.blit(sprite,(round(x-cam.x-sprite.get_width()/2),round(y-cam.y-sprite.get_height()+wobble)))
            if p and p.kind in ("npc","council","quiet"):
                c=(242,209,130) if p.kind=="npc" else (223,230,191)
                point=(round(x-cam.x),round(y-cam.y-sprite.get_height()-7))
                if high_contrast:pygame.draw.circle(self.low,(20,40,29),point,5)
                pygame.draw.circle(self.low,c,point,3)
            if p and self.nearest and p.id==self.nearest.id:
                pygame.draw.ellipse(self.low,(248,225,158),(x-cam.x-14,y-cam.y-6,28,10),1)
        if "factory_shared" not in state.flags and state.choices.get("theo")=="restart":
            self.draw_smoke(t,reduce_motion,cam)
        if not high_contrast:
            # A colour grade: cool and grey while the village struggles, warm as it heals.
            if balance<.5:
                self.grade.fill((92,108,122));self.grade.set_alpha(round((.5-balance)/.5*58))
            else:
                self.grade.fill((255,208,140));self.grade.set_alpha(round((balance-.5)/.5*34))
            if self.grade.get_alpha(): self.low.blit(self.grade,(0,0))
        self.draw_particles(t,balance,reduce_motion,cam)
        self.draw_weather(state,t,reduce_motion,cam,high_contrast)
        if marker is not None:
            self.draw_marker(marker,t,reduce_motion,cam)
        if self.path:
            end=self.path[-1]-cam
            pygame.draw.circle(self.low,(244,228,177),(round(end.x),round(end.y)),5,1)
        screen.blit(pygame.transform.scale(self.low,VIEW.size),VIEW.topleft)

    def draw_weather(self,state,t,reduce_motion,cam,high_contrast=False):
        """Overcast before the storm, heavy rain and lit windows during it, wet ground and puddles after."""
        weather=state.weather()
        if weather=="clear": return
        colour,alpha=WEATHER_TINT[weather]
        if high_contrast: alpha=round(alpha*.45)
        self.weather_layer.fill(colour);self.weather_layer.set_alpha(alpha)
        self.low.blit(self.weather_layer,(0,0))
        if weather=="storm":
            for x,y,w,h in LIT_WINDOWS:
                rect=pygame.Rect(round(x-cam.x),round(y-cam.y),w,h)
                if self.low.get_rect().colliderect(rect):
                    pygame.draw.rect(self.low,(255,226,142),rect)
                    pygame.draw.rect(self.low,(255,244,200),rect.inflate(-8,-10))
        if weather=="aftermath":
            for x,y,size in self.puddles:
                sx,sy=x-cam.x,y-cam.y
                if 0<=sx<640 and 0<=sy<318:
                    pygame.draw.ellipse(self.low,(110,138,158),(round(sx-size/2),round(sy),round(size),round(size/3)))
                    pygame.draw.ellipse(self.low,(150,176,194),(round(sx-size/3),round(sy+1),round(size*2/3),max(1,round(size/6))))
            return
        count=150 if weather=="storm" else 22
        speed=260 if weather=="storm" else 90
        for i,(bx,by,rate) in enumerate(self.rain[:count]):
            y=by if reduce_motion else (by+t*speed*rate)%318
            x=bx if reduce_motion else (bx-t*speed*rate*.25)%640
            pygame.draw.line(self.low,(176,194,216) if weather=="storm" else (190,202,214),(round(x),round(y)),(round(x-2),round(y+(7 if weather=="storm" else 4))))

    def draw_smoke(self,t,reduce_motion,cam):
        """Dark puffs rise from the chimney while the old line is running."""
        for i in range(5):
            age=((0 if reduce_motion else t*.35)+i*.2)%1
            x=MILL[0]+26+math.sin(age*5+i)*4+age*10-cam.x
            y=MILL[1]-112-age*38-cam.y
            radius=3+age*6
            shade=int(70+age*40)
            pygame.draw.circle(self.low,(shade,shade+2,shade-2),(round(x),round(y)),round(radius))

    def screen_to_world(self,position):
        return pygame.Vector2((position[0]-VIEW.x)/2+self.camera.x,(position[1]-VIEW.y)/2+self.camera.y)

    def object_at(self,point,state):
        near=[p for p in self.places if not self.hidden(p,state) and pygame.Vector2(point).distance_to((p.x,p.y))<24]
        return min(near,key=lambda p:pygame.Vector2(point).distance_to((p.x,p.y))) if near else None
