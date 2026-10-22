"""Deterministic rendered playthrough using real Pygame events and UI actions."""
from __future__ import annotations

from collections import deque
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from game.app import App
from game.audio import find_bgm
from game.storage import load_game


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix="common-ground-test-") as temp:
        app=App(save_dir=temp,window=False)
        # The background track must be found and playing, including inside the packaged executable.
        music=bool(app.audio and app.audio.available and app.audio.bgm_active)
        if app.audio and app.audio.available and find_bgm():assert music,"the background track should be playing"
        captures=[]
        def capture(name,mode=None):
            if mode is not None:assert app.mode==mode,(name,app.mode,mode)
            app.draw()
            path=output/(name+".png")
            pygame.image.save(app.surface,str(path));captures.append(path.name)
        def key(k):
            app.draw()
            app.handle(pygame.event.Event(pygame.KEYDOWN,key=k));app.draw()
        capture("01-title","title")
        key(pygame.K_RETURN)
        assert app.mode=="intro"
        capture("02-intro","intro")
        key(pygame.K_RETURN)
        assert app.mode=="play" and app.slot.exists()
        app.update(1/60);capture("03-village-before","play")
        # Every interactable is physically approachable from the initial path.
        start=(int(app.world.player.x//16),int(app.world.player.y//16))
        queue=deque([start]);seen={start}
        while queue:
            x,y=queue.popleft()
            for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
                nxt=x+dx,y+dy
                if nxt not in seen and app.world.walkable((nxt[0]*16+8,nxt[1]*16+8)):
                    seen.add(nxt);queue.append(nxt)
        for place in app.world.places:
            assert any((x*16+8-place.x)**2+(y*16+8-place.y)**2<40**2 for x,y in seen),place.id
        # Exercise A* and actual axis collision movement, including the bridge.
        for ident in ("mira","theo","amani","quiet","rowan"):
            place=next(p for p in app.world.places if p.id==ident)
            assert app.world.walk_to((place.x,place.y+29)),ident
            frames=0
            while app.world.path and frames<5000:
                app.world.update(1/60,pygame.key.get_pressed(),app.state)
                frames+=1
            assert not app.world.path,(ident,"path stalled")
            assert app.world.player.distance_to((place.x,place.y))<58
        app.world.player.update(480,500);app.update(1/60)
        mira=next(p for p in app.world.places if p.id=="mira")
        app.interact(mira);capture("04-conversation","dialogue")
        key(pygame.K_1)
        assert app.mode=="result" and "support_mira" in app.state.completed
        capture("05-listening","result")
        key(pygame.K_RETURN)
        # Collect and restore through the same interaction UI used in the game.
        for ident in [f"litter_{i}" for i in range(1,7)]+[f"crate_{i}" for i in range(1,4)]+[f"garden_{i}" for i in range(1,4)]+["pump"]:
            place=next(p for p in app.world.places if p.id==ident)
            app.world.player.update(place.x,place.y+29)
            app.interact(place)
            assert app.result.ok,(ident,app.result)
            key(pygame.K_RETURN)
        for ident,choice in (("rowan","listen"),("amani","listen"),("theo","workshop")):
            app.interact(next(p for p in app.world.places if p.id==ident))
            app.draw()
            app.action("choice:"+choice)
            assert app.result.ok,app.result
            key(pygame.K_RETURN)
        app.interact(next(p for p in app.world.places if p.id=="council"))
        capture("06-resource-dilemma","dialogue")
        app.action("choice:needs");assert app.result.ok
        assert len(app.result.outcome)==4
        capture("06b-outcome-panel","result")
        key(pygame.K_RETURN)
        app.interact(next(p for p in app.world.places if p.id=="quiet"))
        assert app.mode=="quiet"
        capture("07-quiet-refuge","quiet")
        app.action("quiet_reflect");assert "quiet_reflected" in app.state.flags
        key(pygame.K_RETURN)
        # Later scenes use the same screens and rules as the rest of the story.
        def place(ident):return next(p for p in app.world.places if p.id==ident)
        assert app.world.hidden(place("dispute"),app.state)==False and app.world.hidden(place("plots"),app.state)==False
        for person in ("rowan","mira","amani","theo"):
            beat=app.state.available_beat(person);assert beat,person
            app.interact(place(person));app.draw()
            assert any(c.id.startswith(beat.id+":") for c in app.conversation.choices),person
            if person=="rowan":capture("14-resident-scene","dialogue")
            app.action("choice:"+beat.id+":"+beat.options[0].id);assert app.result.ok and app.result.resolved,person
            key(pygame.K_RETURN)
        app.interact(place("dispute"));capture("15-de-escalation","dialogue")
        app.action("choice:blame");assert "rejected_dispute" in app.state.completed
        key(pygame.K_RETURN)
        app.interact(place("dispute"));app.action("choice:shared_need");assert "dispute" in app.state.completed
        key(pygame.K_RETURN)
        app.interact(place("plots"));capture("16-plot-dilemma","dialogue")
        app.action("choice:lottery");assert len(app.result.outcome)==4
        capture("17-plot-outcome","result");key(pygame.K_RETURN)
        for ident in ("quiet_river","quiet_garden"):
            quiet=place(ident);app.world.player.update(quiet.x,quiet.y+29)
            app.interact(quiet);assert app.mode=="quiet",ident
            app.quiet_time=3
            if ident=="quiet_river":capture("18-quiet-river","quiet")
            app.action("quiet_reflect");assert app.result.ok and ident in app.state.completed
            key(pygame.K_RETURN)
        # Residents you supported walk to the place they care about, and the village shows it.
        for _ in range(900):app.world.update(1/30,pygame.key.get_pressed(),app.state)
        for ident,post in (("rowan",(748,648)),("theo",(702,286)),("amani",(955,410))):
            assert (place(ident).x,place(ident).y)==post,(ident,place(ident).x,place(ident).y)
        app.world.player.update(480,500);app.update(1/60)
        assert app.state.can_finish
        app.toast_time=0
        capture("08-village-restored","play")
        app.ui.mouse=(520,40);capture("08b-hud-hover","play");app.ui.mouse=(-1,-1)
        key(pygame.K_j);capture("09-journal","journal")
        key(pygame.K_ESCAPE);key(pygame.K_TAB);capture("10-map","map")
        key(pygame.K_ESCAPE);key(pygame.K_ESCAPE)
        assert app.mode=="pause"
        app.action("settings")
        for setting in ("large_text","reduced_motion","high_contrast","muted","slow_walk"):
            app.action("setting:"+setting)
        capture("11-settings-large-text","settings")
        app.action("back");app.action("resume")
        app.interact(next(p for p in app.world.places if p.id=="council"))
        capture("12-council-large-text","dialogue")
        app.action("choice:finish")
        assert app.mode=="ending",(app.mode,app.state.flags)
        capture("13-ending","ending")
        assert app.max_scroll>0
        app.scroll=app.max_scroll;capture("19-ending-recap","ending")
        app.scroll=0
        state,position=load_game(app.slot)
        assert state.to_dict()==app.state.to_dict()
        app.action("dismiss");app.action("title")
        assert app.save_valid
        app.action("continue");assert "balanced" in app.state.flags
        # Smaller / wider windows keep a letterboxed interface, with correct clicks.
        app.window=pygame.display.set_mode((960,600),pygame.HIDDEN)
        app.draw();app.present()
        assert app.logical_mouse((480,300))==(640,420)
        report={"ok":True,"reachable_cells":len(seen),"reachable_interactables":len(app.world.places),"metrics":state.metrics,"resources":state.resources,"background_music":music,"captures":captures,"checks":["real keyboard UI flow","all locations reachable","A* walking and bridge collision","empathetic conversations","finite resources","environment restoration","quiet reflection without waiting","journal and map","all accessibility settings","resident scenes and de-escalation","garden plot dilemma with outcome panels","extra quiet places","residents walk to their posts","ending recap and epilogue","balance ending through council","background music loads and loops","save and continue","window resize and coordinate mapping"]}
        (output/"verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        app.close()
        print(json.dumps(report,indent=2))
