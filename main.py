# +
# Input first the TS parameters
# TS = getTS()

# Pseudo
TS = 0.012007717043161392
# -

filepath = extract()

data = annotate(filepath)

analyze(filepath, data)                                                  

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
top_color = (0, 255, 0) # Green color for the RPE
bottom_color = (255, 255, 0) # Blue color for the CSI
color = top_color  # Start with the top layer color
window_size = 0
original_image_width = 0
window_sizes = [1,3,6]
data_arrays = []
thickness_multiplier = 3.87
aspect_ratio = 1


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

            rpe_array, sci_array = draw(imagepath, filepath, top_color, bottom_color, number_of_files_in_folder, i)
            
            # Add data to the dictionary and to function return
            image_data = {'image_code': image, 'rpe': rpe_array, 'sci': sci_array}
            data_arrays.append(image_data)
                    
        print("\n🎉🎉🎉 All images have been analyzed!")
        
    else: 
        user_selection = input('Indicate which image you want to analyze: ')
        
        [image, imagepath] = extractImage(int(user_selection), contents, tempfolder)
        
        drawInstructions()

        rpe_array, sci_array = draw(imagepath, filepath, top_color, bottom_color, 1, 0)
        
        # Add data to the dictionary and to function return
        image_data = {'image_code': image, 'rpe': rpe_array, 'sci': sci_array}
        data_arrays.append(image_data)
        
    return data_arrays


def analyze(filepath, previous_data = []):
    global window_size
    
    number_of_files_in_folder = len(os.listdir(annotatedfolder))
    
    number_of_files = input(f'Do you want to analyze ALL {number_of_files_in_folder} files? y/n: ')
    
    contents = showFolderContents(annotatedfolder)
    
    # deleteFolderContent(csvfolder)
    
    dataframes = []
    
    if number_of_files == 'y':

        # Analyze all images
        for i in range(0, number_of_files_in_folder):
            [file, imagepath] = extractImage(i, contents, annotatedfolder)

            # -> Get retina line & fovea position
            print(f"Locating Retina layer for {imagepath}")
            image = cv2.imread(imagepath)
            _, retina_y_values = getRetina(image)

            # -> Add retina & fovea position to dictionary
            index = findDataArrayElement(data_arrays, imagepath)
            data_arrays[index]["retina"] = retina_y_values
            data_arrays[index]["fovea"] = findFovea(retina_y_values)

            if not previous_data:
                # -> Add choroid & retina to dictionary
                # ⚠️ NEEDS TESTING OF ANALYSIS FUNCTION ⚠️

                print("Running general analysis with new image")
                rpe_line, sci_line, retina_line = analysis(imagepath)
                data_arrays[index]["rpe"] = rpe_line
                data_arrays[index]["sci"] = sci_line
        
        # -> raw
        # -> loop through dictionary
        
        # -> window sizes
        for window in window_sizes:
            window_size = window
            print(f"Analyzing at {window_size} mm")
            
            # Create an empty dataframe before the loop
            combined_dataframe = pd.DataFrame()

            # -> loop through dictionary
            for entry in data_arrays:
                retina_line, choroid_thickness = getEyeParametersFromDictionary(entry)

                data = createDataFrame(choroid_thickness, retina_line, entry['image_code'])

                # Append the data to the combined_dataframe
                combined_dataframe = pd.concat([combined_dataframe, data], axis=1)

            dataframes.append(combined_dataframe)

        print("\n🎉🎉🎉 All images have been analyzed!")
        
    else: 
        imagepath = getFolderContent(annotatedfolder)
        
        # -> Get retina line
        print(f"Locating Retina layer for {imagepath}")
        image = cv2.imread(imagepath)
        _, retina_y_values = getRetina(image)
        
        # -> Add retina & fovea position to dictionary
        index = findDataArrayElement(data_arrays, imagepath)
        data_arrays[index]["retina"] = retina_y_values
        data_arrays[index]["fovea"] = findFovea(retina_y_values)
        
        if not previous_data:
            print("Running general analysis with new image")
            # ⚠️ NEEDS TESTING OF ANALYSIS FUNCTION ⚠️
            rpe_line, sci_line, retina_line = analysis(imagepath)
            data_arrays[index]["rpe"] = rpe_line
            data_arrays[index]["sci"] = sci_line

        for window in window_sizes:
            window_size = window
            print(f"Analyzing at {window_size} mm")
                
            retina_line, choroid_thickness = getEyeParametersFromDictionary(data_arrays[index])

            combined_dataframe = createDataFrame(choroid_thickness, retina_line, filepath)
            
            dataframes.append(combined_dataframe)
    
    # Add Raw data
    combined_dataframe = pd.DataFrame()
    
    for entry in data_arrays:
        choroid_thickness = [entry['sci'][x] - entry['rpe'][x] for x in range(0, original_image_width)]
        
        data = createDataFrame(choroid_thickness, entry['retina'], entry['image_code'])
        
        combined_dataframe = pd.concat([combined_dataframe, data], axis=1)
        
    dataframes.append(combined_dataframe)
                    
    createExcel(dataframes, filepath)


# # Heyex Analysis

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


# # Folder handling: find, retrieve, return

def showFolderContents(selectedfolder):

    entries = os.listdir(selectedfolder)
    counter = 0
    for entry in entries:
        print('[{}] {}'.format(counter, entry))
        counter += 1
    
    return entries


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


def extractImage(user_selection, entries, folder):
        
    image = entries[int(user_selection)]
    
    imagepath = folder + '/'+ image
    
    return image, imagepath


def deleteFolderContent(directory):
    # Delete everything in folder
    for f in os.listdir(directory):
        os.remove(os.path.join(directory, f))


# # Draw Functions

def drawInstructions():
    
    print("⏲️ A window will open in a couple of seconds...")

    time.sleep(1)

    print("Window loaded!")

    time.sleep(0.2)

    print("💡 To change color Right-click on your mouse")

    time.sleep(0.2)

    print("⚠️ When you are finished, press the 'Esc' button in your keyboard 2x to save the image")


# +
drawing=False # true if mouse is pressed
top_color = (0, 255, 0) # Green color for the RPE
bottom_color = (255, 255, 0) # Blue color for the CSI
fovea_color = (0, 255, 255) # _ color for the Fovea
colors = [top_color, bottom_color, fovea_color]
color = top_color  # Start with the top layer color
color_index = 0
brush_size = 1
# Create Array for y-coordinate pixels
choroid_sclera_coordinates = []
rpe_coordinates = []

def draw(imagepath, original_filepath, top_color, bottom_color, image_set, image_pos):
    global original_image_width, choroid_sclera_coordinates, rpe_coordinates, aspect_ratio
    
    drawing=False # true if mouse is pressed
    top_color = top_color
    bottom_color = bottom_color
    
    # Initialize the index
    color_index = 0

    im = cv2.imread(imagepath)
    
    # Get original image width and store in variable
    original_image_width = im.shape[1]
    
    aspect_ratio = original_image_width // im.shape[0]
    
    image = cv2.resize(im, (original_image_width, im.shape[0] * aspect_ratio))  
    
    # Create Array for y-coordinate pixels
    choroid_sclera_coordinates = [0] * image.shape[1]
    rpe_coordinates = [0] * image.shape[1]
    
    # Replace with new coordinates
    _, rpe_coordinates = getOriginalRPELine(image)
    
    #####
    
    
    # ⚠️ This line replaces the original RPE line, to verify with Linjiang
    redrawOriginalRPE(image, rpe_coordinates)
    
    
    #####
    
    def draw_lines(event, former_x, former_y, flags, param):

        global current_former_x, current_former_y, drawing, mode, color, color_index, brush_size

        if event==cv2.EVENT_LBUTTONDOWN:
            drawing=True
            current_former_x,current_former_y=former_x,former_y

        elif event==cv2.EVENT_MOUSEMOVE:
            if drawing==True:
                if former_x <= 0 or former_x >= image.shape[1]-1 or former_y <= 0 or former_y >= image.shape[0]-1:
                    drawing = False
                else:
                    if former_x > current_former_x:
                        # This only works if we go left to right
                        drawPoint(image, current_former_x, former_x, former_y, color)

                        current_former_x = former_x
                        current_former_y = former_y


        elif event==cv2.EVENT_LBUTTONUP:
            drawing=False
            if color_index == 2:
                cv2.circle(image, (former_x, former_y), 5, color, -1)
                
        elif event==cv2.EVENT_RBUTTONDOWN:
            # Increment the index
            color_index += 1

            # If the index is at the end of the list, reset it to 0
            if color_index == len(colors):
                color_index = 0
                
            if color_index == 2:
                brush_size = 5
            else:
                brush_size = 0

            # Get the next color from the list
            color = colors[color_index]

#             print('Switching color to', color)
                
            # Overwrite previous display
            cv2.line(image, (image.shape[1] - 150, 30), (image.shape[1], 30), (0,0,0), 60)
            # Update color selection
            indicateActiveColor(color)

        return former_x, former_y, color    
    
    def indicateActiveColor(color):
        # Color for the text
        text_color = (255, 255, 255)  # white

        # Define the position for the text overlay
        text_position = (image.shape[1] - 350, 30)

        color_info = "Active Color: "
        if color == top_color:
            color_info += "Green"
        elif color == bottom_color:
            color_info += "Blue"
        elif color == fovea_color:
            color_info += "Yellow"

        # Overwrite previous display
        cv2.putText(image, color_info, text_position, cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2, cv2.LINE_AA)
    
    def indicateImageNumber(image_set, image_pos):
        # Color for the text
        text_color = (255, 255, 255)  # white

        # Define the position for the text overlay
        text_position = (image.shape[1] - 350, 80)

        image_info = f"Image {image_pos+1}/{image_set}"

        # Overwrite previous display
        cv2.putText(image, image_info, text_position, cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2, cv2.LINE_AA)
        
    def drawPoint(image, current_former_x, former_x, former_y, color):
    
        global choroid_sclera_coordinates, rpe_coordinates

        for x_pixels in range(current_former_x, former_x+1):
            pix_color = image[former_y, x_pixels]
            
            if color == top_color:
                add_color =(int(pix_color[0]), 255, int(pix_color[0]))

                # Erase Method
                if rpe_coordinates[x_pixels] != 0:
                    original_pixel = image[rpe_coordinates[x_pixels],x_pixels]
    
#                     print("erasing!")
                    old_color = (int(original_pixel[0]), int(original_pixel[0]), int(original_pixel[0]))
                    cv2.circle(image, (x_pixels, rpe_coordinates[x_pixels]), 0, old_color, -1)

                rpe_coordinates[x_pixels] = former_y

                cv2.circle(image, (x_pixels, rpe_coordinates[x_pixels]), 0, add_color, -1)
            elif color == bottom_color: 
                add_color =(255, 255, int(pix_color[2]))

                # Erase Method
                if choroid_sclera_coordinates[x_pixels] != 0:
                    original_pixel = image[choroid_sclera_coordinates[x_pixels],x_pixels]

                    old_color = (int(original_pixel[2]), int(original_pixel[2]), int(original_pixel[2]))
                    cv2.circle(image, (x_pixels, choroid_sclera_coordinates[x_pixels]), 0, old_color, -1)

                choroid_sclera_coordinates[x_pixels] = former_y

                cv2.circle(image, (x_pixels, choroid_sclera_coordinates[x_pixels]), 0, add_color, -1)
#             else:
#                 add_color =(int(pix_color[0]), 255, 255)
#                 cv2.circle(image, (x_pixels, former_y), 5, add_color, -1)
                

    # Add indicator of active color to the image
    # Set the starting color to red
    indicateActiveColor(color)
    indicateImageNumber(image_set, image_pos)
    
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
    
    return rpe_coordinates, choroid_sclera_coordinates


# -

def redrawOriginalRPE(image, rpe_coordinates):
    for i in range(0, len(rpe_coordinates)):
        pixel_y_position = rpe_coordinates[i]

        # Range is 7 because that seems to be the size of the effect
        for j in range(0,7):
            pixel_color = image[pixel_y_position+j, i]
            old_color = (int(pixel_color[0]), int(pixel_color[0]), int(pixel_color[0]))

            if j == 2:
                add_color =(int(pixel_color[0]), 255, int(pixel_color[0]))

            cv2.circle(image, (i, pixel_y_position+j), 0, old_color, -1)

        # Redraw with full color
        cv2.circle(image, (i, pixel_y_position+2), 0, add_color, -1)
        rpe_coordinates[i] = pixel_y_position+2


# # Analysis

# +
# 🤔 (TBD)
def analysis(imagepath):
    image = cv2.imread(imagepath)
    height, width, _ = image.shape

# ⚠️⚠️⚠️ COLORS NEED TO BE ADJUSTED FOR ONGOING COLORS SINCE IT'S NO LONGER PURE RGB GREEN AND BLUE
    bottom_color = (255, 255, 0)
    top_color = (0, 255, 0)

#     coordinates, min_y_coordinates, max_y_coordinates = get_coordinates_of_pixels(image)

#     y_diffs = [max_y_coordinates[x] - min_y_coordinates[x] for x in range(width)]

    _, retina_y_values = getRetina(image)
    
    _, rpe_y_value = getOriginalRPELine(image)
    
    _, top_choroid_y_value = getChoroidLine(image, top_color)
    
    _, bottom_choroid_y_value = getChoroidLine(image, bottom_color)
    
    # Compute differences in coordinates from top to bottom
    y_diffs = [bottom_choroid_y_value[x] - top_choroid_y_value[x] for x in range(width)]
        
    fovea_index = findFovea(retina_y_values)

    if window_size != 0:
        start_index, end_index = selectWindowSize(window_size, fovea_index, image)
    
        # Compute only the selected window
        window_retina_line_y_values = retina_y_values[start_index: end_index]

        window_size_scaled = end_index - start_index

        # Compute differences in coordinates from top to bottom
        y_diffs = [bottom_choroid_y_value[start_index:end_index][x] - top_choroid_y_value[start_index:end_index][x] for x in range(window_size_scaled)]
    else:
        # Compute differences in coordinates from top to bottom
        y_diffs = [bottom_choroid_y_value[x] - top_choroid_y_value[x] for x in range(width)]
    
    return top_choroid_y_value, bottom_choroid_y_value, window_retina_line_y_values


# -
# # Data Dictionary Handling

# +
def findDataArrayElement(array, target_image_code):

    index = 0
    # Iterate through the list and check the 'name' key in each dictionary
    for i in range(0, len(array)):
        entry_without_extension = array[i]['image_code'][:-4]
        if entry_without_extension in target_image_code:
            print(f"Entry {entry_without_extension}")
            index = i
            break
            
    return index

def getEyeParametersFromDictionary(entry):
    start_index, end_index = selectWindowSize(window_size, entry['fovea'])
    
    # Compute only the selected window
    window_retina_line_y_values = entry['retina'][start_index: end_index]
    
    window_size_scaled = end_index - start_index
    
    # Compute differences in coordinates from top to bottom
    choroid_thickness = [entry['sci'][start_index:end_index][x] - entry['rpe'][start_index:end_index][x] for x in range(window_size_scaled)]
    
    # Multiply it by the pixel_to_thickness multiplier from Heidelberg (see above variable = 3.87) and divide any image correction done
    choroid_thickness_corrected = []
    for pixel_thickness in choroid_thickness:
        choroid_thickness_corrected.append(pixel_thickness * thickness_multiplier / aspect_ratio)
        
    return window_retina_line_y_values, choroid_thickness_corrected


# -

# # Identify window size for analysis

# Find the Min of the RPE Line
def findFovea(array):
    # Ignore 1/4 on each side of the array to count for optic nerve
    start_index = len(array) // 4
    end_index = len(array) - start_index
    short_array = array[start_index:end_index]

    minimum = np.max(short_array)
    indices = np.where(short_array == minimum)[0]
    middle_index = indices[len(indices) // 2] + start_index
    
    print("Fovea x-position: ", middle_index)
    
    return middle_index


# window_size : in millimiters
def selectWindowSize(window_size, fovea_index):
    
    # ⚠️ with different images this may need to be changed
    width = original_image_width
    
    # New TS as computed by the extension of the original image
#     TS_corrected = (TS * original_image_width) / width
    
    real_x_size = original_image_width * TS
    
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


# # Find colored lines in the image

def getRetina(image):
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
            
            # Remove requirement for pure red (0,0,255) 🟥
            if (pixel_color[2] > pixel_color[0]) and (pixel_color[2] > pixel_color[1]) and (pixel_color[0] == pixel_color[1]):
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                
                break
                
                # Should I add a break here since it already found the coordinate to make it faster?
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True
        
        # Validation is that there should be exactly the width-of-the-image in pixels

    return coordinates, y_values


def getOriginalRPELine(image):
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

            # ⚠️👀 Potential for an issue if there is a rogue green pixel somewhere
            
            if pixel_color[0] < pixel_color[1] and pixel_color[2] < pixel_color[1] and pixel_color[0] == pixel_color[2]:
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                break
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True

    return coordinates, y_values

# +
########


# ⚠️ THIS FUNCTION IS INACTIVE UNLESS IT CAN DETECT BLENDED COLORS BETWEEN TARGET COLOR AND BACKGROUND IMAGE COLOR


########
def getChoroidLine(image, line_color):
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
#             if np.equal(pixel_color, line_color).all():
            if detectPixelMatch(pixel_color, line_color):
                # If it matches, add the coordinates to the list
                coordinates.append((x, y))
                y_values.append(y)
                add_y_value_for_missing_x_coordinate = False
                break
        
        if add_y_value_for_missing_x_coordinate:
            y_values.append(0)
        
        add_y_value_for_missing_x_coordinate = True

    return coordinates, y_values


# -

def detectPixelMatch(incoming_pixel, target_color):
    if target_color == top_color:
        # logic for detecting green
        if incoming_pixel[0] == incoming_pixel[2] and incoming_pixel[1] > incoming_pixel[0] and incoming_pixel[1] == 255:
            return true
    elif target_color == bottom_color:
        # logic for detecting blue
        if incoming_pixel[0] == incoming_pixel[1] and incoming_pixel[1] > incoming_pixel[2] and incoming_pixel[1] == 255:
            return true


# # Dataframe generation and saving to a CSV/Excel 

def createDataFrame(choroid_thickness, retina_line, filename):
    # Convert the list to a DataFrame
    df = pd.DataFrame()
    
    df['Retina Coordinates_'+filename] = retina_line
    df['Choroid Thickness_'+filename] = choroid_thickness
    
    return df


def appendToDataFrame(df1, df2):
    
    combined_dataframe = pd.concat([df1, df2], axis=1)
    
    return combined_dataframe


def createCSV(dataframe, imagepath):
    # Get file name
    file_name = os.path.basename(imagepath)
    file_name_without_extension = os.path.splitext(file_name)[0]

    # Add "_analysis" to the file name
    csv_file_name = "csv_data/" + file_name_without_extension + "_analysis_" + str(window_size) + "mm.csv"

    print("CSV file name:", csv_file_name)

    # Save the DataFrame as a CSV file
    dataframe.to_csv(csv_file_name, index=False)

    print("🎉 Your analysis file has been saved!")


def createExcel(dataframes, imagepath):
    # Get file name
    file_name = os.path.basename(imagepath)
    file_name_without_extension = os.path.splitext(file_name)[0]
    
    # Add "_analysis" to the sheet name
    filename = "csv_data/" + file_name_without_extension + "_analysis.xlsx"

    # Create the Excel writer object
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')

    for i, dataframe in enumerate(dataframes[:-1]):
        sheet_name = str(window_sizes[i])+"mm"
        # Write the dataframe to a sheet in the Excel file
        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    
    sheet_name = "Raw Data"
    # Write the dataframe to a sheet in the Excel file
    dataframes[-1].to_excel(writer, sheet_name=sheet_name, index=False)

    # Save the Excel file
    writer.save()

    print("🎉 Your analysis file has been saved!")


# # Get TS Scaling

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


# Add each window size to a separate tab
# Cut out a window size in the red line that avoids optic nerve, it will either be left or right
# Overwrite the green line
# Depth enhanced mode displays the choroid at higher contrast, try to increase contrast of all bottom part of image to analyze

# -
# # (unused) Image handling: Cutting excess & Contrast conversion

def trimmExcessImage(imagepath):
    image = cv2.imread(imagepath)
    
    height, width, _ = image.shape
    
    # Trim 2/4 of the image away 
    start_index = width // 4
    end_index = width - start_index
    
    trimmed_image = image[0:height, start_index:end_index]
    
    return trimmed_image


# +
def contrastConversion():
    # Contrast Testing
    content = getFolderContent(tempfolder)

    # Contrast Testing
    image = cv2.imread(content, cv2.IMREAD_COLOR)
    image = cv2.resize(image, (original_image_width, image.shape[0]))   
    height, width, num_channels = image.shape

    # Pick the lowest point of the fovea to do the contrast conversion
#     coor, y_values = getRPE(image)
#     fovea = max(y_values) 

    # Set coordinates for contrast enhancement
    y_start = 300
    y_end = y_start + 400
    x_start = 0
    x_end = width

    roi = image[y_start:y_end, x_start:x_end]

    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
    roi_enhanced = clahe.apply(roi_gray)

    image[y_start:y_end, x_start:x_end, 0] = roi_enhanced
    image[y_start:y_end, x_start:x_end, 1] = roi_enhanced
    image[y_start:y_end, x_start:x_end, 2] = roi_enhanced

    cv2.imshow('Enhanced Image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
# contrastConversion()


# -


# # Code to make testing easier

def printPixelOnImage(image):
    
    image = cv2.imread("annotated_images/TEST_T_2731_0_oct-000_annotated.png")
    # Callback function to capture mouse events
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            pixel_color = image[y, x]
        elif event == cv2.EVENT_LBUTTONDOWN:
            pixel_color = image[y, x]
            print("Hovered Pixel Color (BGR):", pixel_color)
            print("Coordinate", [x, y])

    # Load the image
    # image = cv2.imread('your_image_path.png')

    # Create a window and set the mouse callback function
    cv2.namedWindow('Image')
    cv2.setMouseCallback('Image', mouse_callback)

    while True:
        cv2.imshow('Image', image)
        key = cv2.waitKey(1)

        # Press 'Esc' to exit
        if key == 27:
            break

    cv2.destroyAllWindows()
# printPixelOnImage(image)

# # Playground

# +
# drawing=False # true if mouse is pressed
# top_color = top_color
# bottom_color = bottom_color

# # Initialize the index
# color_index = 0
# colors = [top_color, bottom_color]

# im = cv2.imread("temp_data/oct-000.png")
# image = cv2.resize(im, (1920, 1080))    

# # Create Array for y-coordinate pixels
# choroid_sclera_coordinates = [0] * image.shape[1]
# rpe_coordinates = [0] * image.shape[1]


# _, rpe_coordinates = getOriginalRPELine(image)

# # ⚠️ TEST IF THIS IS DESIRED!
# redrawOriginalRPE(image, rpe_coordinates)

# def draw_lines(event, former_x, former_y, flags, param):

#     global current_former_x, current_former_y, drawing, mode, color, color_index

#     if event==cv2.EVENT_LBUTTONDOWN:
#         drawing=True
#         current_former_x,current_former_y=former_x,former_y

#     elif event==cv2.EVENT_MOUSEMOVE:
#         if drawing==True:
#             if former_x <= 0 or former_x >= image.shape[1]-1 or former_y <= 0 or former_y >= image.shape[0]-1:
#                 drawing = False
#             else:
#                 if former_x > current_former_x:
#                     # This only works if we go left to right
#                     drawPoint(image, current_former_x, former_x, former_y, color)
            
#                     current_former_x = former_x
#                     current_former_y = former_y
                

#     elif event==cv2.EVENT_LBUTTONUP:
#         drawing=False

#     elif event==cv2.EVENT_RBUTTONDOWN:
#         print(former_y, former_x)
#         print(image[former_y,former_x])
        
#         # Clean up Original RPE
#         # ⚠️ TEST IF THIS IS DESIRED!
# #         redrawOriginalRPE(image, rpe_coordinates)
        
#         # Increment the index
#         color_index += 1

#         # If the index is at the end of the list, reset it to 0
#         if color_index == len(colors):
#             color_index = 0

#         # Get the next color from the list
#         color = colors[color_index]

#         print('Switching color to', color)
# #         print(y_coordinates)

#     return former_x, former_y, color   

# def redrawOriginalRPE(image, rpe_coordinates):
#     for i in range(0, len(rpe_coordinates)):
#         pixel_y_position = rpe_coordinates[i]

#         # Range is 7 because that seems to be the size of the effect
#         for j in range(0,7):
#             pixel_color = image[pixel_y_position+j, i]
#             old_color = (int(pixel_color[0]), int(pixel_color[0]), int(pixel_color[0]))

#             if j == 2:
#                 add_color =(int(pixel_color[0]), 255, int(pixel_color[0]))

#             cv2.circle(image, (i, pixel_y_position+j), 0, old_color, -1)

#         # Redraw with full color
#         cv2.circle(image, (i, pixel_y_position+2), 0, add_color, -1)
#         rpe_coordinates[i] = pixel_y_position+2

# def drawPoint(image, current_former_x, former_x, former_y, color):
    
#     global choroid_sclera_coordinates, rpe_coordinates
    
#     for x_pixels in range(current_former_x, former_x+1):
#         pix_color = image[former_y, x_pixels]
# #                         print(pix_color)
#         if color == top_color:
#             add_color =(int(pix_color[0]), 255, int(pix_color[0]))
            
#             # Erase Method
#             if rpe_coordinates[x_pixels] != 0:
#                 original_pixel = image[rpe_coordinates[x_pixels],x_pixels]
#                 print(original_pixel)
                
#                 old_color = (int(original_pixel[0]), int(original_pixel[0]), int(original_pixel[0]))
#                 cv2.circle(image, (x_pixels, rpe_coordinates[x_pixels]), 0, old_color, -1)

#             rpe_coordinates[x_pixels] = former_y

#             cv2.circle(image, (x_pixels, rpe_coordinates[x_pixels]), 0, add_color, -1)
#         elif color == bottom_color: 
#             add_color =(255, 255, int(pix_color[2]))
            
#             # Erase Method
#             if choroid_sclera_coordinates[x_pixels] != 0:
#                 original_pixel = image[choroid_sclera_coordinates[x_pixels],x_pixels]
                
#                 old_color = (int(original_pixel[2]), int(original_pixel[2]), int(original_pixel[2]))
#                 cv2.circle(image, (x_pixels, choroid_sclera_coordinates[x_pixels]), 0, old_color, -1)

#             choroid_sclera_coordinates[x_pixels] = former_y

#             cv2.circle(image, (x_pixels, choroid_sclera_coordinates[x_pixels]), 0, add_color, -1)
#         else:
#             print("error no color detected")


# cv2.namedWindow("Choroid Measure OpenCV")
# cv2.setMouseCallback('Choroid Measure OpenCV',draw_lines)

# while(1):
#     cv2.imshow('Choroid Measure OpenCV',image)
#     k=cv2.waitKey(1) & 0xFF
#     if k==27:
#         break

# # Wait for a key press
# cv2.waitKey(0)

# # Close the window
# cv2.destroyAllWindows()

# # # Save image
# # cv2.imwrite("temp_data/test.png", image)

# +
# image = cv2.imread("annotated_images/6154_oct-005_annotated.png")
# _, test_val = getChoroidLine(image, bottom_color) # Bottom color no longer exists, we have to define the new logic
# print(len(test_val))
# print(test_val)
# -




