# Choroid-Measurement-Python
 Repository to create a function to analyze choroid thickness from Heidelberg OCT images



#  ⚠️ This program is under development ⚠️

# How to use this program

Requirements
- Jupyter Notebook -> Install Jupyter Notebook first from https://jupyter.org/

Then use:

```$ pip install -r requirements.txt```

To pull all the dependencies you need to run

# Run

In Terminal

```$ cd PATH_TO_YOUR_DIRECTORY/Choroid-Measurement-Python```

```$ jupyter notebook```

This should launch your brower and initiate a Jupyter Session. Click on main.py

1. With main.py open you want to run all the cells below the ```imports``` block 

2. To run the cells you can go to 'Cells' > 'Run all below'

3. Wait for all the cells have run (there won't be any * marks on the left)

4. **For Drawing**: Edit the directory path in ```directory = 'data/RAW_OCT_Files/'``` to the folder name where you are storing your OCT images. Then run this ```def main()``` cell block.

5. Run the ```main()``` block in the top of the file.

6. Go through the prompts in the UI selecting first the image .vol file you want to analyze, and then the frame within that .vol image. **Use numbers when you are selecting the image (i.e. 1)**

7. A window will appear with the sample image for analysis. Click with your mouse on it to draw the boundary

8. **For Analysis**: Edit the file path in ```"data/example_1/example_1-0001_modified.tif"``` to the image that has just been generated in the ```temp_data/``` folder. It will be something like ```temp_data/OCT_0001_modified.tif```. Then run this code block.

9. Run the ```analysis()``` code block at the top of the file.

10. A csv with the pixel thickness will appear after a few seconds
