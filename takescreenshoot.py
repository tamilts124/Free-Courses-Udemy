import pyautogui
import requests, sys
import base64, io


def get_url():
    # take screenshot
    screenshot = pyautogui.screenshot()
    # convert image to base64 string
    img_buffer = io.BytesIO()
    screenshot.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode('ascii')
    # set API endpoint and parameters
    url = 'https://freeimage.host/api/1/upload'
    params = {
        'key': sys.argv[1],
        'action': 'upload',
        'source': img_str,
        'format': 'json'
    }
    # send POST request to API
    response = requests.post(url, data=params, verify=False)
    # print response
    return response.json()['image']['url']
