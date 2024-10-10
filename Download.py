from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import time
import numpy as np
from io import BytesIO
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import load_model
import base64
import random
import shutil
import string
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select



folder_name = ''.join(random.choices(string.ascii_lowercase, k=9))

# Function to decode base64 to an image using PIL
def decode_base64_to_image(base64_string):
    prefix = 'data:image/jpg;base64,'
    base64_data = base64_string[len(prefix):]  # Remove the prefix
    image_data = base64.b64decode(base64_data)
    image = Image.open(BytesIO(image_data))
    return image

def segment_image(image, segments):
    # Ensure the directory exists
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    segmented_images = []
    for i, (start, end) in enumerate(segments):
        cropped_image = image.crop((start, 0, end, image.height))
        segmented_images.append(cropped_image)
        # Save each segment to the folder
        filename = f"segment_{i+1}_{start}-{end}.png"
        filepath = os.path.join(folder_name, filename)
        cropped_image.save(filepath)
    print(f"Segments saved.")

def prepare_image_for_model(filepath, target_size):
    img = load_img(filepath, target_size=target_size)
    img_array = img_to_array(img)
    img_array /= 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def predict_segments(model):
    predictions = []
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    paths = [f'{folder_name}\segment_1_23-57.png', f'{folder_name}\segment_2_47-81.png', f'{folder_name}\segment_3_73-107.png', f'{folder_name}\segment_4_97-131.png', f'{folder_name}\segment_5_123-157.png', f'{folder_name}\segment_6_147-181.png']
    for path in paths:
        prepared_image = prepare_image_for_model(path, (34, 80))  # Adjust size as per the model's requirement
        probabilities = model.predict(prepared_image)
        class_index = np.argmax(probabilities)
        predictions.append(class_labels[class_index])
    return ''.join(predictions)

def delete_folder(path):
    try:
        shutil.rmtree(path)
        print(f"Folder '{path}' successfully deleted.")
    except Exception as e:
        print(f"Failed to delete folder '{path}'. Reason: {e}")

def find_file(root_folder, filename):
    """Search for a file in a directory and its subfolders."""
    for root, dirs, files in os.walk(root_folder):
        if filename in files:
            return os.path.join(root, filename)
    return None  # Return None if the file isn't found

DistrictIndex = int(input("Please enter the District Index:"))
AssemblyIndex = int(input("Please enter the Assembly Index:"))
    

# Load the model once to avoid reloading it on each function call
model = load_model('model_epoch_1000_loss_0.00000000.keras')

# Define class labels from 0-9 and a-z
class_labels = {i: ch for i, ch in enumerate('0123456789abcdefghijklmnopqrstuvwxyz')}

driver = webdriver.Chrome()

driver.get('https://voters.eci.gov.in/download-eroll?stateCode=S15')
print(driver.title)


try:
    div_element = WebDriverWait(driver, 10000000).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.row.col-md-8')))
    img_element = WebDriverWait(div_element, 10000000).until(EC.visibility_of_element_located((By.TAG_NAME, 'img')))
    WebDriverWait(driver, 10000000).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.form-select')))

    print("Selecting options...")
    element = driver.find_elements(By.CLASS_NAME, "form-select")[1]
    select = Select(element)
    expected_options_count = DistrictIndex+1  # Change this to the number of options you expect
    WebDriverWait(driver, 10000000).until(
        lambda driver: len(select.options) >= expected_options_count
    )
    select.select_by_index(DistrictIndex+1)

    print("Waiting for visibility of the spinner...")
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.spinner-border.spinner-border-sm.spinner_custom')))
    print("Waiting for invisibility of the spinner...")
    WebDriverWait(driver, 10000000).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.spinner-border.spinner-border-sm.spinner_custom')))
    print("Loaded.")

    element = driver.find_element(By.CLASS_NAME, "css-1xc3v61-indicatorContainer")
    actions = ActionChains(driver)
    actions.move_to_element(element).click(element).perform()

    element = driver.find_element(By.ID, f"react-select-2-option-{AssemblyIndex+1}")
    
    district = select.first_selected_option.text
    assembly = element.get_attribute('innerHTML')
    print(f"District: {district}")
    print(f"Assembly Constituency: {assembly}")

    actions = ActionChains(driver)
    actions.move_to_element(element).click(element).perform()

    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.spinner-border.spinner-border-sm.spinner_custom')))
    WebDriverWait(driver, 10000000).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.spinner-border.spinner-border-sm.spinner_custom')))

    print("Options selected, proceeding to download the files...")
    
    input_element = driver.find_element(By.CLASS_NAME, 'library-input.form-control')
    numberOfElements = len(driver.find_elements(By.CLASS_NAME, 'mr-3'))
    nextButton = driver.find_elements(By.CLASS_NAME, 'control-btn')[2]
    
    j = 0
    
    i = 0
    while i<numberOfElements-1:
        year = '2023' if i%3==0 else '2024'
        revision = '2' if i%3==2 else '1'
        fc = "FC-" if i%3==2 else ''
        roll = 'DraftRoll' if i%3==0 else "FinalRoll"
        assembly_index = assembly.split(" - ")[0]
        file_name = f"{year}-{fc}EROLLGEN-S15-{assembly_index}-{roll}-Revision{revision}-ENG-{str(int(i/3)+1+j*20)}-WI.pdf"
        found_file = find_file(r"C:/Users/0321i/Downloads", file_name)
        if found_file:
            print(f'File: {file_name} is already downloaded, skipping...')
            disabled_attribute = nextButton.get_attribute('disabled')
            if i == numberOfElements-2 and disabled_attribute is None:
                nextButton.click()
                numberOfElements = len(driver.find_elements(By.CLASS_NAME, 'mr-3'))
                i=-1
                j=j+1
            i=i+1
            continue
        else:
            print(print(f'File: {file_name} is not there, has to be downloaded.'))

        time.sleep(3)
        
        img_element = div_element.find_element(By.TAG_NAME, 'img')
        img_src = img_element.get_attribute('src')
        original_image = decode_base64_to_image(img_src)
        segments = [(23, 23+34), (47, 47+34), (73, 73+34), (97, 97+34), (123, 123+34), (147, 147+34)]
        image_segments = segment_image(original_image, segments)
        captcha_text = predict_segments(model)
        print(f"Captcha contains the letters {captcha_text}")
        
        input_element.send_keys(''.join(captcha_text))
        img_element = driver.find_elements(By.CLASS_NAME, 'mr-3')[i]
        
        time.sleep(1)

        driver.execute_script(f"document.getElementsByClassName('mr-3')[{i}].click()")
        driver.execute_script("arguments[0].style.filter = 'contrast(0) brightness(2) sepia(1) hue-rotate(-50deg)';", img_element)

        WebDriverWait(driver, 10000000).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.spinner-border.spinner-border-sm.spinner_custom')))
        WebDriverWait(driver, 10000000).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.spinner-border.spinner-border-sm.spinner_custom')))

        alert = driver.find_elements(By.CSS_SELECTOR, '.alert_content')
        if alert:
            print("Alert Detected! Retrying...")
            driver.execute_script("var element = document.querySelector('.alert_content'); if (element) element.parentNode.removeChild(element);")
            i = i-1
        else:
            time.sleep(3)
            year = '2023' if i%3==0 else '2024'
            revision = '2' if i%3==2 else '1'
            fc = "FC-" if i%3==2 else ''
            roll = 'DraftRoll' if i%3==0 else "FinalRoll"
            assembly_index = assembly.split(" - ")[0]
            file_name = f"{year}-{fc}EROLLGEN-S15-{assembly_index}-{roll}-Revision{revision}-ENG-{str(int(i/3)+1+j*20)}-WI.pdf"
            print(f"Downloading: {file_name}")
            found_file = find_file(r"C:/Users/0321i/Downloads", file_name)
            if not found_file:
                i=i-1
                print(f'Could not find the downloaded file, trying again...')
            else:
                print(f"Downloaded File: {i}, Page: {j}, Name: {file_name}")
            
            disabled_attribute = nextButton.get_attribute('disabled')

            if i == numberOfElements-2 and disabled_attribute is None:
                nextButton.click()
                numberOfElements = len(driver.find_elements(By.CLASS_NAME, 'mr-3'))
                i=-1
                j=j+1
        i = i+1
    print("Out of loop, waiting. All files downloaded.")
    time.sleep(20)
    delete_folder(folder_name)
except Exception as e:
    print(f"An error occurred: {e}")
    delete_folder(folder_name)

finally:
    driver.quit()