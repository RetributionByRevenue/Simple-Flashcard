from fasthtml.common import *
import time
import re
import base64
import texttoimage

cdn = 'https://cdn.jsdelivr.net/npm/bootstrap'
bootstrap_links = [
    Link(href=cdn+"@5.3.3/dist/css/bootstrap.min.css", rel="stylesheet"),
    Script(src=cdn+"@5.3.3/dist/js/bootstrap.bundle.min.js"),
    Link(href=cdn+"-icons@1.11.3/font/bootstrap-icons.min.css", rel="stylesheet"),
    NotStr('''
    <style>
    #question, #answer, H2 {
        text-align: left;
        width: 80%;
        height: auto;
        display: block;
        margin: auto;
        border: 1px solid black;
        outline: none;
    }
    </style>
    <script>
    function senddata(){
        data = new FormData()
        let question = document.getElementById("question").innerHTML;
        if(question.includes("<span")){question = document.getElementById("question").innerText}
        let answer = document.getElementById("answer").innerHTML;
        if(answer.includes("<span")){answer = document.getElementById("answer").innerText}
        data.set('question', question )
        data.set('answer', answer     )
        let request = new XMLHttpRequest();
        request.open("POST", '/', true);
        request.send(data)
    }
    </script>
''')
]

app, rt = fast_app(hdrs=bootstrap_links)

def SidebarItem(text, hx_get, hx_target, **kwargs):
    return Div(
        I(cls=f'bi bi-{text}'),
        Span(text),
        hx_get=hx_get, hx_target=hx_target,
        data_bs_parent='#sidebar', role='button',
        cls='list-group-item border-end-0 d-inline-block text-truncate',
        **kwargs)

def Sidebar(sidebar_items, hx_get, hx_target):
    return Div(
        Div(*(SidebarItem(o, f"{hx_get}?menu={o}", hx_target) for o in sidebar_items),
            id='sidebar-nav',
            cls='list-group border-0 rounded-0 text-sm-start min-vh-100'
        ),
        id='sidebar',
        cls='collapse collapse-horizontal show border-end')

sidebar_items = ('View Flashcard', 'Add Flashcard')

def generate_img_tags(directory_path):
    img_tags = "<br>"
    # Loop through all files in the directory
    for filename in os.listdir(directory_path):
        # Check if the file is an image
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # Create an IMG tag with _id set to the filename
            
            bootstrap_modal=f'''
                                <!-- Button trigger modal -->
                                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#{filename}">
                                <IMG src="./questions/{filename}" class="{filename}">
                                </button>
                                <!-- Modal -->
                                <div class="modal fade" id="{filename}" tabindex="-1" aria-hidden="true">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                    <IMG src="./answers/{filename}" class="{filename}">
                                    </div>
                                </div>
                                </div>'''
            img_tags+=bootstrap_modal
            
    return img_tags

@app.get('/menucontent')
def menucontent(menu : str):
    if menu == "Add Flashcard":
        return (
                Br(),P("📋 Paste Picture or Edit Textbox"),Div(
                    H2("Input Flashcard Question"),
                    Div(
                        "",
                        _id="question",
                        contenteditable=""
                    ),
                    id="current-menu-content"
                  ), Hr(),
                Div(
                    H2("Input Flashcard Answer"),
                    Div(
                        "",
                        _id="answer",
                        contenteditable=""
                    ),
                    id="current-menu-content"
                  ),Br(),
                Button("Submit Flashcard",
                        **{'onclick': 'senddata(); '} )
                )
    else:
        
        return generate_img_tags('./questions')

@app.post('/')
async def submit(request):
    form_data = await request.form()
    timestr=str(int(time.time()))
    #process question
    question_content = form_data.get('question')
    question_process = re.search(r'<img[^>]*>', question_content)
    if question_process:
        img=question_process.group()
        base64_str= ((re.search(r',[^"]*"', img)).group()[1:-1]).encode()
        file_format= (re.search(r'/([^;]*);', img)).group()[1:-1]
        file_name="./questions/"+timestr+"."+file_format
        with open(file_name, "wb") as fh:
            fh.write(base64.decodebytes(base64_str))
    else:
        ''
        texttoimage.convert(question_content, image_file="./questions/"+timestr+".png", font_size=30, color='red')
    #process answer
    answer_content = form_data.get('answer')
    answer_process = re.search(r'<img[^>]*>', answer_content)
    #print(answer_content)
    if answer_process:
        img=answer_process.group()
        base64_str= ((re.search(r',[^"]*"', img)).group()[1:-1]).encode()
        file_format= (re.search(r'/([^;]*);', img)).group()[1:-1]
        file_name="./answers/"+timestr+"."+file_format
        with open(file_name, "wb") as fh:
            fh.write(base64.decodebytes(base64_str))        
    else:
        print(answer_content)
        texttoimage.convert(answer_content, image_file="./answers/"+timestr+".png", font_size=30, color='red')
    return "Flashcard submitted successfully"

@app.get('/')
def homepage():
    return Div(
        Div(
            Div(
                Sidebar(sidebar_items, hx_get='/menucontent', hx_target='#current-menu-content'),
                cls='col-auto px-0'),
            Main(
                A(I(cls='bi bi-list bi-lg py-2 p-1'), 'Menu',
                  href='#', data_bs_target='#sidebar', data_bs_toggle='collapse',
                  cls='border rounded-3 p-1 text-decoration-none'),
                Div(
                  Div(
                    Div(
                    hx_get='/menucontent?menu=View%20Flashcard',
                    hx_trigger="load", 
                    hx_target='#current-menu-content',
                    hx_swap="outerhtml",
                    _id="current-menu-content"),
                    cls='col-12'
                ), cls='row'),
                cls='col ps-md-2 pt-2'),
            cls='row flex-nowrap'),
        cls='container-fluid')

serve(port=5002)
