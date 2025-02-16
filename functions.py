import difflib
import os.path
import re
# from fuzzywuzzy import fuzz
from PyQt5 import QtCore
import time
import pymupdf
import numpy

class BackgroundTask(QtCore.QThread):    
    
    add_to_buffer = QtCore.pyqtSignal(list)
    update_progress = QtCore.pyqtSignal(int)
    new_mail=[]
    InboxPath=""
    archived_PDF_list=[]
    preexisting_file_contents = []
    speed_up_background_task = True
    
    def __init__(self, data):
        super().__init__()
        self.new_mail = data[0]
        self.InboxPath = data[1]
        self.archived_PDF_list = data[2]
        self.buffer_list=[[],[],[],[],[],[]]
    def run(self):
        start_time = time.time()
        # Read the contents of each preexisting file and store in a list
        for file in self.archived_PDF_list:
            try:#use error handling to simply skip faulty PDFs
                self.preexisting_file_contents.append(read_PDF_text(file))
            except:
                print("Error reading "+file+". File will be skipped.")
                self.archived_PDF_list.remove(file)
                continue
            progress=int(50*self.archived_PDF_list.index(file)/len(self.archived_PDF_list))
            self.update_progress.emit(progress)
            
        processing_time = time.time() - start_time
        print("PDF text extraction time:", processing_time, "seconds")
        
        # buffer PDF info in the background
        for file_path in self.new_mail:
            self.buffer_list[0]=file_path.split(self.InboxPath)[1]
            self.buffer_list[1]=suggest_date(file_path)
            paths, names = self.suggest_archive_folders(file_path, self.archived_PDF_list)
            self.buffer_list[2]=paths
            self.buffer_list[3]=names
            self.buffer_list[4]=render_PDF(file_path)
            self.buffer_list[5]=file_path
            self.add_to_buffer.emit(self.buffer_list)
        #self.finished.emit()   
    
    def suggest_archive_folders(self, new_file, file_list):
        new_file_contents = read_PDF_text(new_file)
            
        # Compare the new file to each preexisting file and store the similarity ratio
        similarity_ratios = []
        for index, preexisting_file in enumerate(self.preexisting_file_contents):
            similarity_ratios.append(difflib.SequenceMatcher(None, new_file_contents, preexisting_file).ratio())
            progress=int(50+50*index/len(self.preexisting_file_contents))
            self.update_progress.emit(progress)
            if not self.speed_up_background_task:
                time.sleep(0.02) #prevents the GUI from becoming unresponsive
            
        # Sort files based on highest similarity ratio
        sorted_files = [x for _, x in sorted(zip(similarity_ratios,file_list), reverse=True)]
        
        sorted_paths=[os.path.dirname(x) for x in sorted_files]
        suggested_paths=[]
        suggested_file_names=[]
        
        #only one suggestion per path
        for index, path in enumerate(sorted_paths):
            if path not in suggested_paths:
                suggested_paths.append(path)
                suggested_file_names.append(sorted_files[index][len(path):len(sorted_files[index])-4])
        self.update_progress.emit(100)
        
        if not self.buffer_list[1] == None:
            month_strings=["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
            _,month,year=self.buffer_list[1].split(".")
            if len(year)==2:
                year="20" + year
            if int(month) <= 12:    
                month=month_strings[int(month)-1]
            suggested_file_names = [re.sub(r"\b\d{4} \w+\b", year + " " + month, name) for name in suggested_file_names]
        suggested_file_names = [x.lstrip("/") for x in suggested_file_names]
        return [suggested_paths, suggested_file_names]
    
    def user_is_waiting(self):
        self.speed_up_background_task = True
        
    def user_is_not_waiting(self):
        self.speed_up_background_task = False
        
def render_PDF(pdf_file_path):
    
    pdf_file = pymupdf.open(pdf_file_path)
    
    # Get the first page
    image = pdf_file[0].get_pixmap(matrix=pymupdf.Matrix(200/72, 200/72), alpha=False)
    # Convert the image data to a NumPy array
    image_array = numpy.frombuffer(image.samples, numpy.uint8).reshape(image.height, image.width, image.n)
          
    pdf_file.close()
    
    return image_array


def find_pdf_files(root_folder, excluded_folders=[]):
    pdf_files = []

    for dirpath, dirnames, filenames in os.walk(root_folder):
        for folder_name in excluded_folders:
            if folder_name in dirnames:
                dirnames.remove(folder_name)
        for filename in filenames:
            if filename.endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, filename))

    return pdf_files

def suggest_archive_folder(new_file, file_list):
    # Open the new file and read its contents
    new_file_contents = read_PDF_text(new_file)
    
    # Read the contents of each preexisting file and store in a list
    preexisting_file_contents = []
    for file in file_list:
        preexisting_file_contents.append(read_PDF_text(file))
    
    # Compare the new file to each preexisting file and store the similarity ratio
    similarity_ratios = []
    for preexisting_file in preexisting_file_contents:
        similarity_ratios.append(difflib.SequenceMatcher(None, new_file_contents, preexisting_file).ratio())
    
    # Find the index of the highest similarity ratio
    highest_similarity_index = similarity_ratios.index(max(similarity_ratios))

    return os.path.dirname(file_list[highest_similarity_index])

# def suggest_archive_folder_fuzzywuzzy(new_file, file_list):
#     new_file_text = read_PDF_text(new_file)

#     max_similarity = 0
#     best_match = None

#     for file in file_list:
#         print(file)
#         existing_file_text = read_PDF_text(file)

#         similarity = fuzz.ratio(new_file_text, existing_file_text)
#         if similarity > max_similarity:
#             max_similarity = similarity
#             best_match = file

#     return os.path.dirname(best_match)

def suggest_date(file_path):
    text=read_PDF_text(file_path)
    
    #return first result that matches a German file format    
    pattern = re.compile(r'\b(\d{2})\.(\d{2})\.(\d{2,4})\b')
    match = pattern.search(text)
    if match:
        return match.group()
    else:
        return None
    
def read_PDF_text(file_path, max_num_pages=1):
        pdf_reader = pymupdf.open(file_path)
        
        # get the number of pages in the PDF
        num_pages = len(pdf_reader)
        num_pages = min(num_pages, max_num_pages)
        # read the text from each page and store it in a list
        text = []
        for page_num in range(num_pages):
            page = pdf_reader[page_num]
            text.append(page.get_text("text"))
        text = "\n".join(text)
        return text
