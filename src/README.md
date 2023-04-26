# Water Map

This application allows users to select a body of water using Google Maps and then generates a line drawing that shows the boundary of the selected water body. 

ChatGPT tells me the line drawing can be useful for various purposes, such as creating artistic representations or for further analysis. I use for long haul sailing races with [Extreme Racer](https://github.com/esensible/extremeracer).

## How it works

The app uses a Dash web interface to display a Google Map centered on a default location. Users can navigate the map to find the body of water they want to convert into a line drawing. A red-bordered square on the map represents the area that will be converted to an edge image when the "Convert" button is clicked.

When the "Convert" button is clicked, the app captures the map data (latitude, longitude, and zoom) and sends it to a callback function. This function downloads the corresponding Google Maps image using the Static Maps API and processes the image to detect and extract the water edges. The processed image is then displayed below the map.

The image processing involves creating a mask for the water region based on a specific color and tolerance, detecting the edges of the water using a Canny edge detector, dilating the edges to make the lines thicker and smoother, and converting the edge image to a 4-channel image (RGBA) with a transparent background.

## Requirements

To run the application, you will need the following:

* Python 3.x
* OpenCV
* Dash
* A Google Maps API key

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/water-boundary-line-drawing.git
```

2. Change to the project directory:
```
cd water-boundary-line-drawing
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Set your Google Maps API key as an environment variable:
```
export GOOGLE_MAPS_API_KEY="your_api_key_here"
```

## Usage
1. Start the application:
```
python main.py
```

2. Open a web browser and navigate to http://127.0.0.1:8050.

3. Use the Google Map to find the body of water you want to convert into a line drawing.

4. Click the "Convert" button to generate the line drawing of the selected water body. The line drawing will appear below the map.

## License
This project is licensed under the MIT License. See the LICENSE file for details.