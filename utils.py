#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات مساعدة للبوت
"""

import os
import hashlib
import datetime
import json
import asyncio
from typing import Dict, List, Optional, Union, Any
import logging
from pathlib import Path

# إعداد التسجيل
logger = logging.getLogger(__name__)

class FileManager:
    """مدير الملفات المتقدم"""
    
    def __init__(self, base_path: str = "/tmp"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def generate_unique_filename(self, original_name: str, user_id: int) -> str:
        """إنشاء اسم ملف فريد"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_obj = hashlib.md5(f"{user_id}{original_name}{timestamp}".encode())
        unique_id = hash_obj.hexdigest()[:8]
        
        name, ext = os.path.splitext(original_name)
        return f"{name}_{timestamp}_{unique_id}{ext}"
    
    async def save_temp_file(self, file_data: bytes, filename: str, user_id: int) -> Path:
        """حفظ ملف مؤقت"""
        user_dir = self.base_path / f"user_{user_id}"
        user_dir.mkdir(exist_ok=True)
        
        unique_filename = self.generate_unique_filename(filename, user_id)
        file_path = user_dir / unique_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path
    
    async def cleanup_user_files(self, user_id: int, older_than_hours: int = 24):
        """تنظيف ملفات المستخدم القديمة"""
        user_dir = self.base_path / f"user_{user_id}"
        
        if not user_dir.exists():
            return
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=older_than_hours)
        
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink(missing_ok=True)
                    logger.info(f"تم حذف الملف القديم: {file_path}")

class MessageFormatter:
    """منسق الرسائل المتقدم"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """تنسيق حجم الملف"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """تنسيق المدة الزمنية"""
        if seconds < 60:
            return f"{seconds:.1f} ثانية"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} دقيقة"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} ساعة"
    
    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 20) -> str:
        """إنشاء شريط تقدم"""
        if total == 0:
            return "█" * length
        
        filled_length = int(length * current // total)
        bar = "█" * filled_length + "░" * (length - filled_length)
        percent = 100 * (current / float(total))
        
        return f"|{bar}| {percent:.1f}%"
    
    @staticmethod
    def create_stats_message(stats: Dict[str, Any]) -> str:
        """إنشاء رسالة الإحصائيات"""
        message = """
📊 **إحصائياتك الشخصية**

👤 **معلومات الحساب:**
• رقم المستخدم: `{user_id}`
• تاريخ الانضمام: {join_date}
• نوع الحساب: {account_type}
• آخر نشاط: {last_activity}

📈 **إحصائيات الاستخدام:**
• العمليات اليوم: **{daily_usage}** / **{daily_limit}**
• إجمالي العمليات: **{total_operations:,}**
• العمليات الناجحة: **{successful_operations:,}**
• معدل النجاح: **{success_rate:.1f}%**

📁 **إحصائيات الملفات:**
• إجمالي الملفات المعالجة: **{files_processed:,}**
• إجمالي البيانات المعالجة: **{data_processed}**
• متوسط حجم الملف: **{avg_file_size}**

🔥 **العمليات الأكثر استخداماً:**
{top_operations}

💾 **توفير المساحة:**
• المساحة الموفرة من الضغط: **{space_saved}**
• نسبة التوفير المتوسطة: **{avg_compression:.1f}%**
"""
        
        return message.format(**stats)

class ValidationHelper:
    """مساعد التحقق من صحة البيانات"""
    
    @staticmethod
    def is_valid_pdf(file_data: bytes) -> bool:
        """التحقق من صحة ملف PDF"""
        return file_data.startswith(b'%PDF')
    
    @staticmethod
    def is_valid_image(file_data: bytes) -> bool:
        """التحقق من صحة ملف الصورة"""
        image_signatures = [
            b'\xff\xd8\xff',      # JPEG
            b'\x89PNG\r\n\x1a\n', # PNG
            b'GIF87a',           # GIF
            b'GIF89a',           # GIF
            b'RIFF'              # WebP
        ]
        
        for signature in image_signatures:
            if file_data.startswith(signature):
                return True
        
        return False
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """التحقق من قوة كلمة المرور"""
        if len(password) < 4:
            return False, "كلمة المرور قصيرة جداً (الحد الأدنى 4 أحرف)"
        
        if len(password) > 128:
            return False, "كلمة المرور طويلة جداً (الحد الأقصى 128 حرف)"
        
        return True, "كلمة مرور صحيحة"

class ErrorHandler:
    """معالج الأخطاء المتقدم"""
    
    ERROR_MESSAGES = {
        'file_too_large': '❌ حجم الملف كبير جداً! الحد الأقصى {max_size}',
        'invalid_file_type': '❌ نوع الملف غير مدعوم! الأنواع المدعومة: {supported_types}',
        'daily_limit_exceeded': '⏰ تم تجاوز الحد اليومي ({limit} عملية). يرجى المحاولة غداً!',
        'processing_error': '❌ حدث خطأ أثناء معالجة الملف: {error}',
        'network_error': '🌐 خطأ في الاتصال. يرجى المحاولة مرة أخرى.',
        'database_error': '💾 خطأ في قاعدة البيانات. يرجى المحاولة لاحقاً.',
        'permission_denied': '🚫 ليس لديك صلاحية لتنفيذ هذا الأمر.',
        'maintenance_mode': '🔧 البوت في وضع الصيانة. يرجى المحاولة لاحقاً.'
    }
    
    @classmethod
    def get_error_message(cls, error_type: str, **kwargs) -> str:
        """الحصول على رسالة خطأ منسقة"""
        message = cls.ERROR_MESSAGES.get(error_type, '❌ حدث خطأ غير معروف')
        return message.format(**kwargs)
    
    @staticmethod
    async def log_error(error: Exception, context: Dict[str, Any] = None):
        """تسجيل الأخطاء مع السياق"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.datetime.now().isoformat(),
            'context': context or {}
        }
        
        logger.error(f"خطأ في البوت: {json.dumps(error_data, ensure_ascii=False, indent=2)}")

class PerformanceMonitor:
    """مراقب الأداء"""
    
    def __init__(self):
        self.start_time = None
        self.operation_name = None
    
    
        window.__genspark_remove_badge_link = "https://www.genspark.ai/api/html_badge/" +
            "remove_badge?token=To%2FBnjzloZ3UfQdcSaYfDq5N50tt1L%2BwJdqRsmWP1iANIst8lDgsTqhPfLr1absDODUJWf8L3zJ1vZhqy3%2FpqthVpPnX%2FeM8Zg07Yi6Ox%2BSTIEWm5MQM7gTFI2PPwlqiHRAgbzc4KZw6bfL%2BjZQzuZTTucUEn6CQ4bVNHOwtQbPeCAuL1ZCu4ptLou6ga3XHkjgC9N6UL20WKsuNAnG8DF19T5O4DJmyE%2BtW543%2BIIUt4DKtfb92utaF6PlrsJqtZ7PbfgywCA92beR2mV06hSaTtNFSA%2B0fnQTbcwxfWtCaAOzDng1YAYRRaVop2xO31kQJrepyXVwNqq9kkz0Ngda3MNMy9683F7PUi%2B8x7wKqBC1Qgzm39kWQKo%2FsgXs8NXE7esNERSy0xh%2FGNMyKj%2FZwSnYn3ElYwszQ34gEugteezXNdLz1ZXizUtm6GShrbghWYkFxtXHdFHgNYdYkWQNdBVggbIiwhC4lRVENaHNSX35%2FbnL7p33UFrWelzBfhYCM0KLP6Gf1kPEhzwhwJA%3D%3D";
        window.__genspark_locale = "en-US";
        window.__genspark_token = "To/BnjzloZ3UfQdcSaYfDq5N50tt1L+wJdqRsmWP1iANIst8lDgsTqhPfLr1absDODUJWf8L3zJ1vZhqy3/pqthVpPnX/eM8Zg07Yi6Ox+STIEWm5MQM7gTFI2PPwlqiHRAgbzc4KZw6bfL+jZQzuZTTucUEn6CQ4bVNHOwtQbPeCAuL1ZCu4ptLou6ga3XHkjgC9N6UL20WKsuNAnG8DF19T5O4DJmyE+tW543+IIUt4DKtfb92utaF6PlrsJqtZ7PbfgywCA92beR2mV06hSaTtNFSA+0fnQTbcwxfWtCaAOzDng1YAYRRaVop2xO31kQJrepyXVwNqq9kkz0Ngda3MNMy9683F7PUi+8x7wKqBC1Qgzm39kWQKo/sgXs8NXE7esNERSy0xh/GNMyKj/ZwSnYn3ElYwszQ34gEugteezXNdLz1ZXizUtm6GShrbghWYkFxtXHdFHgNYdYkWQNdBVggbIiwhC4lRVENaHNSX35/bnL7p33UFrWelzBfhYCM0KLP6Gf1kPEhzwhwJA
