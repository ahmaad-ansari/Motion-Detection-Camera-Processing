# Motion-Detection-Camera-Processing

#### Description:
This repository contains a Python script for motion detection and camera processing. It utilizes OpenCV and requests libraries to detect motion in camera streams, record videos upon detection, and upload them to a specified server endpoint.

#### Installation:
1. Clone the repository:
   ```
   git clone https://github.com/your-username/Motion-Detection-Camera-Processing.git
   ```

#### Usage:
1. Ensure Python 3.10 is installed on your system.
2. Run the script `motion_detection.py`:
   ```
   python motion_detection.py
   ```

#### Configuration:
- Update the endpoint URLs:
  - Update the camera endpoint URL in the `fetch_cameras` method.
  - Update the video upload endpoint URL in the `upload_video` method.

#### Requirements:
- Python 3.10
- OpenCV
- requests
