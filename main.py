filepath = extract()

annotate(filepath)

analysis()

getTS()

import cv2
import numpy as np
import pandas as pd
import os
from PIL import Image
import heyexReader
import time
import shutil
import numpy as np


def extract():
    directory = getDirectory()
    
    filepath = getImage(directory)
    
    folder = loadImagesInFolder(filepath)

    return filepath


def annotate(filepath):
    [image, imagepath] = extractImage()
    
    draw(image, imagepath, filepath)


def getDirectory():
    
    directory = 'data/'
    
    print(f'Here is a list of folders in the {directory} directory')
    entries = os.listdir(directory)
    
    counter = 0
    for entry in entries:
        print('[{}] {}'.format(counter, entry))
        counter += 1
    
    time.sleep(0.2)
    
    user_selection = input('Indicate which folder you want to open: ')
        
    folder = entries[int(user_selection)]
    
    # Get the base name of the file
#     file_name = os.path.basename(image_path)
#     directory = os.path.dirname(image_path)
    
    folderpath = directory + folder
    
    return folderpath 


def getImage(directory):
    
    print(f'Here is a list of files in the {directory} directory')
    entries = os.listdir(directory)
    
    counter = 0
    for entry in entries:
        print('[{}] {}'.format(counter, entry))
        counter += 1
    
    time.sleep(0.2)
    
    user_selection = input('Indicate which file you want to analyze: ')
        
    image_path = entries[int(user_selection)]
    
    # Get the base name of the file
#     file_name = os.path.basename(image_path)
#     directory = os.path.dirname(image_path)
    
    filepath = directory + "/" + image_path
    
    return filepath 


# +
def loadImagesInFolder(filepath):
    tempfolder = "temp_data"
    
    vol = heyexReader.volFile(filepath)

    vol.renderIRslo("slo.png", renderGrid = True)
    vol.renderOCTscans("oct", renderSeg = True)

#     print(vol.oct.shape)
#     print(vol.irslo.shape)
    
    image_file = vol.oct
    
    # Delete everything in folder
    for f in os.listdir(tempfolder):
            os.remove(os.path.join(tempfolder, f))
            
    for i in range(0, 6):
        try:
            source_file = f"oct-00{i}.png"  # Replace "image{i}.png" with the actual filename pattern of your generated PNG files
            shutil.move(source_file, tempfolder)
        except FileNotFoundError:
#             print(f"File 'oct-00{i}.png' does not exist")
            break    
    
    # Get file name
    filename = os.path.basename(filepath)
    
    print(f"The file {filename} will be extracted into individual images...")
    
    print(f"🎉 The images have been extracted into /{tempfolder}")
    
    return tempfolder


# -

def extractImage():
    
    folder = "temp_data"

    entries = os.listdir(folder)
    counter = 0
    for entry in entries:
        print('[{}] {}'.format(counter, entry))
        counter += 1
    
    user_selection = input('Indicate which image you want to analyze: ')
        
    image = entries[int(user_selection)]
    
    imagepath = folder + '/'+ image
    
    print("⏲️ A window will open in a couple of seconds...")
    
    time.sleep(1)
    
    print("Window loaded!")
    
    time.sleep(0.2)
    
    print("⚠️ When you are finished, press the 'Esc' button in your keyboard 2x to save the image")
    
    return image, imagepath


# +
drawing=False # true if mouse is pressed
mode=True # if True, draw rectangle. Press 'm' to toggle to curve

def draw(image, imagepath, original_filepath):

    drawing=False # true if mouse is pressed
    mode=True # if True, draw rectangle. Press 'm' to toggle to curve

    image = cv2.imread(imagepath)
    
    def draw_lines(event,former_x,former_y,flags,param):

        global current_former_x,current_former_y,drawing, mode

        if event==cv2.EVENT_LBUTTONDOWN:
            drawing=True
            current_former_x,current_former_y=former_x,former_y

        elif event==cv2.EVENT_MOUSEMOVE:
            if drawing==True:
                if mode==True:
                    cv2.line(image,(current_former_x,current_former_y),(former_x,former_y),(0, 0, 255), 2)
                    current_former_x = former_x
                    current_former_y = former_y
                    #print former_x,former_y
        elif event==cv2.EVENT_LBUTTONUP:
            drawing=False
            if mode==True:
                cv2.line(image,(current_former_x,current_former_y),(former_x,former_y),(0, 0, 255), 2)
                current_former_x = former_x
                current_former_y = former_y
        return former_x,former_y   

    cv2.namedWindow("Choroid Measure OpenCV")
    cv2.setMouseCallback('Choroid Measure OpenCV',draw_lines)

    while(1):
        cv2.imshow('Choroid Measure OpenCV',image)
        k=cv2.waitKey(1)&0xFF
        if k==27:

            break

    # Wait for a key press
    cv2.waitKey(0)

    # Close the window
    cv2.destroyAllWindows()

    # Get file name
    file_name = os.path.basename(imagepath)
    file_name_without_extension = os.path.splitext(file_name)[0]
    
    # Get file directory
    directory = "annotated_images/"
    
    # Get original file name
    original_file_name = os.path.basename(original_filepath)
    original_file_name_without_extension = os.path.splitext(original_file_name)[0] 

    new_image_path = directory + original_file_name_without_extension + "_" +file_name_without_extension + "_annotated.png"
    cv2.imwrite(new_image_path, image)
    
    print("Annotated file name:", new_image_path)
    
    print("🎉 Your anotated image has been saved!")


# +
def get_coordinates_of_pixels(image, target_color):
    coordinates = []

    # Get the shape of the image
#     image_shape = image.shape
    height, width, _ = image.shape

    min_y_coordinates = [height] * width
    max_y_coordinates = [0] * width

    for x in range(width):
        for y in range(height):
            # Get the color of the pixel at the current coordinates
            pixel_color = image[y, x]
            
            # Check if the pixel color matches the target color
            if np.array_equal(pixel_color, target_color):
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                min_y_coordinates[x] = min(min_y_coordinates[x], y)
                max_y_coordinates[x] = max(max_y_coordinates[x], y)

    return coordinates, min_y_coordinates, max_y_coordinates


def analysis():
    
    imagepath = getImage("annotated_images/")
    
    image = cv2.imread(imagepath)
    height, width, _ = image.shape
    print("Height of image is", height)
    print("Width of image is", width)
    target_color = (0, 0, 255)

    coordinates, min_y_coordinates, max_y_coordinates = get_coordinates_of_pixels(image, target_color)
    # print("Coordinates of pixels with color", target_color, ":", coordinates)

    # for x in range(width):
    #     print("For X coordinate", x, ":")
    #     print("Minimum Y coordinate:", min_y_coordinates[x])
    #     print("Maximum Y coordinate:", max_y_coordinates[x])

    y_diffs = [max_y_coordinates[x] - min_y_coordinates[x] for x in range(width)]

    # print("Differences between Min and Max Y coordinates for each X coordinate:", y_diffs)

    # Convert the list to a DataFrame
    df = pd.DataFrame(y_diffs, columns=['Pixel Thickness'])
    
    # Get file name
    file_name = os.path.basename(imagepath)
    file_name_without_extension = os.path.splitext(file_name)[0]

    # Add "_analysis" to the file name
    csv_file_name = "csv_data/" + file_name_without_extension + "_analysis.csv"

    print("CSV file name:", csv_file_name)

    # Save the DataFrame as a CSV file
    df.to_csv(csv_file_name, index=False)

    print("🎉 Your analysis file has been saved!")


# -
def getTS():

    #calculations based on Bennett and Rabbetts 3-surface schematic eye

    #user needs to input corneal radius, anterior chamber depth (ACD), lens thickness (LT), and axial length (AL)
    #these values will be provided from the LenStar
    
    corneaRadBoolean = input("Is Corneal Radius provided by the Instrument? Type y/n")
    
    if corneaRadBoolean == 'y':
        corneaRad = float(input('Please type the corneal radius: '))
#         corneaRad = 7.8

    else:
        corneaCurvature = float(input('Please type the corneal curvature: '))
        corneaRad = 337.5/corneaCurvature
        
    ACD = float(input("Please type the anterior chamber depth (ACD): "))
    LT = float(input("Please type the lens thickness (LT): "))
    AL = float(input("Please type the axial length (AL): "))

    #corneaRad = 337.5/corneaCurvature 
    #above equation is to convert corneal curvature (in diopters) to corneal radius (in mm)
    #if the LenStar provides corneal curvature, we will need to convert it into corneal radius for the equations below
#     ACD = 3.6
#     LT = 3.7
#     AL = 24.09

    #lens radius, based on Bennett and Rabbetts schematic emmetropic eye model
    #LenStar does not provide lens curvature, so it can only be estimated 
    antLensRad = 11
    posLensRad = -6.47515

    #refractive indices, these values do not change
    n1 = 1 #air
    n2 = 1.336 #aqueous humor
    n3 = 1.422 #equivalent lens 
    n4 = 1.336 #vitreous humor

    #surface powers
    F1 =(1000*(n2-n1))/corneaRad #cornea power
    F2 =(1000*(n3-n2))/antLensRad #anterior lens power
    F3 = (1000*(n4-n3))/posLensRad #posterior lens power

    FL = F2+F3-((LT*F2*F3)/(1000*n3)) #lens equivalent power

    #lens principal points
    A2P2 = (n2*LT*F3)/(n3*FL) #e2
    A3Pp2 = -(n4*LT*F2)/(n3*FL) #e'2

    F0 = F1+FL-(((ACD+A2P2)*F1*FL)/(1000*n2)) #eye equivalent power

    #focal lengths of the eye
    f0 = -1000*n1/F0
    f1 = 1000*n4/F0

    #eye's principal points
    Pp2Pp = -(n4*(ACD+A2P2)*F1)/(n2*F0) #e'
    A1Pp = ACD+LT+A3Pp2+Pp2Pp

    A1Np = A1Pp+f1+f0 #second nodal point

    NpFp = AL-A1Np #second nodal point to back of the eye

    RS = np.pi/180*NpFp*1000 #retinal scaling in microns/deg
    TS = RS/(1536/30) #transverse scaling in microns/pixel

    return TS

