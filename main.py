import cv2
import numpy as np
import pandas as pd
import os

main()

# +
image_path = "data/example_1/example_1-0001.tif"
# image_path = "data/RAW_OCT_Files/TEST_T_2708"
# Get the base name of the file
file_name = os.path.basename(image_path)
directory = os.path.dirname(image_path)

# Remove the file extension
file_name_without_extension = os.path.splitext(file_name)[0]

# +
# import vtk

# # Create a volume reader
# reader = vtk.vtkVolume16Reader()
# reader.SetFilePrefix(image_path)
# reader.SetFilePattern("%s.vol")
# reader.SetDataDimensions(512, 512)
# reader.SetDataByteOrderToLittleEndian()
# reader.SetImageRange(1, 92)
# reader.SetDataSpacing(3.2, 3.2, 1.5)
# reader.Update()

# # Get the volume data
# volume_data = reader.GetOutput()

# # Perform further processing or visualization with the volume data
# # Create a volume mapper
# volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
# volume_mapper.SetInputData(volume_data)

# # Create a volume property
# volume_property = vtk.vtkVolumeProperty()
# volume_property.ShadeOff()
# volume_property.SetInterpolationTypeToLinear()

# # Create a volume
# volume = vtk.vtkVolume()
# volume.SetMapper(volume_mapper)
# volume.SetProperty(volume_property)

# # Create a renderer and add the volume to it
# renderer = vtk.vtkRenderer()
# renderer.AddVolume(volume)

# # Create a render window
# render_window = vtk.vtkRenderWindow()
# render_window.AddRenderer(renderer)

# # Create an interactor
# interactor = vtk.vtkRenderWindowInteractor()
# interactor.SetRenderWindow(render_window)

# # Start the rendering and interaction
# render_window.Render()
# interactor.Start()


# +
drawing=False # true if mouse is pressed
mode=True # if True, draw rectangle. Press 'm' to toggle to curve
image = cv2.imread(image_path)


def main():
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
    
    new_image_path = directory + "/" + file_name_without_extension + "_modified.tif"
    cv2.imwrite(new_image_path, image)


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

image = cv2.imread("data/example_1/example_1-0001_modified.tif")
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

# Add "_analysis" to the file name
csv_file_name = directory + "/" + file_name_without_extension + "_analysis.csv"

print("CSV file name:", csv_file_name)

# Save the DataFrame as a CSV file
df.to_csv(csv_file_name, index=False)

print("Saved your analysis file!")
# -


