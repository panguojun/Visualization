from PIL import Image
import zlib
import math

def text_to_pixel_image(input_file, output_image, scale=1):
    """将文本文件转换为压缩像素图"""
    try:
        with open(input_file, 'rb') as f:
            text_data = f.read()
        
        # 压缩并添加长度头信息
        compressed_data = zlib.compress(text_data)
        data_length = len(compressed_data)
        # 在数据前添加4字节的长度信息
        length_header = data_length.to_bytes(4, 'big')
        full_data = length_header + compressed_data
        
        # 计算需要的图像尺寸
        total_bytes = len(full_data)
        side_length = math.ceil(math.sqrt(total_bytes))
        total_pixels = side_length * side_length
        # 填充数据到完整图像尺寸
        padded_data = full_data + bytes(total_pixels - total_bytes)
        
        img = Image.new('L', (side_length, side_length))
        img.putdata(padded_data)
        
        if scale > 1:
            img = img.resize((side_length * scale, side_length * scale), Image.NEAREST)
        
        # 使用无损PNG格式保存
        img.save(output_image, format='PNG', compress_level=0)
        print(f"成功转换: {input_file} → {output_image}")
        print(f"原始大小: {len(text_data)}字节 → 压缩后: {len(compressed_data)}字节")
        print(f"图像尺寸: {img.width}x{img.height}像素 (缩放比例: {scale}x)")
        return True
    except Exception as e:
        print(f"编码失败: {str(e)}")
        return False

def pixel_image_to_text(input_image, output_file=None):
    """从像素图恢复原始文本"""
    try:
        img = Image.open(input_image)
        img = img.convert('L')  # 确保是灰度模式
        
        # 获取原始尺寸(不缩放的情况)
        width, height = img.size
        pixel_data = list(img.getdata())
        byte_data = bytes(pixel_data)
        
        # 提取长度头信息
        if len(byte_data) < 4:
            raise ValueError("图像数据太短，缺少长度头信息")
        
        data_length = int.from_bytes(byte_data[:4], 'big')
        compressed_data = byte_data[4:4+data_length]
        
        if len(compressed_data) != data_length:
            raise ValueError("图像数据不完整或已损坏")
        
        # 解压缩数据
        decompressed_data = zlib.decompress(compressed_data)
        
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(decompressed_data)
            print(f"成功恢复: {input_image} → {output_file}")
            print(f"恢复文件大小: {len(decompressed_data)}字节")
            return True
        else:
            try:
                text = decompressed_data.decode('utf-8')
                print("\n恢复的文本内容:")
                print("=" * 40)
                print(text[:1000])  # 只打印部分内容避免控制台溢出
                print("=" * 40)
                return True
            except UnicodeDecodeError:
                print("\n恢复的二进制数据(非UTF-8文本)，前200字节:")
                print(decompressed_data[:200])
                return True
                
    except Exception as e:
        print(f"解码失败: {str(e)}")
        print("可能原因: 1) 图像已损坏 2) 不是有效的编码图像 3) 图像被修改过")
        return False

if __name__ == "__main__":
    # 文件路径设置
    TEXT_FILE = "C:/Users/18858/Desktop/hanger_phg.py"
    IMAGE_FILE = "C:/Users/18858/Desktop/output.png"
    RESTORED_FILE = "C:/Users/18858/Desktop/restored.py"
    
    print("=== 文本转像素图工具 ===")
    
    # 1. 编码
    print("\n[1] 正在编码文本文件...")
    if text_to_pixel_image(TEXT_FILE, IMAGE_FILE, scale=1):
        # 2. 解码
        print("\n[2] 正在解码图像文件...")
        if not pixel_image_to_text(IMAGE_FILE, RESTORED_FILE):
            print("\n尝试使用备用解码方法...")
            # 备用方法：尝试不使用长度头
            try:
                img = Image.open(IMAGE_FILE).convert('L')
                pixel_data = list(img.getdata())
                byte_data = bytes(pixel_data)
                decompressed_data = zlib.decompress(byte_data)
                with open(RESTORED_FILE, 'wb') as f:
                    f.write(decompressed_data)
                print("备用方法解码成功！")
            except Exception as e:
                print(f"备用方法也失败: {str(e)}")