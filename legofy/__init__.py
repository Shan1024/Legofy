from __future__ import unicode_literals

from PIL import Image, ImageSequence
import sys
import os

# Python 2 and 3 support
# TODO: Proper images2gif version that supports both Py 2 and Py 3 (mostly handling binary data)
if sys.version_info < (3,):
    import legofy.images2gif_py2 as images2gif
else:
    import legofy.images2gif_py3 as images2gif
from legofy import palettes


def apply_color_overlay(image, color):
    '''Small function to apply an effect over an entire image'''
    overlay_red, overlay_green, overlay_blue = color
    channels = image.split()

    r = channels[0].point(lambda color: overlay_effect(color, overlay_red))
    g = channels[1].point(lambda color: overlay_effect(color, overlay_green))
    b = channels[2].point(lambda color: overlay_effect(color, overlay_blue))


    channels[0].paste(r)
    channels[1].paste(g)
    channels[2].paste(b)

    return Image.merge(image.mode, channels)

def overlay_effect(color, overlay):
    '''Actual overlay effect function'''
    if color < 33:
        return overlay - 100
    elif color > 233:
        return overlay + 100
    else:
        return overlay - 133 + color

def make_lego_image(thumbnail_image, palette_mode, brick_image):
    '''Create a lego version of an image from an image'''
    base_width, base_height = thumbnail_image.size
    brick_width, brick_height = brick_image.size

    rgb_image = thumbnail_image.convert('RGB')

    lego_image = Image.new("RGB", (base_width * brick_width,
                                   base_height * brick_height), "white")

    total_bricks = base_width * base_height

    brick_stats = {
        "width": base_width,
        "height": base_height,
        "total_bricks": total_bricks,
        "bricks": { }
    }
    print("Width: " + str(base_width))
    print("Height: " + str(base_height))
    print("Total Bricks: " + str(total_bricks))

    for brick_x in range(base_width):
        for brick_y in range(base_height):
            color = rgb_image.getpixel((brick_x, brick_y))
            lego_image.paste(apply_color_overlay(brick_image, color),
                             (brick_x * brick_width, brick_y * brick_height))

            '''update brick stats'''
            for pallet in palettes.LEGOS:
                for lego_color_code in palettes.LEGOS[pallet]:
                    rgb_lego_color = palettes.LEGOS[pallet][lego_color_code]
                    if rgb_lego_color[0] == color[0] and rgb_lego_color[1] == color[1] and rgb_lego_color[2] == color[2]:

                        # print("Found: [" + str(brick_x) + ", " + str(brick_y) + "]")

                        color_name = palettes.COLORS[pallet][lego_color_code]
                        if color_name in brick_stats["bricks"]:
                            brick_stats["bricks"][color_name] = brick_stats["bricks"][color_name] + 1
                        else:
                            brick_stats["bricks"][color_name] = 1
                        break
                else:
                    continue
                break

    total = 0
    for color, count in brick_stats["bricks"].items():
        total = total + count
    
    print("Bricks Count: " + str(total))

    # brick_stats["total"] = total

    return lego_image, brick_stats


def get_new_filename(file_path, ext_override=None):
    '''Returns the save destination file path'''
    folder, basename = os.path.split(file_path)
    base, extention = os.path.splitext(basename)
    if ext_override:
        extention = ext_override
    new_filename = os.path.join(folder, "{0}_lego{1}".format(base, extention))
    return new_filename

def get_new_filename_for_stats(file_path, ext_override=None):
    '''Returns the save destination file path'''
    folder, basename = os.path.split(file_path)
    base, extention = os.path.splitext(basename)
    if ext_override:
        extention = ext_override
    new_filename = os.path.join(folder, "{0}{1}".format(base, extention))
    return new_filename

def get_new_size(base_image, brick_image, size=None):
    '''Returns a new size the first image should be so that the second one fits neatly in the longest axis'''
    new_size = base_image.size
    if size:
        scale_x, scale_y = size, size
    else:
        scale_x, scale_y = brick_image.size

    if new_size[0] > scale_x or new_size[1] > scale_y:
        if new_size[0] < new_size[1]:
            scale = new_size[1] / scale_y
        else:
            scale = new_size[0] / scale_x

        new_size = (int(round(new_size[0] / scale)) or 1,
                    int(round(new_size[1] / scale)) or 1)

    return new_size

def get_lego_palette(palette_mode):
    '''Gets the palette for the specified lego palette mode'''
    legos = palettes.legos()
    palette = legos[palette_mode]
    return palettes.extend_palette(palette)


def apply_thumbnail_effects(image, palette, dither):
    '''Apply effects on the reduced image before Legofying'''
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette)
    return image.im.convert("P",
                        Image.FLOYDSTEINBERG if dither else Image.NONE,
                        palette_image.im)

def legofy_gif(base_image, brick_image, output_path, size, palette_mode, dither):
    '''Alternative function that legofies animated gifs, makes use of images2gif - uses numpy!'''
    im = base_image

    # Read original image duration
    original_duration = im.info['duration']

    # Split image into single frames
    frames = [frame.copy() for frame in ImageSequence.Iterator(im)]

    # Create container for converted images
    frames_converted = []

    print("Number of frames to convert: " + str(len(frames)))

    # Iterate through single frames
    for i, frame in enumerate(frames, 1):
        print("Converting frame number " + str(i))

        new_size = get_new_size(frame, brick_image, size)
        frame.thumbnail(new_size, Image.ANTIALIAS)
        if palette_mode:
            palette = get_lego_palette(palette_mode)
            frame = apply_thumbnail_effects(frame, palette, dither)
        new_frame = make_lego_image(frame, palette_mode, brick_image)
        frames_converted.append(new_frame)

    # Make use of images to gif function
    images2gif.writeGif(output_path, frames_converted, duration=original_duration/1000.0, dither=0, subRectangles=False)

def legofy_image(base_image, brick_image, output_path, size, palette_mode, dither, stats):
    '''Legofy an image'''
    new_size = get_new_size(base_image, brick_image, size)
    base_image.thumbnail(new_size, Image.ANTIALIAS)

    if palette_mode:
        palette = get_lego_palette(palette_mode)
        base_image = apply_thumbnail_effects(base_image, palette, dither)
    lego_image, brick_stats = make_lego_image(base_image, palette_mode, brick_image)
    lego_image.save(output_path)

    if stats:
        stats_output_path = get_new_filename_for_stats(output_path, '.json')
        print("stats will be saved to {0}".format(stats_output_path))
        import json
        # with open(stats_output_path, 'w') as stats_file:
        #     json.dump(brick_stats, stats_file)
        stats = json.dumps(brick_stats, indent=4)
        stats_file = open(stats_output_path, 'w')
        print >> stats_file, stats
        stats_file.close()

def main(image_path, output_path=None, size=None,
         palette_mode=None, dither=False, stats=None):
    '''Legofy image or gif with brick_path mask'''
    image_path = os.path.realpath(image_path)
    if not os.path.isfile(image_path):
        print('Image file "{0}" was not found.'.format(image_path))
        sys.exit(1)

    brick_path = os.path.join(os.path.dirname(__file__), "assets",
                              "bricks", "1x1.png")

    if not os.path.isfile(brick_path):
        print('Brick asset "{0}" was not found.'.format(brick_path))
        sys.exit(1)

    base_image = Image.open(image_path)
    brick_image = Image.open(brick_path)

    if palette_mode:
        print ("LEGO Palette {0} selected...".format(palette_mode.title()))
    elif dither:
        palette_mode = 'all'

    if image_path.lower().endswith(".gif") and base_image.is_animated:
        if output_path is None:
            output_path = get_new_filename(image_path)
        print("Animated gif detected, will now legofy to {0}".format(output_path))
        legofy_gif(base_image, brick_image, output_path, size, palette_mode, dither, stats)
    else:
        if output_path is None:
            output_path = get_new_filename(image_path, '.png')
        print("Static image detected, will now legofy to {0}".format(output_path))
        legofy_image(base_image, brick_image, output_path, size, palette_mode, dither, stats)

    base_image.close()
    brick_image.close()
    print("Finished!")

# main("/Users/shan/Documents/sources/lego/opm.jpg", size=50, palette_mode="solid", stats=True)
