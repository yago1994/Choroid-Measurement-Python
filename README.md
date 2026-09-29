# Choroid-Measurement-Python
 Repository to create a function to analyze choroid thickness from Heidelberg OCT images



#  ⚠️ This program is under development ⚠️

# Getting Started
1. Have a usable command prompt, i.e. Windows PowerShell, Terminal
2. Install Python 3.11 (the target version for this dependency set).
3. Install Git, which pip uses to install the pinned HeyexReader source revision.
4. (Optional) Install Jupyter Notebook from https://jupyter.org/

Create a fresh virtual environment:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

On Windows, create the environment with `py -3.11 -m venv .venv` and activate
it with `.venv\Scripts\Activate.ps1` in PowerShell.

The published `heyexReader==0.1.3` package reads OCT buffers with
`array.fromstring()`, which was removed in Python 3.9. The requirement above
pins an immutable upstream revision containing the `frombytes()` fix from
[HeyexReader PR #6](https://github.com/ayl/heyexReader/pull/6). Installing the
old PyPI release instead will break OCT reading on Python 3.11.

If you reuse an environment containing the PyPI reader, explicitly replace
it: both builds report version 0.1.3, so pip may otherwise retain the old code.

```sh
python -m pip install --force-reinstall --no-deps "heyexReader @ git+https://github.com/ayl/heyexReader.git@73aa32cf7aa283446aee1be8808651598052bc26"
```

NumPy, Pillow, and OpenCV have also been updated to address the reported
dependency alerts. Keep this dependency set together; Pillow 12.3.0 requires
Python 3.10 or newer.

## Reader regression checks

```sh
python -m unittest discover -s tests -v
```

These checks read and render a synthetic OCT volume without patient data or
a display. They cover the installed reader and dependencies; they do not
replace manual checks of the annotation GUI and measurement exports.

# Run

In Terminal:

TKinter Implementation:
1. You can use the standard GUI and run the code using that instead of the Jupyter CLI

Jupyter Implementation:

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
