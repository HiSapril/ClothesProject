from PIL import Image

def create_image():
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save('test_image.png')
    print("Created test_image.png")

if __name__ == "__main__":
    create_image()
