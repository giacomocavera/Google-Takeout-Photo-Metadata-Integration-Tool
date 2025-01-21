import os
import json
import time
import shutil
from datetime import datetime, timezone
import piexif
from tkinter import Tk, filedialog
from tqdm import tqdm

# Updates the file's timestamp based on a given timestamp
def update_file_timestamp(image_path, timestamp):
    try:
        # Convert the timestamp to UTC datetime
        creation_time = datetime.fromtimestamp(int(timestamp), timezone.utc)
        # Update the file's access and modification times
        os.utime(image_path, (time.mktime(creation_time.timetuple()), time.mktime(creation_time.timetuple())))
    except Exception:
        pass

# Sets EXIF metadata for an image based on corresponding JSON metadata
def set_exif_from_json(image_path, json_path, output_folder):
    try:
        # Read metadata from the JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        new_image_path = os.path.join(output_folder, os.path.basename(image_path))
        shutil.copy(image_path, new_image_path)

        # Handle images (JPEG, PNG, JPG)
        if image_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            exif_dict = piexif.load(new_image_path)
            exif_dict["Exif"] = exif_dict.get("Exif", {})  # Ensure the "Exif" section exists

            photo_taken_time = metadata.get("photoTakenTime", {}).get("timestamp")
            if photo_taken_time:
                date_time_original = datetime.fromtimestamp(
                    int(photo_taken_time), timezone.utc
                ).strftime('%Y:%m:%d %H:%M:%S')
                exif_dict["Exif"][36867] = date_time_original.encode('utf-8')
                exif_dict["Exif"][36868] = date_time_original.encode('utf-8')

            exif_bytes = piexif.dump(exif_dict)
            try:
                piexif.insert(exif_bytes, new_image_path)
            except (ValueError, OverflowError):
                pass  # Handle invalid EXIF data gracefully

            update_file_timestamp(new_image_path, photo_taken_time)

        # Handle video files (MP4)
        elif image_path.lower().endswith(('.mp4')):
            photo_taken_time = metadata.get("photoTakenTime", {}).get("timestamp")
            if photo_taken_time:
                update_file_timestamp(new_image_path, photo_taken_time)

    except Exception:
        pass

def process_photos(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    total_files = 0  # Counter for the total number of processed files

    # Loop through subdirectories
    for year_folder in os.listdir(input_folder):
        year_path = os.path.join(input_folder, year_folder)
        if os.path.isdir(year_path):
            year_output_path = os.path.join(output_folder, year_folder)
            os.makedirs(year_output_path, exist_ok=True)

            files = [f for f in os.listdir(year_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4'))]
            total_files += len(files)

            for filename in tqdm(files, desc=f"Processing {year_folder}"):
                image_path = os.path.join(year_path, filename)
                json_path = f"{image_path}.json"

                if os.path.exists(json_path):
                    set_exif_from_json(image_path, json_path, year_output_path)
                else:
                    new_image_path = os.path.join(year_output_path, filename)
                    shutil.copy(image_path, new_image_path)

    return total_files

def main():
    Tk().withdraw()
    input_folder = filedialog.askdirectory(title="Select Input Folder")
    output_folder = filedialog.askdirectory(title="Select Output Folder")

    if not input_folder or not output_folder:
        print("Input or output folder not selected. Exiting...")
        return

    print("Starting processing...")
    total_files = process_photos(input_folder, output_folder)
    print(f"Processing complete! Total files processed: {total_files}")

    input("\nPress space to exit...")

if __name__ == "__main__":
    main()
