# +
# Input first the TS parameters
# TS = getTS()

# Pseudo
TS = 0.012007717043161392
# -

filepath = extract()

# +
# Set starting color as green
color = top_color

annotate(filepath)
# -

analyze(filepath)

import cv2
import numpy as np
import pandas as pd
import os
from PIL import Image
import heyexReader
import time
import shutil
import numpy as np

# Persistent variables
datafolder = "data"
tempfolder = "temp_data"
annotatedfolder = "annotated_images"
csvfolder = "csv_data"
filepath = ""
TS = 0


def extract():
    directory = getFolderContent(datafolder)
    
    filepath = getFolderContent(directory)
    
    loadImagesInFolder(filepath)

    return filepath


def annotate(filepath):
    number_of_files_in_folder = len(os.listdir(tempfolder))
    
    number_of_files = input(f'Do you want to analyze ALL {number_of_files_in_folder} files? y/n: ')
    
    contents = showFolderContents(tempfolder)
    
    deleteFolderContent(annotatedfolder)
    
    if number_of_files == 'y':
        
        # Analyze all images
        for i in range(0,number_of_files_in_folder):
            [image, imagepath] = extractImage(i, contents, tempfolder)
            
            if i == 0:
                drawInstructions()

            draw(image, imagepath, filepath, top_color, bottom_color)
        
        print("\n🎉🎉🎉 All images have been analyzed!")
        
    else: 
        user_selection = input('Indicate which image you want to analyze: ')
        
        [image, imagepath] = extractImage(int(user_selection), contents, tempfolder)
        
        drawInstructions()

        draw(image, imagepath, filepath, top_color, bottom_color)


def analyze(filepath):
    number_of_files_in_folder = len(os.listdir(annotatedfolder))
    
    number_of_files = input(f'Do you want to analyze ALL {number_of_files_in_folder} files? y/n: ')
    
    contents = showFolderContents(annotatedfolder)
    
    deleteFolderContent(csvfolder)
    
    if number_of_files == 'y':
        
        # Create an empty dataframe before the loop
        combined_dataframe = pd.DataFrame()
        
        # Analyze all images
        for i in range(0, number_of_files_in_folder):
            [file, imagepath] = extractImage(i, contents, annotatedfolder)
                        
            pixeldata, rpe_line = analysis(imagepath)
    
            data = createDataFrame(pixeldata, rpe_line, filepath)
        
            # Append the data to the combined_dataframe
            combined_dataframe = pd.concat([combined_dataframe, data], axis=1, ignore_index=True)

        print("\n🎉🎉🎉 All images have been analyzed!")
        
    else: 
        imagepath = getFolderContent(annotatedfolder)
        
        pixeldata, rpe_line = analysis(imagepath)

        combined_dataframe = createDataFrame(pixeldata, rpe_line, filepath)
        
    createCSV(combined_dataframe, filepath)


def getFolderContent(directory):
    print(f'Here is a list of folders in the {directory} directory')
    
    entries = showFolderContents(directory)
    
    time.sleep(0.2)
    
    user_selection = input('Indicate which file/folder you want to open: ')
        
    folder = entries[int(user_selection)]
    
    # Get the base name of the file
#     file_name = os.path.basename(image_path)
#     directory = os.path.dirname(image_path)
    
    path = directory + '/' + folder
    
    return path 


def deleteFolderContent(directory):
    # Delete everything in folder
    for f in os.listdir(directory):
        os.remove(os.path.join(directory, f))


def loadImagesInFolder(filepath):
    
    vol = heyexReader.volFile(filepath)

    vol.renderIRslo("slo.png", renderGrid = True)
    vol.renderOCTscans("oct", renderSeg = True)
    scaleX = vol.fileHeader['scaleX']
    scaleZ = vol.fileHeader['scaleZ']
    
    print("\nThis is the scaleX from the Heidelberg measurement", scaleX)
    print("This is the scaleZ from the Heidelberg measurement", scaleZ)
#     print(vol.oct.shape)
#     print(vol.irslo.shape)
    
    image_file = vol.oct
    
    deleteFolderContent(tempfolder)
            
    for i in range(0, 6):
        try:
            source_file = f"oct-00{i}.png"  # Replace "image{i}.png" with the actual filename pattern of your generated PNG files
            shutil.move(source_file, tempfolder)
        except FileNotFoundError:
#             print(f"File 'oct-00{i}.png' does not exist")
            break    
    
    # Get file name
    filename = os.path.basename(filepath)
    
    print(f"\nThe file {filename} will be extracted into individual images...")
    
    print(f"🎉 The images have been extracted into /{tempfolder}")


def showFolderContents(selectedfolder):

    entries = os.listdir(selectedfolder)
    counter = 0
    for entry in entries:
        print('[{}] {}'.format(counter, entry))
        counter += 1
    
    return entries


# +
# imagepath = 'temp_data/oct-001.png'
# image = cv2.imread(imagepath)
# print(image.shape, image.dtype)

# # b, g, r = cv2.split(image)
# # rgb_image = cv2.merge([b, g, r])
# print(image)
# # cv2.imshow("RGB Image", image)

# # Extract the desired channel
# channel_index = 2  # Replace 0 with the index of the channel you want to view
# channel_image = rgb_image[:, :, channel_index]

# print(channel_image.shape,channel_image.dtype)

# # Display the channel image
# # Assuming the image is in BGR format
# # cv2.imshow("RGB Image", channel_image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# -

def extractImage(user_selection, entries, folder):
        
    image = entries[int(user_selection)]
    
    imagepath = folder + '/'+ image
    
    return image, imagepath


def drawInstructions():
    
    print("⏲️ A window will open in a couple of seconds...")

    time.sleep(1)

    print("Window loaded!")

    time.sleep(0.2)

    print("💡 To change color to blue Right-click on your mouse")

    time.sleep(0.2)

    print("⚠️ When you are finished, press the 'Esc' button in your keyboard 2x to save the image")


# +
drawing=False # true if mouse is pressed
top_color = (0, 255, 0) # Green color for the RPE
bottom_color = (255, 255, 0) # Yellow color for the CSI
color = top_color  # Start with the top layer color
brush_size = 1

def draw(image, imagepath, original_filepath, top_color, bottom_color):

    drawing=False # true if mouse is pressed
    top_color = top_color
    bottom_color = bottom_color
    
    color = top_color  # Start with the top layer color

    image = cv2.imread(imagepath)
    
        # Add transparent layer to image
#     transparent_image = np.zeros_like(image, dtype=np.uint8)
#     overlay = image.copy()
#     alpha = 0.2  # Opacity of the rectangle (adjust as needed)
#     print(image.shape)
#     cv2.rectangle(overlay, (0, 0), (image.shape[1], image.shape[0]), (255, 255, 255), -1)  # Draw the rectangle on the overlay
#     image = cv2.addWeighted(overlay, alpha, image, 1, 0)
    
    def draw_lines(event, former_x, former_y, flags, param):

        global current_former_x, current_former_y, drawing, mode, color

        if event==cv2.EVENT_LBUTTONDOWN:
            drawing=True
            current_former_x,current_former_y=former_x,former_y

        elif event==cv2.EVENT_MOUSEMOVE:
            if drawing==True:
                if former_x <= 0 or former_x >= image.shape[1]-1 or former_y <= 0 or former_y >= image.shape[0]-1:
                    drawing = False
                else:
                    cv2.line(image, (current_former_x, current_former_y), (former_x, former_y), color, brush_size)
                    current_former_x = former_x
                    current_former_y = former_y
                        
        elif event==cv2.EVENT_LBUTTONUP:
            drawing=False
            cv2.line(image,(current_former_x,current_former_y),(former_x,former_y), color, brush_size)
            current_former_x = former_x
            current_former_y = former_y
                
        elif event==cv2.EVENT_RBUTTONDOWN:
            if color == bottom_color:
                print('switching color to green')
                color = top_color  # switch to green
            else:
                print('switching color to blue')
                color = bottom_color  # switch back to blue
                
            # Overwrite previous display
            cv2.line(image, (image.shape[1] - 100, 30), (image.shape[1], 30), (0,0,0), 100)
            # Update color selection
            indicateActiveColor(color)

        return former_x, former_y, color   
    
    def indicateActiveColor(color):
        # Color for the text
        text_color = (255, 255, 255)  # white

        # Define the position for the text overlay
        text_position = (image.shape[1] - 300, 30)

        color_info = "Active Color: "
        if color == top_color:
            color_info += "Green"
        elif color == bottom_color:
            color_info += "Blue"

        # Overwrite previous display
        cv2.putText(image, color_info, text_position, cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2, cv2.LINE_AA)

    # Add indicator of active color to the image
    # Set the starting color to red
    indicateActiveColor(color)
    
    cv2.namedWindow("Choroid Measure OpenCV")
    cv2.setMouseCallback('Choroid Measure OpenCV',draw_lines)
    
    while(1):
        cv2.imshow('Choroid Measure OpenCV',image)
        k=cv2.waitKey(1) & 0xFF
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
def get_coordinates_of_pixels(image):
    
    # Format should be like this
#     bottom_color = red
#     top_color = green
    
    coordinates = []

    # Get the shape of the image
#     image_shape = image.shape
    height, width, _ = image.shape

    min_y_coordinates = [height] * width
    max_y_coordinates = [0] * width
    
    add_y_value_for_missing_x_coordinate = True

    for x in range(width):
        for y in range(height):
            # Get the color of the pixel at the current coordinates
            pixel_color = image[y, x]
            
            # Check if the pixel color matches the target color
            if np.array_equal(pixel_color, top_color) or np.array_equal(pixel_color, bottom_color):
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                if np.array_equal(pixel_color, bottom_color):
                    max_y_coordinates.append(max(max_y_coordinates[x], y))
                elif np.array_equal(pixel_color, top_color):
                    min_y_coordinates.append(min(min_y_coordinates[x], y))
                    
                add_y_value_for_missing_x_coordinate = False
                    
        if add_y_value_for_missing_x_coordinate:
            max_y_coordinates.append(0)
            min_y_coordinates.append(0)
        
        add_y_value_for_missing_x_coordinate = True

    return coordinates, min_y_coordinates, max_y_coordinates


def analysis(imagepath):
    image = cv2.imread(imagepath)
    height, width, _ = image.shape
    print("Height of image is", height)
    print("Width of image is", width)
    bottom_color = (0, 0, 255)
    top_color = (0, 255, 0)

#     coordinates, min_y_coordinates, max_y_coordinates = get_coordinates_of_pixels(image)

#     y_diffs = [max_y_coordinates[x] - min_y_coordinates[x] for x in range(width)]

    r_line_coordinates, rpe_line_y_values = getRPE(image)
    
    ogtopcoords, ogtop_choroid_y_value = getOriginalChoroidLine(image)
    
    topcoords, top_choroid_y_value = getTopChoroidLine(image)
    
    bcoords, bottom_choroid_y_value = getBottomChoroidLine(image)
    
    # Compute differences in coordinates from top to bottom
    y_diffs = [bottom_choroid_y_value[x] - top_choroid_y_value[x] for x in range(width)]
    
    r_line_coordinates, rpe_line_y_values = getRPE(image)
    
    fovea_index = findFovea(rpe_line_y_values)
    
    window_size = int(input("What's your desired window size in mm?: "))
    
    start_index, end_index = selectWindowSize(window_size, fovea_index, image)
    
    # Compute only the selected window
    window_rpe_line_y_values = rpe_line_y_values[start_index: end_index]
    
    window_size_scaled = end_index - start_index
    
    # Compute differences in coordinates from top to bottom
    y_diffs = [bottom_choroid_y_value[start_index:end_index][x] - top_choroid_y_value[start_index:end_index][x] for x in range(window_size_scaled)]
        
    return y_diffs, window_rpe_line_y_values


# -
# Find the Min of the RPE Line
def findFovea(array):
    minimum = np.max(array)
    indices = np.where(array == minimum)[0]
    middle_index = indices[len(indices) // 2]
    
    print("Middle index:", middle_index)
    
    return middle_index


# window_size : in millimiters
def selectWindowSize(window_size, fovea_index, image):
    
    height, width, _ = image.shape
    
    real_x_size = width * TS
    print(real_x_size)
    
    total_pixels_needed = (window_size * width) / real_x_size
    
    # Calculate how many pixels in each direction are needed
    start_index = int(fovea_index - total_pixels_needed / 2)
    end_index = int(fovea_index + total_pixels_needed / 2)
    
    # Fail safe if numbers are beyond size of image
    if start_index < 0:
        start_index = 0
    
    if end_index > width:
        end_index = width
    
    
    return start_index, end_index


# +
# imagepath = 'annotated_images/TEST_T_2713_oct-003_annotated.png'
# image = cv2.imread(imagepath)
# print(image.shape)
# [coord, y_values] = getOriginalChoroidLine(image)
# print(y_values)
# print(image)
# cv2.imshow('Choroid Measure OpenCV',image)
# # Wait for a key press
# cv2.waitKey(0)

# # # Close the window
# cv2.destroyAllWindows()
# -

def getRPE(image):
    coordinates = []
    y_values = []

    # Get the shape of the image
    height, width, _ = image.shape

    min_y_coordinates = [height] * width
    max_y_coordinates = [0] * width
    
    add_y_value_for_missing_x_coordinate = True

    for x in range(width):
        for y in range(height):
            # Get the color of the pixel at the current coordinates
            pixel_color = image[y, x]
            
            if (pixel_color[2] == 255 and (pixel_color[2] > pixel_color[0]) and (pixel_color[2] > pixel_color[1])):
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                
                # Should I add a break here since it already found the coordinate to make it faster?
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True
        
        # Validation is that there should be exactly the width-of-the-image in pixels

    return coordinates, y_values


def getOriginalChoroidLine(image):
    coordinates = []
    y_values = []

    # Get the shape of the image
    height, width, _ = image.shape

    min_y_coordinates = [height] * width
    max_y_coordinates = [0] * width
    
    add_y_value_for_missing_x_coordinate = True

    for x in range(width):
        for y in range(height):
            # Get the color of the pixel at the current coordinates
            pixel_color = image[y, x]

            # Avoid the same green color that we draw manually
            if pixel_color[1] == 255 and np.not_equal(pixel_color, top_color).any() and np.not_equal(pixel_color, bottom_color).any():
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                break
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True

    return coordinates, y_values


def getTopChoroidLine(image):
    coordinates = []
    y_values = []

    # Get the shape of the image
    height, width, _ = image.shape

    min_y_coordinates = [height] * width
    max_y_coordinates = [0] * width
    
    add_y_value_for_missing_x_coordinate = True

    for x in range(width):
        for y in range(height):
            # Get the color of the pixel at the current coordinates
            pixel_color = image[y, x]
            
            # Avoid the same green color that we draw manually
            if np.equal(pixel_color, top_color).all():
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                break
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True

    return coordinates, y_values


def getBottomChoroidLine(image):
    coordinates = []
    y_values = []

    # Get the shape of the image
    height, width, _ = image.shape

    min_y_coordinates = [height] * width
    max_y_coordinates = [0] * width
    
    add_y_value_for_missing_x_coordinate = True

    for x in range(width):
        for y in range(height):
            # Get the color of the pixel at the current coordinates
            pixel_color = image[y, x]
            
            # Avoid the same green color that we draw manually
            if np.equal(pixel_color, bottom_color).all():
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                break
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True

    return coordinates, y_values


def createDataFrame(choroid_top_line, rpe_line, filepath):
    filename = os.path.basename(filepath)
    
    # Convert the list to a DataFrame
    df = pd.DataFrame()
    
    df['RPE Coordinates'] = rpe_line
    df['Top Choroid Coordinates'] = choroid_top_line
    
    return df


def appendToDataFrame(df1, df2):
    
    combined_dataframe = pd.concat([df1, df2], axis=1)
    
    return combined_dataframe


def createCSV(dataframe, imagepath):
    # Get file name
    file_name = os.path.basename(imagepath)
    file_name_without_extension = os.path.splitext(file_name)[0]

    # Add "_analysis" to the file name
    csv_file_name = "csv_data/" + file_name_without_extension + "_analysis.csv"

    print("CSV file name:", csv_file_name)

    # Save the DataFrame as a CSV file
    dataframe.to_csv(csv_file_name, index=False)

    print("🎉 Your analysis file has been saved!")


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


# +
# The TS defines the amount of pixels we want to grab in X direction to compute the Thickness

# Enhanced Early Diabetic Something defines the regions where you want to calculate thickness from

# Take deepest point of the fovea and take a 1mm, 3mm, 6mm diameter going to the sides of the fovea
# We might want to get donuts outside of the center
# We are unsure how the VR will work

# Edit the original Heidelberg lines
# Use the Heidelberg lines for analysis

# Display all pixel thicknesses in the same file
# Display the 1mm, 3mm, 6mm

