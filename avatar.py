"""
用户头像生成模块
根据用户姓名自动生成彩色首字母头像
"""
from PIL import Image, ImageDraw, ImageFont
import hashlib
import io
from pathlib import Path

# 预定义的柔和配色
AVATAR_COLORS = [
    "#FF6B6B",  # 红
    "#4ECDC4",  # 青
    "#45B7D1",  # 蓝
    "#96CEB4",  # 绿
    "#FFEAA7",  # 黄
    "#DDA0DD",  # 紫
    "#98D8C8",  # 薄荷
    "#F7DC6F",  # 金
    "#BB8FCE",  # 淡紫
    "#85C1E9",  # 天蓝
    "#F8B500",  # 橙
    "#00CED1",  # 深青
]


def get_color_for_name(name: str) -> str:
    """根据姓名哈希值选择颜色"""
    hash_val = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return AVATAR_COLORS[hash_val % len(AVATAR_COLORS)]


def get_initial(name: str) -> str:
    """获取姓名首字"""
    if not name:
        return "?"
    return name[0].upper()


def create_avatar(name: str, size: int = 80) -> Image.Image:
    """
    创建圆形头像
    
    Args:
        name: 用户姓名
        size: 头像尺寸（像素）
    
    Returns:
        PIL Image 对象
    """
    # 创建透明背景
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 获取颜色和首字
    bg_color = get_color_for_name(name)
    initial = get_initial(name)
    
    # 绘制圆形背景
    draw.ellipse([0, 0, size - 1, size - 1], fill=bg_color)
    
    # 选择字体
    font_size = int(size * 0.5)
    try:
        # 尝试使用系统中文字体
        font = ImageFont.truetype("msyh.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("simhei.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), initial, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # 绘制白色文字
    draw.text((x, y), initial, fill="white", font=font)
    
    return image


def create_avatar_bytes(name: str, size: int = 80) -> bytes:
    """创建头像并返回 PNG 字节数据"""
    image = create_avatar(name, size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def save_avatar(name: str, path: str, size: int = 80):
    """保存头像到文件"""
    image = create_avatar(name, size)
    image.save(path, format="PNG")


# 缓存已生成的头像
_avatar_cache = {}


def get_cached_avatar(name: str, size: int = 80) -> Image.Image:
    """获取缓存的头像"""
    cache_key = f"{name}_{size}"
    if cache_key not in _avatar_cache:
        _avatar_cache[cache_key] = create_avatar(name, size)
    return _avatar_cache[cache_key]


def clear_avatar_cache():
    """清除头像缓存"""
    _avatar_cache.clear()
