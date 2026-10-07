import os
from PIL import Image, ImageDraw, ImageFont

DEFAULT_SIZE=(1920,1080)
BACKGROUND=(245,247,250); SURFACE=(255,255,255); INK=(18,28,45); MUTED=(91,105,122)
ACCENT=(37,99,235); SUCCESS=(22,163,74); DANGER=(220,38,38); BORDER=(221,227,235); HIGHLIGHT=(219,234,254)
DEV="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf" if os.name!="nt" else "C:/Windows/Fonts/NirmalaUI.ttf"
DEV_B="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if os.name!="nt" else "C:/Windows/Fonts/Nirmala.ttf"
LAT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" if os.name!="nt" else "C:/Windows/Fonts/arial.ttf"
LAT_B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if os.name!="nt" else "C:/Windows/Fonts/arialbd.ttf"

def _dev(text): return any("\u0900"<=c<="\u097f" for c in text)

def _font(size,bold=False,dev=False):
    return ImageFont.truetype(DEV_B if dev and bold else DEV if dev else LAT_B if bold else LAT,size)

def _measure(draw,text,size,bold):
    words=text.split()
    return sum(draw.textlength(w,font=_font(size,bold,_dev(w))) for w in words)+max(0,len(words)-1)*draw.textlength(" ",font=_font(size,bold))

def _wrap(draw,text,size,bold,width):
    out=[]; line=""
    for word in text.strip().split():
        test=word if not line else line+" "+word
        if _measure(draw,test,size,bold)<=width: line=test
        else:
            if line: out.append(line)
            line=word
    if line: out.append(line)
    return out

def _lines(d,xy,text,size,bold,width,spacing=12,fill=INK):
    x,y=xy
    for line in _wrap(d,text,size,bold,width):
        cursor=x
        for word in line.split():
            f=_font(size,bold,_dev(word)); token=word+" "; d.text((cursor,y),token,font=f,fill=fill); cursor+=d.textlength(token,font=f)
        y+=size+spacing
    return y

def _card(d,box,outline=BORDER,width=2,radius=28):
    d.rounded_rectangle(box,radius,fill=SURFACE,outline=outline,width=width)

def draw_question_card(image,question,box,*,question_number=None,total_questions=None):
    d=ImageDraw.Draw(image); x1,y1,x2,_=box; _card(d,box)
    d.text((x1+42,y1+32),"QUESTION",font=_font(28,1),fill=ACCENT)
    if question_number is not None:
        label=f"Q{question_number}/{total_questions}" if total_questions is not None else f"Q{question_number}"; f=_font(30,1)
        d.text((x2-42-d.textlength(label,font=f),y1+34),label,font=f,fill=MUTED)
    _lines(d,(x1+42,y1+112),question,58,1,x2-x1-84,14)

def draw_choices(image,choices,box,*,selected_index=None,correct_index=None):
    d=ImageDraw.Draw(image); x1,y1,x2,y2=box; gap=18; row=(y2-y1-gap*(len(choices)-1))/max(len(choices),1); size=max(30,min(46,int(row*.32)))
    for i,choice in enumerate(choices):
        top=int(y1+i*(row+gap)); bottom=int(top+row); fill,outline=SURFACE,BORDER
        if i==correct_index: fill,outline=(236,253,245),SUCCESS
        elif i==selected_index: fill,outline=(254,242,242),DANGER
        d.rounded_rectangle((x1,top,x2,bottom),22,fill=fill,outline=outline,width=3 if outline!=BORDER else 2)
        d.rounded_rectangle((x1+22,top+18,x1+84,bottom-18),14,fill=HIGHLIGHT)
        d.text((x1+43,top+25),chr(65+i),font=_font(28,1),fill=ACCENT)
        _lines(d,(x1+112,top+16),str(choice),size,0,x2-x1-130,8)

def draw_timer(image,seconds,center,*,radius=72):
    d=ImageDraw.Draw(image); cx,cy=center; d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=SURFACE,outline=ACCENT,width=8)
    f=_font(44,1); label=f"{seconds}s"; b=d.textbbox((0,0),label,font=f); d.text((cx-(b[2]-b[0])/2,cy-(b[3]-b[1])/2-4),label,font=f,fill=INK)

def draw_answer_reveal(image,answer,box,*,correct=True):
    d=ImageDraw.Draw(image); x1,y1,x2,_=box; color=SUCCESS if correct else DANGER; _card(d,box,color,4)
    d.text((x1+42,y1+30),"ANSWER REVEAL",font=_font(28,1),fill=color)
    _lines(d,(x1+42,y1+100),str(answer),64,1,x2-x1-84,10)

def draw_calculation_step(image,steps,box,*,step_number=None):
    d=ImageDraw.Draw(image); x1,y1,x2,_=box; _card(d,box)
    d.text((x1+42,y1+30),"SOLUTION" if step_number is None else f"STEP {step_number}",font=_font(28,1),fill=ACCENT)
    y=y1+100
    for step in steps: y=_lines(d,(x1+42,y),str(step),46,0,x2-x1-84,8)+20

def draw_highlighted_text(image,segments,box,*,font_size=46):
    d=ImageDraw.Draw(image); x1,y1,x2,_=box; x,y=x1,y1
    for text,highlighted in segments:
        for word in str(text).split():
            token=word+" "; f=_font(font_size,0,_dev(word)); w=d.textlength(token,font=f)
            if x+w>x2 and x>x1: x,y=x1,y+font_size+16
            if highlighted: d.rounded_rectangle((x-5,y-2,x+w+3,y+font_size+6),8,fill=HIGHLIGHT)
            d.text((x,y),token,font=f,fill=INK); x+=w

def draw_flow_diagram(image,nodes,edges):
    d=ImageDraw.Draw(image)
    for a,b in edges:
        p,q=nodes[a][1],nodes[b][1]; d.line(((p[0]+p[2])/2,(p[1]+p[3])/2,(q[0]+q[2])/2,(q[1]+q[3])/2),fill=MUTED,width=5)
    for label,box in nodes:
        _card(d,box,ACCENT,3,20); _lines(d,(box[0]+16,box[1]+25),label,36,1,box[2]-box[0]-32,8)

def draw_progress(image,current,total,box):
    d=ImageDraw.Draw(image); x1,y1,x2,y2=box; r=(y2-y1)//2; d.rounded_rectangle(box,r,fill=BORDER)
    ratio=0 if total<=0 else max(0,min(1,current/total)); d.rounded_rectangle((x1,y1,x1+int((x2-x1)*ratio),y2),r,fill=ACCENT)
    d.text((x2+18,y1),f"{current}/{total}",font=_font(24,1),fill=MUTED)

def draw_score_result(image,score,total,box):
    d=ImageDraw.Draw(image); x1,y1,x2,y2=box; _card(d,box); d.text((x1+42,y1+32),"RESULT",font=_font(28,1),fill=ACCENT)
    f=_font(92,1); label=f"{score}/{total}"; b=d.textbbox((0,0),label,font=f); d.text((x1+(x2-x1-b[2])/2,y1+120),label,font=f,fill=INK)
    pct=0 if total<=0 else round(score/total*100); f=_font(40,1); label=f"{pct}%"; b=d.textbbox((0,0),label,font=f); d.text((x1+(x2-x1-b[2])/2,y2-90),label,font=f,fill=SUCCESS if pct>=50 else DANGER)
