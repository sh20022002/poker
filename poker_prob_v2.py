import pygame
import os
import sys
import random
from collections import Counter
from itertools import combinations

################################################################################
# 1. Configuration & Window Setup
################################################################################

# Desired startup window size
WIN_WIDTH = 1200
WIN_HEIGHT = 800


# Initialize Pygame with that window size
pygame.init()
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Texas Hold'em (Scaled UI & Background)")

# Load & scale your background image to fill the window
# Provide the actual path to your background PNG below
background_path = r"C:\Users\shmue\projects\python\open_pojects\poker\background.png"
try:
    bg_image = pygame.image.load(background_path)
    bg_image = pygame.transform.scale(bg_image, (WIN_WIDTH, WIN_HEIGHT))
except:
    bg_image = None
    print("Could not load background. Will use a plain color instead.")

# We define a “scale factor” for layout. All coordinates will be relative
# to a baseline 1200x800 design. If you change WIN_WIDTH/HEIGHT, everything scales.
SCALE_X = WIN_WIDTH / 1200.0
SCALE_Y = WIN_HEIGHT / 800.0

GAP = int(10 * SCALE_X)

# We’ll set up some fonts (scaled if you want them bigger/smaller).
base_font_size = 24
font_size = int(base_font_size * (SCALE_X + SCALE_Y)/2)  # average scale
font_20 = pygame.font.SysFont(None, font_size)
font_30 = pygame.font.SysFont(None, int(font_size * 1.5))

# The number of players (2..10)
num_players = 2

################################################################################
# 2. Minimal 7-card evaluator and probability (same as before)
################################################################################

RANKS_EVAL = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
RANK_TO_VAL = {r:i for i,r in enumerate(RANKS_EVAL, start=2)}

def best_7card_rank(cards7):
    # (Same simplified ranking logic as before)
    values = sorted([RANK_TO_VAL[c[0]] for c in cards7], reverse=True)
    suits = [c[1] for c in cards7]
    vcount = Counter(values)
    scount = Counter(suits)
    flush_suit = None
    for s in scount:
        if scount[s]>=5:
            flush_suit=s
            break
    flush_cards = []
    if flush_suit:
        flush_cards = sorted([v for v,su in zip(values,suits) if su==flush_suit], reverse=True)

    def top_straight(vals):
        uniq = sorted(set(vals), reverse=True)
        if 14 in uniq:
            uniq.append(1)
        run=1
        best=-1
        for i in range(len(uniq)-1):
            if uniq[i]-1==uniq[i+1]:
                run+=1
                if run>=5:
                    best = max(best, uniq[i-run+2])
            else:
                run=1
        return best

    straight_top= top_straight(values)
    flush_str_top= -1
    if len(flush_cards)>=5:
        flush_str_top= top_straight(flush_cards)

    # Category approach
    counts = sorted(vcount.values(), reverse=True)
    v_by_desc = sorted(vcount, key=lambda v: (vcount[v],v), reverse=True)

    if flush_str_top>0:
        return 9_00000000 + flush_str_top
    if counts[0]==4:  # quads
        fourv= v_by_desc[0]
        kicker= v_by_desc[1]
        return 8_00000000 + fourv*100 + kicker
    if counts[0]==3 and counts[1]==2:  # full house
        tv= v_by_desc[0]
        pv= v_by_desc[1]
        return 7_00000000 + tv*100 + pv
    if flush_suit:
        sc=0
        top5= flush_cards[:5]
        for v in top5:
            sc= sc*100+v
        return 6_00000000 + sc
    if straight_top>0:
        return 5_00000000 + straight_top
    if counts[0]==3:
        threev= v_by_desc[0]
        k1= v_by_desc[1]
        k2= v_by_desc[2]
        return 4_00000000 + threev*10000 + k1*100 + k2
    if counts[0]==2 and counts[1]==2:
        p1= v_by_desc[0]
        p2= v_by_desc[1]
        k= v_by_desc[2]
        if p1<p2: p1,p2=p2,p1
        return 3_00000000 + p1*10000 + p2*100 + k
    if counts[0]==2:
        pv= v_by_desc[0]
        ks= v_by_desc[1:4]
        sc= pv*1000000
        mul=10000
        for x in ks:
            sc+= x*mul
            mul//=100
        return 2_00000000+sc
    # high card
    sc=0
    top5= v_by_desc[:5]
    for v in top5:
        sc= sc*100+v
    return 1_00000000+sc

def hero_win_probability(hero2, known_comm, opponents, sims=2000):
    deck= [r+s for r in RANKS_EVAL for s in 'cdhs']
    used= set(hero2+ known_comm)
    deck= [c for c in deck if c not in used]
    need= 5- len(known_comm)
    if need<0: need=0
    if need> len(deck):
        return 0.0
    from random import sample
    wins=0
    ties=0
    for _ in range(sims):
        if need>0:
            draw= sample(deck, need)
            board= known_comm+ draw
        else:
            board= known_comm
        leftover= [x for x in deck if x not in board]
        hero7= hero2+ board
        hero_sc= best_7card_rank(hero7)
        best_opp= -1
        eq_opp=0
        use_deck= leftover[:]
        if len(use_deck)< opponents*2:
            continue
        for o in range(opponents):
            oc= sample(use_deck,2)
            for y in oc: use_deck.remove(y)
            sc= best_7card_rank(oc+ board)
            if sc> best_opp:
                best_opp= sc
                eq_opp=1
            elif sc== best_opp:
                eq_opp+=1
        if hero_sc> best_opp:
            wins+=1
        elif hero_sc== best_opp:
            ties+=1
    total= sims
    if total==0: return 0.0
    return (wins+0.5* ties)/ total

################################################################################
# 3. Load a background & define geometry for placeholders / deck region
################################################################################

# We'll define a “deck area” that starts lower. We'll define placeholders near top.
# We scale all distances by our scale factors.

# Base geometry for hero placeholders
BASE_HERO_POS = [(50,30), (140,30)]  # x,y pairs in 1200x800 coordinates
BASE_COMM_POS = [(300,30),(390,30),(480,30),(570,30),(660,30)]

# We'll define “plusRect” etc in base coords, then scale
BASE_PLUS_RECT = (210, 5, 30, 30)   # x,y,w,h
BASE_MINUS_RECT= (250, 5, 30, 30)
BASE_RESET_RECT= (290, 5, 70, 30)

# Card deck base offset
# We will place suits in rows, ranks in columns, starting at y=200 in the base design
CARD_START_Y= 200

def scaled_rect(x,y,w,h):
    return pygame.Rect(int(x*SCALE_X), int(y*SCALE_Y), int(w*SCALE_X), int(h*SCALE_Y))

def scale_coord(x,y):
    return (int(x*SCALE_X), int(y*SCALE_Y))

# We'll store hero_coords, comm_coords in actual screen coords:
hero_coords= [scale_coord(*p) for p in BASE_HERO_POS]
comm_coords= [scale_coord(*p) for p in BASE_COMM_POS]
plusRect= scaled_rect(*BASE_PLUS_RECT)
minusRect= scaled_rect(*BASE_MINUS_RECT)
resetRect= scaled_rect(*BASE_RESET_RECT)

# We'll define cardWidth/cardHeight after scaling
CARD_WIDTH = int(72 * SCALE_X)
CARD_HEIGHT= int(100 * SCALE_Y)

################################################################################
# 4. Load & Sort the actual card images
################################################################################

SUIT_ORDER = ["clubs","diamonds","hearts","spades"]
RANK_ORDER = ["2","3","4","5","6","7","8","9","10","jack","queen","king","ace"]

def parse_filename(fn):
    base= fn.lower().replace('.png','').replace('.svg','')
    parts= base.split('_')
    if len(parts)<5:
        return ("unknown","unknown")
    # e.g. "english","pattern","10","of","diamonds"
    rank= parts[2]
    suit= parts[4]
    return (suit, rank)

cards_folder= r"C:\Users\shmue\projects\python\open_pojects\poker\cards"  # set your path
all_files= [f for f in os.listdir(cards_folder) if f.lower().endswith(('.png','.svg'))]

card_entries=[]
for fn in all_files:
    path= os.path.join(cards_folder, fn)
    try:
        surf= pygame.image.load(path)
    except:
        print("Could not load", fn)
        continue
    suit,rank= parse_filename(fn)
    card_entries.append((fn, surf, suit, rank))

def card_sort_key(e):
    fn,surf,su,ra=e
    try: si= SUIT_ORDER.index(su)
    except: si=99
    try: ri= RANK_ORDER.index(ra)
    except: ri=99
    return (si,ri)

card_entries.sort(key=card_sort_key)


# Build a list of dict with scaled positions
sorted_cards=[]
for i,(fn,surf,su,ra) in enumerate(card_entries):
    si= SUIT_ORDER.index(su) if su in SUIT_ORDER else 99
    ri= RANK_ORDER.index(ra) if ra in RANK_ORDER else 99
    x= ri*(CARD_WIDTH+GAP)+ GAP
    y= si*(CARD_HEIGHT+ GAP)+ GAP + int(CARD_START_Y*SCALE_Y)
    sorted_cards.append({
        "filename":fn,
        "surface": surf,
        "suit": su,
        "rank": ra,
        "x": x,
        "y": y,
        "picked": False
    })

################################################################################
# 5. Data structures for placeholders
################################################################################
hero_place= [None,None]
comm_place= [None]*5

def card_eval_str(index):
    """Convert sorted_cards[index] => e.g. 'Ah','Td' for evaluation."""
    c= sorted_cards[index]
    su= c["suit"]
    ra= c["rank"]
    SUIT_MAP= {"clubs":"c","diamonds":"d","hearts":"h","spades":"s"}
    RANK_MAP= {"2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9",
               "10":"T","jack":"J","queen":"Q","king":"K","ace":"A"}
    if su not in SUIT_MAP or ra not in RANK_MAP:
        return "??"
    return RANK_MAP[ra]+ SUIT_MAP[su]

def get_hero_eval():
    out=[]
    for pl in hero_place:
        if pl is not None:
            out.append(card_eval_str(pl))
    return out

def get_comm_eval():
    out=[]
    for pl in comm_place:
        if pl is not None:
            out.append(card_eval_str(pl))
    return out

def current_probability():
    # need 2 hero
    hero2= get_hero_eval()
    if len(hero2)<2:
        return 0.0
    comm= get_comm_eval()
    opp= max(num_players-1,0)
    return hero_win_probability(hero2, comm, opp, 2000)

def reset_all():
    global hero_place, comm_place
    for c in sorted_cards:
        c["picked"]=False
    hero_place=[None,None]
    comm_place=[None]*5

prob=0.0

################################################################################
# 6. Main Loop
################################################################################
running=True
clock= pygame.time.Clock()

while running:
    clock.tick(30)
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.MOUSEBUTTONDOWN:
            mx,my= pygame.mouse.get_pos()
            # plus?
            if plusRect.collidepoint(mx,my):
                if num_players<10:
                    num_players+=1
                    prob= current_probability()
            elif minusRect.collidepoint(mx,my):
                if num_players>2:
                    num_players-=1
                    prob= current_probability()
            elif resetRect.collidepoint(mx,my):
                reset_all()
                prob=0.0
            else:
                # placeholders: hero
                for i,(sx,sy) in enumerate(hero_coords):
                    r= pygame.Rect(sx,sy, CARD_WIDTH, CARD_HEIGHT)
                    if r.collidepoint(mx,my):
                        # if there's a card, unpick
                        if hero_place[i] is not None:
                            idx= hero_place[i]
                            sorted_cards[idx]["picked"]=False
                            hero_place[i]=None
                            prob= current_probability()
                        break
                else:
                    # placeholders: community
                    for i,(sx,sy) in enumerate(comm_coords):
                        r= pygame.Rect(sx,sy, CARD_WIDTH, CARD_HEIGHT)
                        if r.collidepoint(mx,my):
                            if comm_place[i] is not None:
                                idx= comm_place[i]
                                sorted_cards[idx]["picked"]=False
                                comm_place[i]=None
                                prob= current_probability()
                            break
                    else:
                        # deck
                        needed_hero= hero_place.count(None)
                        needed_comm= comm_place.count(None)
                        if needed_hero>0 or needed_comm>0:
                            for i,c in enumerate(sorted_cards):
                                if c["picked"]:
                                    continue
                                rx,ry= c["x"], c["y"]
                                rr= pygame.Rect(rx, ry, CARD_WIDTH,CARD_HEIGHT)
                                if rr.collidepoint(mx,my):
                                    # pick
                                    c["picked"]= True
                                    placed=False
                                    # hero first
                                    for hh in range(2):
                                        if hero_place[hh] is None:
                                            hero_place[hh]= i
                                            placed=True
                                            break
                                    if not placed:
                                        for cc in range(5):
                                            if comm_place[cc] is None:
                                                comm_place[cc]= i
                                                break
                                    prob= current_probability()
                                    break

    # draw background or fill color
    if bg_image:
        screen.blit(bg_image,(0,0))
    else:
        screen.fill((0,120,0))

    # draw plus/minus/reset
    pygame.draw.rect(screen,(0,200,0), plusRect)
    txtp= font_20.render("+",True,(0,0,0))
    screen.blit(txtp, (plusRect.x+ plusRect.w//3, plusRect.y))

    pygame.draw.rect(screen,(200,0,0), minusRect)
    txtm= font_20.render("-",True,(0,0,0))
    screen.blit(txtm, (minusRect.x+ minusRect.w//3, minusRect.y))

    pygame.draw.rect(screen,(80,80,80), resetRect)
    txtr= font_20.render("Reset", True, (255,255,255))
    screen.blit(txtr, (resetRect.x+5, resetRect.y+5))

    # label
    txtn= font_20.render(f"Players: {num_players}", True, (255,255,255))
    screen.blit(txtn, (int(100*SCALE_X), int(10*SCALE_Y)))

    # draw placeholders hero
    for i,(sx,sy) in enumerate(hero_coords):
        pygame.draw.rect(screen, (255,255,255), (sx,sy,CARD_WIDTH,CARD_HEIGHT),2)
        idx= hero_place[i]
        if idx is not None:
            card_surf= sorted_cards[idx]["surface"]
            scaled= pygame.transform.scale(card_surf,(CARD_WIDTH,CARD_HEIGHT))
            screen.blit(scaled,(sx,sy))

    # placeholders community
    for i,(sx,sy) in enumerate(comm_coords):
        pygame.draw.rect(screen, (255,255,0), (sx,sy,CARD_WIDTH,CARD_HEIGHT),2)
        idx= comm_place[i]
        if idx is not None:
            card_surf= sorted_cards[idx]["surface"]
            scaled= pygame.transform.scale(card_surf,(CARD_WIDTH,CARD_HEIGHT))
            screen.blit(scaled,(sx,sy))

    # deck
    for i,c in enumerate(sorted_cards):
        if not c["picked"]:
            surf= c["surface"]
            sc= pygame.transform.scale(surf,(CARD_WIDTH,CARD_HEIGHT))
            screen.blit(sc, (c["x"], c["y"]))

    # Probability
    ptxt= font_30.render(f"Win%: {prob*100:.1f}%", True, (255,255,255))
    screen.blit(ptxt, (int(800*SCALE_X), int(10*SCALE_Y)))

    pygame.display.flip()

pygame.quit()
sys.exit(0)
