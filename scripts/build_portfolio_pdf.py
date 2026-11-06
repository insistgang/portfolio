"""Typeset Leo's source-grounded portfolio. Run with reportlab and Pillow installed.
Design: A4 landscape, charcoal / warm paper / slate blue, Chinese editorial typography.
Source facts: index.html + CONTENT_NOTES.md. No invented metrics or publication claims.
"""
from pathlib import Path
from io import BytesIO
import json, re, html
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/pdf/刘钢_Leo_软件工程与研究作品集.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
(ROOT/'.tmp/pdf-preview').mkdir(parents=True,exist_ok=True)
DATA=json.JSONDecoder().raw_decode((ROOT/'index.html').read_text().split('const projects = ',1)[1])[0]
P={p['id']:p for p in DATA}
W,H=841.89,595.28
M=42
PAPER='#F3F0E8'; INK='#20282C'; MUTED='#667177'; BLUE='#52717E'; LINE='#D4D8D5'; DARK='#171D20'; LIGHT='#BACBD1'; WHITE='#FFFFFF'
for name,path,idx in [
 ('CJK','/System/Library/Fonts/Supplemental/Arial Unicode.ttf',0),
 ('Title','/System/Library/Fonts/Supplemental/Songti.ttc',1),
 ('Song','/System/Library/Fonts/Supplemental/Songti.ttc',6),
 ('Latin','/System/Library/Fonts/Avenir Next.ttc',7),
 ('Demi','/System/Library/Fonts/Avenir Next.ttc',2),
 ('Bold','/System/Library/Fonts/Avenir Next.ttc',0),
 ('Mono','/System/Library/Fonts/Menlo.ttc',0)]:
 pdfmetrics.registerFont(TTFont(name,path,subfontIndex=idx))
pdfmetrics.registerFontFamily('CJK',normal='CJK',bold='CJK',italic='CJK',boldItalic='CJK')
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('刘钢 Leo | 软件工程与研究作品集')
c.setAuthor('刘钢 Leo')
c.setSubject('精选项目、研究工作、产业实践、竞赛与软件目录')
c.setCreator('Leo Portfolio | ReportLab')
c.setViewerPreference('DisplayDocTitle','true')
num=0
checks=[]

def rect(x,y,w,h,color,stroke=None):
 c.setFillColor(HexColor(color))
 if stroke:c.setStrokeColor(HexColor(stroke))
 c.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))
def line(x1,y1,x2,y2,color=LINE,width=.6):
 c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x1,H-y1,x2,H-y2)
def txt(s,x,y,size=11,color=INK,font='CJK'):
 c.setFillColor(HexColor(color));c.setFont(font,size);c.drawString(x,H-y-size,s)
 # all text uses top coordinates; keep within the page safety zone.
 tw=pdfmetrics.stringWidth(s,font,size)
 checks.append({'page':num,'text':s,'x':round(x,2),'top':round(y,2),'right':round(x+tw,2),'bottom':round(y+size,2)})
 return tw
def para(s,x,y,w,size=11,leading=None,color=INK,font='CJK',max_h=None):
 style=ParagraphStyle('body',fontName=font,fontSize=size,leading=leading or size*1.65,textColor=HexColor(color),wordWrap='CJK',splitLongWords=True)
 p=Paragraph(html.escape(s).replace('\n','<br/>'),style)
 aw,ah=p.wrap(w,1000)
 if max_h is not None and ah>max_h+.1:raise ValueError(f'Page {num} paragraph overflow: {ah}>{max_h}: {s}')
 if y+ah>H-32:raise ValueError(f'Page {num} paragraph outside safe area: {s}')
 p.drawOn(c,x,H-y-ah)
 checks.append({'page':num,'text':s,'x':x,'top':y,'right':x+w,'bottom':round(y+ah,2)})
 return ah
def eyebrow(s,x=M,y=73,dark=False):txt(s,x,y,9,LIGHT if dark else BLUE,'Demi')
def heading(s,sub=None,dark=False,size=30):
 txt(s,M,92,size,PAPER if dark else INK,'Title')
 if sub:para(sub,M,138,W-2*M,10.5,16,LIGHT if dark else MUTED,max_h=34)
def img(path,x,y,w,h,background=None,fit='contain'):
 if background:rect(x,y,w,h,background)
 im=Image.open(ROOT/path).convert('RGB')
 if fit=='cover':
  ratio=max(w/im.width,h/im.height); sw,sh=w/ratio,h/ratio
  left=(im.width-sw)/2;top=(im.height-sh)/2
  im=im.crop((left,top,left+sw,top+sh))
 ratio=min(w/im.width,h/im.height)
 dw,dh=im.width*ratio,im.height*ratio
 im.thumbnail((2200,1600),Image.Resampling.LANCZOS)
 b=BytesIO();im.save(b,format='JPEG',quality=94,subsampling=0)
 c.drawImage(ImageReader(b),x+(w-dw)/2,H-y-(h-dh)/2-dh,dw,dh)
 return (x+(w-dw)/2,y+(h-dh)/2,dw,dh)
def logo(x,y,size=26):
 # Preserve exact geometry and colors from assets/brand/leo-mark.svg as vector paths.
 c.saveState();c.translate(x,H-y-size);c.scale(size/64,size/64)
 c.setFillColor(HexColor('#eeeae0'));c.roundRect(0,0,64,64,12,fill=1,stroke=0)
 for points,color in [([(16,12),(28,12),(28,40),(48,40),(48,52),(16,52)],'#141719'), ([(44,12),(56,12),(44,32),(32,32)],'#5d747d')]:
  p=c.beginPath();p.moveTo(points[0][0],64-points[0][1])
  for a,b in points[1:]:p.lineTo(a,64-b)
  p.close();c.setFillColor(HexColor(color));c.drawPath(p,fill=1,stroke=0)
 c.restoreState()
def page(section,title,dark=False,key=None):
 global num
 num+=1
 rect(0,0,W,H,DARK if dark else PAPER)
 color=LIGHT if dark else MUTED
 logo(M,28,20)
 txt('LEO / SELECTED WORK',M+30,32,8.5,color,'Demi')
 tw=pdfmetrics.stringWidth(section,'Demi',8)
 txt(section,W-M-tw,32,8,color,'Demi')
 line(M,60,W-M,60,'#3C474C' if dark else LINE)
 line(M,H-38,W-M,H-38,'#3C474C' if dark else LINE)
 txt('刘钢  /  软件工程与研究',M,H-29,8,color)
 txt('PORTFOLIO 2026',W/2-44,H-28,8,color,'Latin')
 txt(f'{num:02d} / 20',W-M-36,H-28,8,color,'Mono')
 c.bookmarkPage(key or f'p{num}')
 c.addOutlineEntry(title,key or f'p{num}',0,False)
def end():c.showPage()
def label_body(label,body,x,y,w,dark=False):
 txt(label,x,y,12,PAPER if dark else INK,'Title')
 ah=para(body,x,y+23,w,10.5,17,LIGHT if dark else MUTED)
 return 25+ah
def link(label,url,x,y,size=9,color=BLUE,w=None):
 tw=txt(label,x,y,size,color,'Latin')
 c.linkURL(url,(x,H-y-size-4,x+(w or tw),H-y+2),relative=0,thickness=0)
 line(x,y+size+3,x+tw,y+size+3,color,.4)
def tags(items,x,y,w,dark=False,size=9):
 cur=x;top=y
 for s in items:
  tw=pdfmetrics.stringWidth(s,'CJK',size)+14
  if cur+tw>x+w:cur=x;top+=23
  rect(cur,top,tw,18,'#273237' if dark else '#E5E8E3')
  txt(s,cur+7,top+3,size,LIGHT if dark else BLUE)
  cur+=tw+5
 return top-y+18
def flow(items,x,y,w,dark=False):
 gap=15;bw=(w-gap*(len(items)-1))/len(items)
 for i,(a,b) in enumerate(items):
  xx=x+i*(bw+gap)
  line(xx,y,xx+bw,y,LIGHT if dark else BLUE,1.2)
  txt(f'{i+1:02}',xx,y+12,9,LIGHT if dark else BLUE,'Mono')
  txt(a,xx,y+31,12,PAPER if dark else INK,'Title')
  para(b,xx,y+54,bw,9.3,15,LIGHT if dark else MUTED,max_h=45)
  if i<len(items)-1:
   line(xx+bw+3,y+40,xx+bw+12,y+40,LIGHT if dark else BLUE,.7)
   line(xx+bw+9,y+37,xx+bw+12,y+40,LIGHT if dark else BLUE,.7)
   line(xx+bw+9,y+43,xx+bw+12,y+40,LIGHT if dark else BLUE,.7)
def note(s,y=532,dark=False):para(s,M,y,W-2*M,8.5,12,LIGHT if dark else MUTED,max_h=23)

# 01 | Cover. Real device photo, deliberate wide whitespace and compact identity.
page('SOFTWARE ENGINEERING & RESEARCH','封面',True,'cover')
eyebrow('LIU GANG / SHANGHAI',y=88,dark=True)
txt('从算法',M,125,42,PAPER,'Title')
txt('到可用的系统',M,182,42,PAPER,'Title')
para('软件工程与研究作品集',M,257,350,17,25,PAPER)
line(M,306,122,306,LIGHT,2)
txt('刘钢',M,331,25,PAPER,'Title');txt('Leo',108,332,26,LIGHT,'Latin')
para('计算机视觉  /  边缘智能  /  全栈工具',M,377,355,11,18,LIGHT)
para('上海工程技术大学 · 硕士在读',M,405,350,11,18,LIGHT)
link('insistgang.top/portfolio','https://insistgang.top/portfolio/',M,479,10,LIGHT)
img('assets/images/soft/submitted-11.png',421,100,379,337,fit='cover')
rect(421,437,379,60,'#252F34')
txt('边缘视觉设备 · 联调现场',437,450,11,PAPER)
txt('EDGE VISION / FIELD WORK',437,474,8,LIGHT,'Demi')
end()

# 02 | Profile + interactive contents.
page('PROFILE & CONTENTS','个人简介与阅读导航',key='contents')
eyebrow('01 / OVERVIEW')
heading('把问题做成可以使用的工具')
para('我关注软件与真实场景之间的连接：从图像检测和端侧部署，到产品交互与日常自动化。开发中的实践与复盘，也会整理在个人博客中。',M,155,326,12,20,max_h=85)
for i,(big,lbl) in enumerate([('21','软件与工具'),('10','竞赛记录'),('03','研究工作'),('04','产业实践')]):
 xx=M+(i%2)*173;yy=265+(i//2)*94
 txt(big,xx,yy,34,INK,'Latin');txt(lbl,xx,yy+47,10,MUTED)
para('共收录 38 条展示记录。\n同一项目可能跨类别展示，条目数不等于独立项目数。',M,466,334,9.5,16,MUTED)
line(410,158,410,516)
items=[('01','精选项目','边缘视觉、无障碍应用与 AI 工具',3,'edge'),('02','个人工具','研究、求职与日常工作流',10,'workflows'),('03','研究工作','多尺度检测、遥感变化检测与跨学科研究',12,'research'),('04','产业实践','后端服务、算法交付与软硬件协作',15,'industry'),('05','竞赛与作品目录','奖项证书与精选软件作品目录',16,'honors')]
for i,(a,b,d,pn,k) in enumerate(items):
 yy=157+i*71
 txt(a,445,yy,10,BLUE,'Mono');txt(b,481,yy-3,17,INK,'Title')
 txt(f'{pn:02d}',768,yy-1,12,BLUE,'Mono')
 para(d,481,yy+24,284,9.5,15,MUTED,max_h=30)
 line(445,yy+59,800,yy+59)
 c.linkRect('',k,(445,H-yy-56,800,H-yy+5),relative=0,thickness=0)
end()

# 03 | EdgeSafe.
page('SELECTED WORK / 01','边缘视觉设备',key='edge')
eyebrow('EDGE AI / SYSTEM INTEGRATION')
heading('边缘视觉设备', '工业预警与辅助通行感知 · 同一硬件平台，两类应用场景')
img('assets/images/soft/submitted-11.png',M,188,443,303,fit='contain',background='#E3E4DF')
para('Jetson 边缘设备与外设联调现场实拍',M,502,440,9,14,MUTED)
x=510
label_body('我的角色','软件设计与开发，参与算法与系统实现。',x,188,286)
label_body('工程路径','在边缘端处理视频，结合 ROI 区域过滤、事件去抖与声光告警，并汇总事件信息。',x,274,286)
tags(['Python','OpenCV','ONNX Runtime','Jetson'],x,366,288)
line(x,420,800,420)
para('2026 西门子杯 · 全国初赛华东一赛区二等奖\n2026 研电赛 · 上海分赛区团队二等奖',x,437,288,10,18,BLUE)
note('关联：comp-02、comp-10、prod-19。辅助通行项目与工业预警项目共用边缘硬件平台，分别参赛。')
end()

# 04 | LinkAble, maintain portrait screenshots without cropping.
page('SELECTED WORK / 02','共感 LinkAble',key='linkable')
eyebrow('ACCESSIBLE DESIGN / MOBILE PROTOTYPE')
heading('共感 LinkAble','无障碍互助应用原型 · 2026 两岸大学生创客大赛逢甲赛区交流展示')
label_body('从需求到交互','将 AI 多模态助手、志愿者协助与 SOS 演练组织在同一交互流程中。',M,191,265)
label_body('我的角色','项目负责人，负责产品方案与无障碍交互原型。',M,300,265)
tags(['Flutter','Dart','Riverpod','交互原型'],M,387,270)
para('逢甲赛区交流展示 · 未获奖\n匹配与 SOS 为本地演示流程',M,436,270,10,17,BLUE)
link('insistgang.top/LinkLab','https://insistgang.top/LinkLab/',M,494,8.7)
for i,path in enumerate(['assets/images/soft/submitted-10.png','assets/images/linklab_img2.jpg','assets/images/linklab_img3.jpg']):
 xx=337+i*157
 img(path,xx,184,145,303,background='#E6E7DF')
 txt(['双角色入口','互助完成反馈','无障碍偏好'][i],xx+10,499,9,MUTED)
note('本页为互助 App 原型，非研电赛获奖边缘设备；不代表真实志愿者网络或救援服务。')
end()

# 05 | Ops hub.
page('SELECTED WORK / 03','Ops-Hub 运维工作总台',key='ops')
eyebrow('OPS-HUB / PERSONAL OPERATIONS')
heading('把多端设备放进一个工作总台','设备状态、任务分流建议和工程进度，在同一处查看')
img('assets/images/opshub-cover.png',M,184,477,248,background='#182232')
label_body('问题','设备与任务分散时，重复检查状态会打断工作。',545,186,250)
label_body('实现','通过 Python CLI、设备探针、静态看板与定时同步，整理连通性、任务建议和交付风险。',545,268,250)
label_body('职责','独立设计与全栈开发。',545,380,250)
flow([('探测','采集设备状态与连通性'),('建议','按任务需要提供执行端建议'),('跟踪','汇总工程进度与交付提示')],M,444,477)
tags(['Python CLI','HTML5','launchd'],545,444,250)
link('github.com/insistgang/ops-hub','https://github.com/insistgang/ops-hub',545,503,8.3)
note('prod-01 · 看板与状态为材料示例，不据截图推断设备当前运行情况。')
end()

# 06 | Quota dark feature.
page('SELECTED WORK / 04','AI-QuotaMonitor',True,'quota')
eyebrow('AI-QUOTAMONITOR / RESOURCE VISIBILITY',dark=True)
heading('让模型使用状态一目了然','将多来源额度、消耗趋势与阈值预警汇总到统一界面',True)
img('assets/images/soft/submitted-12.png',M,185,473,299,background='#0D1116')
label_body('采集','整理不同模型服务的额度与消耗状态。',546,191,249,True)
label_body('分析','展示历史趋势和阈值预警，辅助安排模型使用计划。',546,277,249,True)
label_body('维护','通过定时守护、数据整理与自动化发布更新展示。',546,375,249,True)
tags(['Python','HTML5','CSS Grid','launchd'],M,498,470,True)
link('github.com/insistgang/ai-quota-monitor','https://github.com/insistgang/ai-quota-monitor',546,486,8.1,LIGHT)
note('prod-02 · 界面来自项目存档，截图中的数值为示例，不作为性能或当前额度的证明。',dark=True)
end()

# 07 | knowledge base.
page('SELECTED WORK / 05','AI 技术知识库',key='knowledge')
eyebrow('KNOWLEDGE WORKFLOW / MCP')
heading('让资料处理有步骤，也有复核','技术资料采集、结构化分析、质量检查与知识归档')
img('assets/images/soft/submitted-13.png',M,185,476,245,background=WHITE)
label_body('系统设计','将资料处理组织为可追踪的工作流，在质量检查后引入人工复核，再完成知识归档。',546,187,249)
label_body('使用方式','记录处理结果，通过 MCP 接口查询已有知识，减少重复整理。',546,310,249)
tags(['Python','MCP','知识管理'],546,406,249)
link('github.com/insistgang/ai-knowledge-base','https://github.com/insistgang/ai-knowledge-base',546,481,7.9)
flow([('采集','收集与整理技术资料'),('检查','结构化分析与质量检查'),('复核','人工复核后归档')],M,444,477)
note('prod-03 · 项目界面示例；图中数值不作为性能评测结果。')
end()

# 08 | Search and security, three compact editorial columns.
page('SELECTED WORK / 06','检索与分析应用')
eyebrow('SEARCH & ANALYSIS')
heading('把非结构化内容变成可检索信息','视频画面检索、安全告警分析与语文智能助学')
cols=[(P['prod-20']['image'],'画面检索','结合 FFmpeg 抽帧、视觉描述与 SQLite FTS5 全文检索定位视频画面内容。',['FastAPI','React','SQLite FTS5']),(P['comp-05']['gallery'][1],'威胁分析','通过本地 Streamlit 工作区组织多源安全告警协同研判与情报检索。',['Streamlit','FastAPI','ChromaDB']),(P['comp-04']['gallery'][1],'智能助学','面向体育生语文基础薄弱点，构建词汇成语专项训练与学情追踪小程序。',['Taro 3.6','React 18','微信云开发'])]
cw=236
for i,(img_path,title,desc,tech) in enumerate(cols):
 xx=M+i*260
 img(img_path,xx,192,cw,161,background=WHITE)
 txt(f'0{i+1}',xx,372,11,BLUE,'Mono');txt(title,xx+33,365,20,INK,'Title')
 para(desc,xx,405,cw,10.5,18,MUTED,max_h=77)
 tags(tech,xx,487,cw,size=8.1)
note('均提供公开静态演示与 GitHub 代码仓库。完整模型配置与部署条件以相应工程说明为准。')
end()

# 09 | App visual gallery.
page('SELECTED WORK / 07','更多软件实践')
eyebrow('SOFTWARE EXPLORATIONS')
heading('面向不同任务的应用实践','从业务数据管理到教育与专注训练，保留每个应用的具体使用场景')
apps=[(P['prod-16']['image'],'食安崇明','家宴备案与公众共治原型'),(P['prod-18']['image'],'慧停管家','车位矩阵与业主排位演示'),(P['comp-04']['gallery'][1],'语文智能助学','专项练习与学情追踪'),(P['prod-20']['image'],'视频画面检索','画面检索静态示例'),(P['comp-05']['gallery'][1],'安全威胁研判','本地告警分析工作区'),(P['prod-22']['image'],'专注力训练','舒尔特方格、N-Back 与 Stroop')]
for i,(img_path,title,desc) in enumerate(apps):
 xx=M+(i%3)*260;yy=184+(i//3)*175
 img(img_path,xx,yy,236,113,background='#E6E7E2')
 txt(title,xx,yy+121,14,INK,'Title')
 txt(desc,xx,yy+144,9.2,MUTED)
note('工程存档实图 · 示例数值不作为评测结果。')
end()

# 10 | Two workflows.
page('PERSONAL TOOLS / 01','求职与科研工作流',key='workflows')
eyebrow('WORKFLOWS / FROM EVIDENCE TO DECISIONS')
heading('将重复工作整理成清晰的流程','Career-Copilot 与 PaperStudio · 本地使用的个人工具')
for i,(name,cn,desc,steps,tech) in enumerate([
 ('Career-Copilot','求职与简历工作流','连接个人经历主库与岗位需求，组织项目证据、定制简历，并跟踪投递进展。',[('经历证据','用主张与证据账本约束描述'),('岗位匹配','组织需求与经历的对应关系'),('简历与跟踪','生成 PDF / HTML 并记录进展')],['Python','Typst','HTML','MCP']),
 ('PaperStudio','论文投前诊断工作流','将研究问题、方法与证据组织成可检查的档案，形成改稿计划与期刊匹配判断。',[('A / 解剖','梳理问题、方法与证据'),('B / 压力测试','识别论证与验证中的缺口'),('C / 判决','形成改稿计划与投稿前检查')],['Markdown','Shell','结构化模板'])]):
 xx=M+i*392
 txt(name,xx,190,24,INK,'Demi');txt(cn,xx,229,15,BLUE,'Title')
 para(desc,xx,265,359,11,18,MUTED,max_h=60)
 for j,(a,b) in enumerate(steps):
  yy=341+j*48
  txt(f'{j+1:02}',xx,yy,9,BLUE,'Mono');txt(a,xx+29,yy-3,11,INK,'Title')
  txt(b,xx+29,yy+17,9.1,MUTED)
 tags(tech,xx,493,359,size=8.6)
line(420,187,420,518)
note('功能流程整理自公开项目简介；不包含私有经历库、投递信息或稿件正文。')
end()

# 11 | smaller personal tools.
page('PERSONAL TOOLS / 02','日常工具')
eyebrow('SMALL TOOLS / DAILY PRACTICE')
heading('把日常需求做成自己的小工具')
# Gema image hero column.
img('assets/images/prod_gema_studio.png',M,170,345,237,background='#ECEAE4')
txt('GeMa-Studio / 格码工坊',M,424,19,INK,'Title')
para('浏览器端创意交互组件与图形生成套件，包含二维码、转盘、签诗和印章等工具。',M,460,345,11,18,MUTED,max_h=60)
x=433
label_body('得到大脑日记工作流','通过 MCP 接口连接笔记读取与本地归档，按 note_id 去重，整理日记时间线与复盘素材。',x,173,363)
tags(['Python','MCP Server','Markdown'],x,262,363)
line(x,311,800,311)
label_body('Weight-Tracker','面向小组协作的轻量健康打卡工具，展示每日记录、变化趋势与阶段进度，适配手机查看。',x,336,363)
tags(['Vue 3','Tailwind CSS','JSON'],x,429,363)
note('私人使用范畴，不提供公开代码仓库。')
note('个人工具共 8 项：另含前述 Ops-Hub、AI-QuotaMonitor、AI 技术知识库、Career-Copilot 与 PaperStudio。')
end()

# 12 | Thesis.
page('RESEARCH / 01','多尺度图像检测研究',key='research')
eyebrow('MASTER’S RESEARCH / COMPUTER VISION')
heading('多尺度图像中的建筑识别','硕士论文主线：面向违法建筑识别的多尺度图像检测方法研究')
img('assets/images/res_weijian_vis.png',M,186,470,295,background=WHITE)
txt('研究场景图 · 空地多源图像中的建筑目标',M,495,9,MUTED)
x=540
label_body('研究问题','复杂背景与不同尺度的建筑目标，给特征表达、目标检测和数据评估带来挑战。',x,188,258)
label_body('研究方法','研究多尺度特征融合与目标检测，开展数据标注复核和独立测试集评估。',x,297,258)
tags(['PyTorch','YOLOv11','遥感图像处理'],x,405,258)
para('独立完成人 · 硕士学位论文\n状态：研究进行中',x,474,258,10,17,BLUE)
note('res-01 · 研究状态依据现有作品集内容。')
end()

# 13 | Change detection, research figure entire.
page('RESEARCH / 02','MS-LightCD 轻量变化检测',True,'mslightcd')
eyebrow('MS-LIGHTCD / BI-TEMPORAL CHANGE DETECTION',dark=True)
heading('在双时相影像中识别变化','面向高分辨率遥感图像的轻量级变化检测网络',True)
img('assets/images/res_ms_lightcd_diff.png',M,185,450,306,background=WHITE)
para('论文工作中的可视化示例 · 完整图面保留',M,504,450,9,14,LIGHT)
x=523
label_body('研究方向','围绕双时相遥感影像，探索多尺度特征表达、特征融合与轻量化网络设计。',x,188,273,True)
label_body('实验工作','整理对比实验、消融结果与端侧模型推理评估，关注检测能力与部署开销。',x,297,273,True)
tags(['Siamese Network','轻量化注意力','遥感影像'],x,404,273,True)
para('学生第一作者\n状态：论文与实验整理',x,475,273,10,17,LIGHT)
note('res-02 · 当前以论文与实验工作收录，不据此表述为已录用或已发表。',dark=True)
end()

# 14 | Research duo.
page('RESEARCH / 03','跨学科研究')
eyebrow('RESEARCH COLLABORATIONS')
heading('将研究方法带到不同场景')
research=[('res-04','网络文化空间与集体行动','将文本处理与数据分析用于网络文化社群研究，参与研究材料组织、图示整理与稿件修订。','数据分析与稿件协作 · 合作研究','assets/images/res_mcssci_governance.jpg')]
for i,(pid,title,desc,status,path) in enumerate(research):
 xx=M+i*392
 img(path,xx,169,359,215,background=WHITE)
 txt(title,xx,399,18,INK,'Title')
 para(desc,xx,436,359,10.5,18,MUTED,max_h=60)
 txt(status,xx,507,9.3,BLUE)
end()

# 15 | Industry, no unsafe unrelated source thumbnails.
page('INDUSTRY / ENGINEERING PRACTICE','产业实践',key='industry')
eyebrow('ENGINEERING IN CONTEXT')
heading('在协作中完成工程交付','从业务需求、服务开发到算法交接与设备联调')
industry=[('01','上海卓繁信息技术股份有限公司','后端开发 / AI 算法落地实习生','参与智慧政务与教育场景的后端研发、系统联调和业务演示，推进排课、停车管理及 AI 应用相关需求。',['Java','Spring Boot','Python','MySQL']),('02','中国电子科技集团第 50 研究所','算法开发与技术交付','参与高校与研究所合作的图像检测项目，整理算法代码、工程测试与结项材料，完成技术交接。',['目标检测','遥感工程化','Linux']),('03','具身智能硬件与小智机器人','全栈与算法协作','围绕设备控制与语音交互参与代码集成、运行环境配置、软硬件联调，以及部署与交付材料整理。',['Python','嵌入式通信','多模态交互']),('04','电商中台与供应链管理','全栈架构与开发负责人','围绕商品数据、订单处理与对账业务，组织数据管道、异步重试和网络超时处理。',['Node.js','MySQL','Redis','Vue'])]
for i,(n,title,role,desc,tech) in enumerate(industry):
 xx=M+(i%2)*392;yy=188+(i//2)*174
 txt(n,xx,yy,11,BLUE,'Mono');txt(title,xx+32,yy-3,15,INK,'Title')
 txt(role,xx+32,yy+24,9.2,BLUE)
 para(desc,xx+32,yy+48,326,10.5,17,MUTED,max_h=56)
 tags(tech,xx+32,yy+113,326,size=8)
 line(xx,yy+149,xx+359,yy+149)
end()

# 16 | Three original certificate highlights.
page('HONORS / VERIFIED RECORDS','竞赛荣誉与证书',key='honors')
eyebrow('COMPETITION / 2025-2026')
heading('以作品参赛，以证书留存','选录学生证书与团队证书，保留年度、赛区和奖项级别')
honors=[('comp-09','2025 西门子杯','华北二赛区一等奖','全国初赛 · 信息化网络化方向'),('comp-02','2026 西门子杯','华东一赛区二等奖','全国初赛 · 自由探索方向'),('comp-10','2026 研电赛','上海分赛区团队二等奖','边缘智能辅助通行感知系统')]
for i,(pid,title,award,desc) in enumerate(honors):
 xx=M+i*260
 img(P[pid]['image'],xx,188,236,246,background=WHITE)
 txt(title,xx,449,16,INK,'Title')
 txt(award,xx,480,11,BLUE)
 para(desc,xx,506,236,9,14,MUTED,max_h=28)
end()

# 17 | all 10 competition records, precise scoped awards.
page('HONORS / COMPLETE INDEX','竞赛记录索引')
eyebrow('10 RECORDS / COMPETITION INDEX')
heading('竞赛记录一览','同一硬件用于不同赛项时分别记录；赛区奖项保留完整范围')
awards=[('2025','西门子杯 · 第十九届','全国初赛华北二赛区一等奖'),('2026','西门子杯 · 第二十届','全国初赛华东一赛区二等奖'),('2025','中国研究生电子设计竞赛 · 第二十届','上海分赛区团队三等奖'),('2026','中国研究生电子设计竞赛 · 第二十一届','上海分赛区团队二等奖'),('第22届','华为杯 · 中国研究生数学建模竞赛','全国二等奖'),('第7届','华为杯 · 中国研究生人工智能创新大赛','全国三等奖'),('第4届','华为杯 · 中国研究生网络安全创新大赛','全国三等奖'),('创芯','中国研究生 EDA 精英挑战赛','全国三等奖'),('第7届','上海市研究生智慧城市创意设计大赛','三等奖（同时为第 5 届长三角赛事）'),('第3届','上海市大学生行业分析大赛','高教组银奖')]
for i,(date,title,award) in enumerate(awards):
 yy=185+i*33
 txt(date,M,yy+1,9,BLUE,'CJK' if not date.isdigit() else 'Mono')
 txt(title,105,yy,11,INK)
 txt(award,545,yy+1,9.3,BLUE)
 line(M,yy+25,800,yy+25)
note('证书图片已收录于在线作品集。')
end()

# 18 & 19 | Selected software & tool catalog, full exact titles, links.
catalog_ids=['prod-01','prod-02','prod-03','prod-07','prod-08','prod-09','prod-11','prod-12','prod-14','prod-16','prod-17','prod-18','prod-19','prod-20']
for chunk in range(2):
 page('SOFTWARE / SELECTED CATALOG',f'软件与工具目录 {chunk+1}',key=f'catalog{chunk+1}')
 eyebrow(f'14 SELECTED PRODUCTS / PART {chunk+1} OF 2')
 heading('软件与工具目录', '涵盖个人数字化工作台、科研/求职工作流与公开在线应用')
 for j in range(7):
  i=chunk*7+j+1;p=P[catalog_ids[i-1]];yy=184+j*46.8
  txt(f'{i:02}',M,yy,12,BLUE,'Mono')
  title=p['title']
  txt(title,79,yy-1,11.3,INK,'CJK')
  para(p['subtitle'],79,yy+20,415,8.9,12,MUTED,max_h=16)
  ts=' / '.join(p['tech'][:3])
  para(ts,512,yy+20,286,8,12,BLUE,max_h=16)
  line(79,yy+39,800,yy+39)
  href=p.get('url') or (p.get('links') and p['links'][0]['href'])
  if href and href.startswith('http'):c.linkURL(href,(79,H-yy-15,799,H-yy+3),relative=0,thickness=0)
 note('图文来源：在线作品集。各项目的演示范围与运行条件见对应详情说明。')
 end()

# 20 | End card with live links and vector QR.
page('CONTACT / CONTINUE THE CONVERSATION','联系与在线作品集',True,'contact')
eyebrow('LET’S BUILD SOMETHING USEFUL',y=98,dark=True)
txt('让想法成为',M,151,42,PAPER,'Title')
txt('可以使用的作品。',M,212,42,PAPER,'Title')
para('感谢阅读。更多项目细节、公开代码与技术复盘，\n欢迎继续访问在线作品集与个人博客。',M,293,430,12,21,LIGHT)
link('insistgang@163.com','mailto:insistgang@163.com',M,392,14,PAPER)
link('insistgang.top/portfolio','https://insistgang.top/portfolio/',M,436,11,LIGHT)
link('github.com/insistgang','https://github.com/insistgang',M,466,11,LIGHT)
link('insistgang.top  /  Leo’s notebook','https://insistgang.top/',M,496,10,LIGHT)
rect(605,184,170,170,PAPER)
q=qr.QrCodeWidget('https://insistgang.top/portfolio/',barLevel='M')
bounds=q.getBounds();qw=bounds[2]-bounds[0];qh=bounds[3]-bounds[1]
d=Drawing(144,144,transform=[144/qw,0,0,144/qh,0,0]);d.add(q)
renderPDF.draw(d,c,618,H-197-144)
txt('扫描查看在线作品集',613,372,10,LIGHT)
txt('刘钢 / Leo',605,455,23,PAPER,'Title')
end()
assert num==20,num
c.save()
(ROOT/'.tmp/pdf-preview/layout-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(OUT)
print(f'{num} pages; {OUT.stat().st_size/1024/1024:.2f} MiB')
