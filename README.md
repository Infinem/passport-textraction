**REST API for text extraction from UZB Passports**

### Usage
1. Send the request to url **`https://passport-textraction.herokuapp.com/detect`** with image file **`{"image": binary_data}`**.
2. Retrieve response from the server as json object, use as you want.
3. For better understanding, I provided the example of request in **`examples/client.py`** file. Also, in **`examples`** folder you can find passport scan samples.

### Specifications
1. For correct and accurate information extraction try to provide image with better resolution (min **`800x600`**).
2. If image was not parsed correctly, check whether letters on scan are visible.
3. The scan may be parsed correctly but could fail the validation step. Validation made by the **`ICAO 9303`** standard for **`TD3 document types`** (**UZB Passport**).

### TODO
1. Implement layout detection.