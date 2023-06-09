import base64
import cv2
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from io import BytesIO
import numpy as np
import os
import requests

api_key = os.environ["GOOGLE_MAPS_API_KEY"]
google_maps = (
    f"https://maps.googleapis.com/maps/api/js?key={api_key}&callback=window.initMap"
)

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Store(id="map-data"),
        html.Div(
            id="map", style={"height": "800px", "width": "100%", "position": "relative"}
        ),
        html.Div(
            html.Button(
                "Convert", id="get-info-button", style={"pointerEvents": "auto"}
            ),
            id="floating-square",
            style={
                "border": "3px solid red",
                "height": "640px",
                "width": "640px",
                "position": "absolute",
                "top": "80px",
                "left": "50%",
                "transform": "translate(-50%, 0)",
                "pointerEvents": "none",
            },
        ),
        html.Img(id="result"),
    ]
)


# lake bonney
default_location = dict(
    lat=-34.220359,
    lon=140.4311491,
    zoom=14,
)

app.clientside_callback(
    f"""
    (function() {{
        let script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);

        var map;
        let markers = [];

        function addMarker(latLng) {{
            let marker = new google.maps.Marker({{
                map: map,
                position: latLng,
                draggable: true,
                icon: 'https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png'
            }});
            markers.push(marker);
            console.log(latLng.lat(), latLng.lng());
        }}

        function createMap() {{
            map = new google.maps.Map(document.getElementById('map'), {{
                center: {{ lat: {default_location["lat"]}, lng: {default_location["lon"]} }},
                zoom: {default_location["zoom"]}
            }});

            map.addListener('click', function(e) {{
                console.log(e);
                addMarker(e.latLng);
            }});
        }}

        window.initMap = function() {{
            if (document.readyState === 'complete') {{
                createMap();
            }} else {{
                window.onload = createMap;
            }}
        }};

        return function(button_clicks) {{
                if (map) {{                
                    let center = map.getCenter();
                    let lat = center.lat();
                    let lng = center.lng();
                    let zoom = map.getZoom();
                
                    return {{lat: lat, lon: lng, zoom: zoom }}; 
                }}
                return "";
        }};
    }})()
    """,
    Output("map-data", "data"),
    Input("get-info-button", "n_clicks"),
)


def download_google_maps_image(lat, lon, zoom, dimensions, api_key):
    map_type = "roadmap"

    # Create the URL for the Google Maps Static API request
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom={zoom}&size={dimensions[0]}x{dimensions[1]}&maptype={map_type}&style=element:labels|visibility:off&key={api_key}"

    # Send the request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Load the image into an OpenCV buffer
        image_buffer = BytesIO(response.content)
        image = cv2.imdecode(
            np.frombuffer(image_buffer.read(), np.uint8), cv2.IMREAD_COLOR
        )
        return image
    else:
        print(f"Error: Unable to download image. Status code: {response.status_code}")
        return None


def extract_water_edge(
    image: np.ndarray,
    water_color: np.ndarray = np.array([249, 192, 156]),
    tolerance: int = 20,
) -> np.ndarray:
    # Create a mask for the water region based on the color and tolerance
    lower_bound = np.clip(water_color - tolerance, 0, 255)
    upper_bound = np.clip(water_color + tolerance, 0, 255)
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # Detect the edges of the water using a Canny edge detector or other edge detection methods
    edges = cv2.Canny(mask, 100, 200)

    dilation_kernel_size = 3
    dilation_iterations = 1
    # Dilate the edges to make the lines thicker and smoother
    kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=dilation_iterations)

    edges = cv2.medianBlur(edges, 5)

    # Remove edges on the border of the image
    edges[0, :] = 0
    edges[-1, :] = 0
    edges[:, 0] = 0
    edges[:, -1] = 0

    # Convert the edge image to a 4-channel image (RGBA) with a transparent background
    rgba = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGBA)

    # # Set the line color to black (0, 0, 0) and the background to transparent

    rgba[:, :, 3] = (rgba[:, :, 0] > 0) * 255
    rgba[(rgba[:, :, 0] > 0), :3] = (204, 204, 204)  # (0, 0, 0)

    return rgba



import math

def lat_lng_to_pixels(lat, lng, zoom):
    TILE_SIZE = 256
    scale = 2 ** zoom
    x = (lng + 180) / 360 * scale * TILE_SIZE
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * scale * TILE_SIZE
    return x, y

def pixels_to_lat_lng(x, y, zoom):
    TILE_SIZE = 256
    scale = 2 ** zoom
    lng = x / (scale * TILE_SIZE) * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / (scale * TILE_SIZE)))))
    return lat, lng

def calculate_bounds(center_lat, center_lng, zoom, img_width=640, img_height=640):
    x, y = lat_lng_to_pixels(center_lat, center_lng, zoom)

    top_left_x = x - img_width / 2
    top_left_y = y - img_height / 2
    bottom_right_x = x + img_width / 2
    bottom_right_y = y + img_height / 2

    top_left_lat, top_left_lng = pixels_to_lat_lng(top_left_x, top_left_y, zoom)
    bottom_right_lat, bottom_right_lng = pixels_to_lat_lng(bottom_right_x, bottom_right_y, zoom)

    return top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng



@app.callback(Output("result", "src"), Input("map-data", "data"))
def generate_map(map_data):
    if not map_data:
        raise PreventUpdate

    bounds = calculate_bounds(map_data["lat"], map_data["lon"], map_data["zoom"])
                 
    img = download_google_maps_image(
        map_data["lat"], map_data["lon"], map_data["zoom"], (640, 640), api_key
    )

    img = extract_water_edge(img)

    compression_level = 9
    cv2.imwrite('output.png', img, [cv2.IMWRITE_PNG_COMPRESSION, compression_level])

    print(map_data["zoom"], *map(math.radians, bounds))

    # Convert the image to a base64-encoded PNG using OpenCV
    _, buffer = cv2.imencode(".png", img)
    img_str = base64.b64encode(buffer).decode("utf-8")

    # Return the base64-encoded image data
    return f"data:image/png;base64,{img_str}"


if __name__ == "__main__":
    app.run_server(debug=True)
