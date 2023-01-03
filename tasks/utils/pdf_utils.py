import base64
import fitz

# Đọc 1 trang
def read_page(page):
    # Trích rút các câu
    sentences = []
    temp = []
    words = page.get_text("words", sort=False)
    for (idx, word) in enumerate(words):
        temp.append(word)
        if word[4][-1] in ['.', '!', '?']:
            sentences.append(temp)
            temp=[]
        if idx == len(words)-1:
            sentences.append(temp)
    return sentences

# Hàm tìm bounding box bao list các bounding box
def find_bounding_box(listStartPoints, listEndPoints):
    x0 = listStartPoints[0][0]
    y0 = min([i[1] for i in listStartPoints])
    x1 = listEndPoints[-1][0]
    y1 = max([i[1] for i in listEndPoints])
    return (x0, y0), (x1, y1)

# Hợp nhất bounding box của các từ trong câu thành các bounding box của các dòng
def merge_bounding_box(wordList):
    startPoints = [(word[0], word[1]) for word in wordList]
    endPoints = [(word[2], word[3]) for word in wordList]

    # Lưu nhóm các bounding box nằm trên cùng 1 dòng
    lineGroupStartPoints=[]
    lineGroupEndPoints=[]

    tempStartPoints=[startPoints[0]]
    tempEndPoints=[endPoints[0]]
    for i in range((len(startPoints)-1)):
        if startPoints[i+1][0]>startPoints[i][0]:
            tempStartPoints.append(startPoints[i+1])
            tempEndPoints.append(endPoints[i+1])
        else:
            lineGroupStartPoints.append(tempStartPoints)
            lineGroupEndPoints.append(tempEndPoints)
            tempStartPoints=[startPoints[i+1]]
            tempEndPoints=[endPoints[i+1]]
        if i == len(startPoints)-2:
            lineGroupStartPoints.append(tempStartPoints)
            lineGroupEndPoints.append(tempEndPoints)
    
    # Lưu bounding box sau khi đã được merge
    lineStartPoints=[]
    lineEndPoints=[]
    for (listStartPoints, listEndPoints) in zip(lineGroupStartPoints, lineGroupEndPoints):
        startPoint, endPoint = find_bounding_box(listStartPoints, listEndPoints)
        lineStartPoints.append(startPoint)
        lineEndPoints.append(endPoint)
    
    return lineStartPoints, lineEndPoints

# Chuyển thông tin bounding box từ top left/bottom right
# sang x_top_left/y_top_left/width/height
def convert_bb_type(startPoint, endPoint):
    return {'x': startPoint[0], 'y': startPoint[1], 'width': endPoint[0]-startPoint[0], 'height': endPoint[1]-startPoint[1]}

# Lấy các câu
def get_text(wordList):
    text = ""
    for (idx, word) in enumerate(wordList):
        if idx == len(wordList)-1:
            text+=word[4]
        else:
            text+=word[4]+" "
    return text

# Từ base64 chuyển thành file pdf
def convert_base64_to_pdf(doc_message):
    base64_doc_bytes = doc_message.encode('ascii')
    doc_bytes = base64.b64decode(base64_doc_bytes)
    doc = fitz.open(stream=doc_bytes, filetype="pdf")
    return doc