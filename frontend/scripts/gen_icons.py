
import os
from PIL import Image
import sys

def generate_icons(source_path, res_dir):
    try:
        img = Image.open(source_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Icon densities and sizes
    densities = {
        'mipmap-mdpi': 48,
        'mipmap-hdpi': 72,
        'mipmap-xhdpi': 96,
        'mipmap-xxhdpi': 144,
        'mipmap-xxxhdpi': 192
    }

    # Splash densities (approximate common sizes)
    # port: portrait, land: landscape
    # We will just generate a generic 'splash.png' in drawable directories for simplicity
    # or strictly follow capacitor defaults if possible. 
    # For this task, we will overwrite `drawable/splash.png` if it exists, 
    # and also generate versions for `drawable-port-*` directories which Capacitor often uses.
    
    # Actually, let's stick to the mipmap icons first as requested.
    for folder, size in densities.items():
        path = os.path.join(res_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        
        # ic_launcher.png (Legacy)
        icon = img.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(os.path.join(path, 'ic_launcher.png'))
        
        # ic_launcher_round.png (Legacy Round)
        icon.save(os.path.join(path, 'ic_launcher_round.png'))

        # ic_launcher_foreground.png (Adaptive Foreground)
        # Adaptive icons are 108x108dp, but the viewport is masked.
        # Foreground should be transparent with the logo in the center 72x72dp zone (66%)
        # For simplicity, we create a square image of the target size, 
        # and resize the logo to be about 70% of that size and center it.
        
        # Determine canvas size (same as legacy size is a good approximation for density buckets if we assume 108dp ~ 1.5x 72dp legacy? 
        # Actually:
        # mdpi: 48px legacy (1x) -> 108px adaptive
        # hdpi: 72px legacy (1.5x) -> 162px adaptive
        # xhdpi: 96px legacy (2x) -> 216px adaptive
        # xxhdpi: 144px legacy (3x) -> 324px adaptive
        # xxxhdpi: 192px legacy (4x) -> 432px adaptive
        
        adaptive_size = int(size * 108 / 48) # Calculate generic adaptive size based on mdpi ratio
        
        foreground_canvas = Image.new("RGBA", (adaptive_size, adaptive_size), (0, 0, 0, 0))
        
        # Resize logo to 60% of canvas to be safe within the 66% safe zone
        logo_size = int(adaptive_size * 0.6)
        logo_resized = img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Center logo
        offset = (adaptive_size - logo_size) // 2
        foreground_canvas.paste(logo_resized, (offset, offset))
        
        foreground_canvas.save(os.path.join(path, 'ic_launcher_foreground.png'))

        print(f"Generated {folder} icons including adaptive foreground")

    # Splash Screen
    # Capacitor standard splash is usually named "splash.png"
    # We will create a large splash image and save it to drawable-port-xxxhdpi (as a catch-all high res)
    # and drawable/splash.png if strict mapping isn't set.
    
    splash_size = (1280, 1920) # Portrait 
    splash_img = img.resize(splash_size, Image.Resampling.LANCZOS)
    
    # Check for drawable dir
    drawable_dirs = ['drawable', 'drawable-port-xxhdpi']
    for d in drawable_dirs:
        path = os.path.join(res_dir, d)
        if os.path.exists(path):
            splash_img.save(os.path.join(path, 'splash.png'))
            print(f"Generated splash for {d}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python gen_icons.py <source_image> <res_dir>")
    else:
        generate_icons(sys.argv[1], sys.argv[2])
