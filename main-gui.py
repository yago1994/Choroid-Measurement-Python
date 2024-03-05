import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Listbox, Button
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import heyexReader
import time
import shutil

# Persistent variables
datafolder = "data"
tempfolder = "temp_data"
annotatedfolder = "annotated_images"
csvfolder = "csv_data"
filepath = ""
TS = None
top_color = (0, 255, 0) # Green color for the RPE
bottom_color = (255, 255, 0) # Blue color for the CSI
color = top_color  # Start with the top layer color
window_size = 0
original_image_width = 0
window_sizes = [1,3,6]
data_arrays = []
thickness_multiplier = 3.87
aspect_ratio = 1

# Define the function to create the main window and its widgets
def create_main_window():
    global window, annotate_btn, analyze_btn

    window = tk.Tk()
    window.title('Choroid Analysis Tool')
    window.geometry("240x220")
    window.resizable(False, False)

    # Add buttons and functionality here
    scaling_btn = tk.Button(window, text="Get Transverse Scaling", command=calculate_TS)
    extract_btn = tk.Button(window, text="Extract Images", command=extract_images)
    annotate_btn = tk.Button(window, text="Annotate Images", command=annotate_images, state=tk.DISABLED)
    analyze_btn = tk.Button(window, text="Analyze Data", command=analyze_images, state=tk.DISABLED)

    # Pack buttons into the window
    scaling_btn.pack(pady=(20, 10)) # Add some padding for better spacing
    extract_btn.pack(pady= 10) 
    annotate_btn.pack(pady=10)
    analyze_btn.pack(pady=(10, 20))

    window.mainloop()

def get_user_input(prompt):
    return simpledialog.askfloat("Input", prompt, parent=window)

def calculate_TS():
    global TS, window

    # Get user input through dialog boxes
    corneaRadBoolean = messagebox.askyesno("Corneal Radius", "Is Corneal Radius provided by the Instrument?", parent=window)

    if corneaRadBoolean:
        corneaRad = get_user_input('Please type the corneal radius: ')
        if corneaRad is None:
            return
    else:
        corneaCurvature = get_user_input('Please type the corneal curvature: ')
        if corneaCurvature is None:
            return
        corneaRad = 337.5 / corneaCurvature
        
    ACD = get_user_input("Please type the anterior chamber depth (ACD): ")
    if ACD is None:
        return
    LT = get_user_input("Please type the lens thickness (LT): ")
    if LT is None:
        return
    AL = get_user_input("Please type the axial length (AL): ")
    if AL is None:
        return

    # Calculation Logic
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

    # Compute TS value and display it
    try:
        TS = RS / (1536 / 30) # Place your calculation logic here
        
        tk.messagebox.showinfo('Result', f'Transverse Scaling (TS) is: {TS}', parent=window)
    except TypeError:
        # Happens when the user closes the dialog or inputs non-numeric value
        tk.messagebox.showerror('Error', 'Invalid input or operation cancelled.', parent=window)

# Functions extract(), annotate(), analyze() need to be adapted to work with Tkinter
def extract_images():
    global filepath

    # Create folder structures for saving files
    createNeededFolders()

    # Ask the user for the directory where the data is located
    directory = filedialog.askopenfilename(
        initialdir=os.getcwd(),  # Start in the current working directory
        title="Select a file",
        filetypes=(("Image files", "*.vol *.png *.jpg *.jpeg"), ("All files", "*.*"))  # Adjust the file types according to your needs
    )
    
    # Check if user canceled the folder selection dialog
    if not directory:
        messagebox.showinfo("Extract", "No folder selected. Operation cancelled.")
        return
    
    # Construct the filepath using the selected directory
    filepath = directory
    
    try:
        # Process of loading the images using heyexReader
        vol = heyexReader.volFile(filepath)

        vol.renderIRslo("slo.png", renderGrid=True)
        vol.renderOCTscans("oct", renderSeg=True)

        print("\nThis is the scaleX from the Heidelberg measurement", vol.fileHeader['scaleX'])
        print("This is the scaleZ from the Heidelberg measurement", vol.fileHeader['scaleZ'])

        # Remove previous images in tempfolder
        deleteFolderContent(tempfolder)

        for i in range(6):
            source_file = f"oct-00{i}.png"  # Replace "image{i}.png" with the actual filename pattern of your generated PNG files
            try:
                shutil.move(source_file, tempfolder)
            except FileNotFoundError:
                print(f"File 'oct-00{i}.png' does not exist or file only has one image")
                break
        
        messagebox.showinfo("Success!", f"🎉 The individual slice images have been extracted into /{tempfolder}")
        
        # Enable other buttons once extraction is complete
        annotate_btn.config(state=tk.NORMAL)
        analyze_btn.config(state=tk.DISABLED)

        return filepath
    
    except Exception as e:
        messagebox.showerror("Extract", f"An error occurred during extraction: {e}")

def deleteFolderContent(directory):
    try:
        # Deleting the contents of the folder
        for f in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, f)):
                os.remove(os.path.join(directory, f))
    except OSError as e:
        messagebox.showerror("Error", f"An error occurred while deleting the contents of {directory}: {e}")

def annotate_images():
    global data_arrays

    # Assume tempfolder is the directory with images to annotate
    number_of_files_in_folder = len(os.listdir(tempfolder))
    
    # Ask user if they want to annotate all files
    annotate_all = messagebox.askyesno(
        "Annotate Images",
        f"Do you want to annotate ALL {number_of_files_in_folder} files?"
    )
    data_arrays = []
    
    contents = showFolderContents(tempfolder)
    deleteFolderContent(annotatedfolder)
    
    if annotate_all:
        # Analyze all images
        for i in range(0, number_of_files_in_folder):
            [image, imagepath] = extractImage(i, contents, tempfolder)
            # ...
            # Invoke your drawing and other processing functions here
            if i == 0:
                drawInstructions()

            print(imagepath)
            print(filepath)
            rpe_array, sci_array = draw(imagepath, filepath, top_color, bottom_color, number_of_files_in_folder, i)
            
            # Add data to the dictionary and to function return
            image_data = {'image_code': image, 'rpe': rpe_array, 'sci': sci_array}
            data_arrays.append(image_data)
            # Note that the actual drawing function will need to remain separate
            # ...

        # print("\n🎉🎉🎉 All images have been annotated!")
        messagebox.showinfo("Success!", f"🎉 The annotated images are available in /{annotatedfolder}")
        
    else:
        annotation_window = tk.Toplevel()  # Create a new window on top of the main window
        annotation_window.title("Select Image to Annotate")
        annotation_window.geometry("240x220")
        annotation_window.resizable(False, False)

        # Get the list of file names in the folder to populate the Listbox
        images_to_select = os.listdir(tempfolder)
        
        # Create Listbox and populate it with the image filenames
        lb_images = Listbox(annotation_window, height=min(10, len(images_to_select)), exportselection=False)
        for image in images_to_select:
            lb_images.insert(tk.END, image)
        lb_images.pack(padx=10, pady=10)

        # Callback function to handle the selection from the Listbox
        def on_image_select():
            selected_indices = lb_images.curselection()  # Get the selected index
            if not selected_indices:  # This is the case when nothing is selected
                tk.messagebox.showwarning("No Selection", "Please select an image.")
                return
            selected_index = selected_indices[0]
            selected_image = lb_images.get(selected_index)
            
            # Now perform the desired action on the selected image
            image_path = os.path.join(tempfolder, selected_image)
            print(f"You selected to annotate: {selected_image} at {image_path}")
            # Call your process function with the selected image path
            # process_selected_image(image_path)

            drawInstructions()
            rpe_array, sci_array = draw(image_path, filepath, top_color, bottom_color, 1, 0)
            
            # Add data to the dictionary and to function return
            image_data = {'image_code': selected_image, 'rpe': rpe_array, 'sci': sci_array}
            data_arrays.append(image_data)
            # ...

            # Close the annotation window after selection is done
            annotation_window.destroy()

            messagebox.showinfo("Success!", f"🎉 The annotated images are available in /{annotatedfolder}")


        # Button to confirm the image selection
        btn_select = Button(annotation_window, text="Annotate Selected Image", command=on_image_select)
        btn_select.pack(pady=10)

    # Enable Analysis button
    analyze_btn.config(state=tk.NORMAL)

        # Ask for specific image to analyze
        # user_selection = simpledialog.askinteger(
        #     "Annotate Image",
        #     "Indicate the number of the image you want to analyze:",
        #     minvalue=0,
        #     maxvalue=number_of_files_in_folder - 1
        # )
        
        # if user_selection is not None:
        #     [image, imagepath] = extractImage(user_selection, contents, tempfolder)
        #     # ...
        #     drawInstructions()

        #     rpe_array, sci_array = draw(imagepath, filepath, top_color, bottom_color, 1, 0)
            
        #     # Add data to the dictionary and to function return
        #     image_data = {'image_code': image, 'rpe': rpe_array, 'sci': sci_array}
        #     data_arrays.append(image_data)
            # ...

# ...
def drawInstructions():
    instructions = (
        "⏲️ A window will open in a couple of seconds...\n"
        "\n"
        "Window loaded!\n"
        "\n"
        "💡 To change color Right-click on your mouse\n"
        "\n"
        "⚠️ When you are finished, press the 'Esc' button in "
        "your keyboard 2x to save the image"
    )
    messagebox.showinfo("Instructions", instructions)

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
    
    aspect_ratio = 2 # original_image_width // im.shape[0]
    
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
            print('Switching color to', color)
            
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
    
    print(f"Annotated file name: {new_image_path}")
    
    # print("🎉 Your anotated image has been saved!")
    
    return rpe_coordinates, choroid_sclera_coordinates


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

def showFolderContents(selectedfolder):
    # You might want to change this function to return just the file names instead of printing them
    # For this example, the function will be left as is
    entries = os.listdir(selectedfolder)
    for counter, entry in enumerate(entries):
        print('[{}] {}'.format(counter, entry))
    return entries

def extractImage(user_selection, entries, folder):
        
    image = entries[int(user_selection)]
    
    imagepath = folder + '/'+ image
    
    return image, imagepath

def deleteFolderContent(directory):
    # Delete everything in folder
    for f in os.listdir(directory):
        os.remove(os.path.join(directory, f))

def analyze_images():
    global window_size, TS
    # GUI components to select files or options for analysis
    # Assume annotatedfolder is the directory with annotated images to analyze
    if TS is None:
        TS_input = get_user_input('Please type the Transverse Scaling factor: ')
        TS = float(TS_input)

    number_of_files_in_folder = len(os.listdir(annotatedfolder))
    
    # Ask user if they want to annotate all files
    # annotate_all = messagebox.askyesno(
    #     "Annotate Images",
    #     f"Do you want to analyze ALL {number_of_files_in_folder} files?"
    # )
    
    contents = showFolderContents(annotatedfolder)
    
    dataframes = []

    # Default to analyze all images
    # Analyze all images
    for i in range(0, number_of_files_in_folder):
        [file, imagepath] = extractImage(i, contents, annotatedfolder)

        # -> Get retina line & fovea position
        print(f"Locating Retina layer for {imagepath}")
        image = cv2.imread(imagepath)
        _, retina_y_values = getRetina(image)

        if not data_arrays:
            # -> Add choroid & retina to dictionary
            # ⚠️ NEEDS TESTING OF ANALYSIS FUNCTION ⚠️
            print("There is no previous data present to carry out the analysis! Please annotate the images first")
            break
            # print("Running general analysis with new image")
            # rpe_line, sci_line, retina_line = analysis(imagepath)
            # data_arrays[index]["rpe"] = rpe_line
            # data_arrays[index]["sci"] = sci_line

        # -> Add retina & fovea position to dictionary
        index = findDataArrayElement(data_arrays, imagepath)
        data_arrays[index]['retina'] = retina_y_values
        data_arrays[index]['fovea'] = findFovea(retina_y_values)
    
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

    # print("\n🎉🎉🎉 All images have been analyzed!")

    messagebox.showinfo("Success!", f"🎉 The analyzed file {os.path.basename(filepath)} is available in /{csvfolder}")

    # if annotate_all:
    #     # Analyze all images
    #     for i in range(0, number_of_files_in_folder):
    #         [file, imagepath] = extractImage(i, contents, annotatedfolder)

    #         # -> Get retina line & fovea position
    #         print(f"Locating Retina layer for {imagepath}")
    #         image = cv2.imread(imagepath)
    #         _, retina_y_values = getRetina(image)

    #         # -> Add retina & fovea position to dictionary
    #         index = findDataArrayElement(data_arrays, imagepath)
    #         data_arrays[index]["retina"] = retina_y_values
    #         data_arrays[index]["fovea"] = findFovea(retina_y_values)

    #         if not data_arrays:
    #             # -> Add choroid & retina to dictionary
    #             # ⚠️ NEEDS TESTING OF ANALYSIS FUNCTION ⚠️
    #             print("There is no previous data present to carry out the analysis! Please annotate the images first")
    #             break
    #             # print("Running general analysis with new image")
    #             # rpe_line, sci_line, retina_line = analysis(imagepath)
    #             # data_arrays[index]["rpe"] = rpe_line
    #             # data_arrays[index]["sci"] = sci_line
        
    #     # -> raw
    #     # -> loop through dictionary
        
    #     # -> window sizes
    #     for window in window_sizes:
    #         window_size = window
    #         print(f"Analyzing at {window_size} mm")
            
    #         # Create an empty dataframe before the loop
    #         combined_dataframe = pd.DataFrame()

    #         # -> loop through dictionary
    #         for entry in data_arrays:
    #             retina_line, choroid_thickness = getEyeParametersFromDictionary(entry)

    #             data = createDataFrame(choroid_thickness, retina_line, entry['image_code'])

    #             # Append the data to the combined_dataframe
    #             combined_dataframe = pd.concat([combined_dataframe, data], axis=1)

    #         dataframes.append(combined_dataframe)

    #     print("\n🎉🎉🎉 All images have been analyzed!")
        
    # else: 
    #     annotation_window = tk.Toplevel()  # Create a new window on top of the main window
    #     annotation_window.title("Select Image to Analyze")

    #     # Get the list of file names in the folder to populate the Listbox
    #     images_to_select = os.listdir(annotatedfolder)
        
    #     # Create Listbox and populate it with the image filenames
    #     lb_images = Listbox(annotation_window, height=min(10, len(images_to_select)), exportselection=False)
    #     for image in images_to_select:
    #         lb_images.insert(tk.END, image)
    #     lb_images.pack(padx=10, pady=10)

    #     # Callback function to handle the selection from the Listbox
    #     def on_image_select():
    #         selected_indices = lb_images.curselection()  # Get the selected index
    #         if not selected_indices:  # This is the case when nothing is selected
    #             tk.messagebox.showwarning("No Selection", "Please select an image.")
    #             return
    #         selected_index = selected_indices[0]
    #         selected_image = lb_images.get(selected_index)
            
    #         # Now perform the desired action on the selected image
    #         image_path = os.path.join(annotatedfolder, selected_image)
    #         print(f"You selected to analyze: {selected_image} at {image_path}")
        
    #         # -> Get retina line
    #         print(f"Locating Retina layer for {image_path}")
    #         image = cv2.imread(image_path)
    #         _, retina_y_values = getRetina(image)
            
    #         # -> Add retina & fovea position to dictionary
    #         index = findDataArrayElement(data_arrays, image_path)
    #         data_arrays[index]["retina"] = retina_y_values
    #         data_arrays[index]["fovea"] = findFovea(retina_y_values)
            
    #         if not data_arrays:
    #             print("There is no previous data present to carry out the analysis! Please annotate the images first")
                    
    #             # print("Running general analysis with new image")
                
    #             # # ⚠️ NEEDS TESTING OF ANALYSIS FUNCTION ⚠️
    #             # rpe_line, sci_line, retina_line = analysis(imagepath)
    #             # data_arrays[index]["rpe"] = rpe_line
    #             # data_arrays[index]["sci"] = sci_line

    #         for window in window_sizes:
    #             window_size = window
    #             print(f"Analyzing at {window_size} mm")
                    
    #             retina_line, choroid_thickness = getEyeParametersFromDictionary(data_arrays[index])

    #             combined_dataframe = createDataFrame(choroid_thickness, retina_line, filepath)
                
    #             dataframes.append(combined_dataframe)

    #         print("\n🎉🎉🎉 Image has been analyzed!")
    #     # Button to confirm the image selection
    #     btn_select = Button(annotation_window, text="Analyze Selected Image", command=on_image_select)
    #     btn_select.pack(pady=10)
    
    # Add Raw data
    combined_dataframe = pd.DataFrame()
    
    for entry in data_arrays:
        choroid_thickness = [entry['sci'][x] - entry['rpe'][x] for x in range(0, original_image_width)]

        data = createDataFrame(choroid_thickness, entry['retina'], entry['image_code'])
        
        combined_dataframe = pd.concat([combined_dataframe, data], axis=1)
        
    dataframes.append(combined_dataframe)
                    
    createExcel(dataframes, filepath)

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
    # TS_corrected = (TS * original_image_width) / width
    
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

    # print("🎉 Your analysis file has been saved!")


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

    # print("🎉 Your analysis file has been saved!")
    messagebox.showinfo("Success!", "🎉 Your analysis file has been saved!")

def createNeededFolders():
    # Make a folder if it doesn't exist
    if not os.path.exists(tempfolder):
        os.makedirs(tempfolder)

    if not os.path.exists(annotatedfolder):
        os.makedirs(annotatedfolder)

    if not os.path.exists(csvfolder):
        os.makedirs(csvfolder)

if __name__ == "__main__":
    create_main_window()




