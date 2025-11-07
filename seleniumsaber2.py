import requests
from bs4 import BeautifulSoup
import os
import time
import re

os.makedirs("lightsaber_images", exist_ok=True)

print("Fetching lightsaber gallery page...")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get("https://disney.fandom.com/wiki/Lightsaber/Gallery", headers=headers, timeout=30)
soup = BeautifulSoup(response.content, "html.parser")

# Find all gallery images - Fandom uses specific classes
image_links = soup.select("a.image, a.lightbox")
print(f"Found {len(image_links)} image links\n")

downloaded = 0
skipped = 0

for idx, a in enumerate(image_links, 1):
    try:
        # Get the thumbnail image to extract the base URL
        img_tag = a.find("img")
        if not img_tag:
            skipped += 1
            continue
        
        # Get the data-src or src
        img_url = img_tag.get("data-src") or img_tag.get("src")
        if not img_url:
            skipped += 1
            continue
        
        # Make it a full URL
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        
        # Debug: Print the first few URLs to see what we're getting
        if idx <= 3:
            print(f"Sample URL {idx}: {img_url[:100]}...")
        
        # Extract the full resolution URL
        # Fandom format: https://static.wikia.nocookie.net/disney/images/thumb/X/XX/Filename.ext/revision/latest/scale-to-width-down/250?cb=...
        # We want: https://static.wikia.nocookie.net/disney/images/X/XX/Filename.ext
        
        if "static.wikia" in img_url or "vignette.wikia" in img_url:
            # Remove everything after the actual filename
            
            if "/images/thumb/" in img_url:
                # Split and reconstruct
                parts = img_url.split("/images/thumb/")
                if len(parts) == 2:
                    base = parts[0] + "/images/"
                    # Get the hash/filename part (e.g., "a/ab/Filename.jpg")
                    remaining = parts[1]
                    # Split by /revision or /scale or /zoom
                    file_path = re.split(r'/revision|/scale|/zoom|/thumbnail', remaining)[0]
                    img_url = base + file_path
            
            elif "/images/" in img_url:
                # Already might be full res, just clean query params
                img_url = img_url.split("?")[0].split("/revision")[0]
        
        # Download
        time.sleep(0.4)
        img_response = requests.get(img_url, headers=headers, timeout=20)
        
        if img_response.status_code == 200:
            file_size = len(img_response.content)
            
            # Skip if too small (probably an icon/logo)
            if file_size < 5000:  # Less than 5KB
                print(f"Skipped {idx}: File too small ({file_size} bytes) - probably not a real image")
                skipped += 1
                continue
            
            ext = os.path.splitext(img_url.split("?")[0])[1]
            if not ext or ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
            
            filename = f"lightsaber_images/lightsaber_{idx:04d}{ext}"
            
            with open(filename, "wb") as f:
                f.write(img_response.content)
            
            downloaded += 1
            
            if downloaded % 25 == 0:
                print(f"Progress: {downloaded} downloaded ({file_size/1024:.1f}KB), {skipped} skipped ({idx}/{len(image_links)})")
        else:
            print(f"Skipped {idx}: HTTP {img_response.status_code}")
            skipped += 1
        
    except Exception as e:
        print(f"Error {idx}: {str(e)[:80]}")
        skipped += 1

print(f"\n{'='*50}")
print(f"Downloaded: {downloaded} images")
print(f"Skipped: {skipped} images")
print(f"{'='*50}")