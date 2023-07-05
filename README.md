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

1. With main.py open you want to run all the cells below the ```imports``` block (that cell included) 

2. To run the cells you can go to 'Cells' > 'Run all below'

3. Wait for all the cells have run (there won't be any * marks on the left)

## **For Extracting the .vol file**: Run the first cell with the ```extract()``` block.

4. Follow the instructions in the UI. This will extract your images in the temp_folder/

## **For Drawing**: Run the ```annotate()``` block.

5. Go through the prompts in the UI selecting first the image you want to analyze. **Use numbers when you are selecting the image (i.e. 1)**

6. A window will appear with the sample image for analysis. Click with your mouse on it to draw the boundary.

7. Press 'Esc' 2x to finish your annotation.

## **For Analysis**: Run the ```analysis()``` code block at the top of the file.

8. Select the image you want to analysis.

9. A csv file including the pixel thickness will be created in the csv_data/ folder after a few seconds
