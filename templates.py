

# templates.py 

import os
import re
import uuid
import tempfile
import shutil
import language_tool_python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont



#   SHARED FONT REGISTER


FONTS_DIR = r"C:\Windows\Fonts"

FONT_MAP = {
    "Arial": "arial.ttf",
    "Arial-Bold": "arialbd.ttf",
    "Calibri": "calibri.ttf",
    "Calibri-Bold": "calibrib.ttf",
    "Times-Roman": "times.ttf",
    "Times-Bold": "timesbd.ttf",
    "Cambria": "cambria.ttf",
    "Cambria-Bold": "cambriab.ttf",
    "Garamond": "garamond.ttf",
    "Garamond-Bold": "garamond-bold.ttf",
    "Georgia": "georgia.ttf",
    "Georgia-Bold": "georgiab.ttf",
    "Tahoma": "tahoma.ttf",
    "Tahoma-Bold": "tahomabd.ttf",
    "Verdana": "verdana.ttf",
    "Verdana-Bold": "verdanab.ttf",
    "TrebuchetMS": "trebuc.ttf",
    "TrebuchetMS-Bold": "trebucbd.ttf",
    "Helvetica": "arial.ttf",
    "Helvetica-Bold": "arialbd.ttf",
}


def register_all_fonts():
    for font_name, file_name in FONT_MAP.items():
        fpath = os.path.join(FONTS_DIR, file_name)
        if not os.path.exists(fpath):
            continue
        try:
            pdfmetrics.registerFont(TTFont(font_name, fpath))
        except:
            pass


register_all_fonts()



#   SHARED VALIDATION


EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

def is_valid_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email or "") is not None


def is_valid_phone(phone: str) -> bool:
    phone = (phone or "").strip()
    if not re.match(r'^\+?[\d\s-]+$', phone):
        return False
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15


#   SHARED TEXT WRAPPER


def wrap_text_dynamic(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    lines = []
    for paragraph in (text or "").split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split(" ")
        line = ""
        for word in words:
            test_line = (line + " " + word).strip()
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                line = test_line
            else:
                if c.stringWidth(word, font_name, font_size) > max_width:
                    sub = ""
                    for ch in word:
                        if c.stringWidth(sub + ch, font_name, font_size) <= max_width:
                            sub += ch
                        else:
                            if sub:
                                lines.append(sub)
                            sub = ch
                    if sub:
                        line = sub
                    else:
                        line = ""
                else:
                    if line:
                        lines.append(line)
                    line = word
        if line:
            lines.append(line)
    return lines

#   SHARED AUTO-CORRECTION


tool = language_tool_python.LanguageTool('en-US')

def auto_correct_text(text: str, skip_fields=()):
    if not text:
        return text
    if text in skip_fields:
        return text
    try:
        corrected = language_tool_python.utils.correct(text, tool.check(text))
        corrected = re.sub(
            r'([^\w\s]\s*)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            corrected
        )
        return corrected
    except:
        return text



#   TEMPLATE 1  (Classic Black)


def template1_draw_resume(c, style, data):

    width, height = A4
    margin = 40
    sidebar_width = width * style["sidebar_width"]
    bottom_margin = 0

    printed_sidebar_headers = set()
    printed_main_headers = set()

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_name = "Helvetica"
    if font_bold not in pdfmetrics.getRegisteredFontNames():
        font_bold = "Helvetica-Bold"

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    def start_new_page():
        c.showPage()
        c.setFillColor(style["sidebar_bg"])
        c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)
        return height - margin

    def draw_content(y_position, sidebar_data, main_data,
                     start_sidebar_idx=0, start_main_idx=0,
                     start_sidebar_line=0, start_main_line=0):

        sx = margin / 2
        mx = sidebar_width + margin
        sidebar_y = y_position
        main_y = y_position

        sidebar_idx = start_sidebar_idx
        main_idx = start_main_idx
        sidebar_line = start_sidebar_line
        main_line = start_main_line

        sidebar_lines = {}
        main_lines = {}

        for i, section in enumerate(sidebar_data):
            key = section["content"]
            if data.get(key):
                sidebar_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    sidebar_width - sx - 10
                )

        for i, section in enumerate(main_data):
            key = section["content"]
            if data.get(key):
                main_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    width - sidebar_width - 2 * margin
                )

        if start_sidebar_idx == 0 and start_main_idx == 0:
            c.setFont(font_bold, title_size)
            c.setFillColor(style["primary"])
            c.drawString(mx, main_y, (data.get("full_name") or "").upper())
            main_y -= title_size + 2

            if data.get("job_role"):
                jsize = style["font_sizes"].get("job_role", header_size)
                c.setFont(font_bold, jsize)
                c.setFillColor(colors.black)
                c.drawString(mx, main_y, data["job_role"])
                main_y -= jsize + section_gap + 5
            else:
                main_y -= section_gap

        while sidebar_idx < len(sidebar_data) or main_idx < len(main_data):
            drew = False

            if sidebar_idx < len(sidebar_data):
                key = sidebar_data[sidebar_idx]["content"]
                if data.get(key):
                    htxt = sidebar_data[sidebar_idx]["header"]
                    if sidebar_line == 0 and htxt not in printed_sidebar_headers:
                        if sidebar_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(sx, sidebar_y, htxt.upper())
                        sidebar_y -= header_size + section_gap
                        printed_sidebar_headers.add(htxt)

                    if sidebar_line < len(sidebar_lines.get(sidebar_idx, [])):
                        if sidebar_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = sidebar_lines[sidebar_idx][sidebar_line]
                        c.drawString(sx, sidebar_y, line)
                        sidebar_y -= body_size + paragraph_gap
                        sidebar_line += 1
                        drew = True

                    if sidebar_line >= len(sidebar_lines.get(sidebar_idx, [])):
                        sidebar_line = 0
                        sidebar_idx += 1
                        if sidebar_idx < len(sidebar_data):
                            sidebar_y -= section_gap

            if main_idx < len(main_data):
                key = main_data[main_idx]["content"]
                if data.get(key):
                    htxt = main_data[main_idx]["header"]
                    if main_line == 0 and htxt not in printed_main_headers:
                        if main_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(mx, main_y, htxt.upper())
                        main_y -= header_size + section_gap
                        printed_main_headers.add(htxt)

                    if main_line < len(main_lines.get(main_idx, [])):
                        if main_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = main_lines[main_idx][main_line]
                        c.drawString(mx, main_y, line)
                        main_y -= body_size + paragraph_gap
                        main_line += 1
                        drew = True

                    if main_line >= len(main_lines.get(main_idx, [])):
                        main_line = 0
                        main_idx += 1
                        if main_idx < len(main_data):
                            main_y -= section_gap

            if not drew:
                break

        y_new = min(sidebar_y, main_y)
        return y_new, sidebar_idx, sidebar_line, main_idx, main_line


    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    y = height - margin

    sidebar_sections = [
        {"content": "email", "header": "email"},
        {"content": "phone", "header": "phone"},
        {"content": "skills", "header": data.get("skills_header", "Skills")},
        {"content": "languages", "header": data.get("languages_header", "Languages")},
        {"content": "certifications", "header": data.get("certifications_header", "Certifications")}
    ]

    main_sections = [
        {"content": "job_role", "header": "job_role"},
        {"content": "profile_summary", "header": data.get("profile_summary_header", "Profile Summary")},
        {"content": "work_experience", "header": data.get("work_experience_header", "Work Experience")},
        {"content": "education", "header": data.get("education_header", "Education")},
        {"content": "interests", "header": data.get("interests_header", "Interests")}
    ]

    sidx = midx = sline = mline = 0

    while sidx < len(sidebar_sections) or midx < len(main_sections):
        y, sidx, sline, midx, mline = draw_content(
            y, sidebar_sections, main_sections,
            sidx, midx, sline, mline
        )
        if sidx < len(sidebar_sections) or midx < len(main_sections):
            y = start_new_page()




#   TEMPLATE 1 GENERATOR (NO FastAPI)


def template1_generate(data):
    temp_dir = tempfile.mkdtemp()
    file_name = f"T1_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.black,
        "secondary": colors.HexColor("#555555"),
        "text": colors.black,
        "sidebar_bg": colors.white,
        "sidebar_width": 0.28,
        "font_name": "Times-Roman",
        "font_name_bold": "Times-Bold",
        "font_sizes": {"title": 18, "job_role": 16, "header": 12, "body": 11},
        "spacing": {"section": 10, "paragraph": 4}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template1_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise





#   TEMPLATE 2  (Modern Green)


def template2_draw_resume(c, style, data):

    width, height = A4
    margin = 40
    sidebar_width = width * style["sidebar_width"]
    bottom_margin = 0

    printed_sidebar_headers = set()
    printed_main_headers = set()

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_name = "Helvetica"
    if font_bold not in pdfmetrics.getRegisteredFontNames():
        font_bold = "Helvetica-Bold"

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    def start_new_page():
        c.showPage()
        c.setFillColor(style["sidebar_bg"])
        c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)
        return height - margin

    def draw_content(
        y_position, sidebar_data, main_data,
        start_sidebar_idx=0, start_main_idx=0,
        start_sidebar_line=0, start_main_line=0
    ):

        sx = margin / 2
        mx = sidebar_width + margin
        sidebar_y = y_position
        main_y = y_position

        sidebar_idx = start_sidebar_idx
        main_idx = start_main_idx
        sidebar_line = start_sidebar_line
        main_line = start_main_line

        sidebar_lines = {}
        main_lines = {}

        for i, section in enumerate(sidebar_data):
            key = section["content"]
            if data.get(key):
                sidebar_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    sidebar_width - sx - 10
                )

        for i, section in enumerate(main_data):
            key = section["content"]
            if data.get(key):
                main_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    width - sidebar_width - 2 * margin
                )

        #  FIRST PAGE TITLE 
        if start_sidebar_idx == 0 and start_main_idx == 0:
            c.setFont(font_bold, title_size)
            c.setFillColor(style["primary"])
            c.drawString(mx, main_y, data["full_name"].upper())
            main_y -= title_size + 2

            if data.get("job_role"):
                jsize = style["font_sizes"].get("job_role", header_size)
                c.setFont(font_bold, jsize)
                c.setFillColor(style["primary"])
                c.drawString(mx, main_y, data["job_role"])
                main_y -= jsize + section_gap + 5
            else:
                main_y -= section_gap

        #  BODY CONTENT 
        while sidebar_idx < len(sidebar_data) or main_idx < len(main_data):
            drew = False

            # SIDEBAR 
            if sidebar_idx < len(sidebar_data):
                key = sidebar_data[sidebar_idx]["content"]
                if data.get(key):

                    htxt = sidebar_data[sidebar_idx]["header"]
                    if sidebar_line == 0 and htxt not in printed_sidebar_headers:
                        if sidebar_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(sx, sidebar_y, htxt.upper())
                        sidebar_y -= header_size + section_gap
                        printed_sidebar_headers.add(htxt)

                    if sidebar_line < len(sidebar_lines.get(sidebar_idx, [])):
                        if sidebar_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = sidebar_lines[sidebar_idx][sidebar_line]
                        c.drawString(sx, sidebar_y, line)
                        sidebar_y -= body_size + paragraph_gap
                        sidebar_line += 1
                        drew = True

                    if sidebar_line >= len(sidebar_lines.get(sidebar_idx, [])):
                        sidebar_line = 0
                        sidebar_idx += 1
                        if sidebar_idx < len(sidebar_data):
                            sidebar_y -= section_gap

            # MAIN 
            if main_idx < len(main_data):
                key = main_data[main_idx]["content"]
                if data.get(key):

                    htxt = main_data[main_idx]["header"]
                    if main_line == 0 and htxt not in printed_main_headers:
                        if main_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(mx, main_y, htxt.upper())
                        main_y -= header_size + section_gap
                        printed_main_headers.add(htxt)

                    if main_line < len(main_lines.get(main_idx, [])):
                        if main_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = main_lines[main_idx][main_line]
                        c.drawString(mx, main_y, line)
                        main_y -= body_size + paragraph_gap
                        main_line += 1
                        drew = True

                    if main_line >= len(main_lines.get(main_idx, [])):
                        main_line = 0
                        main_idx += 1
                        if main_idx < len(main_data):
                            main_y -= section_gap

            if not drew:
                break

        return min(sidebar_y, main_y), sidebar_idx, sidebar_line, main_idx, main_line


    # INITIAL PAGE SETUP
    

    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    y = height - margin

    sidebar_sections = [
        {"content": "email", "header": "email"},
        {"content": "phone", "header": "phone"},
        {"content": "skills", "header": data.get("skills_header", "Skills")},
        {"content": "languages", "header": data.get("languages_header", "Languages")},
        {"content": "certifications", "header": data.get("certifications_header", "Certifications")},
    ]

    main_sections = [
        {"content": "profile_summary", "header": data.get("profile_summary_header", "Profile Summary")},
        {"content": "work_experience", "header": data.get("work_experience_header", "Work Experience")},
        {"content": "education", "header": data.get("education_header", "Education")},
        {"content": "interests", "header": data.get("interests_header", "Interests")},
    ]

    sidx = midx = sline = mline = 0

    while sidx < len(sidebar_sections) or midx < len(main_sections):
        y, sidx, sline, midx, mline = draw_content(
            y, sidebar_sections, main_sections,
            sidx, midx, sline, mline
        )
        if sidx < len(sidebar_sections) or midx < len(main_sections):
            y = start_new_page()


#   TEMPLATE 2 GENERATOR (NO FastAPI)


def template2_generate(data):

    temp_dir = tempfile.mkdtemp()
    file_name = f"T2_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.HexColor("#27AE60"),
        "secondary": colors.HexColor("#2ECC71"),
        "text": colors.HexColor("#333333"),
        "sidebar_bg": colors.HexColor("#ECF0F1"),
        "sidebar_width": 0.30,
        "font_name": "Calibri",
        "font_name_bold": "Calibri-Bold",
        "font_sizes": {"title": 22, "job_role": 16, "header": 12, "body": 11},
        "spacing": {"section": 14, "paragraph": 5}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template2_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise







#   TEMPLATE 3  (Creative Teal)


def template3_draw_resume(c, style, data):

    width, height = A4
    margin = 40
    sidebar_width = width * style["sidebar_width"]
    bottom_margin = 0

    printed_sidebar_headers = set()
    printed_main_headers = set()

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_name = "Helvetica"
    if font_bold not in pdfmetrics.getRegisteredFontNames():
        font_bold = "Helvetica-Bold"

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    def start_new_page():
        c.showPage()
        c.setFillColor(style["sidebar_bg"])
        c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)
        return height - margin

    def draw_content(
        y_position, sidebar_data, main_data,
        start_sidebar_idx=0, start_main_idx=0,
        start_sidebar_line=0, start_main_line=0
    ):

        sx = margin / 2
        mx = sidebar_width + margin
        sidebar_y = y_position
        main_y = y_position

        sidebar_idx = start_sidebar_idx
        main_idx = start_main_idx
        sidebar_line = start_sidebar_line
        main_line = start_main_line

        sidebar_lines = {}
        main_lines = {}

        for i, section in enumerate(sidebar_data):
            key = section["content"]
            if data.get(key):
                sidebar_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    sidebar_width - sx - 10
                )

        for i, section in enumerate(main_data):
            key = section["content"]
            if data.get(key):
                main_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    width - sidebar_width - 2 * margin
                )

        #  FIRST PAGE TITLE
        if start_sidebar_idx == 0 and start_main_idx == 0:
            c.setFont(font_bold, title_size)
            c.setFillColor(style["primary"])
            c.drawString(mx, main_y, data["full_name"].upper())
            main_y -= title_size + 2

            if data.get("job_role"):
                jsize = style["font_sizes"].get("job_role", header_size)
                c.setFont(font_bold, jsize)
                c.setFillColor(style["primary"])
                c.drawString(mx, main_y, data["job_role"])
                main_y -= jsize + section_gap + 5
            else:
                main_y -= section_gap

        # MAIN DRAW LOOP 
        while sidebar_idx < len(sidebar_data) or main_idx < len(main_data):
            drew = False

            #  SIDEBAR 
            if sidebar_idx < len(sidebar_data):
                key = sidebar_data[sidebar_idx]["content"]
                if data.get(key):

                    htxt = sidebar_data[sidebar_idx]["header"]
                    if sidebar_line == 0 and htxt not in printed_sidebar_headers:
                        if sidebar_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(sx, sidebar_y, htxt.upper())
                        sidebar_y -= header_size + section_gap
                        printed_sidebar_headers.add(htxt)

                    if sidebar_line < len(sidebar_lines.get(sidebar_idx, [])):
                        if sidebar_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = sidebar_lines[sidebar_idx][sidebar_line]
                        c.drawString(sx, sidebar_y, line)
                        sidebar_y -= body_size + paragraph_gap
                        sidebar_line += 1
                        drew = True

                    if sidebar_line >= len(sidebar_lines.get(sidebar_idx, [])):
                        sidebar_line = 0
                        sidebar_idx += 1
                        if sidebar_idx < len(sidebar_data):
                            sidebar_y -= section_gap

            # MAIN 
            if main_idx < len(main_data):
                key = main_data[main_idx]["content"]
                if data.get(key):

                    htxt = main_data[main_idx]["header"]
                    if main_line == 0 and htxt not in printed_main_headers:
                        if main_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(mx, main_y, htxt.upper())
                        main_y -= header_size + section_gap
                        printed_main_headers.add(htxt)

                    if main_line < len(main_lines.get(main_idx, [])):
                        if main_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = main_lines[main_idx][main_line]
                        c.drawString(mx, main_y, line)
                        main_y -= body_size + paragraph_gap
                        main_line += 1
                        drew = True

                    if main_line >= len(main_lines.get(main_idx, [])):
                        main_line = 0
                        main_idx += 1
                        if main_idx < len(main_data):
                            main_y -= section_gap

            if not drew:
                break

        return min(sidebar_y, main_y), sidebar_idx, sidebar_line, main_idx, main_line


    #  INITIAL PAGE 
    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    y = height - margin

    sidebar_sections = [
        {"content": "email", "header": "email"},
        {"content": "phone", "header": "phone"},
        {"content": "skills", "header": data.get("skills_header", "Skills")},
        {"content": "languages", "header": data.get("languages_header", "Languages")},
        {"content": "certifications", "header": data.get("certifications_header", "Certifications")}
    ]

    main_sections = [
        {"content": "profile_summary", "header": data.get("profile_summary_header", "Profile Summary")},
        {"content": "work_experience", "header": data.get("work_experience_header", "Work Experience")},
        {"content": "education", "header": data.get("education_header", "Education")},
        {"content": "interests", "header": data.get("interests_header", "Interests")}
    ]

    sidx = midx = sline = mline = 0
    while sidx < len(sidebar_sections) or midx < len(main_sections):
        y, sidx, sline, midx, mline = draw_content(
            y,
            sidebar_sections,
            main_sections,
            sidx,
            midx,
            sline,
            mline
        )
        if sidx < len(sidebar_sections) or midx < len(main_sections):
            y = start_new_page()




#   TEMPLATE 3 GENERATOR


def template3_generate(data):

    temp_dir = tempfile.mkdtemp()
    file_name = f"T3_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.HexColor("#12A89D"),
        "secondary": colors.HexColor("#16C2B3"),
        "text": colors.HexColor("#222222"),
        "sidebar_bg": colors.HexColor("#F8F9FA"),
        "sidebar_width": 0.32,
        "font_name": "Arial",
        "font_name_bold": "Arial-Bold",
        "font_sizes": {"title": 18, "job_role": 16, "header": 12, "body": 11},
        "spacing": {"section": 13, "paragraph": 8}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template3_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise










#   TEMPLATE 4  (Professional Blue)


def template4_draw_resume(c, style, data):

    width, height = A4
    margin = 40
    sidebar_width = width * style["sidebar_width"]
    bottom_margin = 0

    printed_sidebar_headers = set()
    printed_main_headers = set()

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_name = "Helvetica"
    if font_bold not in pdfmetrics.getRegisteredFontNames():
        font_bold = "Helvetica-Bold"

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    def start_new_page():
        c.showPage()
        c.setFillColor(style["sidebar_bg"])
        c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)
        return height - margin

    def draw_content(
        y_position, sidebar_data, main_data,
        start_sidebar_idx=0, start_main_idx=0,
        start_sidebar_line=0, start_main_line=0
    ):

        sx = margin / 2
        mx = sidebar_width + margin
        sidebar_y = y_position
        main_y = y_position

        sidebar_idx = start_sidebar_idx
        main_idx = start_main_idx
        sidebar_line = start_sidebar_line
        main_line = start_main_line

        sidebar_lines = {}
        main_lines = {}

        for i, section in enumerate(sidebar_data):
            key = section["content"]
            if data.get(key):
                sidebar_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    sidebar_width - sx - 10
                )

        for i, section in enumerate(main_data):
            key = section["content"]
            if data.get(key):
                main_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    width - sidebar_width - 2 * margin
                )

        #  FIRST PAGE HEADER
        if start_sidebar_idx == 0 and start_main_idx == 0:
            c.setFont(font_bold, title_size)
            c.setFillColor(style["primary"])
            c.drawString(mx, main_y, data["full_name"].upper())
            main_y -= title_size + 2

            if data.get("job_role"):
                jsize = style["font_sizes"].get("job_role", header_size)
                c.setFont(font_bold, jsize)
                c.setFillColor(style["primary"])
                c.drawString(mx, main_y, data["job_role"])
                main_y -= jsize + section_gap + 5
            else:
                main_y -= section_gap

        #  MAIN CONTENT LOOP 
        while sidebar_idx < len(sidebar_data) or main_idx < len(main_data):
            drew = False

            # Sidebar
            if sidebar_idx < len(sidebar_data):
                key = sidebar_data[sidebar_idx]["content"]
                if data.get(key):

                    htxt = sidebar_data[sidebar_idx]["header"]
                    if sidebar_line == 0 and htxt not in printed_sidebar_headers:
                        if sidebar_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(sx, sidebar_y, htxt.upper())
                        sidebar_y -= header_size + section_gap
                        printed_sidebar_headers.add(htxt)

                    if sidebar_line < len(sidebar_lines.get(sidebar_idx, [])):
                        if sidebar_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = sidebar_lines[sidebar_idx][sidebar_line]
                        c.drawString(sx, sidebar_y, line)
                        sidebar_y -= body_size + paragraph_gap
                        sidebar_line += 1
                        drew = True

                    if sidebar_line >= len(sidebar_lines.get(sidebar_idx, [])):
                        sidebar_line = 0
                        sidebar_idx += 1
                        if sidebar_idx < len(sidebar_data):
                            sidebar_y -= section_gap

            # Main
            if main_idx < len(main_data):
                key = main_data[main_idx]["content"]
                if data.get(key):

                    htxt = main_data[main_idx]["header"]
                    if main_line == 0 and htxt not in printed_main_headers:
                        if main_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(mx, main_y, htxt.upper())
                        main_y -= header_size + section_gap
                        printed_main_headers.add(htxt)

                    if main_line < len(main_lines.get(main_idx, [])):
                        if main_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = main_lines[main_idx][main_line]
                        c.drawString(mx, main_y, line)
                        main_y -= body_size + paragraph_gap
                        main_line += 1
                        drew = True

                    if main_line >= len(main_lines.get(main_idx, [])):
                        main_line = 0
                        main_idx += 1
                        if main_idx < len(main_data):
                            main_y -= section_gap

            if not drew:
                break

        return min(sidebar_y, main_y), sidebar_idx, sidebar_line, main_idx, main_line

    #  DRAW SIDEBAR (FIRST PAGE) 
    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    y = height - margin

    sidebar_sections = [
        {"content": "email", "header": "email"},
        {"content": "phone", "header": "phone"},
        {"content": "skills", "header": data.get("skills_header", "Skills")},
        {"content": "languages", "header": data.get("languages_header", "Languages")},
        {"content": "certifications", "header": data.get("certifications_header", "Certifications")},
    ]

    main_sections = [
        {"content": "profile_summary", "header": data.get("profile_summary_header", "Profile Summary")},
        {"content": "work_experience", "header": data.get("work_experience_header", "Work Experience")},
        {"content": "education", "header": data.get("education_header", "Education")},
        {"content": "interests", "header": data.get("interests_header", "Interests")},
    ]

    sidx = midx = sline = mline = 0
    while sidx < len(sidebar_sections) or midx < len(main_sections):
        y, sidx, sline, midx, mline = draw_content(
            y,
            sidebar_sections,
            main_sections,
            sidx,
            midx,
            sline,
            mline
        )
        if sidx < len(sidebar_sections) or midx < len(main_sections):
            y = start_new_page()



#   TEMPLATE 4 GENERATOR


def template4_generate(data):

    temp_dir = tempfile.mkdtemp()
    file_name = f"T4_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.HexColor("#2C4850"),
        "secondary": colors.HexColor("#3498DB"),
        "text": colors.black,
        "sidebar_bg": colors.HexColor("#BEA47D"),
        "sidebar_width": 0.30,
        "font_name": "Calibri",
        "font_name_bold": "Calibri-Bold",
        "font_sizes": {"title": 22, "job_role": 18, "header": 12, "body": 11},
        "spacing": {"section": 12, "paragraph": 4}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template4_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise







#   TEMPLATE 5  (Refined Garamond)


def template5_draw_resume(c, style, data):

    width, height = A4
    margin = 40
    sidebar_width = width * style["sidebar_width"]
    bottom_margin = 0

    printed_sidebar_headers = set()
    printed_main_headers = set()

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_name = "Helvetica"
    if font_bold not in pdfmetrics.getRegisteredFontNames():
        font_bold = "Helvetica-Bold"

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    def start_new_page():
        c.showPage()
        c.setFillColor(style["sidebar_bg"])
        c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)
        return height - margin

    def draw_content(
        y_position, sidebar_data, main_data,
        start_sidebar_idx=0, start_main_idx=0,
        start_sidebar_line=0, start_main_line=0
    ):

        sx = margin / 2
        mx = sidebar_width + margin
        sidebar_y = y_position
        main_y = y_position

        sidebar_idx = start_sidebar_idx
        main_idx = start_main_idx
        sidebar_line = start_sidebar_line
        main_line = start_main_line

        sidebar_lines = {}
        main_lines = {}

        # Prepare sidebar wrapped text
        for i, section in enumerate(sidebar_data):
            key = section["content"]
            if data.get(key):
                sidebar_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    sidebar_width - sx - 10
                )

        # Prepare main wrapped text
        for i, section in enumerate(main_data):
            key = section["content"]
            if data.get(key):
                main_lines[i] = wrap_text_dynamic(
                    c, data[key], font_name, body_size,
                    width - sidebar_width - 2 * margin
                )

        # First page header
        if start_sidebar_idx == 0 and start_main_idx == 0:
            c.setFont(font_bold, title_size)
            c.setFillColor(style["primary"])
            c.drawString(mx, main_y, data["full_name"].upper())
            main_y -= title_size + 2

            if data.get("job_role"):
                jsize = style["font_sizes"].get("job_role", header_size)
                c.setFont(font_bold, jsize)
                c.setFillColor(style["primary"])
                c.drawString(mx, main_y, data["job_role"])
                main_y -= (jsize + section_gap + 5)
            else:
                main_y -= section_gap

        # Content loop
        while sidebar_idx < len(sidebar_data) or main_idx < len(main_data):
            drew = False

            # Sidebar
            if sidebar_idx < len(sidebar_data):
                key = sidebar_data[sidebar_idx]["content"]
                if data.get(key):

                    htxt = sidebar_data[sidebar_idx]["header"]
                    if sidebar_line == 0 and htxt not in printed_sidebar_headers:
                        if sidebar_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(sx, sidebar_y, htxt.upper())
                        sidebar_y -= header_size + section_gap
                        printed_sidebar_headers.add(htxt)

                    if sidebar_line < len(sidebar_lines.get(sidebar_idx, [])):
                        if sidebar_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = sidebar_lines[sidebar_idx][sidebar_line]
                        c.drawString(sx, sidebar_y, line)
                        sidebar_y -= body_size + paragraph_gap
                        sidebar_line += 1
                        drew = True

                    if sidebar_line >= len(sidebar_lines.get(sidebar_idx, [])):
                        sidebar_line = 0
                        sidebar_idx += 1
                        if sidebar_idx < len(sidebar_data):
                            sidebar_y -= section_gap

            # Main
            if main_idx < len(main_data):
                key = main_data[main_idx]["content"]
                if data.get(key):

                    htxt = main_data[main_idx]["header"]
                    if main_line == 0 and htxt not in printed_main_headers:
                        if main_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(mx, main_y, htxt.upper())
                        main_y -= header_size + section_gap
                        printed_main_headers.add(htxt)

                    if main_line < len(main_lines.get(main_idx, [])):
                        if main_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = main_lines[main_idx][main_line]
                        c.drawString(mx, main_y, line)
                        main_y -= body_size + paragraph_gap
                        main_line += 1
                        drew = True

                    if main_line >= len(main_lines.get(main_idx, [])):
                        main_line = 0
                        main_idx += 1
                        if main_idx < len(main_data):
                            main_y -= section_gap

            if not drew:
                break

        return min(sidebar_y, main_y), sidebar_idx, sidebar_line, main_idx, main_line


    # Draw sidebar
    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    y = height - margin

    sidebar_sections = [
        {"content": "email", "header": "email"},
        {"content": "phone", "header": "phone"},
        {"content": "skills", "header": data.get("skills_header", "Skills")},
        {"content": "languages", "header": data.get("languages_header", "Languages")},
        {"content": "certifications", "header": data.get("certifications_header", "Certifications")},
    ]

    main_sections = [
        {"content": "profile_summary", "header": data.get("profile_summary_header", "Profile Summary")},
        {"content": "work_experience", "header": data.get("work_experience_header", "Work Experience")},
        {"content": "education", "header": data.get("education_header", "Education")},
        {"content": "interests", "header": data.get("interests_header", "Interests")},
    ]

    sidx = midx = sline = mline = 0
    while sidx < len(sidebar_sections) or midx < len(main_sections):
        y, sidx, sline, midx, mline = draw_content(
            y,
            sidebar_sections,
            main_sections,
            sidx,
            midx,
            sline,
            mline
        )
        if sidx < len(sidebar_sections) or midx < len(main_sections):
            y = start_new_page()




#   TEMPLATE 5 GENERATOR


def template5_generate(data):

    temp_dir = tempfile.mkdtemp()
    file_name = f"T5_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.HexColor("#2E2E2E"),
        "secondary": colors.HexColor("#4F4F4F"),
        "text": colors.black,
        "sidebar_bg": colors.HexColor("#9E8FAA"),
        "sidebar_width": 0.30,
        "font_name": "Garamond",
        "font_name_bold": "Garamond-Bold",
        "font_sizes": {"title": 20, "header": 13, "body": 11},
        "spacing": {"section": 12, "paragraph": 4}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template5_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise










#   TEMPLATE 6  (Plain Resume)


def template6_wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    lines = []
    for paragraph in (text or "").split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split(" ")
        line = ""
        for word in words:
            test_line = (line + " " + word).strip()
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def template6_ensure_space(c, y, needed, height, margin):
    if y - needed < margin:
        c.showPage()
        register_all_fonts()
        return height - margin
    return y


def template6_draw_resume(c, style, data):

    width, height = A4
    margin = 50

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]

    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    y = height - margin

    #  NAME 
    c.setFont(font_bold, title_size)
    c.setFillColor(style["primary"])
    c.drawCentredString(width / 2, y, data["full_name"].upper())
    y -= title_size + 8

    # JOB ROLE 
    if data.get("job_role"):
        c.setFont(font_name, header_size)
        c.setFillColor(style["secondary"])
        c.drawCentredString(width / 2, y, data["job_role"])
        y -= header_size + 15

    #  CONTACT LINE 
    c.setFont(font_name, body_size)
    c.setFillColor(style["text"])
    contact_line = f"{data['phone']}  |  {data['email']}"
    c.drawCentredString(width / 2, y, contact_line)
    y -= body_size + (section_gap * 2)

    #  SECTION CONTENT 

    sections = [
        ("Profile Summary", data.get("profile_summary")),
        ("Work Experience", data.get("work_experience")),
        ("Education", data.get("education")),
        ("Skills", data.get("skills")),
        ("Languages", data.get("languages")),
        ("Certifications", data.get("certifications")),
        ("Interests", data.get("interests")),
    ]

    for title, content in sections:
        if not content:
            continue

        # Header
        c.setFont(font_bold, header_size)
        c.setFillColor(style["primary"])

        needed = header_size + paragraph_gap
        y = template6_ensure_space(c, y, needed, height, margin)
        c.drawString(margin, y, title.upper())
        y -= header_size + (paragraph_gap * 2)

        # Body
        c.setFont(font_name, body_size)
        c.setFillColor(style["text"])

        lines = template6_wrap_text(c, content, font_name, body_size, width - 2 * margin)

        for line in lines:
            needed = body_size + paragraph_gap
            y = template6_ensure_space(c, y, needed, height, margin)
            c.drawString(margin, y, line)
            y -= body_size + paragraph_gap

        y -= section_gap



#   TEMPLATE 6 GENERATOR


def template6_generate(data):

    temp_dir = tempfile.mkdtemp()
    file_name = f"T6_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.HexColor("#2E2E2E"),
        "secondary": colors.HexColor("#4F4F4F"),
        "text": colors.black,
        "font_name": "Helvetica",
        "font_name_bold": "Helvetica-Bold",
        "font_sizes": {"title": 20, "header": 13, "body": 11},
        "spacing": {"section": 14, "paragraph": 5}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template6_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise






# ============================================================
#   TEMPLATE 7  (Horizontal Resume)
# ============================================================

def template7_draw_underline(c, x, y, width, color=colors.black, thickness=1):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    c.line(x, y, x + width, y)
    c.restoreState()


def template7_draw_rounded_rect(c, x, y, width, height, radius, fill_color=None):
    c.saveState()
    if fill_color:
        c.setFillColor(fill_color)

    p = c.beginPath()
    p.moveTo(x + radius, y)
    p.lineTo(x + width - radius, y)
    p.curveTo(x + width, y, x + width, y, x + width, y + radius)
    p.lineTo(x + width, y + height - radius)
    p.curveTo(x + width, y + height, x + width, y + height, x + width - radius, y + height)
    p.lineTo(x + radius, y + height)
    p.curveTo(x, y + height, x, y + height, x, y + height - radius)
    p.lineTo(x, y + radius)
    p.curveTo(x, y, x, y, x + radius, y)

    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def template7_wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    lines = []
    for paragraph in (text or "").split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split(" ")
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, font_name, font_size) <= max_width:
                line = test
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def template7_ensure_space(c, y, needed, height, margin):
    if y - needed < margin:
        c.showPage()
        register_all_fonts()
        return height - margin
    return y


def template7_draw_resume(c, style, data):

    width, height = A4
    margin = 50

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    title_size = style["font_sizes"]["title"]
    head_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]

    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    header_height = 100

    template7_draw_rounded_rect(
        c,
        margin - 10,
        height - margin - header_height,
        width - 2 * (margin - 10),
        header_height,
        radius=10,
        fill_color=style["header_bg"]
    )

    y = height - margin - 15

    c.setFont(font_bold, title_size)
    c.setFillColor(colors.white)
    c.drawCentredString(width / 2, y - 20, data["full_name"].upper())
    y -= title_size + 25

    if data.get("job_role"):
        c.setFont(font_name, head_size)
        c.setFillColor(colors.white)
        c.drawCentredString(width / 2, y, data["job_role"])
        y -= head_size + 15

    c.setFont(font_name, body_size)
    c.setFillColor(colors.white)
    contact_line = f"{data['phone']}  |  {data['email']}"
    c.drawCentredString(width / 2, y, contact_line)

    y = height - margin - header_height - 40

    sections = [
        ("Profile Summary", data.get("profile_summary")),
        ("Work Experience", data.get("work_experience")),
        ("Education", data.get("education")),
        ("Skills", data.get("skills")),
        ("Languages", data.get("languages")),
        ("Certifications", data.get("certifications")),
        ("Interests", data.get("interests")),
    ]

    for title, content in sections:
        if not content:
            continue

        c.setFont(font_bold, head_size)
        c.setFillColor(style["primary"])

        needed = head_size + paragraph_gap
        y = template7_ensure_space(c, y, needed, height, margin)

        c.drawString(margin, y, title.upper())
        text_w = c.stringWidth(title.upper(), font_bold, head_size)
        template7_draw_underline(c, margin, y - 2, text_w, style["primary"], 1)

        y -= head_size + (paragraph_gap * 2)

        c.setFont(font_name, body_size)
        c.setFillColor(style["text"])
        lines = template7_wrap_text(c, content, font_name, body_size, width - 2 * margin)

        for line in lines:
            needed = body_size + paragraph_gap
            y = template7_ensure_space(c, y, needed, height, margin)
            c.drawString(margin, y, line)
            y -= body_size + paragraph_gap

        y -= section_gap


# ============================================================
#   TEMPLATE 7 GENERATOR
# ============================================================

def template7_generate(data):

    temp_dir = tempfile.mkdtemp()
    file_name = f"T7_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    style = {
        "primary": colors.HexColor("#2E2E2E"),
        "secondary": colors.HexColor("#D8E27A"),
        "text": colors.black,
        "header_bg": colors.HexColor("#523A4E"),
        "font_name": "Helvetica",
        "font_name_bold": "Helvetica-Bold",
        "font_sizes": {"title": 20, "header": 13, "body": 11},
        "spacing": {"section": 14, "paragraph": 5}
    }

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        template7_draw_resume(c, style, data)
        c.save()
        return file_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


#   EXPORT LIST FOR main.py


TEMPLATES = [
    template1_generate,
    template2_generate,
    template3_generate,
    template4_generate,
    template5_generate,
    template6_generate,
    template7_generate
]



