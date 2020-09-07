import requests

def get_response(path):
   url = "https://passport-textraction.herokuapp.com/detect"
   files = {'image': open(path, 'rb')}
   response = requests.post(url, files=files)
   print(response.text)

if __name__ == "__main__":
    get_response("./examples/example1.jpg")