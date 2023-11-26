import cv2
import numpy as np
import requests
import threading
import datetime
import os


class CameraProcessor:
    def __init__(self, camera_data):
        self.camera_id = camera_data['_id']  # Updated line
        self.stream_url = camera_data['streamUrl']
        self.camera_name = camera_data['name']
        self.camera_location = camera_data['location']
        self.backSub = cv2.createBackgroundSubtractorMOG2()
        self.is_recording = False

    @staticmethod
    def fetch_cameras():
        url = 'http://10.0.0.2:3002/cameras'  # Update with your cameras endpoint
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch cameras: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching cameras: {e}")
        return []

    def record_video(self, initial_frame):
        max_post_motion_duration = 2  # seconds
        last_motion_time = datetime.datetime.now()

        recordings_dir = 'recordings'
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)

        sanitized_url = self.stream_url.replace('://', '_').replace('/', '_')
        filename = f"motion_{sanitized_url}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        filepath = os.path.join(recordings_dir, filename)

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))

        out.write(initial_frame)  # Write the frame that detected motion

        for frame in self.read_stream():
            current_time = datetime.datetime.now()

            if self.is_motion_detected(frame):
                print("Motion is detected from ", self.stream_url)
                last_motion_time = current_time  # Update the last motion time

            if (current_time - last_motion_time).seconds > max_post_motion_duration:
                break  # Stop recording if no motion detected for a certain duration

            out.write(frame)

        out.release()
        self.is_recording = False
        self.upload_video(filepath)

    def is_motion_detected(self, frame):
        fg_mask = self.backSub.apply(frame)
        _, thresh = cv2.threshold(fg_mask, 25, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                return True
        return False

    def read_stream(self):
        stream = requests.get(self.stream_url, stream=True)
        byte_stream = bytes()
        for chunk in stream.iter_content(chunk_size=1024):
            byte_stream += chunk
            a = byte_stream.find(b'\xff\xd8')
            b = byte_stream.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = byte_stream[a:b + 2]
                byte_stream = byte_stream[b + 2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                yield frame

    def process_stream(self):
        for frame in self.read_stream():
            if frame is None:
                break
            if not self.is_recording and self.is_motion_detected(frame):
                self.is_recording = True
                threading.Thread(target=self.record_video, args=(frame,)).start()

    def upload_video(self, filepath):
        url = 'http://10.0.0.2:3003/videos/upload'  # Update with your video upload endpoint
        files = {'video': open(filepath, 'rb')}
        data = {
            'cameraId': self.camera_id,
            'name': self.camera_name,
            'location': self.camera_location,
            'streamUrl': self.stream_url
        }

        try:
            response = requests.post(url, files=files, data=data)
            print(f"Video uploaded: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            print(f"Error uploading video: {e}")
        finally:
            files['video'].close()  # Close the file
            os.remove(filepath)  # Remove the file after uploading


def start_camera_streams():
    cameras_data = CameraProcessor.fetch_cameras()
    print(cameras_data)  # Add this line to inspect the fetched camera data

    camera_processors = [CameraProcessor(camera_data) for camera_data in cameras_data]

    threads = [threading.Thread(target=processor.process_stream) for processor in camera_processors]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

start_camera_streams()
